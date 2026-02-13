"""
ETSAI Growth Bot — Listener Agent
Monitors Reddit, RSS feeds, and forums for relevant conversations.
Uses Claude for thread classification and reply drafting.
"""
import json
import logging
import time
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engine import call_claude, AI_MODEL_CHEAP, AI_MODEL_SMART
from growth.growth_db import (
    add_growth_message, log_agent_action, add_content,
)
from growth.growth_config import (
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET,
    REDDIT_TARGET_SUBREDDITS, REDDIT_KEYWORDS,
    CHANNEL_REDDIT,
)

logger = logging.getLogger("etsai.growth.listener")

# Track threads we've already seen (in-memory for current process)
_seen_threads = set()


# =============================================================
# REDDIT SCANNING
# =============================================================

def _get_reddit():
    """Get a PRAW Reddit instance."""
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        return None
    try:
        import praw
        return praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            username=os.getenv("REDDIT_USERNAME", ""),
            password=os.getenv("REDDIT_PASSWORD", ""),
            user_agent=os.getenv("REDDIT_USER_AGENT", "ETSAI-GrowthBot/1.0"),
        )
    except ImportError:
        logger.warning("PRAW not installed — Listener requires it for Reddit monitoring")
        return None
    except Exception as e:
        logger.error(f"Reddit connection error: {e}")
        return None


def scan_reddit(subreddits=None, keywords=None, since_hours=6, limit=25):
    """
    Fetch recent posts matching keywords from target subreddits.
    Returns list of thread dicts with title, body, url, subreddit, author.
    """
    reddit = _get_reddit()
    if not reddit:
        return []

    if not subreddits:
        subreddits = REDDIT_TARGET_SUBREDDITS
    if not keywords:
        keywords = REDDIT_KEYWORDS

    keyword_set = set(kw.lower() for kw in keywords)
    threads = []
    cutoff = time.time() - (since_hours * 3600)

    for sub_name in subreddits:
        try:
            subreddit = reddit.subreddit(sub_name)
            for post in subreddit.new(limit=limit):
                if post.created_utc < cutoff:
                    continue
                if post.id in _seen_threads:
                    continue

                text = f"{post.title} {post.selftext}".lower()
                matched_keywords = [kw for kw in keyword_set if kw in text]
                if not matched_keywords:
                    continue

                _seen_threads.add(post.id)
                threads.append({
                    "id": post.id,
                    "subreddit": sub_name,
                    "title": post.title,
                    "body": post.selftext[:1000],
                    "url": f"https://reddit.com{post.permalink}",
                    "author": str(post.author) if post.author else None,
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "created_utc": post.created_utc,
                    "matched_keywords": matched_keywords,
                })

        except Exception as e:
            logger.error(f"Listener: Error scanning r/{sub_name}: {e}")

    logger.info(f"Listener: Scanned {len(subreddits)} subreddits, found {len(threads)} relevant threads")
    return threads


# =============================================================
# RSS / GOOGLE ALERTS
# =============================================================

def scan_rss_feeds(feed_urls=None):
    """
    Check RSS feeds (e.g., Google Alerts) for relevant mentions.
    Returns list of items with title, link, summary.
    """
    if not feed_urls:
        feed_urls = [
            # Google Alerts RSS (user must set these up and add URLs here)
            # "https://www.google.com/alerts/feeds/...",
        ]

    if not feed_urls:
        return []

    try:
        import feedparser
    except ImportError:
        logger.warning("feedparser not installed — skipping RSS scan")
        return []

    items = []
    for url in feed_urls:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                items.append({
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", "")[:500],
                    "published": entry.get("published", ""),
                    "source": "rss",
                })
        except Exception as e:
            logger.error(f"Listener: RSS error for {url}: {e}")

    return items


# =============================================================
# CLAUDE CLASSIFICATION
# =============================================================

def classify_thread(thread_data):
    """
    Use Claude Haiku to classify a thread's relevance and opportunity score.
    Returns: {relevance: "relevant"/"maybe"/"irrelevant", score: 0-100, reasoning: str}
    """
    prompt = f"""Classify this Reddit thread for ETSAI outreach opportunity.

ETSAI is an AI tool that helps Etsy sellers collect custom order specifications from buyers via a smart chat link (replaces messy back-and-forth Etsy messages).

THREAD:
Subreddit: r/{thread_data.get('subreddit', '?')}
Title: {thread_data.get('title', '')}
Body: {thread_data.get('body', '')[:600]}

Is this thread relevant for ETSAI? Would a helpful reply mentioning ETSAI be appropriate?

Consider:
- Is the poster an Etsy seller struggling with custom order management?
- Are they asking about intake forms, spec collection, or buyer communication?
- Would mentioning ETSAI feel natural and helpful (not spammy)?
- Is this a thread where the community would welcome tool recommendations?

RESPOND IN JSON:
{{"relevance": "relevant", "score": 85, "reasoning": "Seller asking about better ways to collect custom order details from buyers"}}

Relevance: "relevant" (respond), "maybe" (queue for review), "irrelevant" (skip).
Score: 0-100 opportunity score.
JSON only."""

    try:
        raw, cost, inp, out = call_claude(prompt, AI_MODEL_CHEAP, max_tokens=200)
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
        parsed = json.loads(clean)

        return {
            "relevance": parsed.get("relevance", "irrelevant"),
            "score": min(max(int(parsed.get("score", 0)), 0), 100),
            "reasoning": parsed.get("reasoning", ""),
            "cost": cost,
        }
    except Exception as e:
        logger.error(f"Listener classify error: {e}")
        return {"relevance": "irrelevant", "score": 0, "reasoning": str(e), "cost": 0}


