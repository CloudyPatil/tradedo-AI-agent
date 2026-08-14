# E:\tradedo\app\backend\data_pipeline\youtube_monitor.py

"""
YOUTUBE MONITORING SYSTEM
Continuously monitors 20+ trusted finance channels.
Fetches new videos via RSS, transcribes, and caches.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging
import sqlite3
import feedparser
import re
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
    )
    TRANSCRIPT_AVAILABLE = True
except ImportError:
    TRANSCRIPT_AVAILABLE = False

from data_pipeline.youtube_channels import (
    TRUSTED_CHANNELS, get_channel_rss_url, get_channel_weight
)

logger = logging.getLogger("tradedo.youtube_monitor")


# ═══════════════════════════════════════════════════════════════
#   CONFIG
# ═══════════════════════════════════════════════════════════════

YT_DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "youtube_cache.db"
VIDEOS_PER_CHANNEL = 20
MAX_VIDEO_AGE_DAYS = 30
MAX_TRANSCRIPT_LENGTH = 5000
TRANSCRIPT_LANGUAGES = ["en", "hi", "en-IN"]


# ═══════════════════════════════════════════════════════════════
#   DATABASE SETUP
# ═══════════════════════════════════════════════════════════════

def init_youtube_db():
    """Create YouTube cache database."""
    YT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(YT_DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            video_id        TEXT PRIMARY KEY,
            channel_id      TEXT,
            channel_name    TEXT,
            title           TEXT,
            description     TEXT,
            published       DATETIME,
            transcript      TEXT,
            transcript_status TEXT DEFAULT 'PENDING',
            trust_weight    REAL,
            channel_type    TEXT,
            fetched_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            analyzed_at     DATETIME
        )
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_channel ON videos(channel_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_published ON videos(published)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON videos(transcript_status)")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id      TEXT,
            channel_name    TEXT,
            videos_added    INTEGER,
            transcripts_fetched INTEGER,
            errors          INTEGER,
            sync_time       DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info(f"✅ YouTube cache DB initialized: {YT_DB_PATH}")


def get_yt_connection():
    """Get YouTube cache DB connection."""
    conn = sqlite3.connect(str(YT_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# ═══════════════════════════════════════════════════════════════
#   RSS FEED FETCHER
# ═══════════════════════════════════════════════════════════════

def fetch_channel_videos_from_rss(channel_id: str, channel_name: str, weight: float, channel_type: str) -> List[Dict]:
    """Fetch latest videos from a YouTube channel via RSS."""
    rss_url = get_channel_rss_url(channel_id)
    
    try:
        feed = feedparser.parse(rss_url)
        
        if not feed.entries:
            logger.warning(f"No videos in RSS for {channel_name}")
            return []
        
        videos = []
        cutoff = datetime.now() - timedelta(days=MAX_VIDEO_AGE_DAYS)
        
        for entry in feed.entries[:VIDEOS_PER_CHANNEL]:
            try:
                video_id_match = re.search(r'v=([a-zA-Z0-9_-]+)', entry.link)
                if not video_id_match:
                    continue
                
                video_id = video_id_match.group(1)
                published = datetime(*entry.published_parsed[:6])
                
                if published < cutoff:
                    continue
                
                videos.append({
                    "video_id":    video_id,
                    "channel_id":  channel_id,
                    "channel_name": channel_name,
                    "title":       entry.title,
                    "description": (entry.get("summary", "") or "")[:1000],
                    "published":   published.isoformat(),
                    "trust_weight": weight,
                    "channel_type": channel_type,
                })
            except Exception as e:
                logger.debug(f"Failed to parse entry: {e}")
                continue
        
        logger.info(f"  ✓ {channel_name}: {len(videos)} recent videos")
        return videos
    
    except Exception as e:
        logger.warning(f"RSS fetch failed for {channel_name}: {e}")
        return []


# ═══════════════════════════════════════════════════════════════
#   TRANSCRIPT FETCHER
# ═══════════════════════════════════════════════════════════════

def fetch_transcript(video_id: str) -> Optional[str]:
    """Fetch transcript for a video - handles both old and new API."""
    if not TRANSCRIPT_AVAILABLE:
        return None
    
    try:
        # Try NEW API (v1.0+)
        try:
            ytt_api = YouTubeTranscriptApi()
            fetched = ytt_api.fetch(video_id, languages=TRANSCRIPT_LANGUAGES)
            
            if hasattr(fetched, 'snippets'):
                text_parts = [s.text for s in fetched.snippets]
            else:
                text_parts = [item.text if hasattr(item, 'text') else item['text'] 
                             for item in fetched]
            
            text = " ".join(text_parts)
        
        except AttributeError:
            # Fallback to OLD API (v0.x)
            transcript_list = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=TRANSCRIPT_LANGUAGES,
            )
            text = " ".join([t["text"] for t in transcript_list])
        
        if len(text) > MAX_TRANSCRIPT_LENGTH:
            text = text[:MAX_TRANSCRIPT_LENGTH] + "..."
        
        return text
    
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable):
        return None
    except Exception as e:
        logger.debug(f"Transcript error for {video_id}: {type(e).__name__}: {str(e)[:100]}")
        return None


# ═══════════════════════════════════════════════════════════════
#   DATABASE OPERATIONS
# ═══════════════════════════════════════════════════════════════

def save_videos(videos: List[Dict]) -> int:
    """Save videos to cache."""
    if not videos:
        return 0
    
    conn = get_yt_connection()
    cursor = conn.cursor()
    
    added = 0
    for video in videos:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO videos
                (video_id, channel_id, channel_name, title, description, 
                 published, trust_weight, channel_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                video["video_id"],
                video["channel_id"],
                video["channel_name"],
                video["title"],
                video["description"],
                video["published"],
                video["trust_weight"],
                video["channel_type"],
            ))
            
            if cursor.rowcount > 0:
                added += 1
        except Exception as e:
            logger.debug(f"Video save error: {e}")
    
    conn.commit()
    conn.close()
    return added


def get_videos_needing_transcript(limit: int = 20) -> List[Dict]:
    """Get videos that need transcript fetching."""
    conn = get_yt_connection()
    rows = conn.execute("""
        SELECT video_id, title, channel_name 
        FROM videos 
        WHERE transcript_status = 'PENDING'
        ORDER BY published DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_transcript(video_id: str, transcript_text: Optional[str]):
    """Save transcript for a video."""
    conn = get_yt_connection()
    
    status = "SUCCESS" if transcript_text else "UNAVAILABLE"
    
    conn.execute("""
        UPDATE videos 
        SET transcript = ?, 
            transcript_status = ?,
            analyzed_at = CURRENT_TIMESTAMP
        WHERE video_id = ?
    """, (transcript_text, status, video_id))
    
    conn.commit()
    conn.close()


