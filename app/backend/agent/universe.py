# E:\tradedo\app\backend\agent\universe.py

"""
Curated stock universe for intraday trading.
Only liquid stocks that can handle intraday volume.
"""

# ─── Tier 1: Nifty 50 (Always Scan) ──────────────────────────
NIFTY_50 = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "HINDUNILVR.NS",
    "INFY.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "HCLTECH.NS", "ASIANPAINT.NS", "MARUTI.NS",
    "BAJFINANCE.NS", "TITAN.NS", "SUNPHARMA.NS", "ULTRACEMCO.NS", "NESTLEIND.NS",
    "WIPRO.NS", "M&M.NS", "TATAMOTORS.NS", "NTPC.NS", "POWERGRID.NS",
    "TECHM.NS", "HDFCLIFE.NS", "ADANIENT.NS", "COALINDIA.NS", "BAJAJFINSV.NS",
    "DIVISLAB.NS", "TATASTEEL.NS", "GRASIM.NS", "JSWSTEEL.NS", "BRITANNIA.NS",
    "CIPLA.NS", "SBILIFE.NS", "ONGC.NS", "DRREDDY.NS", "EICHERMOT.NS",
    "APOLLOHOSP.NS", "INDUSINDBK.NS", "HINDALCO.NS", "BAJAJ-AUTO.NS", "TATACONSUM.NS",
    "HEROMOTOCO.NS", "ADANIPORTS.NS", "UPL.NS", "BPCL.NS", "SHRIRAMFIN.NS"
]

# ─── Tier 2: High-Volume Mid Caps (Scan if Tier 1 gives < 5 signals) ─
NIFTY_NEXT_50 = [
    "DMART.NS", "PIDILITIND.NS", "GODREJCP.NS", "SIEMENS.NS", "AMBUJACEM.NS",
    "DABUR.NS", "MARICO.NS", "HAVELLS.NS", "BERGEPAINT.NS", "GAIL.NS",
    "IOC.NS", "TORNTPHARM.NS", "MCDOWELL-N.NS", "BOSCHLTD.NS", "COLPAL.NS",
    "MOTHERSON.NS", "BEL.NS", "VEDL.NS", "TVSMOTOR.NS", "BANKBARODA.NS",
    "CANBK.NS", "PNB.NS", "TRENT.NS", "ADANIPOWER.NS", "ADANIGREEN.NS",
    "JINDALSTEL.NS", "PFC.NS", "RECLTD.NS", "IRCTC.NS", "ZOMATO.NS",
    "PAYTM.NS", "NAUKRI.NS", "POLYCAB.NS", "SAIL.NS", "IDEA.NS",
    "ABCAPITAL.NS", "MUTHOOTFIN.NS", "CHOLAFIN.NS", "PIIND.NS", "AUROPHARMA.NS",
    "LUPIN.NS", "BIOCON.NS", "GLENMARK.NS", "ALKEM.NS", "CADILAHC.NS",
    "PGHH.NS", "OFSS.NS", "MPHASIS.NS", "MINDTREE.NS", "LTIM.NS"
]

# ─── Tier 3: Popular Traders' Picks ──────────────────────────
POPULAR_MIDCAPS = [
    "IRFC.NS", "IRCTC.NS", "YESBANK.NS", "IDFCFIRSTB.NS", "BANDHANBNK.NS",
    "SUZLON.NS", "RVNL.NS", "IREDA.NS", "TATAPOWER.NS", "NHPC.NS",
    "DELHIVERY.NS", "NYKAA.NS", "POLICYBZR.NS", "MAPMYINDIA.NS", "FSL.NS",
    "PVR.NS", "INDIGO.NS", "SPICEJET.NS", "GMRINFRA.NS", "MANAPPURAM.NS",
    "BATAINDIA.NS", "PAGEIND.NS", "ASTRAL.NS", "DEEPAKNTR.NS", "GNFC.NS",
    "IEX.NS", "ANGELONE.NS", "CAMS.NS", "CDSL.NS", "BSE.NS",
    "PERSISTENT.NS", "COFORGE.NS", "ZENSAR.NS", "KPITTECH.NS", "TATAELXSI.NS",
    "DIXON.NS", "AMBER.NS", "VBL.NS", "TATAMTRDVR.NS", "ITI.NS",
    "NATIONALUM.NS", "HINDCOPPER.NS", "NMDC.NS", "COALINDIA.NS", "HINDPETRO.NS",
    "MFSL.NS", "LICHSGFIN.NS", "BAJAJHLDNG.NS", "UBL.NS", "GODREJPROP.NS"
]


# ─── Combined Universe ──────────────────────────────────────
INTRADAY_UNIVERSE = list(set(NIFTY_50 + NIFTY_NEXT_50 + POPULAR_MIDCAPS))


def get_scan_universe(tier: str = "full") -> list:
    """
    Get stock universe for scanning.
    
    Args:
        tier: "tier1" (50), "tier2" (100), "full" (150)
    
    Returns:
        List of symbols
    """
    if tier == "tier1":
        return NIFTY_50
    elif tier == "tier2":
        return list(set(NIFTY_50 + NIFTY_NEXT_50))
    else:
        return INTRADAY_UNIVERSE


if __name__ == "__main__":
    print(f"Total universe: {len(INTRADAY_UNIVERSE)} stocks")
    print(f"Tier 1: {len(NIFTY_50)}")
    print(f"Tier 2: {len(set(NIFTY_50 + NIFTY_NEXT_50))}")