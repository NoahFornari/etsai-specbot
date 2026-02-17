"""
ETSAI Growth Bot — Configuration
Loads from env vars with sensible defaults. All quotas are daily limits.
"""
import os
from dotenv import load_dotenv

load_dotenv(override=True)


# =============================================================
# BUDGET
# =============================================================

DAILY_BUDGET = float(os.environ.get("GROWTH_DAILY_BUDGET", "5.00"))

# =============================================================
# PER-AGENT QUOTAS (daily)
# =============================================================

SCOUT_MAX_LEADS_PER_DAY = int(os.environ.get("GROWTH_SCOUT_MAX_LEADS", "200"))
WRITER_MAX_EMAILS_PER_DAY = int(os.environ.get("GROWTH_WRITER_MAX_EMAILS", "50"))
WRITER_MAX_REDDIT_COMMENTS_PER_DAY = int(os.environ.get("GROWTH_WRITER_MAX_REDDIT_COMMENTS", "3"))
WRITER_MAX_DMS_PER_DAY = int(os.environ.get("GROWTH_WRITER_MAX_DMS", "20"))
LISTENER_MAX_SCANS_PER_DAY = int(os.environ.get("GROWTH_LISTENER_MAX_SCANS", "48"))
CREATOR_MAX_VIDEOS_PER_DAY = int(os.environ.get("GROWTH_CREATOR_MAX_VIDEOS", "2"))

# =============================================================
# CHANNEL TOGGLES (on by default, disable via env)
# =============================================================

CHANNEL_EMAIL = os.environ.get("GROWTH_CHANNEL_EMAIL", "1") == "1"
CHANNEL_REDDIT = os.environ.get("GROWTH_CHANNEL_REDDIT", "1") == "1"
CHANNEL_YOUTUBE = os.environ.get("GROWTH_CHANNEL_YOUTUBE", "1") == "1"
CHANNEL_ETSY_CONVO = os.environ.get("GROWTH_CHANNEL_ETSY_CONVO", "1") == "1"
CHANNEL_TIKTOK = os.environ.get("GROWTH_CHANNEL_TIKTOK", "0") == "1"
CHANNEL_INSTAGRAM = os.environ.get("GROWTH_CHANNEL_INSTAGRAM", "0") == "1"

# =============================================================
# REVIEW QUEUE — off = auto-post, on = human approves first
# =============================================================

REVIEW_QUEUE_REDDIT = os.environ.get("GROWTH_REVIEW_REDDIT", "1") == "1"
REVIEW_QUEUE_EMAIL = os.environ.get("GROWTH_REVIEW_EMAIL", "0") == "1"
REVIEW_QUEUE_VIDEO = os.environ.get("GROWTH_REVIEW_VIDEO", "1") == "1"
REVIEW_QUEUE_ETSY_CONVO = os.environ.get("GROWTH_REVIEW_ETSY_CONVO", "1") == "1"

# =============================================================
# ANTI-SPAM SAFEGUARDS
# =============================================================

MIN_FOLLOWUP_GAP_DAYS = int(os.environ.get("GROWTH_MIN_FOLLOWUP_GAP", "3"))
CROSS_CHANNEL_COOLDOWN_HOURS = int(os.environ.get("GROWTH_CROSS_CHANNEL_COOLDOWN", "48"))
MIN_RESPONSE_RATE_PCT = float(os.environ.get("GROWTH_MIN_RESPONSE_RATE", "2.0"))
MAX_FOLLOWUPS_PER_LEAD = int(os.environ.get("GROWTH_MAX_FOLLOWUPS", "3"))

# =============================================================
# REDDIT API (PRAW)
# =============================================================

REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
REDDIT_USERNAME = os.environ.get("REDDIT_USERNAME", "")
REDDIT_PASSWORD = os.environ.get("REDDIT_PASSWORD", "")
REDDIT_USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "ETSAI-GrowthBot/1.0")

REDDIT_TARGET_SUBREDDITS = [
    "Etsy", "EtsySellers", "smallbusiness", "Entrepreneur",
    "ecommerce", "craftit", "handmade",
]

REDDIT_KEYWORDS = [
    "custom order", "custom orders", "intake form", "order details",
    "collect specs", "buyer information", "personalized order",
    "order management", "etsy messages", "etsy communication",
    "client questionnaire", "order form", "commission",
    "made to order", "personalized", "bespoke", "custom work",
    "engraving", "monogram", "handmade", "etsy shop", "etsy seller",
    "small business", "how do you collect", "buyer details",
    "customize", "specification", "questionnaire",
]

