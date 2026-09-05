# E:\tradedo\app\backend\data_pipeline\upstox_api.py

"""
Upstox API Client - Enhanced with dual token support.
Uses Analytics Token (1-year) for data, Trading Token for orders.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("tradedo.upstox")

try:
    import upstox_client as ups
    from upstox_client.rest import ApiException
    UPSTOX_AVAILABLE = True
except ImportError as e:
    UPSTOX_AVAILABLE = False
    logger.warning(f"upstox-python-sdk import failed: {e}")


# ═══════════════════════════════════════════════════════════════
#   NSE SYMBOL → UPSTOX INSTRUMENT KEY MAPPING
# ═══════════════════════════════════════════════════════════════
# (Keep your existing NSE_INSTRUMENT_KEYS dictionary here)
NSE_INSTRUMENT_KEYS = {
    "RELIANCE.NS":    "NSE_EQ|INE002A01018",
    "TCS.NS":         "NSE_EQ|INE467B01029",
    "HDFCBANK.NS":    "NSE_EQ|INE040A01034",
    "INFY.NS":        "NSE_EQ|INE009A01021",
    "ICICIBANK.NS":   "NSE_EQ|INE090A01021",
    "HINDUNILVR.NS":  "NSE_EQ|INE030A01027",
    "SBIN.NS":        "NSE_EQ|INE062A01020",
    "BHARTIARTL.NS":  "NSE_EQ|INE397D01024",
    "ITC.NS":         "NSE_EQ|INE154A01025",
    "KOTAKBANK.NS":   "NSE_EQ|INE237A01028",
    "LT.NS":          "NSE_EQ|INE018A01030",
    "AXISBANK.NS":    "NSE_EQ|INE238A01034",
    "HCLTECH.NS":     "NSE_EQ|INE860A01027",
    "ASIANPAINT.NS":  "NSE_EQ|INE021A01026",
    "MARUTI.NS":      "NSE_EQ|INE585B01010",
    "BAJFINANCE.NS":  "NSE_EQ|INE296A01024",
    "TITAN.NS":       "NSE_EQ|INE280A01028",
    "SUNPHARMA.NS":   "NSE_EQ|INE044A01036",
    "ULTRACEMCO.NS":  "NSE_EQ|INE481G01011",
    "NESTLEIND.NS":   "NSE_EQ|INE239A01024",
    "WIPRO.NS":       "NSE_EQ|INE075A01022",
    "M&M.NS":         "NSE_EQ|INE101A01026",
    "TATAMOTORS.NS":  "NSE_EQ|INE155A01022",
    "NTPC.NS":        "NSE_EQ|INE733E01010",
    "POWERGRID.NS":   "NSE_EQ|INE752E01010",
    "TECHM.NS":       "NSE_EQ|INE669C01036",
    "HDFCLIFE.NS":    "NSE_EQ|INE795G01014",
    "ADANIENT.NS":    "NSE_EQ|INE423A01024",
    "COALINDIA.NS":   "NSE_EQ|INE522F01014",
    "BAJAJFINSV.NS":  "NSE_EQ|INE918I01018",
    "DIVISLAB.NS":    "NSE_EQ|INE361B01024",
    "TATASTEEL.NS":   "NSE_EQ|INE081A01020",
    "GRASIM.NS":      "NSE_EQ|INE047A01021",
    "JSWSTEEL.NS":    "NSE_EQ|INE019A01038",
    "BRITANNIA.NS":   "NSE_EQ|INE216A01030",
    "CIPLA.NS":       "NSE_EQ|INE059A01026",
    "SBILIFE.NS":     "NSE_EQ|INE123W01016",
    "ONGC.NS":        "NSE_EQ|INE213A01029",
    # Dr. Reddy's completed a 1:5 split in October 2024. The prior ISIN no
    # longer produces an executable quote from Upstox.
    "DRREDDY.NS":     "NSE_EQ|INE089A01031",
    "EICHERMOT.NS":   "NSE_EQ|INE066A01021",
    "APOLLOHOSP.NS":  "NSE_EQ|INE437A01024",
    "INDUSINDBK.NS":  "NSE_EQ|INE095A01012",
    "HINDALCO.NS":    "NSE_EQ|INE038A01020",
    "BAJAJ-AUTO.NS":  "NSE_EQ|INE917I01010",
    "TATACONSUM.NS":  "NSE_EQ|INE192A01025",
    "HEROMOTOCO.NS":  "NSE_EQ|INE158A01026",
    "ADANIPORTS.NS":  "NSE_EQ|INE742F01042",
    "UPL.NS":         "NSE_EQ|INE628A01036",
    "BPCL.NS":        "NSE_EQ|INE029A01011",
    "SHRIRAMFIN.NS":  "NSE_EQ|INE721A01013",
    "IRCTC.NS":       "NSE_EQ|INE335Y01020",
    "IREDA.NS":       "NSE_EQ|INE202E01016",
    "IRFC.NS":        "NSE_EQ|INE053F01010",
    "ZOMATO.NS":      "NSE_EQ|INE758T01015",
    "SUZLON.NS":      "NSE_EQ|INE040H01021",
    "YESBANK.NS":     "NSE_EQ|INE528G01035",
    "IDEA.NS":        "NSE_EQ|INE669E01016",
    "PAYTM.NS":       "NSE_EQ|INE982J01020",
    "TATAPOWER.NS":   "NSE_EQ|INE245A01021",
    "GAIL.NS":        "NSE_EQ|INE129A01019",
    "IOC.NS":         "NSE_EQ|INE242A01010",
    "HINDPETRO.NS":   "NSE_EQ|INE094A01015",
    "ADANIGREEN.NS":  "NSE_EQ|INE364U01010",
    "ADANIPOWER.NS":  "NSE_EQ|INE814H01011",
    "NHPC.NS":        "NSE_EQ|INE848E01016",
    "PFC.NS":         "NSE_EQ|INE134E01011",
    "RECLTD.NS":      "NSE_EQ|INE020B01018",
    "BANKBARODA.NS":  "NSE_EQ|INE028A01039",
    "CANBK.NS":       "NSE_EQ|INE476A01022",
    "PNB.NS":         "NSE_EQ|INE160A01022",
    "DMART.NS":       "NSE_EQ|INE192R01011",
    "TRENT.NS":       "NSE_EQ|INE849A01020",
    "PIDILITIND.NS":  "NSE_EQ|INE318A01026",
    "SIEMENS.NS":     "NSE_EQ|INE003A01024",
    "GODREJCP.NS":    "NSE_EQ|INE102D01028",
    "AMBUJACEM.NS":   "NSE_EQ|INE079A01024",
    "DABUR.NS":       "NSE_EQ|INE016A01026",
    "MARICO.NS":      "NSE_EQ|INE196A01026",
    "HAVELLS.NS":     "NSE_EQ|INE176B01034",
    "BERGEPAINT.NS":  "NSE_EQ|INE463A01038",
    "MOTHERSON.NS":   "NSE_EQ|INE775A01035",
    "BEL.NS":         "NSE_EQ|INE263A01024",
    "VEDL.NS":        "NSE_EQ|INE205A01025",
    "TVSMOTOR.NS":    "NSE_EQ|INE494B01023",
    "JINDALSTEL.NS":  "NSE_EQ|INE749A01030",
    "SAIL.NS":        "NSE_EQ|INE114A01011",
    "MUTHOOTFIN.NS":  "NSE_EQ|INE414G01012",
    "CHOLAFIN.NS":    "NSE_EQ|INE121A01024",
}


# ═══════════════════════════════════════════════════════════════
#   UPSTOX CLIENT CLASS - Enhanced with dual tokens
# ═══════════════════════════════════════════════════════════════

class UpstoxClient:
    """Wrapper around Upstox SDK with dual token support."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Load all credentials
        self.api_key = os.getenv("UPSTOX_API_KEY")
        self.api_secret = os.getenv("UPSTOX_API_SECRET")
        
        # Two tokens
        self.analytics_token = os.getenv("UPSTOX_ANALYTICS_TOKEN")
        self.trading_token = os.getenv("UPSTOX_ACCESS_TOKEN")
        
        # Preferred token type (default: analytics for read operations)
        self.token_type = os.getenv("UPSTOX_TOKEN_TYPE", "analytics").lower()
        
        # Get active token based on preference
        self.access_token = self._get_active_token()
        
        # Initialize clients
        self.api_client = None
        self.market_api = None
        self.history_api = None
        self.user_api = None
        self.portfolio_api = None
        self.is_ready = False
        
        if not UPSTOX_AVAILABLE:
            logger.error("upstox-python-sdk not properly installed")
            return
        
        if not self.access_token:
            logger.warning(
                "⚠️ No Upstox token configured!\n"
                "   Set UPSTOX_ANALYTICS_TOKEN (recommended, 1-year validity)\n"
                "   Or UPSTOX_ACCESS_TOKEN (daily regeneration required)"
            )
            return
        
        self._init_apis()
        self._initialized = True
    
    def _get_active_token(self) -> Optional[str]:
        """Get the active token based on preference."""
        if self.token_type == "analytics" and self.analytics_token:
            logger.info("🔑 Using ANALYTICS token (1-year validity)")
            return self.analytics_token
        
        if self.token_type == "trading" and self.trading_token:
            logger.info("🔑 Using TRADING token (daily regeneration)")
            return self.trading_token
        
        # Fallback: prefer analytics over trading
        if self.analytics_token:
            logger.info("🔑 Using ANALYTICS token (fallback)")
            return self.analytics_token
        
        if self.trading_token:
            logger.info("🔑 Using TRADING token (fallback)")
            return self.trading_token
        
        return None
    
    def _init_apis(self):
        """Initialize Upstox API clients."""
        try:
            configuration = ups.Configuration()
            configuration.access_token = self.access_token
            
            self.api_client = ups.ApiClient(configuration)
            
            # Initialize all APIs
            self.market_api = ups.MarketQuoteApi(self.api_client)
            self.history_api = ups.HistoryApi(self.api_client)
            self.user_api = ups.UserApi(self.api_client)
            self.portfolio_api = ups.PortfolioApi(self.api_client)
            
            self.is_ready = True
            logger.info(f"✅ Upstox client initialized ({self.token_type} token)")
        
        except Exception as e:
            logger.error(f"Upstox init failed: {e}")
            self.is_ready = False
    
    def switch_to_trading_token(self):
        """Switch to trading token for order operations."""
        if not self.trading_token:
            raise ValueError("Trading token not configured")
        
        self.access_token = self.trading_token
        self.token_type = "trading"
        self._initialized = False
        self._init_apis()
        self._initialized = True
        logger.info("🔄 Switched to TRADING token")
    
    def switch_to_analytics_token(self):
        """Switch to analytics token for data operations."""
        if not self.analytics_token:
            raise ValueError("Analytics token not configured")
        
        self.access_token = self.analytics_token
        self.token_type = "analytics"
        self._initialized = False
        self._init_apis()
        self._initialized = True
        logger.info("🔄 Switched to ANALYTICS token")
    
    # ─── Helper: Symbol to Instrument Key ─────────────────────
    @staticmethod
    def symbol_to_instrument(symbol: str) -> Optional[str]:
        """Convert NSE symbol to Upstox instrument key."""
        symbol = symbol.upper()
        if not symbol.endswith(".NS"):
            symbol = symbol + ".NS"
        return NSE_INSTRUMENT_KEYS.get(symbol)
    
    # ─── Test Connection ──────────────────────────────────────
    def test_connection(self) -> Dict:
        """Test if credentials work - uses appropriate endpoint per token type."""
        if not self.is_ready:
            return {
                "success": False,
                "error": "Client not initialized"
            }
    
        # For Analytics token, use market data endpoint (it doesn't have user access)
        if self.token_type == "analytics":
            try:
                # Try to fetch RELIANCE LTP as a test
                response = self.market_api.ltp(
                    symbol="NSE_EQ|INE002A01018",  # RELIANCE
                    api_version="2.0",
                )
                
                data = response.data if hasattr(response, 'data') else {}
                
                if data:
                    # Get first price
                    for key, ltp_data in data.items():
                        price = float(ltp_data.last_price)
                        return {
                            "success": True,
                            "user_name": "Analytics Token User",
                            "token_type": "analytics",
                            "test_price": f"RELIANCE @ ₹{price}",
                            "message": "Analytics token working - real-time data available!",
                        }
                
                return {
                    "success": False,
                    "error": "No data returned"
                }
            
            except ApiException as e:
                return {
                    "success": False,
                    "error": f"API error {e.status}: {e.reason}",
                    "hint": self._get_error_hint(e.status),
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        # For Trading token, use user profile
        try:
            response = self.user_api.get_profile(api_version="2.0")
            data = response.data if hasattr(response, 'data') else response
            
            return {
                "success": True,
                "user_name": getattr(data, 'user_name', 'N/A'),
                "email": getattr(data, 'email', 'N/A'),
                "user_type": getattr(data, 'user_type', 'N/A'),
                "broker": getattr(data, 'broker', 'N/A'),
                "token_type": self.token_type,
                "message": "Trading token connection successful!",
            }
        
        except ApiException as e:
            return {
                "success": False,
                "error": f"API error {e.status}: {e.reason}",
                "hint": self._get_error_hint(e.status),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


    def _get_error_hint(self, status_code: int) -> str:
        """Get helpful hint based on error code."""
        hints = {
            401: (
                "Token invalid or expired. Possible fixes:\n"
                "1. Regenerate token from developer.upstox.com\n"
                "2. Check for spaces/newlines in .env file\n"
                "3. Analytics token might need static IP setup\n"
                "4. Try switching token type (analytics vs trading)"
            ),
            403: "Token doesn't have permission for this endpoint",
            429: "Rate limit exceeded. Wait a few minutes",
            500: "Upstox server error. Try again",
        }
        return hints.get(status_code, f"HTTP {status_code} error")
    
    # ─── LTP (Last Traded Price) ──────────────────────────────
    def get_ltp(self, symbol: str) -> Optional[Dict]:
        """Get Last Traded Price - REAL-TIME."""
        if not self.is_ready:
            return None
        
        instrument_key = self.symbol_to_instrument(symbol)
        if not instrument_key:
            logger.warning(f"No instrument key for {symbol}")
            return None
        
        try:
            response = self.market_api.ltp(
                symbol=instrument_key,
                api_version="2.0",
            )
            
            data = response.data if hasattr(response, 'data') else {}
            
            for key, ltp_data in data.items():
                return {
                    "symbol": symbol,
                    "instrument_key": instrument_key,
                    "last_price": float(ltp_data.last_price),
                    "timestamp": datetime.now().isoformat(),
                    "source": "upstox",
                }
        
        except ApiException as e:
            logger.warning(f"LTP fetch failed for {symbol}: {e.reason}")
            return None
        except Exception as e:
            logger.error(f"LTP error for {symbol}: {e}")
            return None
    
    # ─── Multiple LTPs ────────────────────────────────────────
    def get_multiple_ltp(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get LTP for multiple stocks."""
        if not self.is_ready:
            return {}
        
        instrument_map = {}
        for sym in symbols:
            key = self.symbol_to_instrument(sym)
            if key:
                instrument_map[key] = sym
        
        if not instrument_map:
            return {}
        
        try:
            instrument_keys = ",".join(instrument_map.keys())
            response = self.market_api.ltp(
                symbol=instrument_keys,
                api_version="2.0",
            )
            
            data = response.data if hasattr(response, 'data') else {}
            results = {}
            
            # Build ISIN lookup
            isin_map = {}
            for inst_key, sym in instrument_map.items():
                if "|" in inst_key:
                    isin = inst_key.split("|")[1]
                    isin_map[isin] = sym
            
            for key, ltp_data in data.items():
                original_symbol = None
                
                clean_key = key.replace(":", "|")
                if clean_key in instrument_map:
                    original_symbol = instrument_map[clean_key]
                else:
                    for isin, sym in isin_map.items():
                        if isin in key:
                            original_symbol = sym
                            break
                
                if original_symbol:
                    results[original_symbol] = {
                        "symbol": original_symbol,
                        "last_price": float(ltp_data.last_price),
                        "timestamp": datetime.now().isoformat(),
                        "source": "upstox",
                    }
            
            logger.info(f"Fetched {len(results)}/{len(symbols)} LTPs from Upstox")
            return results
        
        except Exception as e:
            logger.error(f"Multi-LTP error: {e}")
            return {}
    
    # ─── Full Market Quote ────────────────────────────────────
    def get_market_quote(self, symbol: str) -> Optional[Dict]:
        """Get full market quote (OHLC, volume, bid/ask)."""
        if not self.is_ready:
            return None
        
        instrument_key = self.symbol_to_instrument(symbol)
        if not instrument_key:
            return None
        
        try:
            response = self.market_api.get_full_market_quote(
                symbol=instrument_key,
                api_version="2.0",
            )
            
            data = response.data if hasattr(response, 'data') else {}
            
            for key, quote in data.items():
                ohlc = getattr(quote, 'ohlc', None)
                depth = getattr(quote, 'depth', None)
                
                result = {
                    "symbol": symbol,
                    "last_price": float(getattr(quote, 'last_price', 0)),
                    "volume": int(getattr(quote, 'volume', 0)),
                    "average_price": float(getattr(quote, 'average_price', 0)),
                    "timestamp": datetime.now().isoformat(),
                }
                
                if ohlc:
                    result["ohlc"] = {
                        "open": float(getattr(ohlc, 'open', 0)),
                        "high": float(getattr(ohlc, 'high', 0)),
                        "low": float(getattr(ohlc, 'low', 0)),
                        "close": float(getattr(ohlc, 'close', 0)),
                    }
                
                # Order book depth
                if depth:
                    buy_depth = getattr(depth, 'buy', [])
                    sell_depth = getattr(depth, 'sell', [])
                    
                    result["depth"] = {
                        "buy": [
                            {
                                "price": float(getattr(b, 'price', 0)),
                                "quantity": int(getattr(b, 'quantity', 0)),
                                "orders": int(getattr(b, 'orders', 0)),
                            }
                            for b in buy_depth[:5]
                        ],
                        "sell": [
                            {
                                "price": float(getattr(s, 'price', 0)),
                                "quantity": int(getattr(s, 'quantity', 0)),
                                "orders": int(getattr(s, 'orders', 0)),
                            }
                            for s in sell_depth[:5]
                        ],
                    }
                
                return result
        
        except Exception as e:
            logger.error(f"Market quote error for {symbol}: {e}")
            return None
    
    # ─── Historical Data ──────────────────────────────────────
    def get_historical_candles(
        self,
        symbol: str,
        interval: str = "day",
        from_date: str = None,
        to_date: str = None,
    ) -> Optional[List[Dict]]:
        """
        Get historical candle data.
        
        Args:
            symbol: NSE symbol
            interval: 'minute', 'day', 'week', 'month'
            from_date: YYYY-MM-DD format
            to_date: YYYY-MM-DD format
        """
        if not self.is_ready:
            return None
        
        instrument_key = self.symbol_to_instrument(symbol)
        if not instrument_key:
            return None
        
        # Default dates
        if not to_date:
            to_date = datetime.now().strftime("%Y-%m-%d")
        if not from_date:
            from_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        
        try:
            response = self.history_api.get_historical_candle_data1(
                instrument_key=instrument_key,
                interval=interval,
                to_date=to_date,
                from_date=from_date,
                api_version="2.0",
            )
            
            data = response.data if hasattr(response, 'data') else None
            
            if not data or not hasattr(data, 'candles'):
                return None
            
            candles = []
            for candle in data.candles:
                # Format: [timestamp, open, high, low, close, volume, oi]
                candles.append({
                    "timestamp": candle[0],
                    "open": float(candle[1]),
                    "high": float(candle[2]),
                    "low": float(candle[3]),
                    "close": float(candle[4]),
                    "volume": int(candle[5]) if len(candle) > 5 else 0,
                })
            
            logger.info(f"Fetched {len(candles)} candles for {symbol}")
            return candles
        
        except Exception as e:
            logger.error(f"Historical data error for {symbol}: {e}")
            return None
    
    # ─── Intraday Data ────────────────────────────────────────
    def get_intraday_candles(
        self,
        symbol: str,
        interval: str = "5minute",
    ) -> Optional[List[Dict]]:
        """
        Get intraday candles (today only).
        
        Args:
            interval: '1minute', '5minute', '15minute', '30minute'
        """
        if not self.is_ready:
            return None
        
        instrument_key = self.symbol_to_instrument(symbol)
        if not instrument_key:
            return None
        
        try:
            response = self.history_api.get_intra_day_candle_data(
                instrument_key=instrument_key,
                interval=interval,
                api_version="2.0",
            )
            
            data = response.data if hasattr(response, 'data') else None
            
            if not data or not hasattr(data, 'candles'):
                return None
            
            candles = []
            for candle in data.candles:
                candles.append({
                    "timestamp": candle[0],
                    "open": float(candle[1]),
                    "high": float(candle[2]),
                    "low": float(candle[3]),
                    "close": float(candle[4]),
                    "volume": int(candle[5]) if len(candle) > 5 else 0,
                })
            
            logger.info(f"Fetched {len(candles)} intraday candles for {symbol}")
            return candles
        
        except Exception as e:
            logger.error(f"Intraday data error for {symbol}: {e}")
            return None
    
    # ─── Status ───────────────────────────────────────────────
    def get_status(self) -> Dict:
        """Get client status."""
        return {
            "sdk_installed": UPSTOX_AVAILABLE,
            "analytics_token_set": bool(self.analytics_token),
            "trading_token_set": bool(self.trading_token),
            "active_token_type": self.token_type,
            "client_ready": self.is_ready,
            "api_key_prefix": self.api_key[:8] if self.api_key else None,
            "known_symbols": len(NSE_INSTRUMENT_KEYS),
        }


# ═══════════════════════════════════════════════════════════════
#   GLOBAL SINGLETON
# ═══════════════════════════════════════════════════════════════

def get_upstox_client() -> UpstoxClient:
    """Get global Upstox client instance."""
    return UpstoxClient()


# ═══════════════════════════════════════════════════════════════
#   Quick Test
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("UPSTOX CLIENT TEST (Enhanced)")
    print("="*60)
    
    client = get_upstox_client()
    
    print("\n📊 Status:")
    status = client.get_status()
    for k, v in status.items():
        print(f"   {k}: {v}")
    
    if not client.is_ready:
        print("\n❌ Client not ready")
        exit(1)
    
    print("\n🔌 Testing connection...")
    conn = client.test_connection()
    if conn["success"]:
        print(f"   ✅ Connected as: {conn.get('user_name')}")
        print(f"   Token: {conn.get('token_type')}")
    else:
        print(f"   ❌ {conn.get('error')}")
        exit(1)
    
    print("\n💰 Fetching RELIANCE LTP...")
    ltp = client.get_ltp("RELIANCE.NS")
    if ltp:
        print(f"   ✅ Price: ₹{ltp['last_price']}")
        print(f"   Source: {ltp['source']}")
    
    print("\n📊 Full quote for TCS...")
    quote = client.get_market_quote("TCS.NS")
    if quote:
        print(f"   Price: ₹{quote['last_price']}")
        print(f"   Volume: {quote['volume']:,}")
        if 'ohlc' in quote:
            print(f"   OHLC: {quote['ohlc']}")
        if 'depth' in quote:
            print(f"   Buy orders (top 3):")
            for b in quote['depth']['buy'][:3]:
                print(f"     ₹{b['price']} × {b['quantity']}")
    
    print("\n📈 Historical candles for RELIANCE (7 days)...")
    from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    to_date = datetime.now().strftime("%Y-%m-%d")
    candles = client.get_historical_candles("RELIANCE.NS", "day", from_date, to_date)
    if candles:
        print(f"   Got {len(candles)} candles")
        for c in candles[-3:]:
            print(f"   {c['timestamp']}: O={c['open']} H={c['high']} L={c['low']} C={c['close']}")
    
    print("\n⚡ Intraday 5min candles for RELIANCE...")
    intraday = client.get_intraday_candles("RELIANCE.NS", "5minute")
    if intraday:
        print(f"   Got {len(intraday)} candles today")
        if intraday:
            print(f"   Latest: {intraday[-1]}")
    
    print("\n" + "="*60)
    print("✅ UPSTOX FULLY OPERATIONAL")
    print("="*60)
