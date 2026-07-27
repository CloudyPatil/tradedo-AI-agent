# E:\tradedo\app\backend\data_pipeline\sentiment.py

import os
import json
import logging
from typing import List, Dict
from utils.llm_manager import llm_call

logger = logging.getLogger("tradedo.sentiment")


def analyze_sentiment(articles: List[Dict]) -> Dict:
    """Analyze news sentiment using LLM pool."""
    if not articles:
        return {
            "score": 0.0,
            "label": "NEUTRAL",
            "reasoning": "No news found",
            "articles_analyzed": 0,
            "risk_flag": False,
        }
    
    # Build compact news text
    news_text = ""
    for i, article in enumerate(articles[:8], 1):
        news_text += f"{i}. {article['title']}\n"
        if article.get("summary"):
            news_text += f"   {article['summary'][:150]}\n"
    
    prompt = f"""Analyze these financial news headlines and return JSON only.

NEWS:
{news_text}

Return ONLY this JSON (no other text):
{{
  "sentiment_score": <float -1.0 to 1.0>,
  "sentiment_label": "<VERY_POSITIVE|POSITIVE|NEUTRAL|NEGATIVE|VERY_NEGATIVE>",
  "key_positive": "<one line or 'None'>",
  "key_negative": "<one line or 'None'>",
  "reasoning": "<2 sentences max>",
  "risk_flag": <true or false>
}}"""

    raw = llm_call(prompt, max_tokens=300, temperature=0.1)
    
    if not raw:
        return _fallback_sentiment(articles)
    
    try:
        # Strip markdown if present
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        
        result = json.loads(raw)
        result["articles_analyzed"] = len(articles)
        
        # Normalize field names
        result["score"] = result.pop("sentiment_score", 0)
        result["label"] = result.pop("sentiment_label", "NEUTRAL")
        
        return result
    
    except Exception as e:
        logger.error(f"JSON parse failed: {e}")
        return _fallback_sentiment(articles)


def generate_trade_reasoning(prediction: Dict, sentiment: Dict) -> str:
    """Generate AI reasoning for a trade signal."""
    prompt = f"""You are TRADEDO AI. Explain this trade signal in 2-3 sentences.
Be specific and factual. No disclaimers.

Signal: {prediction.get('signal')} ({prediction.get('strength')})
Symbol: {prediction.get('symbol')}
Confidence: {prediction.get('confidence_pct')}%
RSI: {prediction.get('indicators', {}).get('rsi')}
News: {sentiment.get('label')} - {sentiment.get('key_positive', 'N/A')}
Risk: {sentiment.get('key_negative', 'None')}

Explanation:"""
    
    result = llm_call(prompt, max_tokens=150, temperature=0.3)
    
    if not result:
        return f"{prediction.get('signal')} signal with {prediction.get('confidence_pct')}% confidence."
    
    return result


def _fallback_sentiment(articles: List[Dict]) -> Dict:
    """Keyword-based fallback when LLM fails."""
    positive_words = ["profit", "growth", "beat", "surge", "gain", "strong", "record", "upgrade"]
    negative_words = ["loss", "decline", "fall", "crash", "weak", "miss", "downgrade", "concern"]
    
    pos_count = neg_count = 0
    for article in articles:
        text = f"{article['title']} {article.get('summary', '')}".lower()
        pos_count += sum(1 for w in positive_words if w in text)
        neg_count += sum(1 for w in negative_words if w in text)
    
    total = pos_count + neg_count
    score = (pos_count - neg_count) / total if total > 0 else 0
    label = "POSITIVE" if score > 0.3 else "NEGATIVE" if score < -0.3 else "NEUTRAL"
    
    return {
        "score": round(score, 2),
        "label": label,
        "reasoning": "Keyword-based fallback",
        "articles_analyzed": len(articles),
        "risk_flag": neg_count > pos_count * 2,
    }


def batch_analyze_sentiments(articles_map: Dict[str, List[Dict]]) -> Dict[str, Dict]:
    """
    Analyze sentiment for multiple stocks in parallel.
    
    Args:
        articles_map: {"RELIANCE": [articles], "TCS": [articles]}
    
    Returns:
        {"RELIANCE": sentiment, "TCS": sentiment}
    """
    from utils.llm_manager import batch_llm_call
    
    # Build prompts for all stocks with articles
    symbols_with_news = [(s, arts) for s, arts in articles_map.items() if arts]
    
    if not symbols_with_news:
        return {s: _fallback_sentiment([]) for s in articles_map}
    
    prompts = []
    for symbol, articles in symbols_with_news:
        news_text = ""
        for i, article in enumerate(articles[:5], 1):
            news_text += f"{i}. {article['title']}\n"
        
        prompt = f"""Return ONLY JSON for {symbol} news:
{news_text}

{{
  "score": <-1.0 to 1.0>,
  "label": "<POSITIVE|NEUTRAL|NEGATIVE>",
  "risk_flag": <true|false>
}}"""
        prompts.append(prompt)
    
    # Batch process
    responses = batch_llm_call(prompts, max_tokens=100)
    
    results = {}
    for (symbol, articles), raw in zip(symbols_with_news, responses):
        try:
            if raw:
                if "```" in raw:
                    raw = raw.split("```")[1].replace("json", "").strip()
                data = json.loads(raw)
                data["articles_analyzed"] = len(articles)
                data["reasoning"] = "Batch analyzed"
                results[symbol] = data
            else:
                results[symbol] = _fallback_sentiment(articles)
        except:
            results[symbol] = _fallback_sentiment(articles)
    
    # Add empty results for stocks without news
    for symbol in articles_map:
        if symbol not in results:
            results[symbol] = _fallback_sentiment([])
    
    return results