# E:\tradedo\app\backend\agent\charges_calculator.py

"""
BROKERAGE & CHARGES CALCULATOR
Calculates real brokerage costs like Upstox/Zerodha.
Includes all taxes and fees per SEBI regulations.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
from typing import Dict
from datetime import datetime

logger = logging.getLogger("tradedo.charges")


# ═══════════════════════════════════════════════════════════════
#   BROKERAGE CONFIGURATION (Upstox Rates - Aug 2026)
# ═══════════════════════════════════════════════════════════════

BROKERAGE_CONFIG = {
    # ── Equity Delivery (CNC) ─────────────────────────────
    "DELIVERY": {
        "brokerage_pct":       0.0,        # ZERO brokerage for delivery
        "brokerage_min":       0,
        "brokerage_max":       0,
        "stt_pct":             0.001,      # 0.1% on both buy & sell
        "exchange_txn_pct":    0.0000325,  # NSE: 0.00325%
        "gst_pct":             0.18,       # 18% on brokerage + txn
        "sebi_charges_pct":    0.000001,   # ₹10 per crore
        "stamp_duty_pct":      0.00015,    # 0.015% on buy side only
    },
    
    # ── Equity Intraday (MIS) ──────────────────────────────
    "INTRADAY": {
        "brokerage_pct":       0.0003,     # 0.03% or ₹20, whichever less
        "brokerage_min":       0,
        "brokerage_max":       20,         # ₹20 max per order
        "stt_pct":             0.00025,    # 0.025% on sell side only
        "exchange_txn_pct":    0.0000325,  # NSE
        "gst_pct":             0.18,
        "sebi_charges_pct":    0.000001,
        "stamp_duty_pct":      0.00003,    # 0.003% on buy side
    },
    
    # ── Futures ────────────────────────────────────────────
    "FUTURES": {
        "brokerage_pct":       0.0003,
        "brokerage_min":       0,
        "brokerage_max":       20,
        "stt_pct":             0.0001,     # 0.01% on sell
        "exchange_txn_pct":    0.0000019,  # NSE: 0.00019%
        "gst_pct":             0.18,
        "sebi_charges_pct":    0.000001,
        "stamp_duty_pct":      0.00002,
    },
    
    # ── Options ────────────────────────────────────────────
    "OPTIONS": {
        "brokerage_pct":       0.0,        # Flat ₹20 per order
        "brokerage_min":       20,
        "brokerage_max":       20,
        "stt_pct":             0.0005,     # 0.05% on sell side (premium)
        "exchange_txn_pct":    0.0005,     # NSE: 0.053%
        "gst_pct":             0.18,
        "sebi_charges_pct":    0.000001,
        "stamp_duty_pct":      0.00003,
    },
}


# ═══════════════════════════════════════════════════════════════
#   MAIN CALCULATOR
# ═══════════════════════════════════════════════════════════════

class ChargesCalculator:
    """Calculates all charges for a trade."""
    
    @staticmethod
    def calculate_charges(
        symbol: str,
        quantity: int,
        price: float,
        side: str,              # BUY or SELL
        product_type: str = "INTRADAY",  # INTRADAY, DELIVERY, FUTURES, OPTIONS
    ) -> Dict:
        """
        Calculate complete charges for a single trade leg.
        
        Returns:
            {
                "gross_value": ₹100,000 (turnover)
                "brokerage": ₹20
                "stt": ₹25
                "exchange_charges": ₹3.25
                "sebi_charges": ₹0.10
                "stamp_duty": ₹3
                "gst": ₹4.19
                "total_charges": ₹55.54
                "net_value": ₹99,944.46 (after all charges)
            }
        """
        config = BROKERAGE_CONFIG.get(product_type.upper(), BROKERAGE_CONFIG["INTRADAY"])
        
        # Turnover
        turnover = quantity * price
        
        # ── Brokerage ────────────────────────────────────────
        brokerage_pct_amt = turnover * config["brokerage_pct"]
        
        if config["brokerage_min"] > 0:
            brokerage = max(config["brokerage_min"], brokerage_pct_amt)
        else:
            brokerage = brokerage_pct_amt
        
        if config["brokerage_max"] > 0:
            brokerage = min(config["brokerage_max"], brokerage)
        
        brokerage = round(brokerage, 2)
        
        # ── STT (Securities Transaction Tax) ─────────────────
        # Applied on BUY for delivery, SELL for intraday/F&O
        stt = 0.0
        if product_type.upper() == "DELIVERY":
            # Both sides
            stt = round(turnover * config["stt_pct"], 2)
        elif side.upper() == "SELL":
            # Only sell side for intraday and F&O
            stt = round(turnover * config["stt_pct"], 2)
        
        # ── Exchange Transaction Charges ─────────────────────
        exchange_charges = round(turnover * config["exchange_txn_pct"], 2)
        
        # ── SEBI Charges ─────────────────────────────────────
        sebi_charges = round(turnover * config["sebi_charges_pct"], 2)
        
        # ── Stamp Duty (only on BUY side) ────────────────────
        stamp_duty = 0.0
        if side.upper() == "BUY":
            stamp_duty = round(turnover * config["stamp_duty_pct"], 2)
        
        # ── GST (18% on brokerage + exchange charges + SEBI) ─
        gst_base = brokerage + exchange_charges + sebi_charges
        gst = round(gst_base * config["gst_pct"], 2)
        
        # ── Total Charges ────────────────────────────────────
        total_charges = round(
            brokerage + stt + exchange_charges + 
            sebi_charges + stamp_duty + gst,
            2
        )
        
        # ── Net Value ────────────────────────────────────────
        if side.upper() == "BUY":
            # For buy: total_paid = turnover + charges
            net_value = round(turnover + total_charges, 2)
        else:
            # For sell: total_received = turnover - charges
            net_value = round(turnover - total_charges, 2)
        
        return {
            "product_type":     product_type.upper(),
            "side":             side.upper(),
            "quantity":         quantity,
            "price":            price,
            "turnover":         round(turnover, 2),
            "brokerage":        brokerage,
            "stt":              stt,
            "exchange_charges": exchange_charges,
            "sebi_charges":     sebi_charges,
            "stamp_duty":       stamp_duty,
            "gst":              gst,
            "total_charges":    total_charges,
            "net_value":        net_value,
            "charges_pct":      round((total_charges / turnover) * 100, 4) if turnover > 0 else 0,
        }
    
    @staticmethod
    def calculate_roundtrip(
        symbol: str,
        quantity: int,
        buy_price: float,
        sell_price: float,
        product_type: str = "INTRADAY",
    ) -> Dict:
        """
        Calculate full round-trip charges (buy + sell) and net P&L.
        
        Returns comprehensive breakdown including net P&L after charges.
        """
        # Buy leg
        buy_leg = ChargesCalculator.calculate_charges(
            symbol=symbol,
            quantity=quantity,
            price=buy_price,
            side="BUY",
            product_type=product_type,
        )
        
        # Sell leg
        sell_leg = ChargesCalculator.calculate_charges(
            symbol=symbol,
            quantity=quantity,
            price=sell_price,
            side="SELL",
            product_type=product_type,
        )
        
        # Gross P&L (before charges)
        gross_pnl = round((sell_price - buy_price) * quantity, 2)
        
        # Total charges (both legs)
        total_charges = round(buy_leg["total_charges"] + sell_leg["total_charges"], 2)
        
        # Net P&L (after charges)
        net_pnl = round(gross_pnl - total_charges, 2)
        
        # P&L percentages
        turnover_avg = (buy_leg["turnover"] + sell_leg["turnover"]) / 2
        gross_pnl_pct = round((gross_pnl / buy_leg["turnover"]) * 100, 2) if buy_leg["turnover"] else 0
        net_pnl_pct = round((net_pnl / buy_leg["turnover"]) * 100, 2) if buy_leg["turnover"] else 0
        charges_pct = round((total_charges / turnover_avg) * 100, 4) if turnover_avg else 0
        
        # Breakeven move needed
        breakeven_move_pct = round((total_charges / buy_leg["turnover"]) * 100, 4) if buy_leg["turnover"] else 0
        
        return {
            "product_type":       product_type.upper(),
            "quantity":           quantity,
            "buy_price":          buy_price,
            "sell_price":         sell_price,
            
            # Legs breakdown
            "buy_leg":            buy_leg,
            "sell_leg":           sell_leg,
            
            # P&L
            "gross_pnl":          gross_pnl,
            "gross_pnl_pct":      gross_pnl_pct,
            "total_charges":      total_charges,
            "net_pnl":            net_pnl,
            "net_pnl_pct":        net_pnl_pct,
            "charges_pct":        charges_pct,
            
            # Breakeven
            "breakeven_move_pct": breakeven_move_pct,
        }


# ═══════════════════════════════════════════════════════════════
#   Convenience Functions
# ═══════════════════════════════════════════════════════════════

def calculate_charges(**kwargs) -> Dict:
    """Wrapper for charge calculation."""
    return ChargesCalculator.calculate_charges(**kwargs)


def calculate_roundtrip_pnl(**kwargs) -> Dict:
    """Wrapper for round-trip P&L calculation."""
    return ChargesCalculator.calculate_roundtrip(**kwargs)


def get_brokerage_rates() -> Dict:
    """Get current brokerage rates for display."""
    return BROKERAGE_CONFIG


# ═══════════════════════════════════════════════════════════════
#   Quick Test
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("BROKERAGE CALCULATOR TEST")
    print("="*60)
    
    # Test 1: Intraday BUY
    print("\n📊 Test 1: INTRADAY BUY - RELIANCE 10 shares @ ₹1300")
    result = calculate_charges(
        symbol="RELIANCE.NS",
        quantity=10,
        price=1300,
        side="BUY",
        product_type="INTRADAY",
    )
    for k, v in result.items():
        print(f"   {k:20s}: {v}")
    
    # Test 2: Full Round-Trip
    print("\n📊 Test 2: ROUND-TRIP - RELIANCE 10 shares, ₹1300 → ₹1320")
    result = calculate_roundtrip_pnl(
        symbol="RELIANCE.NS",
        quantity=10,
        buy_price=1300,
        sell_price=1320,
        product_type="INTRADAY",
    )
    print(f"   Gross P&L:          ₹{result['gross_pnl']}")
    print(f"   Total Charges:      ₹{result['total_charges']}")
    print(f"   Net P&L:            ₹{result['net_pnl']}")
    print(f"   Net P&L %:          {result['net_pnl_pct']}%")
    print(f"   Charges %:          {result['charges_pct']}%")
    print(f"   Breakeven needed:   {result['breakeven_move_pct']}% up")
    
    # Test 3: Delivery
    print("\n📊 Test 3: DELIVERY - TCS 5 shares @ ₹3900")
    result = calculate_charges(
        symbol="TCS.NS",
        quantity=5,
        price=3900,
        side="BUY",
        product_type="DELIVERY",
    )
    print(f"   Turnover:           ₹{result['turnover']}")
    print(f"   Brokerage:          ₹{result['brokerage']} (Delivery is FREE)")
    print(f"   Total Charges:      ₹{result['total_charges']}")
    print(f"   Net Value:          ₹{result['net_value']}")
    
    # Test 4: Options
    print("\n📊 Test 4: OPTIONS - Nifty CE Buy")
    result = calculate_charges(
        symbol="NIFTY_CE",
        quantity=50,  # 1 lot
        price=100,
        side="BUY",
        product_type="OPTIONS",
    )
    print(f"   Turnover:           ₹{result['turnover']}")
    print(f"   Brokerage:          ₹{result['brokerage']}")
    print(f"   Total Charges:      ₹{result['total_charges']}")