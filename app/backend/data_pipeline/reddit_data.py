# E:\tradedo\app\backend\data_pipeline\reddit_data.py

"""
Reddit sentiment scraper for Indian stock market discussion.
Uses free Reddit API (PRAW).
"""

import os
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False

load_dotenv()
logger = logging.getLogger("tradedo.reddit")


# ─── Config ───────────────────────────────────────────────────
INDIAN_STOCK_SUBREDDITS = [
    "IndianStockMarket",
    "IndianStreetBets",
    "IndiaInvestments",
    "DalalStreetTalks",
    "StockMarketIndia",
]

GLOBAL_STOCK_SUBREDDITS = [
    "stocks",
    "wallstreetbets",
    "investing",
]

# Sentiment keywords for scoring
BULLISH_WORDS = [
    "bullish", "buy", "long", "moon", "rocket", "up", "gain", "profit",
    "breakout", "rally", "surge", "strong", "positive", "growth", "target",
    "hold", "accumulate", "undervalued", "momentum", "green", "🚀", "📈",
]

BEARISH_WORDS = [
    "bearish", "sell", "short", "crash", "down", "loss", "dump", "fall",
    "breakdown", "weak", "negative", "decline", "avoid", "exit", "risk",
    "overvalued", "correction", "red", "🔴", "📉", "puts",
]


