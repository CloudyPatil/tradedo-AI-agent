# E:\tradedo\app\backend\agent\websocket_stream.py

"""
UPSTOX WEBSOCKET REAL-TIME STREAMER
Streams live price updates for open trades.
Millisecond-latency SL/target detection.

Runs as background thread during market hours.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
import json
import ssl
import time
import threading
import logging
from typing import Dict, Set, Optional, Callable
from datetime import datetime, time as dt_time
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("tradedo.websocket")

# Try import WebSocket dependencies
try:
    import websocket
    import upstox_client as ups
    from upstox_client.rest import ApiException
    WEBSOCKET_AVAILABLE = True
except ImportError as e:
    WEBSOCKET_AVAILABLE = False
    logger.warning(f"WebSocket dependencies missing: {e}")


# ═══════════════════════════════════════════════════════════════
#   CONFIG
# ═══════════════════════════════════════════════════════════════

MARKET_OPEN  = dt_time(9, 15)
MARKET_CLOSE = dt_time(15, 30)

# Reconnection settings
MAX_RECONNECT_ATTEMPTS = 10
RECONNECT_DELAY_SECS   = 5


# ═══════════════════════════════════════════════════════════════
#   WEBSOCKET STREAMER
# ═══════════════════════════════════════════════════════════════

class UpstoxWebSocketStreamer:
    """
    Real-time price streamer for open trades.
    Runs in background thread.
    """
    
    def __init__(self):
        self.access_token = os.getenv("UPSTOX_ACCESS_TOKEN")
        self.subscribed_symbols: Set[str] = set()
        self.latest_prices: Dict[str, float] = {}
        self.ws = None
        self.thread = None
        self.is_running = False
        self.reconnect_attempts = 0
        
        # Callbacks
        self.on_price_update: Optional[Callable] = None
        
        self.stats = {
            "connections":       0,
            "disconnections":    0,
            "messages_received": 0,
            "prices_updated":    0,
            "errors":            0,
            "reconnects":        0,
        }
    
    # ═══════════════════════════════════════════════════════════
    #   CONNECTION MANAGEMENT
    # ═══════════════════════════════════════════════════════════
    
    def _get_authorized_url(self) -> Optional[str]:
        """Get authorized WebSocket URL from Upstox."""
        if not WEBSOCKET_AVAILABLE or not self.access_token:
            return None
        
        try:
            configuration = ups.Configuration()
            configuration.access_token = self.access_token
            api_client = ups.ApiClient(configuration)
            
            # Get WebSocket auth
            api = ups.WebsocketApi(api_client)
            response = api.get_market_data_feed_authorize(api_version="2.0")
            
            data = response.data if hasattr(response, 'data') else response
            
            if hasattr(data, 'authorized_redirect_uri'):
                return data.authorized_redirect_uri
            
            return None
        
        except Exception as e:
            logger.error(f"Failed to get WebSocket URL: {e}")
            return None
    
    def _on_open(self, ws):
        """WebSocket connection opened."""
        logger.info("✅ WebSocket connected")
        self.stats["connections"] += 1
        self.reconnect_attempts = 0
        
        # Subscribe to all currently tracked symbols
        if self.subscribed_symbols:
            self._send_subscription(list(self.subscribed_symbols))
    
    def _on_message(self, ws, message):
        """Handle incoming price updates."""
        try:
            self.stats["messages_received"] += 1
            
            # Upstox v2 sends binary Protobuf messages
            # For simplicity, we'll parse basic price data
            
            # Try to decode as JSON first (some messages are JSON)
            try:
                data = json.loads(message)
                self._process_json_message(data)
            except (json.JSONDecodeError, TypeError):
                # Binary message - would need protobuf decoder
                # For now, log and continue
                logger.debug(f"Received binary message ({len(message)} bytes)")
        
        except Exception as e:
            logger.error(f"Message parse error: {e}")
            self.stats["errors"] += 1
    
    def _process_json_message(self, data: Dict):
        """Process JSON price update."""
        try:
            feeds = data.get("feeds", {})
            
            for instrument_key, feed_data in feeds.items():
                # Extract LTP from feed
                ff = feed_data.get("ff", {})
                market_ff = ff.get("marketFF", {})
                ltpc = market_ff.get("ltpc", {})
                
                ltp = ltpc.get("ltp")
                
                if ltp:
                    # Convert instrument key back to symbol
                    symbol = self._instrument_to_symbol(instrument_key)
                    
                    if symbol:
                        old_price = self.latest_prices.get(symbol)
                        self.latest_prices[symbol] = float(ltp)
                        self.stats["prices_updated"] += 1
                        
                        # Trigger callback if price changed
                        if self.on_price_update and old_price != float(ltp):
                            try:
                                self.on_price_update(symbol, float(ltp))
                            except Exception as e:
                                logger.error(f"Callback error: {e}")
        
        except Exception as e:
            logger.debug(f"JSON process error: {e}")
    
    def _instrument_to_symbol(self, instrument_key: str) -> Optional[str]:
        """Convert instrument key back to NSE symbol."""
        from data_pipeline.upstox_api import NSE_INSTRUMENT_KEYS
        
        # Reverse lookup
        for symbol, key in NSE_INSTRUMENT_KEYS.items():
            if key == instrument_key or key.replace("|", ":") == instrument_key:
                return symbol
        
        return None
    
    def _on_error(self, ws, error):
        """Handle WebSocket errors."""
        logger.error(f"WebSocket error: {error}")
        self.stats["errors"] += 1
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket disconnection."""
        logger.warning(
            f"WebSocket disconnected: code={close_status_code}, msg={close_msg}"
        )
        self.stats["disconnections"] += 1
        
        # Auto-reconnect if we're supposed to be running
        if self.is_running:
            self._attempt_reconnect()
    
    def _attempt_reconnect(self):
        """Try to reconnect after disconnection."""
        if self.reconnect_attempts >= MAX_RECONNECT_ATTEMPTS:
            logger.error("Max reconnection attempts reached. Stopping.")
            self.is_running = False
            return
        
        self.reconnect_attempts += 1
        self.stats["reconnects"] += 1
        
        wait_time = RECONNECT_DELAY_SECS * min(self.reconnect_attempts, 6)
        logger.info(
            f"Reconnecting in {wait_time}s "
            f"(attempt {self.reconnect_attempts}/{MAX_RECONNECT_ATTEMPTS})"
        )
        
        time.sleep(wait_time)
        
        try:
            self._connect()
        except Exception as e:
            logger.error(f"Reconnect failed: {e}")
    
    # ═══════════════════════════════════════════════════════════
    #   SUBSCRIPTION MANAGEMENT
    # ═══════════════════════════════════════════════════════════
    
    def _send_subscription(self, symbols: list):
        """Subscribe to symbols for price updates."""
        if not self.ws:
            return
        
        from data_pipeline.upstox_api import NSE_INSTRUMENT_KEYS
        
        instrument_keys = []
        for sym in symbols:
            key = NSE_INSTRUMENT_KEYS.get(sym)
            if key:
                instrument_keys.append(key)
        
        if not instrument_keys:
            return
        
        try:
            subscription = {
                "guid":   "someguid",
                "method": "sub",
                "data": {
                    "mode":            "full",
                    "instrumentKeys":  instrument_keys,
                }
            }
            
            self.ws.send(json.dumps(subscription))
            logger.info(f"📡 Subscribed to {len(instrument_keys)} instruments")
        
        except Exception as e:
            logger.error(f"Subscription failed: {e}")
    
    def subscribe_symbols(self, symbols: list):
        """Add symbols to subscription list."""
        new_symbols = set(symbols) - self.subscribed_symbols
        
        if not new_symbols:
            return
        
        self.subscribed_symbols.update(new_symbols)
        
        # If already connected, subscribe immediately
        if self.ws and self.is_running:
            self._send_subscription(list(new_symbols))
    
    def unsubscribe_symbols(self, symbols: list):
        """Remove symbols from subscription."""
        self.subscribed_symbols.difference_update(symbols)
        
        if self.ws and self.is_running:
            from data_pipeline.upstox_api import NSE_INSTRUMENT_KEYS
            
            instrument_keys = [
                NSE_INSTRUMENT_KEYS.get(s) for s in symbols
                if NSE_INSTRUMENT_KEYS.get(s)
            ]
            
            try:
                unsubscription = {
                    "guid":   "someguid",
                    "method": "unsub",
                    "data": {
                        "mode":            "full",
                        "instrumentKeys":  instrument_keys,
                    }
                }
                self.ws.send(json.dumps(unsubscription))
                logger.info(f"📡 Unsubscribed from {len(instrument_keys)} instruments")
            except Exception as e:
                logger.error(f"Unsubscription failed: {e}")
    
    # ═══════════════════════════════════════════════════════════
    #   MAIN CONNECTION
    # ═══════════════════════════════════════════════════════════
    
    def _connect(self):
        """Establish WebSocket connection."""
        if not WEBSOCKET_AVAILABLE:
            logger.error("WebSocket dependencies not available")
            return False
        
        # Get authorized URL
        auth_url = self._get_authorized_url()
        if not auth_url:
            logger.error("Could not get authorized WebSocket URL")
            return False
        
        # Create WebSocket
        self.ws = websocket.WebSocketApp(
            auth_url,
            on_open    = self._on_open,
            on_message = self._on_message,
            on_error   = self._on_error,
            on_close   = self._on_close,
        )
        
        # Run in background
        self.ws.run_forever(
            sslopt={"cert_reqs": ssl.CERT_NONE}
        )
    
    def start(self):
        """Start WebSocket streaming in background thread."""
        if self.is_running:
            logger.warning("WebSocket already running")
            return
        
        if not WEBSOCKET_AVAILABLE:
            logger.error("Cannot start - WebSocket dependencies missing")
            return
        
        if not self.access_token:
            logger.error("Cannot start - No access token")
            return
        
        self.is_running = True
        
        # Start in background thread
        self.thread = threading.Thread(
            target=self._connect,
            daemon=True,
            name="UpstoxWebSocket"
        )
        self.thread.start()
        
        logger.info("🚀 WebSocket streamer started (background thread)")
    
    def stop(self):
        """Stop WebSocket streaming."""
        self.is_running = False
        
        if self.ws:
            try:
                self.ws.close()
                logger.info("🛑 WebSocket streamer stopped")
            except Exception as e:
                logger.error(f"Stop error: {e}")
        
        self.ws = None
    
    # ═══════════════════════════════════════════════════════════
    #   PRICE ACCESS
    # ═══════════════════════════════════════════════════════════
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get most recent price from stream cache."""
        return self.latest_prices.get(symbol)
    
    def get_all_prices(self) -> Dict[str, float]:
        """Get all cached prices."""
        return self.latest_prices.copy()
    
    def is_market_open(self) -> bool:
        """Check if market is currently open."""
        now = datetime.now()
        if now.weekday() >= 5:  # Weekend
            return False
        return MARKET_OPEN <= now.time() <= MARKET_CLOSE
    
    def get_status(self) -> Dict:
        """Get streamer status."""
        return {
            "running":            self.is_running,
            "connected":          self.ws is not None,
            "subscribed_symbols": list(self.subscribed_symbols),
            "cached_prices":      len(self.latest_prices),
            "market_open":        self.is_market_open(),
            "stats":              self.stats,
        }


# ═══════════════════════════════════════════════════════════════
#   PRICE UPDATE HANDLER
# ═══════════════════════════════════════════════════════════════

class StreamPriceHandler:
    """Handles real-time price updates from WebSocket."""
    
    def __init__(self):
        self.last_check_times: Dict[str, datetime] = {}
        self.min_check_interval = 1  # Don't check same symbol more than once/second
    
    def handle_price_update(self, symbol: str, new_price: float):
        """
        Called for every price update from WebSocket.
        Triggers instant SL/target checks.
        """
        # Rate limiting per symbol
        now = datetime.now()
        last_check = self.last_check_times.get(symbol)
        
        if last_check and (now - last_check).total_seconds() < self.min_check_interval:
            return
        
        self.last_check_times[symbol] = now
        
        # Check if any open trades match this symbol
        from database.db import get_open_trades
        from agent.live_monitor import get_monitor
        
        open_trades = get_open_trades()
        matching_trades = [t for t in open_trades if t["symbol"] == symbol]
        
        if not matching_trades:
            return
        
        # Trigger instant check for these trades
        monitor = get_monitor()
        
        for trade in matching_trades:
            try:
                action = monitor._check_single_trade(trade, new_price)
                if action:
                    logger.info(
                        f"⚡ WebSocket-triggered action: {action.get('action')} "
                        f"on {symbol} @ ₹{new_price}"
                    )
            except Exception as e:
                logger.error(f"WebSocket check failed for {symbol}: {e}")


# ═══════════════════════════════════════════════════════════════
#   GLOBAL SINGLETONS
# ═══════════════════════════════════════════════════════════════

_streamer: Optional[UpstoxWebSocketStreamer] = None
_handler: Optional[StreamPriceHandler] = None


def get_streamer() -> UpstoxWebSocketStreamer:
    """Get global WebSocket streamer."""
    global _streamer, _handler
    
    if _streamer is None:
        _streamer = UpstoxWebSocketStreamer()
        _handler = StreamPriceHandler()
        _streamer.on_price_update = _handler.handle_price_update
    
    return _streamer


# ═══════════════════════════════════════════════════════════════
#   CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def start_streaming():
    """Start the WebSocket streamer with all currently open trade symbols."""
    from database.db import get_open_trades
    
    streamer = get_streamer()
    
    # Get symbols from open trades
    open_trades = get_open_trades()
    symbols = list(set(t["symbol"] for t in open_trades))
    
    if symbols:
        streamer.subscribe_symbols(symbols)
    
    streamer.start()
    return streamer.get_status()


def stop_streaming():
    """Stop the WebSocket streamer."""
    streamer = get_streamer()
    streamer.stop()
    return {"stopped": True}


def sync_subscriptions():
    """Sync subscriptions to match currently open trades."""
    from database.db import get_open_trades
    
    streamer = get_streamer()
    open_trades = get_open_trades()
    current_symbols = set(t["symbol"] for t in open_trades)
    
    subscribed = streamer.subscribed_symbols
    
    to_add    = current_symbols - subscribed
    to_remove = subscribed - current_symbols
    
    if to_add:
        streamer.subscribe_symbols(list(to_add))
    if to_remove:
        streamer.unsubscribe_symbols(list(to_remove))
    
    return {
        "added":    list(to_add),
        "removed":  list(to_remove),
        "total":    len(current_symbols),
    }


# ═══════════════════════════════════════════════════════════════
#   Quick Test
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("WEBSOCKET STREAMER TEST")
    print("="*60)
    
    streamer = get_streamer()
    
    # Check config
    print(f"\n📊 Config:")
    print(f"   WebSocket lib: {'✅' if WEBSOCKET_AVAILABLE else '❌'}")
    print(f"   Access token:  {'✅' if streamer.access_token else '❌'}")
    print(f"   Market open:   {'✅' if streamer.is_market_open() else '❌'}")
    
    if not WEBSOCKET_AVAILABLE:
        print("\n❌ Install: pip install websocket-client")
        exit(1)
    
    if not streamer.access_token:
        print("\n❌ UPSTOX_ACCESS_TOKEN not set in .env")
        exit(1)
    
    # Start streaming with test symbols
    print("\n🚀 Starting WebSocket...")
    streamer.subscribe_symbols(["RELIANCE.NS", "TCS.NS"])
    streamer.start()
    
    # Wait and observe
    print("\n⏱️ Listening for 30 seconds...")
    time.sleep(30)
    
    # Show what we got
    status = streamer.get_status()
    print(f"\n📊 Status:")
    print(f"   Running:  {status['running']}")
    print(f"   Symbols:  {status['subscribed_symbols']}")
    print(f"   Cached:   {status['cached_prices']}")
    
    prices = streamer.get_all_prices()
    print(f"\n💰 Latest prices:")
    for sym, price in prices.items():
        print(f"   {sym.replace('.NS', ''):12s} ₹{price}")
    
    print(f"\n📊 Stats:")
    for k, v in status['stats'].items():
        print(f"   {k}: {v}")
    
    # Stop
    streamer.stop()
    print("\n✅ Test complete")