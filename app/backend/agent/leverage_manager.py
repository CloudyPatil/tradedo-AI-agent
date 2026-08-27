# E:\tradedo\app\backend\agent\leverage_manager.py

"""
LEVERAGE MANAGER
Calculates leverage/margin for intraday trades.
Matches Upstox MIS margins.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
from typing import Dict, Optional

logger = logging.getLogger("tradedo.leverage")


# ═══════════════════════════════════════════════════════════════
#   LEVERAGE CONFIGURATION (Based on Upstox MIS - Aug 2026)
# ═══════════════════════════════════════════════════════════════

LEVERAGE_MULTIPLIERS = {
    # Product-based leverage
    "INTRADAY": 5.0,       # MIS: 5x leverage (20% margin)
    "DELIVERY": 1.0,       # CNC: No leverage (100% margin)
    "FUTURES":  8.0,       # NRML: ~8x leverage
    "OPTIONS":  1.0,       # Full premium required
}

# Category-based margin overrides
# High volatility stocks have lower leverage
HIGH_VOLATILITY_STOCKS = {
    "SUZLON.NS", "YESBANK.NS", "IDEA.NS", "IREDA.NS",
    "PAYTM.NS", "ZOMATO.NS", "IRCTC.NS",
    "ADANIENT.NS", "ADANIPOWER.NS", "ADANIGREEN.NS",
    "IRFC.NS", "RVNL.NS", "NHPC.NS",
}

# Reduce leverage for these
VOLATILE_LEVERAGE_MULTIPLIER = 3.0   # 3x instead of 5x

# Nifty 50 gets full leverage
NIFTY_50_STOCKS = {
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "INFY.NS", "SBIN.NS", "BHARTIARTL.NS",
    "ITC.NS", "KOTAKBANK.NS", "LT.NS", "AXISBANK.NS",
    "HCLTECH.NS", "ASIANPAINT.NS", "MARUTI.NS", "BAJFINANCE.NS",
    "TITAN.NS", "SUNPHARMA.NS", "ULTRACEMCO.NS", "NESTLEIND.NS",
    "WIPRO.NS", "M&M.NS", "TATAMOTORS.NS", "NTPC.NS",
    "POWERGRID.NS", "TECHM.NS", "HDFCLIFE.NS", "COALINDIA.NS",
    "BAJAJFINSV.NS", "DIVISLAB.NS", "TATASTEEL.NS", "GRASIM.NS",
    "JSWSTEEL.NS", "BRITANNIA.NS", "CIPLA.NS", "SBILIFE.NS",
    "ONGC.NS", "DRREDDY.NS", "EICHERMOT.NS", "APOLLOHOSP.NS",
    "INDUSINDBK.NS", "HINDALCO.NS", "BAJAJ-AUTO.NS", "TATACONSUM.NS",
    "HEROMOTOCO.NS", "ADANIPORTS.NS", "UPL.NS", "BPCL.NS",
    "SHRIRAMFIN.NS", "ADANIENT.NS",
}


# ═══════════════════════════════════════════════════════════════
#   LEVERAGE MANAGER
# ═══════════════════════════════════════════════════════════════

class LeverageManager:
    """Manages leverage and margin calculations."""
    
    @staticmethod
    def get_leverage(symbol: str, product_type: str) -> float:
        """Get applicable leverage for a stock."""
        product_type = product_type.upper()
        symbol = symbol.upper()
        
        # Delivery has no leverage
        if product_type == "DELIVERY":
            return 1.0
        
        # High volatility stocks
        if symbol in HIGH_VOLATILITY_STOCKS:
            return VOLATILE_LEVERAGE_MULTIPLIER
        
        # Standard leverage
        return LEVERAGE_MULTIPLIERS.get(product_type, 1.0)
    
    @staticmethod
    def calculate_margin_required(
        symbol: str,
        quantity: int,
        price: float,
        product_type: str = "INTRADAY",
    ) -> Dict:
        """
        Calculate margin required for a trade.
        
        Returns:
            {
                "turnover": Full trade value
                "leverage": Leverage multiplier
                "margin_required": Actual money needed
                "margin_pct": Margin as % of turnover
                "buying_power": How much you can buy with available capital
            }
        """
        turnover = quantity * price
        leverage = LeverageManager.get_leverage(symbol, product_type)
        
        margin_required = turnover / leverage
        margin_pct = (margin_required / turnover) * 100 if turnover else 0
        
        return {
            "symbol":            symbol,
            "product_type":      product_type.upper(),
            "quantity":          quantity,
            "price":             price,
            "turnover":          round(turnover, 2),
            "leverage":          leverage,
            "margin_required":   round(margin_required, 2),
            "margin_pct":        round(margin_pct, 2),
        }
    
    @staticmethod
    def calculate_buying_power(
        available_capital: float,
        symbol: str,
        price: float,
        product_type: str = "INTRADAY",
    ) -> Dict:
        """
        Calculate maximum shares/value you can buy with available capital.
        """
        leverage = LeverageManager.get_leverage(symbol, product_type)
        
        max_buying_value = available_capital * leverage
        max_shares = int(max_buying_value / price) if price > 0 else 0
        
        return {
            "available_capital":  available_capital,
            "leverage":           leverage,
            "max_buying_value":   round(max_buying_value, 2),
            "max_shares":         max_shares,
            "product_type":       product_type.upper(),
        }
    
    @staticmethod
    def validate_position_size(
        symbol: str,
        quantity: int,
        price: float,
        available_capital: float,
        product_type: str = "INTRADAY",
    ) -> Dict:
        """
        Check if position size is valid given available capital.
        """
        margin_info = LeverageManager.calculate_margin_required(
            symbol=symbol,
            quantity=quantity,
            price=price,
            product_type=product_type,
        )
        
        margin_required = margin_info["margin_required"]
        
        return {
            "valid":              margin_required <= available_capital,
            "margin_required":    margin_required,
            "available_capital":  available_capital,
            "shortfall":          max(0, margin_required - available_capital),
            "leverage":           margin_info["leverage"],
        }


# ═══════════════════════════════════════════════════════════════
#   Convenience Functions
# ═══════════════════════════════════════════════════════════════

def get_leverage(symbol: str, product_type: str = "INTRADAY") -> float:
    return LeverageManager.get_leverage(symbol, product_type)


def calculate_margin(**kwargs) -> Dict:
    return LeverageManager.calculate_margin_required(**kwargs)


def calculate_buying_power(**kwargs) -> Dict:
    return LeverageManager.calculate_buying_power(**kwargs)


# ═══════════════════════════════════════════════════════════════
#   Quick Test
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("LEVERAGE CALCULATOR TEST")
    print("="*60)
    
    # Test 1: Intraday RELIANCE
    print("\n📊 Test 1: INTRADAY - RELIANCE 100 shares @ ₹1300")
    result = calculate_margin(
        symbol="RELIANCE.NS",
        quantity=100,
        price=1300,
        product_type="INTRADAY",
    )
    print(f"   Turnover:         ₹{result['turnover']:,}")
    print(f"   Leverage:         {result['leverage']}x")
    print(f"   Margin Required:  ₹{result['margin_required']:,}")
    print(f"   Margin %:         {result['margin_pct']}%")
    print(f"   → Buy ₹{result['turnover']:,} worth with only ₹{result['margin_required']:,}!")
    
    # Test 2: Volatile stock (Suzlon)
    print("\n📊 Test 2: INTRADAY - SUZLON 1000 shares @ ₹60 (volatile)")
    result = calculate_margin(
        symbol="SUZLON.NS",
        quantity=1000,
        price=60,
        product_type="INTRADAY",
    )
    print(f"   Turnover:         ₹{result['turnover']:,}")
    print(f"   Leverage:         {result['leverage']}x (reduced due to volatility)")
    print(f"   Margin Required:  ₹{result['margin_required']:,}")
    
    # Test 3: Delivery (no leverage)
    print("\n📊 Test 3: DELIVERY - HDFCBANK 20 shares @ ₹1700")
    result = calculate_margin(
        symbol="HDFCBANK.NS",
        quantity=20,
        price=1700,
        product_type="DELIVERY",
    )
    print(f"   Turnover:         ₹{result['turnover']:,}")
    print(f"   Leverage:         {result['leverage']}x (no leverage for delivery)")
    print(f"   Margin Required:  ₹{result['margin_required']:,} (100%)")
    
    # Test 4: Buying Power
    print("\n📊 Test 4: BUYING POWER - ₹20,000 capital for RELIANCE @ ₹1300")
    result = calculate_buying_power(
        available_capital=20000,
        symbol="RELIANCE.NS",
        price=1300,
        product_type="INTRADAY",
    )
    print(f"   Available:        ₹{result['available_capital']:,}")
    print(f"   Leverage:         {result['leverage']}x")
    print(f"   Max Buying Value: ₹{result['max_buying_value']:,}")
    print(f"   Max Shares:       {result['max_shares']}")