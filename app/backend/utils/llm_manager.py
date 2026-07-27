# E:\tradedo\app\backend\utils\llm_manager.py

"""
Multi-key Groq LLM manager with rotation, rate limiting,
and automatic fallback. Uses ALL your API keys efficiently.
"""

import os
import time
import logging
import threading
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
logger = logging.getLogger("tradedo.llm")


# ─── Rate Limit Config (Groq Free Tier) ───────────────────────
REQUESTS_PER_MINUTE = 28    # Slightly under 30 for safety
TOKENS_PER_MINUTE   = 5500  # Under 6000 limit for safety


class GroqKeyPool:
    """
    Manages a pool of Groq API keys with smart rotation.
    
    Features:
    - Round-robin key selection
    - Per-key rate limit tracking
    - Automatic failover on errors
    - Thread-safe
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._keys = self._load_keys()
        self._clients = {k: Groq(api_key=k) for k in self._keys}
        
        # Track usage per key
        self._request_times: Dict[str, deque] = defaultdict(deque)
        self._token_usage:   Dict[str, deque] = defaultdict(deque)
        self._error_count:   Dict[str, int]   = defaultdict(int)
        self._current_idx    = 0
        
        logger.info(f"✅ LLM Pool initialized with {len(self._keys)} keys")
    
    def _load_keys(self) -> List[str]:
        """Load all API keys from environment."""
        # Multi-key setup
        keys_str = os.getenv("GROQ_API_KEYS", "")
        keys = [k.strip() for k in keys_str.split(",") if k.strip()]
        
        # Fallback to single key
        if not keys:
            single_key = os.getenv("GROQ_API_KEY")
            if single_key:
                keys = [single_key]
        
        if not keys:
            raise ValueError("No Groq API keys configured!")
        
        return keys
    
    def _cleanup_old_records(self, key: str):
        """Remove records older than 1 minute."""
        cutoff = time.time() - 60
        
        # Clean request times
        while self._request_times[key] and self._request_times[key][0] < cutoff:
            self._request_times[key].popleft()
        
        # Clean token usage
        while self._token_usage[key] and self._token_usage[key][0][0] < cutoff:
            self._token_usage[key].popleft()
    
    def _is_key_available(self, key: str) -> bool:
        """Check if a key has capacity for another request."""
        self._cleanup_old_records(key)
        
        # Check request rate
        if len(self._request_times[key]) >= REQUESTS_PER_MINUTE:
            return False
        
        # Check token rate
        total_tokens = sum(t[1] for t in self._token_usage[key])
        if total_tokens >= TOKENS_PER_MINUTE:
            return False
        
        # Skip keys with too many recent errors
        if self._error_count[key] >= 3:
            return False
        
        return True
    
    def get_available_key(self) -> Optional[str]:
        """
        Get the next available key using round-robin.
        Returns None if all keys are rate-limited.
        """
        with self._lock:
            attempts = 0
            
            while attempts < len(self._keys):
                key = self._keys[self._current_idx]
                self._current_idx = (self._current_idx + 1) % len(self._keys)
                
                if self._is_key_available(key):
                    return key
                
                attempts += 1
            
            return None   # All keys busy
    
    def record_usage(self, key: str, tokens: int):
        """Record usage for a key."""
        with self._lock:
            now = time.time()
            self._request_times[key].append(now)
            self._token_usage[key].append((now, tokens))
            # Reset error count on success
            if self._error_count[key] > 0:
                self._error_count[key] = max(0, self._error_count[key] - 1)
    
    def record_error(self, key: str):
        """Record error for a key."""
        with self._lock:
            self._error_count[key] += 1
    
    def get_stats(self) -> Dict:
        """Get current pool statistics."""
        with self._lock:
            stats = {
                "total_keys": len(self._keys),
                "keys": []
            }
            
            for key in self._keys:
                self._cleanup_old_records(key)
                masked_key = f"{key[:8]}...{key[-4:]}"
                
                stats["keys"].append({
                    "key":       masked_key,
                    "requests":  len(self._request_times[key]),
                    "req_limit": REQUESTS_PER_MINUTE,
                    "tokens":    sum(t[1] for t in self._token_usage[key]),
                    "tok_limit": TOKENS_PER_MINUTE,
                    "errors":    self._error_count[key],
                    "available": self._is_key_available(key),
                })
            
            return stats


# ─── Global Pool Instance ─────────────────────────────────────
_pool: Optional[GroqKeyPool] = None

def get_pool() -> GroqKeyPool:
    global _pool
    if _pool is None:
        _pool = GroqKeyPool()
    return _pool


# ─── High-Level LLM Call Function ─────────────────────────────
def llm_call(
    prompt: str,
    model: str = "llama-3.1-8b-instant",
    max_tokens: int = 500,
    temperature: float = 0.2,
    max_retries: int = 3,
    wait_on_limit: bool = True,
) -> Optional[str]:
    """
    Make an LLM call using the key pool.
    Auto-retries with different keys on failure.
    """
    pool = get_pool()
    
    for attempt in range(max_retries):
        # Get available key
        key = pool.get_available_key()
        
        if key is None:
            if wait_on_limit:
                wait_time = 5
                logger.warning(f"All keys rate-limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                logger.warning("All keys rate-limited. Skipping.")
                return None
        
        # Estimate tokens (rough: 1 token ~ 4 chars)
        estimated_tokens = len(prompt) // 4 + max_tokens
        
        try:
            client = pool._clients[key]
            response = client.chat.completions.create(
                model      = model,
                messages   = [{"role": "user", "content": prompt}],
                max_tokens = max_tokens,
                temperature = temperature,
            )
            
            # Record actual usage
            actual_tokens = response.usage.total_tokens if response.usage else estimated_tokens
            pool.record_usage(key, actual_tokens)
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            error_msg = str(e).lower()
            pool.record_error(key)
            
            if "rate" in error_msg or "429" in error_msg:
                logger.warning(f"Key {key[:8]}... rate limited")
                time.sleep(2)
                continue
            
            if attempt == max_retries - 1:
                logger.error(f"LLM call failed after {max_retries} attempts: {e}")
                return None
            
            logger.warning(f"LLM attempt {attempt+1} failed: {e}")
            time.sleep(1)
    
    return None


def batch_llm_call(
    prompts: List[str],
    model: str = "llama-3.1-8b-instant",
    max_tokens: int = 500,
) -> List[Optional[str]]:
    """
    Process multiple prompts in parallel using all available keys.
    Much faster than sequential calls.
    """
    from concurrent.futures import ThreadPoolExecutor
    
    pool = get_pool()
    max_workers = min(len(pool._keys), 10)
    
    results = [None] * len(prompts)
    
    def process_one(idx_prompt):
        idx, prompt = idx_prompt
        return idx, llm_call(prompt, model, max_tokens)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for idx, result in executor.map(process_one, enumerate(prompts)):
            results[idx] = result
    
    return results


# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    pool = get_pool()
    print(f"\nLoaded {len(pool._keys)} API keys\n")
    
    # Test single call
    result = llm_call("Say 'Hello TRADEDO' in 5 words.")
    print(f"Single: {result}\n")
    
    # Test batch call
    prompts = [f"Say number {i}" for i in range(1, 6)]
    results = batch_llm_call(prompts, max_tokens=20)
    for i, r in enumerate(results):
        print(f"Batch {i+1}: {r}")
    
    # Show stats
    print("\n📊 Pool Stats:")
    import json
    print(json.dumps(pool.get_stats(), indent=2))