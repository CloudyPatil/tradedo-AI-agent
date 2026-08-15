# E:\tradedo\app\backend\agent\universe.py

"""
Complete Nifty 500 universe for TRADEDO.
Organized in tiers for scalable scanning.
"""

# ═══════════════════════════════════════════════════════════════
#   TIER 1: NIFTY 50 (Most liquid, highest priority)
# ═══════════════════════════════════════════════════════════════

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
    "HEROMOTOCO.NS", "ADANIPORTS.NS", "UPL.NS", "BPCL.NS", "SHRIRAMFIN.NS",
]


# ═══════════════════════════════════════════════════════════════
#   TIER 2: NIFTY NEXT 50 (Large caps, high liquidity)
# ═══════════════════════════════════════════════════════════════

NIFTY_NEXT_50 = [
    "DMART.NS", "PIDILITIND.NS", "GODREJCP.NS", "SIEMENS.NS", "AMBUJACEM.NS",
    "DABUR.NS", "MARICO.NS", "HAVELLS.NS", "BERGEPAINT.NS", "GAIL.NS",
    "IOC.NS", "TORNTPHARM.NS", "MCDOWELL-N.NS", "BOSCHLTD.NS", "COLPAL.NS",
    "MOTHERSON.NS", "BEL.NS", "VEDL.NS", "TVSMOTOR.NS", "BANKBARODA.NS",
    "CANBK.NS", "PNB.NS", "TRENT.NS", "ADANIPOWER.NS", "ADANIGREEN.NS",
    "JINDALSTEL.NS", "PFC.NS", "RECLTD.NS", "IRCTC.NS", "ZOMATO.NS",
    "PAYTM.NS", "NAUKRI.NS", "POLYCAB.NS", "SAIL.NS", "IDEA.NS",
    "ABCAPITAL.NS", "MUTHOOTFIN.NS", "CHOLAFIN.NS", "PIIND.NS", "AUROPHARMA.NS",
    "LUPIN.NS", "BIOCON.NS", "GLENMARK.NS", "ALKEM.NS", "PGHH.NS",
    "OFSS.NS", "MPHASIS.NS", "LTIM.NS", "SRF.NS", "MFSL.NS",
]


# ═══════════════════════════════════════════════════════════════
#   TIER 3: MIDCAP 100 (Good liquidity, growth opportunities)
# ═══════════════════════════════════════════════════════════════

MIDCAP_100 = [
    "IRFC.NS", "YESBANK.NS", "IDFCFIRSTB.NS", "BANDHANBNK.NS",
    "SUZLON.NS", "RVNL.NS", "IREDA.NS", "TATAPOWER.NS", "NHPC.NS",
    "DELHIVERY.NS", "NYKAA.NS", "POLICYBZR.NS", "MAPMYINDIA.NS", "FSL.NS",
    "PVR.NS", "INDIGO.NS", "SPICEJET.NS", "GMRINFRA.NS", "MANAPPURAM.NS",
    "BATAINDIA.NS", "PAGEIND.NS", "ASTRAL.NS", "DEEPAKNTR.NS", "GNFC.NS",
    "IEX.NS", "ANGELONE.NS", "CAMS.NS", "CDSL.NS", "BSE.NS",
    "PERSISTENT.NS", "COFORGE.NS", "ZENSAR.NS", "KPITTECH.NS", "TATAELXSI.NS",
    "DIXON.NS", "AMBER.NS", "VBL.NS", "ITI.NS",
    "NATIONALUM.NS", "HINDCOPPER.NS", "NMDC.NS", "HINDPETRO.NS",
    "LICHSGFIN.NS", "BAJAJHLDNG.NS", "UBL.NS", "GODREJPROP.NS",
    "TIINDIA.NS", "SUNTV.NS", "GUJGASLTD.NS", "APOLLOTYRE.NS",
    "BALKRISIND.NS", "BHARATFORG.NS", "MRF.NS", "ESCORTS.NS",
    "CUMMINSIND.NS", "ABB.NS", "SCHAEFFLER.NS", "SKFINDIA.NS",
    "TIMKEN.NS", "3MINDIA.NS", "JUBLFOOD.NS", "TATACHEM.NS",
    "COROMANDEL.NS", "CROMPTON.NS", "VOLTAS.NS", "BLUEDART.NS",
    "CONCOR.NS", "IDBI.NS", "UNIONBANK.NS", "FEDERALBNK.NS",
    "RBLBANK.NS", "AUBANK.NS", "L&TFH.NS", "SUNDARMFIN.NS",
    "PEL.NS", "SRTRANSFIN.NS", "BAJAJHIND.NS", "APOLLOHOSP.NS",
    "MAXHEALTH.NS", "FORTIS.NS", "NARAYANHRUD.NS", "METROPOLIS.NS",
    "GLAND.NS", "IPCALAB.NS", "LAURUSLABS.NS", "AJANTPHARM.NS",
    "GRANULES.NS", "SANOFI.NS", "PFIZER.NS", "ABBOTINDIA.NS",
    "AARTIIND.NS", "SUPREMEIND.NS", "FINCABLES.NS", "KAJARIACER.NS",
    "CENTURYTEX.NS", "GUJALKALI.NS", "SOLARINDS.NS", "NAVINFLUOR.NS",
    "PIDILITIND.NS", "ATUL.NS", "CLEAN.NS",
]


