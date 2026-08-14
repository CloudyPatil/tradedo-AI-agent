# E:\tradedo\app\backend\data_pipeline\youtube_channels.py

"""
VERIFIED trusted Indian finance YouTube channels.
Channel IDs verified from actual YouTube URLs.
"""

TRUSTED_CHANNELS = {
    # ══════════════════════════════════════════════════════
    #   EDUCATIONAL & FUNDAMENTAL ANALYSIS
    # ══════════════════════════════════════════════════════
    "CA Rachana Ranade": {
        "channel_id": "UCD-qZSqFPqyx43L6gAR8qfQ",
        "weight": 1.0,
        "type": "educational",
        "handle": "@CARachanaRanade",
    },
    "Pranjal Kamra": {
        "channel_id": "UCwVEhEzsjLym_u1he4XWFkg",
        "weight": 1.0,
        "type": "educational",
        "handle": "@pranjalkamra",
    },
    "Akshat Shrivastava": {
        "channel_id": "UCqW8jxh4tH1Z1sWPbkGWL4g",  # Verified
        "weight": 0.95,
        "type": "educational",
        "handle": "@AkshatZayn",
    },
    "Asset Yogi": {
        "channel_id": "UCsI-xS88_7T0C9R-U33F53g",  # Verified
        "weight": 0.90,
        "type": "personal_finance",
        "handle": "@AssetYogi",
    },
    "Labour Law Advisor": {
        "channel_id": "UC8LQKvQviSRXGuz5wrXdmmw",  # Verified
        "weight": 0.90,
        "type": "personal_finance",
        "handle": "@LabourLawAdvisor",
    },
    "Groww": {
        "channel_id": "UCbWW7i7KnwQfqp6HFg1diFw",
        "weight": 0.85,
        "type": "educational",
        "handle": "@Groww",
    },
    "Finology Legal": {
        "channel_id": "UCY7jk-Hd0LxT73sGjGMkG_w",
        "weight": 0.85,
        "type": "educational",
        "handle": "@finologyLegal",
    },
    "Zerodha Online": {
        "channel_id": "UCP7WmQ_U4GB3K51Od9QvM0w",  # Verified
        "weight": 0.95,
        "type": "educational",
        "handle": "@ZerodhaOnline",
    },
    "Elearnmarkets": {
        "channel_id": "UCmkNoDHBfKzPnXWTNoYQc7A",
        "weight": 0.85,
        "type": "educational",
        "handle": "@elearnmarkets",
    },
    
    # ══════════════════════════════════════════════════════
    #   NEWS & MARKET ANALYSIS
    # ══════════════════════════════════════════════════════
    "CNBC-TV18": {
        "channel_id": "UCMvVyOooFvK05eB8tH25oYQ",  # Verified
        "weight": 0.95,
        "type": "news",
        "handle": "@CNBCTV18Live",
    },
    "ET NOW": {
        "channel_id": "UCI_mwTKUhicNzFrhm33MzBQ",  # Verified
        "weight": 0.95,
        "type": "news",
        "handle": "@ETNOW",
    },
    "Zee Business": {
        "channel_id": "UCkXopQ3ubd-rnXnStZqCl2w",
        "weight": 0.90,
        "type": "news",
        "handle": "@zeebusiness",
    },
    "Moneycontrol": {
        "channel_id": "UC-crZTQNRzZgzyighTKF0nQ",  # Verified
        "weight": 0.90,
        "type": "news",
        "handle": "@moneycontrol",
    },
    "Business Today": {
        "channel_id": "UCyfX_e9C2P1LOHA-S9sS13A",  # Verified
        "weight": 0.85,
        "type": "news",
        "handle": "@BusinessToday",
    },
    
    # ══════════════════════════════════════════════════════
    #   TRADING & TECHNICAL ANALYSIS
    # ══════════════════════════════════════════════════════
    "PR Sundar": {
        "channel_id": "UCS2NdYUmv_PUyyKeDAo5zYA",  # Verified
        "weight": 0.90,
        "type": "options",
        "handle": "@PRSundar64",
    },
    "Booming Bulls": {
        "channel_id": "UC63I5t71w30qWve6SdNUGgw",
        "weight": 0.85,
        "type": "trading",
        "handle": "@BoomingBulls",
    },
    "Power of Stocks": {
        "channel_id": "UCEaoapLYhXhawGCuv8zwSJQ",  # Verified
        "weight": 0.85,
        "type": "trading",
        "handle": "@POWEROFSTOCKSBySubasish",
    },
    "Vivek Bajaj": {
        "channel_id": "UCMec1m9iUC3agiEK-nsndSg",  # Verified
        "weight": 0.85,
        "type": "trading",
        "handle": "@VivekBajaj",
    },
    "Nitin Bhatia": {
        "channel_id": "UCqvVj1LkOpA8tjb7RadTvOg",  # Verified
        "weight": 0.85,
        "type": "value_investing",
        "handle": "@NitinBhatia",
    },
    "Sunil Minglani": {
        "channel_id": "UCjfzE0hYDaRP15O-XJ6dZoA",
        "weight": 0.80,
        "type": "value_investing",
        "handle": "@sunilminglani",
    },
    
    # ══════════════════════════════════════════════════════
    #   VALUE INVESTING & DEEP ANALYSIS
    # ══════════════════════════════════════════════════════
    "SOIC (School of Intrinsic Value)": {
        "channel_id": "UC0AQrC3gYBVLqIGBOvKprKg",  # Verified
        "weight": 0.95,
        "type": "value_investing",
        "handle": "@SOICfinance",
    },
    "Wint Wealth": {
        "channel_id": "UCggPd3Vf9ooG2r4I_ZNWBzA",
        "weight": 0.85,
        "type": "investment",
        "handle": "@WintWealth",
    },
}

CHANNEL_NAMES = list(TRUSTED_CHANNELS.keys())


def get_channel_weight(channel_name: str) -> float:
    """Get trust weight for a channel."""
    for name, info in TRUSTED_CHANNELS.items():
        if name.lower() in channel_name.lower() or channel_name.lower() in name.lower():
            return info["weight"]
    return 0.5


def is_trusted_channel(channel_name: str) -> bool:
    """Check if channel is in trusted list."""
    return get_channel_weight(channel_name) > 0.5


def get_channel_rss_url(channel_id: str) -> str:
    """Get RSS feed URL for a channel."""
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def get_all_channel_ids() -> list:
    """Get all channel IDs."""
    return [info["channel_id"] for info in TRUSTED_CHANNELS.values()]