def log_sync(channel_id: str, channel_name: str, videos_added: int, transcripts: int, errors: int):
    """Log sync operation."""
    conn = get_yt_connection()
    conn.execute("""
        INSERT INTO sync_log (channel_id, channel_name, videos_added, transcripts_fetched, errors)
        VALUES (?, ?, ?, ?, ?)
    """, (channel_id, channel_name, videos_added, transcripts, errors))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════
#   MAIN MONITORING FUNCTION
# ═══════════════════════════════════════════════════════════════

def sync_all_channels() -> Dict:
    """Main sync function."""
    logger.info("🎥 YouTube Sync: Starting...")
    logger.info(f"   Monitoring {len(TRUSTED_CHANNELS)} channels")
    
    init_youtube_db()
    
    start_time = time.time()
    total_videos_added = 0
    total_transcripts = 0
    total_errors = 0
    
    # ── Step 1: Fetch RSS from all channels ──────────────────
    logger.info("📡 Step 1: Fetching RSS feeds...")
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        rss_futures = {
            executor.submit(
                fetch_channel_videos_from_rss,
                info["channel_id"],
                name,
                info["weight"],
                info["type"]
            ): name
            for name, info in TRUSTED_CHANNELS.items()
        }
        
        for future in as_completed(rss_futures):
            channel_name = rss_futures[future]
            try:
                videos_list = future.result(timeout=30)
                added_count = save_videos(videos_list)
                total_videos_added += added_count
                
                if added_count > 0:
                    log_sync(
                        channel_id=TRUSTED_CHANNELS[channel_name]["channel_id"],
                        channel_name=channel_name,
                        videos_added=added_count,
                        transcripts=0,
                        errors=0,
                    )
            except Exception as e:
                logger.warning(f"Failed for {channel_name}: {e}")
                total_errors += 1
    
    logger.info(f"   ✓ Added {total_videos_added} new videos")
    
    # ── Step 2: Fetch transcripts ───────────────────────────
    logger.info("📝 Step 2: Fetching transcripts...")
    
    pending_videos = get_videos_needing_transcript(limit=50)
    logger.info(f"   {len(pending_videos)} videos need transcripts")
    
    if pending_videos:
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit tasks and store video info by future
            transcript_futures = {}
            for pending_video in pending_videos:
                p_video_id = pending_video.get("video_id")
                p_title = pending_video.get("title", "Unknown")
                p_channel = pending_video.get("channel_name", "Unknown")
                
                if not p_video_id:
                    continue
                
                fut = executor.submit(fetch_transcript, p_video_id)
                transcript_futures[fut] = {
                    "video_id": p_video_id,
                    "title": p_title,
                    "channel": p_channel,
                }
            
            # Process results
            for fut in as_completed(transcript_futures):
                video_info = transcript_futures[fut]
                v_id = video_info["video_id"]
                v_title = video_info["title"]
                
                try:
                    transcript_result = fut.result(timeout=30)
                    save_transcript(v_id, transcript_result)
                    
                    if transcript_result:
                        total_transcripts += 1
                        logger.info(f"  ✓ Transcript: {v_title[:60]}")
                    else:
                        logger.debug(f"  ✗ No transcript: {v_title[:60]}")
                
                except Exception as e:
                    err_type = type(e).__name__
                    err_msg = str(e)[:100]
                    logger.warning(f"  ✗ Error [{err_type}]: {v_title[:60]}: {err_msg}")
                    total_errors += 1
    
    elapsed = round(time.time() - start_time, 1)
    
    logger.info(f"✅ YouTube Sync Complete in {elapsed}s")
    logger.info(f"   Added: {total_videos_added} videos")
    logger.info(f"   Transcripts: {total_transcripts}")
    logger.info(f"   Errors: {total_errors}")
    
    return {
        "success": True,
        "videos_added": total_videos_added,
        "transcripts_fetched": total_transcripts,
        "errors": total_errors,
        "duration_seconds": elapsed,
    }


