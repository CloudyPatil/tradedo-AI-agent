# E:\tradedo\app\backend\data_pipeline\youtube_channels.py

"""
Curated list of trusted Indian finance YouTube channels.
Only these channels are scraped — filters out spam.
"""

TRUSTED_CHANNELS = {
    # ── Educational & Analysis ─────────────────────────────
    "CA Rachana Phadke Ranade": {
        "channel_id": "UCwAC2r_9jcbBLL6Bt3TrIVw",
        "weight": 1.0,   # Trust weight (higher = more influence)
        "type": "educational",
    },
    "Pranjal Kamra": {
        "channel_id": "UCwVEhEzsjLym_u1he4XWFkg",
        "weight": 1.0,
        "type": "educational",
    },
    "Finology": {
        "channel_id": "UC4T4kR3NmfmnBcaBw8i7dhQ",
        "weight": 0.9,
        "type": "educational",
    },
    "Groww": {
        "channel_id": "UC72Ho_UnKfKAdmUmuoAKgug",
        "weight": 0.9,
        "type": "educational",
    },
    "Zerodha Varsity": {
        "channel_id": "UCJU_g7lzKzKjLzKzKjLzKzKj",
        "weight": 1.0,
        "type": "educational",
    },
    
    # ── Market Analysis & Trading ──────────────────────────
    "Nitin Bhatia": {
        "channel_id": "UCyHqp3TnQyxxYnmvw3udbvw",
        "weight": 0.9,
        "type": "analysis",
    },
    "Sunil Minglani": {
        "channel_id": "UCfHhBRK5RRr2A5UkODhoUsg",
        "weight": 0.85,
        "type": "analysis",
    },
    "PR Sundar": {
        "channel_id": "UCw3Y1Tp1QqBFhH0N8YrUeSg",
        "weight": 0.9,
        "type": "options",
    },
    "Vivek Bajaj (Elearnmarkets)": {
        "channel_id": "UCJ9RB5m0TSC5oQI2i2wDG0Q",
        "weight": 0.9,
        "type": "educational",
    },
    "Booming Bulls Academy": {
        "channel_id": "UCV_UPnQzHhg6r7bKzZ6q8Rg",
        "weight": 0.8,
        "type": "trading",
    },
    "Trading Chanakya": {
        "channel_id": "UCe5vlm6EqvKrGZTvKvHIlow",
        "weight": 0.8,
        "type": "trading",
    },
    "Ghanshyam Tech": {
        "channel_id": "UCH2VRhJbA82pWNPEfjE4mNg",
        "weight": 0.75,
        "type": "trading",
    },
    "Power of Stocks (Subhasish)": {
        "channel_id": "UC1XkYCFI-jvIf8_qSKGl8fA",
        "weight": 0.8,
        "type": "trading",
    },
    
    # ── News & Updates ─────────────────────────────────────
    "CNBC-TV18": {
        "channel_id": "UCa4B_LIgVI-uKl4CxAxhqTQ",
        "weight": 0.95,
        "type": "news",
    },
    "ET Now": {
        "channel_id": "UC-f7r46JhYv78q5pGrO6ivA",
        "weight": 0.95,
        "type": "news",
    },
    "Zee Business": {
        "channel_id": "UCX6a-vE_C8bWmYbrJqNBBUw",
        "weight": 0.9,
        "type": "news",
    },
    "Moneycontrol": {
        "channel_id": "UCwPDf-NnyfXYFo6uW-tNhAg",
        "weight": 0.9,
        "type": "news",
    },
    "Business Today": {
        "channel_id": "UCJPFrJUiJ87RVLtoOwYq0Vg",
        "weight": 0.85,
        "type": "news",
    },
    
    # ── Fundamental Analysis ───────────────────────────────
    "Wint Wealth": {
        "channel_id": "UCggPd3Vf9ooG2r4I_ZNWBzA",
        "weight": 0.85,
        "type": "fundamental",
    },
    "Kuvera": {
        "channel_id": "UCbrTa02NGuP-mTG4jQAP8xg",
        "weight": 0.8,
        "type": "fundamental",
    },
}

# Simplified list for quick access
CHANNEL_NAMES = list(TRUSTED_CHANNELS.keys())


def get_channel_weight(channel_name: str) -> float:
    """Get trust weight for a channel."""
    for name, info in TRUSTED_CHANNELS.items():
        if name.lower() in channel_name.lower() or channel_name.lower() in name.lower():
            return info["weight"]
    return 0.5  # Unknown channel = lower weight


def is_trusted_channel(channel_name: str) -> bool:
    """Check if channel is in trusted list."""
    return get_channel_weight(channel_name) > 0.5