def classify_threads(threads):
    """Classify a batch of threads and return sorted by relevance/score."""
    results = []
    total_cost = 0

    for thread in threads:
        classification = classify_thread(thread)
        total_cost += classification.get("cost", 0)
        thread.update(classification)
        results.append(thread)
        time.sleep(0.2)

    # Sort: relevant first, then by score
    relevance_order = {"relevant": 0, "maybe": 1, "irrelevant": 2}
    results.sort(key=lambda t: (relevance_order.get(t.get("relevance", "irrelevant"), 2), -t.get("score", 0)))

    log_agent_action("listener", "classify_threads", True,
                     {"classified": len(results), "relevant": sum(1 for r in results if r.get("relevance") == "relevant")},
                     cost=total_cost)

    return results


# =============================================================
# PAIN POINT EXTRACTION
# =============================================================

def find_pain_points(threads, limit=10):
    """
    Extract common pain points from threads for content creation.
    Returns list of pain point themes with frequency.
    """
    if not threads:
        return []

    thread_summaries = "\n".join(
        f"- [{t.get('subreddit', '?')}] {t.get('title', '')} — {t.get('body', '')[:100]}"
        for t in threads[:limit]
    )

    prompt = f"""Analyze these Reddit threads from Etsy seller communities and extract the TOP 5 pain points related to custom order management.

THREADS:
{thread_summaries}

For each pain point:
- theme: short name (e.g., "buyer_communication", "spec_tracking")
- description: what sellers are struggling with
- frequency: how many threads mention this (approximate)
- video_topic: a short-form video title that addresses this pain point

RESPOND IN JSON:
[{{"theme": "...", "description": "...", "frequency": 3, "video_topic": "..."}}]
JSON array only."""

    try:
        raw, cost, inp, out = call_claude(prompt, AI_MODEL_CHEAP, max_tokens=500)
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
        pain_points = json.loads(clean)

        log_agent_action("listener", "find_pain_points", True,
                         {"count": len(pain_points)}, cost=cost)
        return pain_points
    except Exception as e:
        logger.error(f"Listener pain points error: {e}")
        return []


# =============================================================
# ENGAGEMENT QUEUE
# =============================================================

def get_engagement_queue():
    """Get prioritized threads to respond to."""
    from growth.growth_db import get_conn
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT * FROM growth_messages
            WHERE channel = 'reddit_reply' AND review_status = 'pending'
            ORDER BY created_at ASC LIMIT 20
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# =============================================================
# MAIN RUN
# =============================================================

def run():
    """Main listener run — scan, classify, draft replies, extract insights."""
    from growth.growth_config import GROWTH_ENABLED
    if not GROWTH_ENABLED:
        return {"status": "disabled"}

    start = time.time()
    result = {
        "threads_found": 0,
        "relevant": 0,
        "replies_drafted": 0,
        "pain_points": [],
    }

    # Scan Reddit
    if CHANNEL_REDDIT:
        threads = scan_reddit()
        result["threads_found"] = len(threads)

        if threads:
            # Classify
            classified = classify_threads(threads)
            relevant = [t for t in classified if t.get("relevance") == "relevant"]
            result["relevant"] = len(relevant)

            # Draft replies for relevant threads
            from growth.writer import draft_reddit_reply
            for thread in relevant[:5]:  # Top 5
                msg_id = draft_reddit_reply(thread)
                if msg_id:
                    result["replies_drafted"] += 1
                time.sleep(0.3)

            # Extract pain points (feed to Creator)
            if len(threads) >= 3:
                result["pain_points"] = find_pain_points(threads)

    # Scan RSS
    rss_items = scan_rss_feeds()
    if rss_items:
        result["rss_items"] = len(rss_items)

    duration_ms = int((time.time() - start) * 1000)
    log_agent_action("listener", "run", True, result, duration_ms=duration_ms)
    return result