# =============================================================
# YOUTUBE API
# =============================================================

YOUTUBE_CLIENT_SECRETS_FILE = os.environ.get("YOUTUBE_CLIENT_SECRETS", "")
YOUTUBE_CREDENTIALS_FILE = os.environ.get("YOUTUBE_CREDENTIALS", "growth/youtube_credentials.json")

# =============================================================
# TTS (Text-to-Speech)
# =============================================================

TTS_ENGINE = os.environ.get("GROWTH_TTS_ENGINE", "edge")  # "edge" (free) or "elevenlabs"
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
EDGE_TTS_VOICE = os.environ.get("GROWTH_EDGE_VOICE", "en-US-AriaNeural")

# =============================================================
# VIDEO
# =============================================================

VIDEO_OUTPUT_DIR = os.environ.get("GROWTH_VIDEO_DIR", "growth/videos")
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920  # Vertical for Shorts/Reels/TikTok
VIDEO_FPS = 30
HUM_ASSETS_DIR = os.environ.get("GROWTH_HUM_ASSETS", "growth/assets/hum")

# =============================================================
# SCHEDULER INTERVALS (minutes)
# =============================================================

SCHEDULE_COMMANDER_MINS = int(os.environ.get("GROWTH_SCHED_COMMANDER", "60"))
SCHEDULE_SCOUT_MINS = int(os.environ.get("GROWTH_SCHED_SCOUT", "360"))
SCHEDULE_LISTENER_MINS = int(os.environ.get("GROWTH_SCHED_LISTENER", "30"))
SCHEDULE_CREATOR_MINS = int(os.environ.get("GROWTH_SCHED_CREATOR", "720"))
SCHEDULE_WRITER_MINS = int(os.environ.get("GROWTH_SCHED_WRITER", "120"))

# =============================================================
# SELF-LEARNING
# =============================================================

LEARNING_ENABLED = os.environ.get("GROWTH_LEARNING_ENABLED", "1") == "1"
LEARNING_EXPLORATION_RATE = float(os.environ.get("GROWTH_LEARNING_EXPLORATION_RATE", "0.20"))

# =============================================================
# KILL SWITCH
# =============================================================

GROWTH_ENABLED = os.environ.get("GROWTH_ENABLED", "1") == "1"


def get_config_summary():
    """Return a dict summarizing current config for dashboard display."""
    return {
        "daily_budget": DAILY_BUDGET,
        "growth_enabled": GROWTH_ENABLED,
        "channels": {
            "email": CHANNEL_EMAIL,
            "etsy_convo": CHANNEL_ETSY_CONVO,
            "reddit": CHANNEL_REDDIT,
            "youtube": CHANNEL_YOUTUBE,
            "tiktok": CHANNEL_TIKTOK,
            "instagram": CHANNEL_INSTAGRAM,
        },
        "quotas": {
            "scout_leads": SCOUT_MAX_LEADS_PER_DAY,
            "writer_emails": WRITER_MAX_EMAILS_PER_DAY,
            "writer_reddit": WRITER_MAX_REDDIT_COMMENTS_PER_DAY,
            "writer_dms": WRITER_MAX_DMS_PER_DAY,
            "creator_videos": CREATOR_MAX_VIDEOS_PER_DAY,
        },
        "review_queue": {
            "reddit": REVIEW_QUEUE_REDDIT,
            "email": REVIEW_QUEUE_EMAIL,
            "video": REVIEW_QUEUE_VIDEO,
            "etsy_convo": REVIEW_QUEUE_ETSY_CONVO,
        },
        "schedule": {
            "commander": f"Every {SCHEDULE_COMMANDER_MINS}m",
            "scout": f"Every {SCHEDULE_SCOUT_MINS}m",
            "listener": f"Every {SCHEDULE_LISTENER_MINS}m",
            "creator": f"Every {SCHEDULE_CREATOR_MINS}m",
            "writer": f"Every {SCHEDULE_WRITER_MINS}m",
        },
        "reddit_configured": bool(REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET),
        "youtube_configured": bool(YOUTUBE_CLIENT_SECRETS_FILE),
        "tts_engine": TTS_ENGINE,
        "learning_enabled": LEARNING_ENABLED,
        "learning_exploration_rate": LEARNING_EXPLORATION_RATE,
    }
