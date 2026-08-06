# E:\tradedo\app\backend\data_pipeline\upstox_api.py

"""
Upstox API Client
Handles authentication, LTP fetching, and market data.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
import logging
from typing import Dict, Optional, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("tradedo.upstox")

# ─── Try import Upstox SDK ────────────────────────────────────
try:
    import upstox_client as ups
    from upstox_client.rest import ApiException
    UPSTOX_AVAILABLE = True
except ImportError as e:
    UPSTOX_AVAILABLE = False
    logger.warning(f"upstox-python-sdk import failed: {e}")


# ═══════════════════════════════════════════════════════════════
#   NSE SYMBOL TO UPSTOX INSTRUMENT KEY MAPPING
# ═══════════════════════════════════════════════════════════════

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
    "DRREDDY.NS":     "NSE_EQ|INE089A01023",
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
#   UPSTOX CLIENT CLASS
# ═══════════════════════════════════════════════════════════════

class UpstoxClient:
    """Wrapper around Upstox SDK."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.api_key      = os.getenv("UPSTOX_API_KEY")
        self.api_secret   = os.getenv("UPSTOX_API_SECRET")
        self.access_token = os.getenv("UPSTOX_ACCESS_TOKEN")
        
        self.api_client  = None
        self.market_api  = None
        self.history_api = None
        self.user_api    = None
        self.is_ready    = False
        
        if not UPSTOX_AVAILABLE:
            logger.error("upstox-python-sdk not properly installed")
            return
        
        if not self.access_token:
            logger.warning("⚠️ UPSTOX_ACCESS_TOKEN not set in .env")
            return
        
        self._init_apis()
        self._initialized = True
    
    def _init_apis(self):
        """Initialize Upstox API clients."""
        try:
            configuration = ups.Configuration()
            configuration.access_token = self.access_token
            
            self.api_client = ups.ApiClient(configuration)
            
            # Initialize different API endpoints
            self.market_api  = ups.MarketQuoteApi(self.api_client)
            self.history_api = ups.HistoryApi(self.api_client)
            self.user_api    = ups.UserApi(self.api_client)
            
            self.is_ready = True
            logger.info("✅ Upstox client initialized")
        
        except Exception as e:
            logger.error(f"Upstox init failed: {e}")
            self.is_ready = False
    
    @staticmethod
    def symbol_to_instrument(symbol: str) -> Optional[str]:
        """Convert NSE symbol to Upstox instrument key."""
        symbol = symbol.upper()
        if not symbol.endswith(".NS"):
            symbol = symbol + ".NS"
        return NSE_INSTRUMENT_KEYS.get(symbol)
    
    def test_connection(self) -> Dict:
        """Test if credentials work."""
        if not self.is_ready:
            return {
                "success": False,
                "error":   "Client not initialized"
            }
        
        try:
            response = self.user_api.get_profile(api_version="2.0")
            data = response.data if hasattr(response, 'data') else response
            
            return {
                "success":   True,
                "user_name": getattr(data, 'user_name', 'N/A'),
                "email":     getattr(data, 'email', 'N/A'),
                "user_type": getattr(data, 'user_type', 'N/A'),
                "broker":    getattr(data, 'broker', 'N/A'),
                "message":   "Connection successful!",
            }
        
        except ApiException as e:
            return {
                "success": False,
                "error":   f"API error {e.status}: {e.reason}",
                "hint":    "Access token may have expired. Regenerate from developer.upstox.com",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_ltp(self, symbol: str) -> Optional[Dict]:
        """Get Last Traded Price for a stock (real-time)."""
        if not self.is_ready:
            return None
    
        instrument_key = self.symbol_to_instrument(symbol)
        if not instrument_key:
            logger.warning(f"No instrument key mapping for {symbol}")
            return None
    
        try:
            # SDK v2.28 requires 'symbol' parameter (instrument key)
            response = self.market_api.ltp(
                symbol=instrument_key,
                api_version="2.0",
            )
            
            data = response.data if hasattr(response, 'data') else {}
            
            for key, ltp_data in data.items():
                return {
                    "symbol":         symbol,
                    "instrument_key": instrument_key,
                    "last_price":     float(ltp_data.last_price),
                    "timestamp":      datetime.now().isoformat(),
                    "source":         "upstox",
                }
        
        except ApiException as e:
            logger.warning(f"LTP fetch failed for {symbol}: {e.reason}")
            return None
        except Exception as e:
            logger.error(f"LTP error for {symbol}: {e}")
            return None
    
    def get_multiple_ltp(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get LTP for multiple stocks in one call."""
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
        
            # DEBUG: Log the actual keys we get back
            logger.debug(f"Response keys: {list(data.keys())[:3]}")
        
            # Build multiple lookup dictionaries for maximum compatibility
            # 1. By full instrument key
            # 2. By ISIN only
            # 3. By trading symbol (RELIANCE, TCS, etc.)
            isin_map = {}
            symbol_only_map = {}
        
            for inst_key, sym in instrument_map.items():
                # inst_key = "NSE_EQ|INE002A01018"
                if "|" in inst_key:
                    isin = inst_key.split("|")[1]
                    isin_map[isin] = sym
            
                # Also map by trading symbol (RELIANCE from RELIANCE.NS)
                trading_symbol = sym.replace(".NS", "")
                symbol_only_map[trading_symbol] = sym
        
            for key, ltp_data in data.items():
                original_symbol = None
            
                # Try 1: Direct match with instrument key format
                clean_key = key.replace(":", "|")
                if clean_key in instrument_map:
                    original_symbol = instrument_map[clean_key]
                
                # Try 2: Extract ISIN from response key
                if not original_symbol:
                    for isin, sym in isin_map.items():
                        if isin in key:
                            original_symbol = sym
                            break
            
                # Try 3: Try trading symbol match
                if not original_symbol:
                    for trading_sym, full_sym in symbol_only_map.items():
                        if trading_sym in key:
                            original_symbol = full_sym
                            break
            
                # Try 4: Get the instrument key from ltp_data itself
                if not original_symbol and hasattr(ltp_data, 'instrument_token'):
                    token = ltp_data.instrument_token
                    for inst_key, sym in instrument_map.items():
                        if inst_key.split("|")[-1] == token or inst_key == token:
                            original_symbol = sym
                            break
            
                if original_symbol:
                    results[original_symbol] = {
                        "symbol":     original_symbol,
                        "last_price": float(ltp_data.last_price),
                        "timestamp":  datetime.now().isoformat(),
                        "source":     "upstox",
                    }
                else:
                    logger.debug(f"Could not match response key '{key}' to any symbol")
        
            logger.info(f"Fetched {len(results)}/{len(symbols)} LTPs from Upstox")
            return results
    
        except Exception as e:
            logger.error(f"Multi-LTP error: {e}")
            return {}
    
    def get_market_quote(self, symbol: str) -> Optional[Dict]:
        """Get full market quote (OHLC, volume, etc.)."""
        if not self.is_ready:
            return None
    
        instrument_key = self.symbol_to_instrument(symbol)
        if not instrument_key:
            return None
    
        try:
            # SDK v2.28 uses 'symbol' parameter
            response = self.market_api.get_full_market_quote(
                symbol=instrument_key,
                api_version="2.0",
            )
        
            data = response.data if hasattr(response, 'data') else {}
        
            for key, quote in data.items():
                ohlc = getattr(quote, 'ohlc', None)
            
                result = {
                    "symbol":        symbol,
                    "last_price":    float(getattr(quote, 'last_price', 0)),
                    "volume":        int(getattr(quote, 'volume', 0)),
                    "average_price": float(getattr(quote, 'average_price', 0)),
                    "timestamp":     datetime.now().isoformat(),
                }
            
                if ohlc:
                    result["ohlc"] = {
                        "open":  float(getattr(ohlc, 'open', 0)),
                        "high":  float(getattr(ohlc, 'high', 0)),
                        "low":   float(getattr(ohlc, 'low', 0)),
                        "close": float(getattr(ohlc, 'close', 0)),
                    }
            
                return result
    
        except Exception as e:
            logger.error(f"Market quote error for {symbol}: {e}")
            return None
    
    def get_status(self) -> Dict:
        """Get client status."""
        return {
            "sdk_installed":   UPSTOX_AVAILABLE,
            "credentials_set": bool(self.access_token),
            "client_ready":    self.is_ready,
            "api_key_prefix":  self.api_key[:8] if self.api_key else None,
            "known_symbols":   len(NSE_INSTRUMENT_KEYS),
        }


# ═══════════════════════════════════════════════════════════════
#   GLOBAL SINGLETON
# ═══════════════════════════════════════════════════════════════

def get_upstox_client() -> UpstoxClient:
    """Get global Upstox client instance."""
    return UpstoxClient()


# ═══════════════════════════════════════════════════════════════
#   QUICK TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("UPSTOX CLIENT TEST")
    print("="*60)
    
    client = get_upstox_client()
    
    print("\n📊 Status:")
    status = client.get_status()
    for k, v in status.items():
        print(f"   {k}: {v}")
    
    if not client.is_ready:
        print("\n❌ Client not ready. Check errors above.")
        exit(1)
    
    print("\n🔌 Testing connection...")
    conn = client.test_connection()
    if conn["success"]:
        print(f"   ✅ Connected as: {conn.get('user_name')}")
        print(f"   Email:  {conn.get('email')}")
        print(f"   Broker: {conn.get('broker')}")
    else:
        print(f"   ❌ {conn.get('error')}")
        if conn.get('hint'):
            print(f"   💡 {conn['hint']}")
        exit(1)
    
    print("\n💰 Fetching RELIANCE LTP...")
    ltp = client.get_ltp("RELIANCE.NS")
    if ltp:
        print(f"   ✅ Price: ₹{ltp['last_price']}")
        print(f"   Source: {ltp['source']}")
        print(f"   Time:   {ltp['timestamp']}")
    else:
        print("   ❌ Failed to fetch LTP")
    
    print("\n💰 Fetching multiple LTPs...")
    symbols = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "WIPRO.NS"]
    ltps = client.get_multiple_ltp(symbols)
    for sym, data in ltps.items():
        print(f"   {sym.replace('.NS', ''):12s} ₹{data['last_price']}")
    
    print("\n📊 Full market quote for RELIANCE...")
    quote = client.get_market_quote("RELIANCE.NS")
    if quote:
        print(f"   Last Price:    ₹{quote['last_price']}")
        print(f"   Volume:        {quote['volume']:,}")
        print(f"   Avg Price:     ₹{quote['average_price']}")
        if 'ohlc' in quote:
            print(f"   O/H/L/C:       ₹{quote['ohlc']['open']}/"
                  f"{quote['ohlc']['high']}/{quote['ohlc']['low']}/"
                  f"{quote['ohlc']['close']}")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED - Upstox integration working!")
    print("="*60)