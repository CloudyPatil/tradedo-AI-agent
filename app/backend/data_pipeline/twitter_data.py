# E:\tradedo\app\backend\data_pipeline\twitter_data.py

"""
Twitter/X scraper with multiple fallback methods.
Since Twitter API is paid, we use scraping techniques.

Fallback order:
1. ntscraper (unofficial library)
2. Nitter instances (Twitter mirrors)
3. Google search for tweets
"""

import logging
import requests
import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

try:
    from ntscraper import Nitter
    NTSCRAPER_AVAILABLE = True
except ImportError:
    NTSCRAPER_AVAILABLE = False

logger = logging.getLogger("tradedo.twitter")


# ─── Config ───────────────────────────────────────────────────
MAX_TWEETS       = 15
DAYS_LOOKBACK    = 3

# Trusted Indian finance Twitter accounts
TRUSTED_ACCOUNTS = [
    "CNBCTV18Live", "ETMarkets", "moneycontrolcom", "livemint",
    "ZeeBusiness", "bsindia", "BloombergQuint", "financialexpress",
    "PRSundar64",     # Options guru
    "vishalmehta06",  # Market analyst
    "iamnitinbhatia", # Trading educator
    "caniravkaria",   # CA & investor
    "GuruSwarajya",   # Fundamental analyst
    "Ashishkyadav1",  # Trader
    "NSEIndia", "BSEIndia",   # Official exchanges
]

BULLISH_KEYWORDS = [
    "buy", "long", "bullish", "target", "upside", "breakout", "rally",
    "accumulate", "positive", "strong", "growth", "🚀", "📈", "moon",
    "call", "up", "gain", "pump"
]

BEARISH_KEYWORDS = [
    "sell", "short", "bearish", "avoid", "downside", "breakdown", "crash",
    "exit", "negative", "weak", "risk", "put", "down", "dump", "correction",
    "🔴", "📉", "fall"
]


class TwitterScraper:
    """Multi-method Twitter scraper with fallbacks."""
    
    def __init__(self):
        self.nitter = None
        self._init_nitter()
    
    def _init_nitter(self):
        """Initialize ntscraper if available."""
        if not NTSCRAPER_AVAILABLE:
            return
        
        try:
            self.nitter = Nitter(log_level=1, skip_instance_check=False)
            logger.info("✅ ntscraper initialized")
        except Exception as e:
            logger.warning(f"ntscraper init failed: {e}")
            self.nitter = None
    
    def search_tweets(self, query: str, max_tweets: int = MAX_TWEETS) -> List[Dict]:
        """
        Search tweets using best available method.
        Falls back through multiple sources.
        """
        # Method 1: ntscraper
        tweets = self._try_ntscraper(query, max_tweets)
        if tweets:
            logger.info(f"  ✓ ntscraper: {len(tweets)} tweets")
            return tweets
        
        # Method 2: Direct Nitter scraping
        tweets = self._try_nitter_direct(query, max_tweets)
        if tweets:
            logger.info(f"  ✓ nitter direct: {len(tweets)} tweets")
            return tweets
        
        # Method 3: Google search fallback
        tweets = self._try_google_search(query, max_tweets)
        if tweets:
            logger.info(f"  ✓ google search: {len(tweets)} tweets")
            return tweets
        
        logger.warning(f"  ✗ All Twitter methods failed for: {query}")
        return []
    
    def _try_ntscraper(self, query: str, max_tweets: int) -> List[Dict]:
        """Try ntscraper library."""
        if not self.nitter:
            return []
        
        try:
            result = self.nitter.get_tweets(
                query,
                mode="term",
                number=max_tweets,
                since=(datetime.now() - timedelta(days=DAYS_LOOKBACK)).strftime("%Y-%m-%d"),
            )
            
            tweets = []
            for tweet in result.get("tweets", []):
                if not tweet:
                    continue
                
                tweets.append({
                    "text":     tweet.get("text", ""),
                    "user":     tweet.get("user", {}).get("name", "unknown"),
                    "username": tweet.get("user", {}).get("username", ""),
                    "likes":    tweet.get("stats", {}).get("likes", 0),
                    "retweets": tweet.get("stats", {}).get("retweets", 0),
                    "replies":  tweet.get("stats", {}).get("comments", 0),
                    "date":     tweet.get("date", ""),
                    "url":      tweet.get("link", ""),
                    "source":   "ntscraper",
                })
            
            return tweets
        
        except Exception as e:
            logger.debug(f"ntscraper failed: {e}")
            return []
    
    def _try_nitter_direct(self, query: str, max_tweets: int) -> List[Dict]:
        """Try direct HTTP scraping from Nitter mirrors."""
        # Public Nitter instances (rotate through)
        nitter_instances = [
            "https://nitter.net",
            "https://nitter.privacydev.net",
            "https://nitter.poast.org",
            "https://nitter.projectsegfau.lt",
        ]
        
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        
        for instance in nitter_instances:
            try:
                url = f"{instance}/search?f=tweets&q={query}"
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.text, "html.parser")
                tweet_items = soup.find_all("div", class_="timeline-item", limit=max_tweets)
                
                tweets = []
                for item in tweet_items:
                    try:
                        # Extract user
                        user_link = item.find("a", class_="username")
                        username = user_link.get_text(strip=True).replace("@", "") if user_link else ""
                        
                        # Extract text
                        content_div = item.find("div", class_="tweet-content")
                        text = content_div.get_text(strip=True) if content_div else ""
                        
                        # Extract stats
                        stats_div = item.find("div", class_="tweet-stats")
                        likes = retweets = replies = 0
                        
                        if stats_div:
                            for stat in stats_div.find_all("span", class_="tweet-stat"):
                                icon = stat.find("div", class_="icon-container")
                                if not icon:
                                    continue
                                text_val = stat.get_text(strip=True)
                                if not text_val:
                                    continue
                                try:
                                    num = int(re.sub(r'[^\d]', '', text_val) or 0)
                                    if "heart" in str(icon):
                                        likes = num
                                    elif "retweet" in str(icon):
                                        retweets = num
                                    elif "comment" in str(icon):
                                        replies = num
                                except:
                                    pass
                        
                        if text:
                            tweets.append({
                                "text":     text[:500],
                                "user":     username,
                                "username": username,
                                "likes":    likes,
                                "retweets": retweets,
                                "replies":  replies,
                                "date":     "",
                                "url":      "",
                                "source":   "nitter_direct",
                            })
                    except Exception:
                        continue
                
                if tweets:
                    return tweets
            
            except Exception as e:
                logger.debug(f"Nitter {instance} failed: {e}")
                continue
        
        return []
    
    def _try_google_search(self, query: str, max_tweets: int) -> List[Dict]:
        """Fallback: Google search for tweets."""
        try:
            search_query = f"site:twitter.com OR site:x.com {query}"
            url = f"https://www.google.com/search?q={search_query}"
            
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            tweets = []
            # Google results are in various formats — try common patterns
            for result in soup.find_all("div", class_="g")[:max_tweets]:
                title_tag = result.find("h3")
                snippet_tag = result.find("div", class_=["VwiC3b", "s"])
                
                title = title_tag.get_text(strip=True) if title_tag else ""
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                
                # Extract username from title (usually "Name (@username)")
                user_match = re.search(r'\(@(\w+)\)', title)
                username = user_match.group(1) if user_match else "unknown"
                
                if snippet:
                    tweets.append({
                        "text":     snippet[:500],
                        "user":     username,
                        "username": username,
                        "likes":    0,  # Google doesn't show
                        "retweets": 0,
                        "replies":  0,
                        "date":     "",
                        "url":      "",
                        "source":   "google_search",
                    })
            
            return tweets
        
        except Exception as e:
            logger.debug(f"Google search failed: {e}")
            return []