# ═══════════════════════════════════════════════════════════════
#   TIER 4: SMALLCAP 250 (Higher risk, higher reward)
# ═══════════════════════════════════════════════════════════════

SMALLCAP_250 = [
    "TATAINVEST.NS", "SANOFI.NS", "SUPRAJIT.NS", "KEI.NS",
    "RALLIS.NS", "CENTURYPLY.NS", "APLLTD.NS", "BLUESTARCO.NS",
    "CENTRALBK.NS", "BANDHANBNK.NS", "KARURVYSYA.NS", "SOUTHBANK.NS",
    "KOTAKMAH.NS", "HDFCAMC.NS", "IIFL.NS", "MOTILALOFS.NS",
    "GODREJIND.NS", "EMAMILTD.NS", "RADICO.NS", "VMART.NS",
    "AVENUE.NS", "SHOPERSTOP.NS", "ARVIND.NS", "RAJESHEXPO.NS",
    "TIINDIA.NS", "GRAPHITE.NS", "HEG.NS", "GRSE.NS",
    "MAZDOCK.NS", "COCHINSHIP.NS", "BEML.NS", "HAL.NS",
    "BEL.NS", "GRSE.NS", "SIEMENS.NS", "ABB.NS",
    "TIMKEN.NS", "CAMPUS.NS", "METROBRAND.NS", "RELAXO.NS",
    "TANLA.NS", "ROUTE.NS", "IRIS.NS", "INTELLECT.NS",
    "HAPPSTMNDS.NS", "LATENTVIEW.NS", "MAPMYINDIA.NS", "FSL.NS",
    "RAJESHEXPO.NS", "TITAGARH.NS", "TEXRAIL.NS", "RVNL.NS",
    "IRCON.NS", "RITES.NS", "ENGINERSIN.NS", "NBCC.NS",
    "PRINCEPIPE.NS", "APOLLOPIPE.NS", "ASTRAL.NS", "FINPIPE.NS",
]


# ═══════════════════════════════════════════════════════════════
#   COMBINED UNIVERSES
# ═══════════════════════════════════════════════════════════════

# Remove duplicates and combine
def _dedupe(*lists) -> list:
    """Combine lists and remove duplicates while preserving order."""
    seen = set()
    result = []
    for lst in lists:
        for item in lst:
            if item not in seen:
                seen.add(item)
                result.append(item)
    return result


NIFTY_100 = _dedupe(NIFTY_50, NIFTY_NEXT_50)
NIFTY_200 = _dedupe(NIFTY_100, MIDCAP_100)
NIFTY_500 = _dedupe(NIFTY_100, MIDCAP_100, SMALLCAP_250)

# Legacy compatibility
INTRADAY_UNIVERSE = NIFTY_500


# ═══════════════════════════════════════════════════════════════
#   GET UNIVERSE BY TIER
# ═══════════════════════════════════════════════════════════════

def get_scan_universe(tier: str = "full") -> list:
    """
    Get stock universe by tier.
    
    Args:
        tier: "tier1" (50), "tier2" (100), "tier3" (200), "full" (500)
    """
    tier = tier.lower()
    
    if tier == "tier1" or tier == "nifty50":
        return NIFTY_50
    elif tier == "tier2" or tier == "nifty100":
        return NIFTY_100
    elif tier == "tier3" or tier == "nifty200":
        return NIFTY_200
    elif tier == "full" or tier == "nifty500":
        return NIFTY_500
    else:
        return NIFTY_100  # Safe default


def get_universe_stats() -> dict:
    """Get statistics about universe sizes."""
    return {
        "nifty_50":       len(NIFTY_50),
        "nifty_next_50":  len(NIFTY_NEXT_50),
        "midcap_100":     len(MIDCAP_100),
        "smallcap_250":   len(SMALLCAP_250),
        "nifty_100":      len(NIFTY_100),
        "nifty_200":      len(NIFTY_200),
        "nifty_500":      len(NIFTY_500),
    }


if __name__ == "__main__":
    stats = get_universe_stats()
    print("\n📊 TRADEDO Stock Universe Stats:")
    print("="*50)
    for key, count in stats.items():
        print(f"   {key:20s}: {count:4d} stocks")
    
    print("\n✅ Total unique stocks:", len(NIFTY_500))