# E:\tradedo\app\backend\data_pipeline\price_provider.py

"""
UNIFIED PRICE PROVIDER
Abstract interface for all price sources.
Auto-fallback: Upstox (primary) → yfinance (backup)

This is the SINGLE source of prices for entire app.
Change providers without touching any other code.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("tradedo.provider")


# ═══════════════════════════════════════════════════════════════
#   ABSTRACT PROVIDER (Interface)
# ═══════════════════════════════════════════════════════════════

class PriceProvider(ABC):
    """Base interface all price providers must implement."""
    
    @abstractmethod
    def get_ltp(self, symbol: str) -> Optional[float]:
        """Get last traded price for a symbol."""
        pass
    
    @abstractmethod
    def get_multiple_ltp(self, symbols: List[str]) -> Dict[str, float]:
        """Get LTP for multiple symbols."""
        pass
    
    @abstractmethod
    def get_quote(self, symbol: str) -> Optional[Dict]:
        """Get full market quote (OHLC, volume)."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is ready to serve requests."""
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Return source name for logging."""
        pass


# ═══════════════════════════════════════════════════════════════
#   UPSTOX PROVIDER (Real-time, primary)
# ═══════════════════════════════════════════════════════════════

class UpstoxProvider(PriceProvider):
    """Real-time prices from Upstox API."""
    
    def __init__(self):
        from data_pipeline.upstox_api import get_upstox_client
        self.client = get_upstox_client()
    
    def is_available(self) -> bool:
        return self.client.is_ready
    
    def get_source_name(self) -> str:
        return "upstox"
    
    def get_ltp(self, symbol: str) -> Optional[float]:
        result = self.client.get_ltp(symbol)
        if result:
            return result.get("last_price")
        return None
    
    def get_multiple_ltp(self, symbols: List[str]) -> Dict[str, float]:
        results = self.client.get_multiple_ltp(symbols)
        return {sym: data["last_price"] for sym, data in results.items()}
    
    def get_quote(self, symbol: str) -> Optional[Dict]:
        result = self.client.get_market_quote(symbol)
        if result:
            return {
                "symbol":     symbol,
                "last_price": result["last_price"],
                "volume":     result.get("volume", 0),
                "open":       result.get("ohlc", {}).get("open"),
                "high":       result.get("ohlc", {}).get("high"),
                "low":        result.get("ohlc", {}).get("low"),
                "close":      result.get("ohlc", {}).get("close"),
                "avg_price":  result.get("average_price"),
                "timestamp":  result.get("timestamp"),
                "source":     "upstox",
            }
        return None


# ═══════════════════════════════════════════════════════════════
#   YFINANCE PROVIDER (Backup, 15-min delayed)
# ═══════════════════════════════════════════════════════════════

class YFinanceProvider(PriceProvider):
    """Backup prices from yfinance (15-20 min delayed)."""
    
    def __init__(self):
        try:
            import yfinance as yf
            self.yf = yf
            self._available = True
        except ImportError:
            self._available = False
            logger.error("yfinance not installed")
    
    def is_available(self) -> bool:
        return self._available
    
    def get_source_name(self) -> str:
        return "yfinance"
    
    def get_ltp(self, symbol: str) -> Optional[float]:
        if not self._available:
            return None
        try:
            if not symbol.endswith(".NS"):
                symbol = symbol + ".NS"
            
            ticker = self.yf.Ticker(symbol)
            price = ticker.fast_info.get("last_price")
            return float(price) if price else None
        except Exception as e:
            logger.debug(f"yfinance LTP failed for {symbol}: {e}")
            return None
    
    def get_multiple_ltp(self, symbols: List[str]) -> Dict[str, float]:
        results = {}
        for sym in symbols:
            price = self.get_ltp(sym)
            if price:
                results[sym] = price
        return results
    
    def get_quote(self, symbol: str) -> Optional[Dict]:
        if not self._available:
            return None
        try:
            if not symbol.endswith(".NS"):
                symbol = symbol + ".NS"
            
            ticker = self.yf.Ticker(symbol)
            info = ticker.fast_info
            
            return {
                "symbol":     symbol,
                "last_price": float(info.get("last_price", 0)),
                "open":       float(info.get("open", 0)) if info.get("open") else None,
                "high":       float(info.get("day_high", 0)) if info.get("day_high") else None,
                "low":        float(info.get("day_low", 0)) if info.get("day_low") else None,
                "close":      float(info.get("regular_market_previous_close", 0)) if info.get("regular_market_previous_close") else None,
                "timestamp":  datetime.now().isoformat(),
                "source":     "yfinance",
            }
        except Exception as e:
            logger.debug(f"yfinance quote failed for {symbol}: {e}")
            return None


# ═══════════════════════════════════════════════════════════════
#   UNIFIED PROVIDER (Auto-fallback)
# ═══════════════════════════════════════════════════════════════

class UnifiedPriceProvider:
    """
    Smart provider that uses Upstox first, falls back to yfinance.
    This is the ONE class the rest of the app uses.
    """
    
    def __init__(self, prefer: str = "upstox"):
        """
        Args:
            prefer: "upstox" (real-time) or "yfinance" (backup)
        """
        self.prefer = prefer
        
        # Initialize both providers
        self.upstox = UpstoxProvider()
        self.yfinance = YFinanceProvider()
        
        # Log status
        logger.info(f"📊 Price Provider initialized:")
        logger.info(f"   Upstox:   {'✅' if self.upstox.is_available() else '❌'}")
        logger.info(f"   YFinance: {'✅' if self.yfinance.is_available() else '❌'}")
        logger.info(f"   Preferred: {self.prefer}")
    
    def _get_provider_order(self) -> List[PriceProvider]:
        """Get providers in priority order."""
        if self.prefer == "upstox" and self.upstox.is_available():
            return [self.upstox, self.yfinance]
        else:
            return [self.yfinance, self.upstox]
    
    def get_ltp(self, symbol: str) -> Optional[Dict]:
        """
        Get LTP with automatic fallback.
        Returns dict with price + source, or None if all fail.
        """
        for provider in self._get_provider_order():
            if not provider.is_available():
                continue
            
            price = provider.get_ltp(symbol)
            if price and price > 0:
                return {
                    "symbol":     symbol,
                    "last_price": price,
                    "source":     provider.get_source_name(),
                    "timestamp":  datetime.now().isoformat(),
                }
        
        return None
    
    def get_multiple_ltp(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get LTP for multiple stocks with fallback.

        A batch market-data response can omit an otherwise valid instrument
        (for example when the broker returns a differently encoded instrument
        key).  Do not treat that as a missing price: retry each omitted symbol
        through the same provider before falling through to the backup.
        """
        results = {}
        
        for provider in self._get_provider_order():
            if not provider.is_available():
                continue
            
            missing = [s for s in symbols if s not in results]
            if not missing:
                break
            
            fetched = provider.get_multiple_ltp(missing)
            source = provider.get_source_name()
            
            for sym, price in fetched.items():
                if price and price > 0:
                    results[sym] = {
                        "symbol":     sym,
                        "last_price": price,
                        "source":     source,
                        "timestamp":  datetime.now().isoformat(),
                    }

            # The individual endpoint is more reliable than a batch response
            # for an instrument whose response key cannot be mapped back to a
            # requested symbol.  This retry is intentionally only for symbols
            # omitted by the batch call, so healthy batch requests stay fast.
            for sym in [s for s in missing if s not in results]:
                try:
                    price = provider.get_ltp(sym)
                except Exception as exc:
                    logger.warning("Individual LTP retry failed for %s via %s: %s", sym, source, exc)
                    continue
                if price and price > 0:
                    results[sym] = {
                        "symbol": sym,
                        "last_price": price,
                        "source": source,
                        "timestamp": datetime.now().isoformat(),
                    }
        
        return results
    
    def get_quote(self, symbol: str) -> Optional[Dict]:
        """Get full quote with fallback."""
        for provider in self._get_provider_order():
            if not provider.is_available():
                continue
            
            quote = provider.get_quote(symbol)
            if quote and quote.get("last_price", 0) > 0:
                return quote
        
        return None
    
    def get_status(self) -> Dict:
        """Get provider status."""
        return {
            "preferred":         self.prefer,
            "upstox_available":  self.upstox.is_available(),
            "yfinance_available": self.yfinance.is_available(),
            "active_source":     "upstox" if (
                self.prefer == "upstox" and self.upstox.is_available()
            ) else "yfinance",
        }