# ─── Global instance ──────────────────────────────────────────
_scraper: Optional[TwitterScraper] = None

def get_scraper() -> TwitterScraper:
    global _scraper
    if _scraper is None:
        _scraper = TwitterScraper()
    return _scraper


# ─── Analysis Functions ───────────────────────────────────────
def analyze_tweets(tweets: List[Dict]) -> Dict:
    """Analyze sentiment from tweets."""
    if not tweets:
        return _empty_analysis()
    
    total_bullish = 0
    total_bearish = 0
    total_engagement = 0
    weighted_score = 0
    trusted_count = 0
    
    scored_tweets = []
    
    for tweet in tweets:
        text = tweet["text"].lower()
        
        bullish = sum(1 for w in BULLISH_KEYWORDS if w in text)
        bearish = sum(1 for w in BEARISH_KEYWORDS if w in text)
        
        # Engagement score
        engagement = tweet["likes"] + (tweet["retweets"] * 3) + tweet["replies"]
        engagement = max(engagement, 1)
        
        # Sentiment for this tweet
        total = bullish + bearish
        sentiment = (bullish - bearish) / total if total > 0 else 0
        
        # Trusted account bonus (3x weight)
        is_trusted = tweet["username"].lower() in [a.lower() for a in TRUSTED_ACCOUNTS]
        weight_mult = 3 if is_trusted else 1
        if is_trusted:
            trusted_count += 1
        
        weighted_score += sentiment * engagement * weight_mult
        total_engagement += engagement * weight_mult
        total_bullish += bullish
        total_bearish += bearish
        
        scored_tweets.append({
            **tweet,
            "sentiment":  round(sentiment, 2),
            "engagement": engagement,
            "is_trusted": is_trusted,
        })
    
    final_score = weighted_score / total_engagement if total_engagement > 0 else 0
    final_score = max(-1.0, min(1.0, final_score))
    
    # Label
    if final_score > 0.3:
        label = "BULLISH"
    elif final_score < -0.3:
        label = "BEARISH"
    else:
        label = "NEUTRAL"
    
    # Buzz score
    buzz = min(100, (len(tweets) * 4) + (total_engagement // 50))
    
    # Top tweets by engagement
    top_tweets = sorted(scored_tweets, key=lambda x: x["engagement"], reverse=True)[:3]
    
    return {
        "score":            round(final_score, 3),
        "label":            label,
        "tweet_count":      len(tweets),
        "trusted_count":    trusted_count,
        "total_engagement": total_engagement,
        "buzz_score":       buzz,
        "bullish_signals":  total_bullish,
        "bearish_signals":  total_bearish,
        "top_tweets":       [
            {
                "text":       t["text"][:200],
                "user":       t["username"],
                "likes":      t["likes"],
                "retweets":   t["retweets"],
                "sentiment":  t["sentiment"],
                "is_trusted": t["is_trusted"],
            }
            for t in top_tweets
        ],
    }


def _empty_analysis() -> Dict:
    return {
        "score":            0.0,
        "label":            "NO_DATA",
        "tweet_count":      0,
        "trusted_count":    0,
        "total_engagement": 0,
        "buzz_score":       0,
        "bullish_signals":  0,
        "bearish_signals":  0,
        "top_tweets":       [],
    }


# ─── Main Entry Point ─────────────────────────────────────────
def fetch_twitter_intel(symbol: str) -> Dict:
    """Main function — fetch Twitter intelligence."""
    scraper = get_scraper()
    
    # Clean symbol
    clean = symbol.replace(".NS", "").replace(".BO", "").upper()
    
    # Build search queries
    stock_names = _get_search_names(clean)
    
    logger.info(f"🐦 Twitter: searching '{stock_names[0]}'...")
    
    # Try each name variation
    all_tweets = []
    for name in stock_names[:2]:  # Try top 2 name variants
        tweets = scraper.search_tweets(name, max_tweets=MAX_TWEETS)
        all_tweets.extend(tweets)
        if len(all_tweets) >= MAX_TWEETS:
            break
    
    # Deduplicate by text
    seen_texts = set()
    unique_tweets = []
    for t in all_tweets:
        text_key = t["text"][:100]  # Dedupe by first 100 chars
        if text_key not in seen_texts:
            seen_texts.add(text_key)
            unique_tweets.append(t)
    
    return analyze_tweets(unique_tweets[:MAX_TWEETS])


def _get_search_names(symbol: str) -> List[str]:
    """Get Twitter-search-friendly names."""
    name_map = {
        "RELIANCE":    ["Reliance", "RIL"],
        "TCS":         ["TCS", "Tata Consultancy"],
        "HDFCBANK":    ["HDFC Bank", "HDFCBank"],
        "INFY":        ["Infosys", "INFY"],
        "WIPRO":       ["Wipro"],
        "TATAMOTORS":  ["Tata Motors", "TATAMOTORS"],
        "ADANIENT":    ["Adani Enterprises", "Adani"],
        "ICICIBANK":   ["ICICI Bank"],
        "SBIN":        ["SBI", "State Bank"],
        "BAJFINANCE":  ["Bajaj Finance"],
        "HDFCLIFE":    ["HDFC Life"],
        "KOTAKBANK":   ["Kotak Bank"],
        "AXISBANK":    ["Axis Bank"],
        "HINDUNILVR":  ["HUL", "Hindustan Unilever"],
        "ITC":         ["ITC"],
        "BHARTIARTL":  ["Airtel", "Bharti Airtel"],
        "MARUTI":      ["Maruti"],
        "TITAN":       ["Titan"],
        "SUNPHARMA":   ["Sun Pharma"],
        "HCLTECH":     ["HCL Tech"],
        "TECHM":       ["Tech Mahindra"],
        "ASIANPAINT":  ["Asian Paints"],
        "IRCTC":       ["IRCTC"],
        "ZOMATO":      ["Zomato"],
        "PAYTM":       ["Paytm"],
        "IREDA":       ["IREDA"],
        "SUZLON":      ["Suzlon"],
    }
    return name_map.get(symbol, [symbol])


# ─── Quick Test ───────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    result = fetch_twitter_intel("RELIANCE")
    
    print("\n🐦 Twitter Intelligence")
    print("=" * 60)
    print(f"Score:       {result['score']}")
    print(f"Label:       {result['label']}")
    print(f"Tweets:      {result['tweet_count']}")
    print(f"Trusted:     {result['trusted_count']}")
    print(f"Engagement:  {result['total_engagement']}")
    print(f"Buzz:        {result['buzz_score']}/100")
    print(f"Bull/Bear:   {result['bullish_signals']}/{result['bearish_signals']}")
    
    if result['top_tweets']:
        print("\n🔥 Top Tweets:")
        for i, t in enumerate(result['top_tweets'], 1):
            trust = "✓" if t['is_trusted'] else " "
            print(f"{i}. [{trust}] @{t['user']} ({t['likes']}❤ {t['retweets']}🔁)")
            print(f"   {t['text'][:200]}")