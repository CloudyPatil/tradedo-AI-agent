# E:\tradedo\app\backend\agent\sectors.py

"""
Sector mapping for diversification.
Prevents concentration risk (e.g., 3 bank trades at once).
"""

STOCK_SECTORS = {
    # ── Banking & Financial ────────────────────────────────
    "HDFCBANK.NS": "BANKING",
    "ICICIBANK.NS": "BANKING",
    "KOTAKBANK.NS": "BANKING",
    "AXISBANK.NS": "BANKING",
    "SBIN.NS": "BANKING",
    "INDUSINDBK.NS": "BANKING",
    "BANKBARODA.NS": "BANKING",
    "CANBK.NS": "BANKING",
    "PNB.NS": "BANKING",
    "YESBANK.NS": "BANKING",
    "IDFCFIRSTB.NS": "BANKING",
    "BANDHANBNK.NS": "BANKING",
    "BAJFINANCE.NS": "NBFC",
    "BAJAJFINSV.NS": "NBFC",
    "SHRIRAMFIN.NS": "NBFC",
    "CHOLAFIN.NS": "NBFC",
    "MUTHOOTFIN.NS": "NBFC",
    "MANAPPURAM.NS": "NBFC",
    "PFC.NS": "NBFC",
    "RECLTD.NS": "NBFC",
    "LICHSGFIN.NS": "NBFC",
    "HDFCLIFE.NS": "INSURANCE",
    "SBILIFE.NS": "INSURANCE",
    "MFSL.NS": "INSURANCE",
    
    # ── IT & Tech ──────────────────────────────────────────
    "TCS.NS": "IT",
    "INFY.NS": "IT",
    "WIPRO.NS": "IT",
    "HCLTECH.NS": "IT",
    "TECHM.NS": "IT",
    "LTIM.NS": "IT",
    "MPHASIS.NS": "IT",
    "MINDTREE.NS": "IT",
    "PERSISTENT.NS": "IT",
    "COFORGE.NS": "IT",
    "ZENSAR.NS": "IT",
    "KPITTECH.NS": "IT",
    "TATAELXSI.NS": "IT",
    "OFSS.NS": "IT",
    
    # ── Auto ───────────────────────────────────────────────
    "MARUTI.NS": "AUTO",
    "M&M.NS": "AUTO",
    "TATAMOTORS.NS": "AUTO",
    "EICHERMOT.NS": "AUTO",
    "HEROMOTOCO.NS": "AUTO",
    "BAJAJ-AUTO.NS": "AUTO",
    "TVSMOTOR.NS": "AUTO",
    "MOTHERSON.NS": "AUTO",
    "BOSCHLTD.NS": "AUTO",
    
    # ── Pharma ─────────────────────────────────────────────
    "SUNPHARMA.NS": "PHARMA",
    "DRREDDY.NS": "PHARMA",
    "CIPLA.NS": "PHARMA",
    "DIVISLAB.NS": "PHARMA",
    "APOLLOHOSP.NS": "HEALTHCARE",
    "TORNTPHARM.NS": "PHARMA",
    "AUROPHARMA.NS": "PHARMA",
    "LUPIN.NS": "PHARMA",
    "BIOCON.NS": "PHARMA",
    "GLENMARK.NS": "PHARMA",
    "ALKEM.NS": "PHARMA",
    "CADILAHC.NS": "PHARMA",
    
    # ── FMCG ───────────────────────────────────────────────
    "HINDUNILVR.NS": "FMCG",
    "ITC.NS": "FMCG",
    "NESTLEIND.NS": "FMCG",
    "BRITANNIA.NS": "FMCG",
    "DABUR.NS": "FMCG",
    "MARICO.NS": "FMCG",
    "GODREJCP.NS": "FMCG",
    "COLPAL.NS": "FMCG",
    "TATACONSUM.NS": "FMCG",
    "PGHH.NS": "FMCG",
    "VBL.NS": "FMCG",
    "UBL.NS": "FMCG",
    "MCDOWELL-N.NS": "FMCG",
    
    # ── Metals ─────────────────────────────────────────────
    "TATASTEEL.NS": "METALS",
    "JSWSTEEL.NS": "METALS",
    "HINDALCO.NS": "METALS",
    "VEDL.NS": "METALS",
    "JINDALSTEL.NS": "METALS",
    "SAIL.NS": "METALS",
    "NMDC.NS": "METALS",
    "NATIONALUM.NS": "METALS",
    "HINDCOPPER.NS": "METALS",
    "COALINDIA.NS": "MINING",
    
    # ── Energy ─────────────────────────────────────────────
    "RELIANCE.NS": "ENERGY",
    "ONGC.NS": "ENERGY",
    "BPCL.NS": "ENERGY",
    "IOC.NS": "ENERGY",
    "HINDPETRO.NS": "ENERGY",
    "GAIL.NS": "ENERGY",
    "NTPC.NS": "POWER",
    "POWERGRID.NS": "POWER",
    "TATAPOWER.NS": "POWER",
    "ADANIPOWER.NS": "POWER",
    "ADANIGREEN.NS": "POWER",
    "NHPC.NS": "POWER",
    "SUZLON.NS": "POWER",
    "IREDA.NS": "POWER",
    
    # ── Cement ─────────────────────────────────────────────
    "ULTRACEMCO.NS": "CEMENT",
    "GRASIM.NS": "CEMENT",
    "AMBUJACEM.NS": "CEMENT",
    
    # ── Consumer ───────────────────────────────────────────
    "ASIANPAINT.NS": "PAINTS",
    "BERGEPAINT.NS": "PAINTS",
    "PIDILITIND.NS": "CHEMICALS",
    "TITAN.NS": "CONSUMER",
    "HAVELLS.NS": "CONSUMER",
    "BATAINDIA.NS": "CONSUMER",
    "PAGEIND.NS": "CONSUMER",
    "TRENT.NS": "RETAIL",
    "DMART.NS": "RETAIL",
    "NYKAA.NS": "RETAIL",
    
    # ── Telecom ────────────────────────────────────────────
    "BHARTIARTL.NS": "TELECOM",
    "IDEA.NS": "TELECOM",
    
    # ── Infrastructure ─────────────────────────────────────
    "LT.NS": "INFRA",
    "ADANIPORTS.NS": "INFRA",
    "ADANIENT.NS": "CONGLOMERATE",
    "SIEMENS.NS": "INFRA",
    "GMRINFRA.NS": "INFRA",
    "IRCTC.NS": "TRANSPORT",
    "INDIGO.NS": "AVIATION",
    "SPICEJET.NS": "AVIATION",
    "RVNL.NS": "INFRA",
    "IRFC.NS": "INFRA",
    
    # ── Others ─────────────────────────────────────────────
    "UPL.NS": "AGRI",
    "PIIND.NS": "CHEMICALS",
    "DEEPAKNTR.NS": "CHEMICALS",
    "GNFC.NS": "CHEMICALS",
    "ASTRAL.NS": "PIPES",
    "POLYCAB.NS": "CABLES",
    "DIXON.NS": "ELECTRONICS",
    "AMBER.NS": "ELECTRONICS",
    "BEL.NS": "DEFENCE",
    "ITI.NS": "TELECOM",
    "PVR.NS": "MEDIA",
    "ZOMATO.NS": "TECH",
    "PAYTM.NS": "TECH",
    "POLICYBZR.NS": "TECH",
    "NAUKRI.NS": "TECH",
    "MAPMYINDIA.NS": "TECH",
    "DELHIVERY.NS": "LOGISTICS",
    "FSL.NS": "IT",
    "CAMS.NS": "FINANCIAL_TECH",
    "CDSL.NS": "FINANCIAL_TECH",
    "BSE.NS": "FINANCIAL_TECH",
    "ANGELONE.NS": "FINANCIAL_TECH",
    "IEX.NS": "POWER",
    "GODREJPROP.NS": "REALTY",
    "BAJAJHLDNG.NS": "HOLDING",
    "ABCAPITAL.NS": "NBFC",
    "TATAMTRDVR.NS": "AUTO",
}