class RedditScraper:
    """Reddit scraper with sentiment analysis."""
    
    def __init__(self):
        self.reddit = None
        self._init_client()
    
    def _init_client(self):
        """Initialize Reddit client."""
        if not PRAW_AVAILABLE:
            logger.error("praw not installed. Run: pip install praw")
            return
        
        client_id     = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent    = os.getenv("REDDIT_USER_AGENT", "TradeAgent/1.0")
        
        if not client_id or not client_secret:
            logger.warning("⚠️ Reddit credentials missing in .env")
            return
        
        try:
            self.reddit = praw.Reddit(
                client_id     = client_id,
                client_secret = client_secret,
                user_agent    = user_agent,
                check_for_async = False,
            )
            self.reddit.read_only = True
            logger.info("✅ Reddit client initialized")
        except Exception as e:
            logger.error(f"Reddit init failed: {e}")
    
    def is_available(self) -> bool:
        return self.reddit is not None
    
    def search_stock_mentions(
        self,
        symbol: str,
        max_posts: int = 15,
        days_back: int = 3,
    ) -> List[Dict]:
        """
        Search Reddit for posts mentioning a stock.
        
        Returns list of posts with metadata.
        """
        if not self.is_available():
            return []
        
        # Clean symbol
        clean = symbol.replace(".NS", "").replace(".BO", "").upper()
        
        # Get company aliases for better matching
        aliases = self._get_company_aliases(clean)
        search_terms = " OR ".join(f'"{a}"' for a in aliases)
        
        posts = []
        cutoff_time = datetime.now() - timedelta(days=days_back)
        
        for sub_name in INDIAN_STOCK_SUBREDDITS:
            try:
                subreddit = self.reddit.subreddit(sub_name)
                
                # Search posts
                for submission in subreddit.search(
                    search_terms, 
                    sort="new",
                    time_filter="week",
                    limit=max_posts // len(INDIAN_STOCK_SUBREDDITS) + 2
                ):
                    post_time = datetime.fromtimestamp(submission.created_utc)
                    if post_time < cutoff_time:
                        continue
                    
                    # Check if actually mentions the stock
                    text = f"{submission.title} {submission.selftext}".lower()
                    if not any(a.lower() in text for a in aliases):
                        continue
                    
                    posts.append({
                        "title":      submission.title,
                        "text":       submission.selftext[:500],
                        "score":      submission.score,
                        "upvote_ratio": submission.upvote_ratio,
                        "comments":   submission.num_comments,
                        "subreddit":  sub_name,
                        "url":        f"https://reddit.com{submission.permalink}",
                        "created":    post_time.isoformat(),
                        "symbol":     clean,
                    })
                    
                    if len(posts) >= max_posts:
                        break
                
            except Exception as e:
                logger.warning(f"Reddit search failed in r/{sub_name}: {e}")
                continue
            
            if len(posts) >= max_posts:
                break
        
        logger.info(f"Reddit: {len(posts)} posts for {clean}")
        return posts
    
    def _get_company_aliases(self, symbol: str) -> List[str]:
        """Common name variations for search."""
        aliases_map = {
            "RELIANCE":    ["Reliance", "RIL", "Ambani"],
            "TCS":         ["TCS", "Tata Consultancy"],
            "HDFCBANK":    ["HDFC Bank", "HDFCBank"],
            "INFY":        ["Infosys", "Infy"],
            "WIPRO":       ["Wipro"],
            "TATAMOTORS":  ["Tata Motors", "TataMotors", "TML"],
            "ADANIENT":    ["Adani", "Adani Enterprises"],
            "ICICIBANK":   ["ICICI Bank", "ICICI"],
            "SBIN":        ["SBI", "State Bank"],
            "BAJFINANCE":  ["Bajaj Finance", "BajajFin"],
            "HDFCLIFE":    ["HDFC Life"],
            "KOTAKBANK":   ["Kotak", "Kotak Bank"],
            "AXISBANK":    ["Axis Bank", "Axis"],
            "HINDUNILVR":  ["HUL", "Hindustan Unilever"],
            "ITC":         ["ITC"],
            "BHARTIARTL":  ["Airtel", "Bharti Airtel"],
            "MARUTI":      ["Maruti", "Maruti Suzuki"],
            "TITAN":       ["Titan"],
            "SUNPHARMA":   ["Sun Pharma", "SunPharma"],
            "HCLTECH":     ["HCL Tech", "HCL"],
            "TECHM":       ["Tech Mahindra", "TechM"],
            "ASIANPAINT":  ["Asian Paints"],
            "M&M":         ["Mahindra", "M&M"],
            "NTPC":        ["NTPC"],
            "POWERGRID":   ["Power Grid", "PowerGrid"],
            "COALINDIA":   ["Coal India"],
            "DIVISLAB":    ["Divis Lab", "Divi's"],
            "NESTLEIND":   ["Nestle"],
            "ULTRACEMCO":  ["Ultratech", "UltraTechCement"],
            "IRCTC":       ["IRCTC"],
            "ZOMATO":      ["Zomato"],
            "PAYTM":       ["Paytm"],
            "IRFC":        ["IRFC"],
            "IREDA":       ["IREDA"],
            "SUZLON":      ["Suzlon"],
            "YESBANK":     ["Yes Bank", "YesBank"],
            "IDEA":        ["Vodafone Idea", "Vi", "Idea"],
        }
        
        # Default: use symbol itself
        return aliases_map.get(symbol, [symbol])
    
    def analyze_sentiment(self, posts: List[Dict]) -> Dict:
        """
        Analyze sentiment of Reddit posts using keyword matching + engagement.
        Fast, no LLM needed.
        """
        if not posts:
            return {
                "score":           0.0,
                "label":           "NEUTRAL",
                "post_count":      0,
                "total_engagement": 0,
                "buzz_score":      0,
                "top_posts":       [],
            }
        
        total_bullish = 0
        total_bearish = 0
        total_engagement = 0
        weighted_score = 0
        
        scored_posts = []
        
        for post in posts:
            text = f"{post['title']} {post.get('text', '')}".lower()
            
            bullish = sum(1 for w in BULLISH_WORDS if w in text)
            bearish = sum(1 for w in BEARISH_WORDS if w in text)
            
            # Engagement = upvotes + (comments * 2)
            engagement = post['score'] + (post['comments'] * 2)
            engagement = max(engagement, 1)  # Avoid divide by zero
            
            # Post score: -1 to +1
            total = bullish + bearish
            post_sentiment = (bullish - bearish) / total if total > 0 else 0
            
            # Weight by engagement (popular posts count more)
            weighted_score += post_sentiment * engagement
            total_engagement += engagement
            
            total_bullish += bullish
            total_bearish += bearish
            
            scored_posts.append({
                **post,
                "bullish_words": bullish,
                "bearish_words": bearish,
                "sentiment":     round(post_sentiment, 2),
                "engagement":    engagement,
            })
        
        # Final weighted score
        final_score = weighted_score / total_engagement if total_engagement > 0 else 0
        final_score = max(-1.0, min(1.0, final_score))
        
        # Label
        if final_score > 0.3:
            label = "BULLISH"
        elif final_score < -0.3:
            label = "BEARISH"
        else:
            label = "NEUTRAL"
        
        # Buzz score (0-100): how much people are talking
        # Higher engagement + more posts = higher buzz
        buzz_score = min(100, (len(posts) * 5) + (total_engagement // 20))
        
        # Top 3 posts by engagement
        top_posts = sorted(scored_posts, key=lambda x: x["engagement"], reverse=True)[:3]
        
        return {
            "score":            round(final_score, 3),
            "label":            label,
            "post_count":       len(posts),
            "total_engagement": total_engagement,
            "buzz_score":       buzz_score,
            "bullish_signals":  total_bullish,
            "bearish_signals":  total_bearish,
            "top_posts":        [
                {
                    "title":      p["title"][:100],
                    "score":      p["score"],
                    "comments":   p["comments"],
                    "sentiment":  p["sentiment"],
                    "url":        p["url"],
                }
                for p in top_posts
            ],
        }


# ─── Global instance ──────────────────────────────────────────
_scraper: Optional[RedditScraper] = None

def get_reddit_scraper() -> RedditScraper:
    global _scraper
    if _scraper is None:
        _scraper = RedditScraper()
    return _scraper


def fetch_reddit_sentiment(symbol: str) -> Dict:
    """Main entry point — fetch and analyze Reddit sentiment."""
    scraper = get_reddit_scraper()
    
    if not scraper.is_available():
        return {
            "score":       0.0,
            "label":       "UNAVAILABLE",
            "post_count":  0,
            "buzz_score":  0,
            "error":       "Reddit not configured",
        }
    
    posts = scraper.search_stock_mentions(symbol, max_posts=15, days_back=3)
    return scraper.analyze_sentiment(posts)


# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    result = fetch_reddit_sentiment("RELIANCE")
    
    print("\n📱 Reddit Sentiment Analysis")
    print("=" * 50)
    print(f"Score:      {result.get('score')}")
    print(f"Label:      {result.get('label')}")
    print(f"Posts:      {result.get('post_count')}")
    print(f"Engagement: {result.get('total_engagement')}")
    print(f"Buzz:       {result.get('buzz_score')}/100")
    print(f"\nBullish signals: {result.get('bullish_signals')}")
    print(f"Bearish signals: {result.get('bearish_signals')}")
    
    if result.get('top_posts'):
        print("\n🔥 Top Posts:")
        for i, p in enumerate(result['top_posts'], 1):
            print(f"{i}. [{p['score']}⬆ {p['comments']}💬] {p['title']}")