# ═══════════════════════════════════════════════════════════════
#   STATS
# ═══════════════════════════════════════════════════════════════

def get_cache_stats() -> Dict:
    """Get YouTube cache statistics."""
    init_youtube_db()
    conn = get_yt_connection()
    
    total = conn.execute("SELECT COUNT(*) as c FROM videos").fetchone()["c"]
    with_transcript = conn.execute(
        "SELECT COUNT(*) as c FROM videos WHERE transcript IS NOT NULL AND transcript != ''"
    ).fetchone()["c"]
    pending = conn.execute(
        "SELECT COUNT(*) as c FROM videos WHERE transcript_status = 'PENDING'"
    ).fetchone()["c"]
    
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    recent = conn.execute(
        "SELECT COUNT(*) as c FROM videos WHERE published > ?",
        (week_ago,)
    ).fetchone()["c"]
    
    channels = conn.execute("""
        SELECT channel_name, COUNT(*) as videos,
               SUM(CASE WHEN transcript IS NOT NULL THEN 1 ELSE 0 END) as with_transcript,
               MAX(published) as latest
        FROM videos
        GROUP BY channel_name
        ORDER BY videos DESC
    """).fetchall()
    
    last_sync = conn.execute("""
        SELECT MAX(sync_time) as last FROM sync_log
    """).fetchone()
    
    conn.close()
    
    return {
        "total_videos": total,
        "with_transcript": with_transcript,
        "pending_transcripts": pending,
        "recent_videos_7d": recent,
        "last_sync": last_sync["last"] if last_sync else None,
        "channels": [dict(c) for c in channels],
    }


# ═══════════════════════════════════════════════════════════════
#   Quick Test
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("YOUTUBE MONITOR TEST")
    print("="*60)
    
    print("\n🎥 Starting sync...")
    result = sync_all_channels()
    
    print(f"\n✅ Sync Result:")
    for k, v in result.items():
        print(f"   {k}: {v}")
    
    print(f"\n📊 Cache Stats:")
    stats = get_cache_stats()
    print(f"   Total videos: {stats['total_videos']}")
    print(f"   With transcript: {stats['with_transcript']}")
    print(f"   Recent (7d): {stats['recent_videos_7d']}")
    print(f"   Last sync: {stats['last_sync']}")
    
    print(f"\n📺 Per Channel:")
    for ch in stats["channels"][:10]:
        print(f"   {ch['channel_name']}: {ch['videos']} videos "
              f"({ch['with_transcript']} with transcript)")