def get_sector(symbol: str) -> str:
    """Get sector for a stock. Returns 'UNKNOWN' if not mapped."""
    return STOCK_SECTORS.get(symbol.upper(), "UNKNOWN")


def get_stocks_by_sector(sector: str) -> list:
    """Get all stocks in a given sector."""
    return [s for s, sec in STOCK_SECTORS.items() if sec == sector]


def get_all_sectors() -> list:
    """Get list of all unique sectors."""
    return list(set(STOCK_SECTORS.values()))


def diversify_candidates(candidates: list, max_per_sector: int = 1) -> list:
    """
    Filter candidates to enforce sector diversification.
    
    Args:
        candidates: List of dicts with 'symbol' key
        max_per_sector: Max trades per sector
    
    Returns:
        Filtered list — no more than max_per_sector per sector
    """
    sector_count = {}
    diversified = []
    
    for candidate in candidates:
        symbol = candidate.get("symbol", "")
        sector = get_sector(symbol)
        
        current = sector_count.get(sector, 0)
        if current < max_per_sector:
            candidate["sector"] = sector
            diversified.append(candidate)
            sector_count[sector] = current + 1
    
    return diversified


if __name__ == "__main__":
    print(f"Total mapped stocks: {len(STOCK_SECTORS)}")
    print(f"Total sectors: {len(get_all_sectors())}")
    print(f"\nSectors: {sorted(get_all_sectors())}")
    print(f"\nBanking stocks: {get_stocks_by_sector('BANKING')}")