# ═══════════════════════════════════════════════════════════════
#   GLOBAL SINGLETON
# ═══════════════════════════════════════════════════════════════

_global_provider: Optional[UnifiedPriceProvider] = None

def get_price_provider() -> UnifiedPriceProvider:
    """Get the global price provider (singleton)."""
    global _global_provider
    if _global_provider is None:
        _global_provider = UnifiedPriceProvider(prefer="upstox")
    return _global_provider


# ═══════════════════════════════════════════════════════════════
#   Convenience Functions
# ═══════════════════════════════════════════════════════════════

def get_live_price(symbol: str) -> Optional[float]:
    """Simplest way to get a live price."""
    provider = get_price_provider()
    result = provider.get_ltp(symbol)
    return result["last_price"] if result else None


def get_live_prices(symbols: List[str]) -> Dict[str, float]:
    """Get multiple live prices."""
    provider = get_price_provider()
    results = provider.get_multiple_ltp(symbols)
    return {sym: data["last_price"] for sym, data in results.items()}


# ═══════════════════════════════════════════════════════════════
#   Quick Test
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("UNIFIED PRICE PROVIDER TEST")
    print("="*60)
    
    provider = get_price_provider()
    
    # Status
    print("\n📊 Status:")
    status = provider.get_status()
    for k, v in status.items():
        print(f"   {k}: {v}")
    
    # Single price
    print("\n💰 Single LTP (RELIANCE):")
    result = provider.get_ltp("RELIANCE.NS")
    if result:
        print(f"   Price:  ₹{result['last_price']}")
        print(f"   Source: {result['source']}")
    
    # Multiple prices
    print("\n💰 Multiple LTPs:")
    symbols = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "WIPRO.NS"]
    results = provider.get_multiple_ltp(symbols)
    for sym, data in results.items():
        print(f"   {sym.replace('.NS', ''):12s} ₹{data['last_price']:>8.2f}  [{data['source']}]")
    
    # Full quote
    print("\n📈 Full Quote (TCS):")
    quote = provider.get_quote("TCS.NS")
    if quote:
        for k, v in quote.items():
            print(f"   {k}: {v}")
    
    # Convenience function
    print("\n⚡ Convenience function:")
    price = get_live_price("HDFCBANK.NS")
    print(f"   HDFCBANK live price: ₹{price}")
    
    print("\n" + "="*60)
    print("✅ Price Provider ready for entire app!")
    print("="*60)
