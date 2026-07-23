# E:\tradedo\app\backend\data_pipeline\sentiment.py

import os
import json
import logging
from typing import List, Dict, Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("tradedo.sentiment")

# ─── Groq Client ──────────────────────────────────────────────
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Free Groq model — fast + capable
GROQ_MODEL = "llama3-8b-8192"


# ─── Sentiment Analyzer ───────────────────────────────────────
def analyze_sentiment(articles: List[Dict]) -> Dict:
    """
    Use Groq LLM to analyze sentiment of news articles.

    Input:  List of news article dicts
    Output: Sentiment score + label + reasoning

    Groq is used ONLY for text classification here
    No price prediction — just sentiment reading
    """
    if not articles:
        return {
            "score":     0.0,
            "label":     "NEUTRAL",
            "reasoning": "No news found for analysis",
            "articles_analyzed": 0,
        }

    # Build compact news summary for LLM
    news_text = ""
    for i, article in enumerate(articles[:8], 1):  # Max 8 articles
        news_text += f"{i}. {article['title']}\n"
        if article.get("summary"):
            news_text += f"   {article['summary'][:150]}\n"

    # Structured prompt — constrained output, no hallucination
    prompt = f"""You are a financial news sentiment analyzer.

Analyze these news headlines/summaries and return a JSON response.

NEWS:
{news_text}

Return ONLY this JSON (no extra text):
{{
  "sentiment_score": <float between -1.0 (very negative) to 1.0 (very positive)>,
  "sentiment_label": "<VERY_POSITIVE|POSITIVE|NEUTRAL|NEGATIVE|VERY_NEGATIVE>",
  "key_positive": "<one line: main positive factor or 'None'>",
  "key_negative": "<one line: main negative factor or 'None'>",
  "reasoning": "<2 sentences max explaining the score>",
  "risk_flag": <true if any major risk detected, false otherwise>
}}"""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,    # Low temp = consistent, factual
            max_tokens=300,
        )

        raw = response.choices[0].message.content.strip()

        

        # Handle cases where LLM adds markdown code blocks
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        result = json.loads(raw)

        result["articles_analyzed"] = len(articles)
        logger.info(
            f"Sentiment: {result['sentiment_label']} "
            f"(score: {result['sentiment_score']})"
        )
        return result

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed: {e}\nRaw: {raw}")
        return _fallback_sentiment(articles)

    except Exception as e:
        logger.error(f"Groq sentiment error: {e}")
        return _fallback_sentiment(articles)


def _fallback_sentiment(articles: List[Dict]) -> Dict:
    """
    Simple keyword-based fallback if Groq fails.
    No external dependency — works offline.
    """
    positive_words = [
        "profit", "growth", "beat", "surge", "rally", "gain",
        "strong", "record", "upgrade", "positive", "bullish",
        "buy", "outperform", "expansion", "deal", "win"
    ]
    negative_words = [
        "loss", "decline", "fall", "crash", "weak", "miss",
        "downgrade", "negative", "bearish", "sell", "risk",
        "concern", "drop", "cut", "layoff", "fraud", "penalty"
    ]

    pos_count = 0
    neg_count = 0

    for article in articles:
        text = f"{article['title']} {article.get('summary', '')}".lower()
        pos_count += sum(1 for w in positive_words if w in text)
        neg_count += sum(1 for w in negative_words if w in text)

    total = pos_count + neg_count
    if total == 0:
        score = 0.0
        label = "NEUTRAL"
    else:
        score = (pos_count - neg_count) / total
        if score > 0.3:
            label = "POSITIVE"
        elif score < -0.3:
            label = "NEGATIVE"
        else:
            label = "NEUTRAL"

    return {
        "score":             round(score, 2),
        "label":             label,
        "reasoning":         "Keyword-based fallback analysis",
        "articles_analyzed": len(articles),
        "risk_flag":         neg_count > pos_count * 2,
    }


def generate_trade_reasoning(prediction: Dict, sentiment: Dict) -> str:
    """
    Generate human-readable explanation for WHY a trade signal
    was generated. Uses Groq LLM for natural language.

    Input:  ML prediction dict + sentiment dict
    Output: 2-3 sentence explanation string
    """
    prompt = f"""You are TRADEDO, an AI trading assistant.
Explain this trading signal in 2-3 clear sentences.
Be specific, factual, mention the key indicators.
Do NOT make price predictions. Do NOT add disclaimers.

Signal Data:
- Symbol: {prediction.get('symbol')}
- Signal: {prediction.get('signal')} ({prediction.get('strength')})
- Confidence: {prediction.get('confidence_pct')}%
- RSI: {prediction.get('indicators', {}).get('rsi')}
- MACD: {prediction.get('indicators', {}).get('macd')}
- Returns 5D: {prediction.get('indicators', {}).get('returns_5d', prediction.get('indicators', {}).get('returns_5'))}%
- News Sentiment: {sentiment.get('label')} (score: {sentiment.get('score')})
- Key Positive: {sentiment.get('key_positive', 'None')}
- Key Risk: {sentiment.get('key_negative', 'None')}

Write the explanation now (2-3 sentences only):"""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=150,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"Trade reasoning error: {e}")
        signal = prediction.get('signal', 'HOLD')
        conf   = prediction.get('confidence_pct', 0)
        return (
            f"ML model signals {signal} with {conf}% confidence. "
            f"News sentiment is {sentiment.get('label', 'neutral')}. "
            f"Please review indicators before trading."
        )


# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing sentiment analyzer...")

    test_articles = [
        {
            "title": "Reliance Q3 profit beats estimates by 15%",
            "summary": "Reliance Industries reported strong quarterly results",
            "source": "ET"
        },
        {
            "title": "RIL announces major green energy investment",
            "summary": "Mukesh Ambani led company plans ₹50,000 crore investment",
            "source": "Mint"
        },
        {
            "title": "Oil prices rise, may impact Reliance margins",
            "summary": "Crude oil surges on geopolitical tensions",
            "source": "BS"
        }
    ]

    result = analyze_sentiment(test_articles)
    print(f"\nSentiment: {result['label']}")
    print(f"Score: {result['score']}")
    print(f"Reasoning: {result['reasoning']}")
    print(f"Risk Flag: {result['risk_flag']}")