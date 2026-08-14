# E:\tradedo\app\backend\data_pipeline\verify_channels.py

"""
Verify all trusted channel IDs by trying to fetch their RSS feeds.
Reports which channels work and which need updating.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import feedparser
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from data_pipeline.youtube_channels import TRUSTED_CHANNELS, get_channel_rss_url

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify")


def verify_channel(name: str, info: dict) -> dict:
    """Test if a channel's RSS feed works."""
    channel_id = info["channel_id"]
    rss_url = get_channel_rss_url(channel_id)
    
    try:
        feed = feedparser.parse(rss_url)
        
        # Check if feed has actual content
        if feed.entries and len(feed.entries) > 0:
            actual_name = feed.feed.get("title", "Unknown")
            latest = feed.entries[0].get("title", "")[:60]
            
            return {
                "name": name,
                "status": "✅ WORKS",
                "channel_id": channel_id,
                "actual_channel_name": actual_name,
                "video_count": len(feed.entries),
                "latest_video": latest,
                "handle": info.get("handle", "N/A"),
            }
        else:
            return {
                "name": name,
                "status": "❌ EMPTY/INVALID",
                "channel_id": channel_id,
                "handle": info.get("handle", "N/A"),
                "error": "No videos in feed",
            }
    
    except Exception as e:
        return {
            "name": name,
            "status": "❌ ERROR",
            "channel_id": channel_id,
            "handle": info.get("handle", "N/A"),
            "error": str(e)[:100],
        }


def verify_all():
    """Test all channels."""
    print("\n" + "="*80)
    print("VERIFYING ALL CHANNEL IDs")
    print("="*80)
    print(f"\nTotal channels to test: {len(TRUSTED_CHANNELS)}\n")
    
    working = []
    broken = []
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(verify_channel, name, info): name
            for name, info in TRUSTED_CHANNELS.items()
        }
        
        for future in as_completed(futures):
            result = future.result()
            
            if "✅" in result["status"]:
                working.append(result)
                print(f"{result['status']} {result['name']}")
                print(f"   ID: {result['channel_id']}")
                print(f"   Actual: {result['actual_channel_name']}")
                print(f"   Videos: {result['video_count']}")
                print(f"   Latest: {result['latest_video']}\n")
            else:
                broken.append(result)
                print(f"{result['status']} {result['name']}")
                print(f"   ID: {result['channel_id']}")
                print(f"   Handle: {result['handle']}")
                print(f"   Error: {result.get('error', 'Unknown')}\n")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ Working: {len(working)}")
    print(f"❌ Broken:  {len(broken)}")
    
    if broken:
        print(f"\n⚠️  Broken channels need updating:")
        for b in broken:
            print(f"   - {b['name']} (handle: {b['handle']})")
        
        print(f"\n💡 To fix:")
        print(f"   1. Visit https://youtube.com/{broken[0]['handle']}")
        print(f"   2. View page source (Ctrl+U)")
        print(f"   3. Search for: 'channelId'")
        print(f"   4. Copy the UC... ID and update TRUSTED_CHANNELS")
    else:
        print(f"\n🎉 ALL CHANNELS WORKING!")
    
    return working, broken


if __name__ == "__main__":
    verify_all()