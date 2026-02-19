"""
ETSAI Growth Bot — Listener Agent
Monitors Reddit, RSS feeds, and forums for relevant conversations.
Uses Claude for thread classification and reply drafting.
"""
import json
import logging
import random
import time
from datetime import datetime
from pathlib import Path

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path, override=True)

from ai_engine import call_claude, AI_MODEL_CHEAP, AI_MODEL_SMART
from growth.growth_db import (
    add_growth_message, log_agent_action, add_content,
    upsert_learning, get_top_learnings, get_learnings,
    is_thread_seen, mark_threads_seen, cleanup_old_seen_threads,
)
from growth.growth_config import (
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET,
    REDDIT_TARGET_SUBREDDITS, REDDIT_KEYWORDS,
    CHANNEL_REDDIT,
    LEARNING_ENABLED, LEARNING_EXPLORATION_RATE,
)

logger = logging.getLogger("etsai.growth.listener")


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
        logger.warning("PRAW not installed — will try JSON fallback")
        return None
    except Exception as e:
        logger.error(f"Reddit connection error: {e}")
        return None


def _scan_reddit_json(subreddits, since_hours=6, limit=25):
    """Fetch ALL recent posts from subreddits — no keyword filter.
    Claude will decide what's relevant downstream."""
    import requests

    threads = []
    cutoff = time.time() - (since_hours * 3600)
    headers = {"User-Agent": "ETSAI-GrowthBot/1.0"}

    for sub_name in subreddits:
        try:
            url = f"https://www.reddit.com/r/{sub_name}/new.json?limit={limit}"
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                logger.warning(f"Listener: Reddit JSON r/{sub_name} returned {resp.status_code}")
                time.sleep(2)
                continue

            data = resp.json()
            posts = data.get("data", {}).get("children", [])

            for post_wrapper in posts:
                post = post_wrapper.get("data", {})
                created_utc = post.get("created_utc", 0)
                if created_utc < cutoff:
                    continue

                post_id = post.get("id", "")
                if is_thread_seen(post_id):
                    continue

                author = post.get("author")
                if not author or author in ("[deleted]", "AutoModerator"):
                    continue

                permalink = post.get("permalink", "")

                threads.append({
                    "id": post_id,
                    "subreddit": sub_name,
                    "title": post.get("title", ""),
                    "body": (post.get("selftext") or "")[:1000],
                    "url": f"https://reddit.com{permalink}",
                    "author": author,
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                    "created_utc": created_utc,
                })

            time.sleep(2)

        except Exception as e:
            logger.error(f"Listener: Reddit JSON error on r/{sub_name}: {e}")

    return threads


def scan_reddit(subreddits=None, since_hours=6, limit=25):
    """
    Fetch ALL recent posts from target subreddits.
    No keyword pre-filter — Claude classifies everything downstream.
    """
    if not subreddits:
        subreddits = REDDIT_TARGET_SUBREDDITS

    logger.info("Listener: PRAW unavailable, using Reddit JSON fallback")
    threads = _scan_reddit_json(subreddits, since_hours, limit)
    method = "json"

    logger.info(f"Listener: Scanned {len(subreddits)} subreddits ({method}), found {len(threads)} relevant threads")
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

def classify_threads(threads):
    """Batch-classify threads using Claude. Processes 8 at a time instead of 1-by-1."""
    if not threads:
        return []

    results = []
    total_cost = 0
    batch_size = 8

    for i in range(0, len(threads), batch_size):
        batch = threads[i:i + batch_size]

        thread_summaries = []
        for idx, t in enumerate(batch):
            age_hours = (time.time() - t.get("created_utc", time.time())) / 3600
            thread_summaries.append(
                f"{idx + 1}. [r/{t.get('subreddit', '?')}] \"{t.get('title', '')}\" "
                f"({age_hours:.0f}h old, {t.get('num_comments', 0)} comments)\n"
                f"   {t.get('body', '')[:200]}"
            )

        prompt = f"""Classify these Reddit threads for outreach opportunity.

We help Etsy sellers who do custom/personalized orders collect buyer specs via an AI chat link.

THREADS:
{chr(10).join(thread_summaries)}

For each thread, classify:
- relevance: "relevant" / "maybe" / "irrelevant"
- score: 0-100
- reasoning: one short sentence

Mark "relevant" if ANY apply:
- Etsy seller discussing custom orders, commissions, made-to-order
- Frustrated with buyer communication or back-and-forth messaging
- Asking how to manage/organize/scale custom orders
- Overwhelmed by personalization requests or order volume
- Discussing tools/systems for custom order workflow

Mark "maybe" if: general Etsy seller discussion or scaling handmade business
Mark "irrelevant" if: not about selling/custom orders, about shipping/taxes/SEO, or just a showcase

IMPORTANT: Newer threads (under 6h) and threads with few comments score HIGHER.

RESPOND IN JSON array:
[{{"thread": 1, "relevance": "relevant", "score": 85, "reasoning": "Seller asking about managing custom orders"}}]
JSON array only."""

        try:
            raw, cost, inp, out = call_claude(prompt, AI_MODEL_CHEAP, max_tokens=600)
            total_cost += cost
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            parsed = json.loads(clean)

            for result in parsed:
                idx = result.get("thread", 0) - 1
                if 0 <= idx < len(batch):
                    batch[idx]["relevance"] = result.get("relevance", "irrelevant")
                    batch[idx]["score"] = min(max(int(result.get("score", 0)), 0), 100)
                    batch[idx]["reasoning"] = result.get("reasoning", "")
                    results.append(batch[idx])

            time.sleep(0.3)
        except Exception as e:
            logger.error(f"Listener batch classify error: {e}")
            # On error, mark batch as irrelevant
            for t in batch:
                t["relevance"] = "irrelevant"
                t["score"] = 0
                t["reasoning"] = f"classify error: {e}"
                results.append(t)

    # Sort: relevant first, then by score
    relevance_order = {"relevant": 0, "maybe": 1, "irrelevant": 2}
    results.sort(key=lambda t: (relevance_order.get(t.get("relevance", "irrelevant"), 2), -t.get("score", 0)))

    log_agent_action("listener", "classify_threads", True,
                     {"classified": len(results), "relevant": sum(1 for r in results if r.get("relevance") in ("relevant", "maybe"))},
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
# SELF-LEARNING — SUBREDDIT & KEYWORD QUALITY
# =============================================================

def update_listener_learnings(classified_threads):
    """Track subreddit relevance rates and keyword quality from classification results."""
    if not LEARNING_ENABLED or not classified_threads:
        return

    # Aggregate by subreddit
    sub_stats = {}
    for t in classified_threads:
        sub = t.get("subreddit", "unknown")
        if sub not in sub_stats:
            sub_stats[sub] = {"total": 0, "relevant": 0, "maybe": 0}
        sub_stats[sub]["total"] += 1
        if t.get("relevance") == "relevant":
            sub_stats[sub]["relevant"] += 1
        elif t.get("relevance") == "maybe":
            sub_stats[sub]["maybe"] += 1

    for sub, stats in sub_stats.items():
        total = stats["total"]
        if total == 0:
            continue
        relevance_rate = ((stats["relevant"] + stats["maybe"] * 0.5) / total) * 100
        confidence = min(total / 10, 1.0)
        upsert_learning(
            agent="listener",
            learning_type="subreddit_quality",
            key=sub,
            value_json={
                "relevance_rate": round(relevance_rate, 1),
                "relevant": stats["relevant"],
                "maybe": stats["maybe"],
                "total": total,
            },
            score=round(relevance_rate, 2),
            sample_size=total,
            confidence=round(confidence, 2),
        )

    # Aggregate by keyword
    kw_stats = {}
    for t in classified_threads:
        for kw in t.get("matched_keywords", []):
            if kw not in kw_stats:
                kw_stats[kw] = {"total": 0, "relevant": 0}
            kw_stats[kw]["total"] += 1
            if t.get("relevance") == "relevant":
                kw_stats[kw]["relevant"] += 1

    for kw, stats in kw_stats.items():
        total = stats["total"]
        if total == 0:
            continue
        hit_rate = (stats["relevant"] / total) * 100
        confidence = min(total / 5, 1.0)
        upsert_learning(
            agent="listener",
            learning_type="keyword_quality",
            key=kw,
            value_json={
                "hit_rate": round(hit_rate, 1),
                "relevant": stats["relevant"],
                "total": total,
            },
            score=round(hit_rate, 2),
            sample_size=total,
            confidence=round(confidence, 2),
        )

    logger.info(f"Listener: Updated learnings for {len(sub_stats)} subreddits, {len(kw_stats)} keywords")


def _get_smart_subreddits(max_subs=None):
    """Pick subreddits based on learnings: top quality + exploration of untested ones."""
    if not LEARNING_ENABLED:
        return REDDIT_TARGET_SUBREDDITS

    if max_subs is None:
        max_subs = len(REDDIT_TARGET_SUBREDDITS)

    top = get_top_learnings("listener", "subreddit_quality", limit=max_subs, min_sample=3)
    tested = {l["key"] for l in get_learnings(agent="listener", learning_type="subreddit_quality")}

    smart_subs = [l["key"] for l in top]

    # Add untested subreddits for exploration
    untested = [s for s in REDDIT_TARGET_SUBREDDITS if s not in tested]
    explore_count = max(1, int(max_subs * LEARNING_EXPLORATION_RATE))
    if untested:
        explore_picks = random.sample(untested, min(explore_count, len(untested)))
        smart_subs.extend(explore_picks)

    # Fill with defaults
    if len(smart_subs) < max_subs:
        remaining = [s for s in REDDIT_TARGET_SUBREDDITS if s not in smart_subs]
        smart_subs.extend(remaining[:max_subs - len(smart_subs)])

    return smart_subs[:max_subs]


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

    # Cleanup old seen threads (keep last 7 days)
    try:
        cleanup_old_seen_threads(days=7)
    except Exception:
        pass

    # Scan Reddit
    if CHANNEL_REDDIT:
        smart_subs = _get_smart_subreddits()
        threads = scan_reddit(subreddits=smart_subs)
        result["threads_found"] = len(threads)

        # Mark all fetched threads as seen (persists across deploys)
        if threads:
            mark_threads_seen([t["id"] for t in threads])

        if threads:
            # Classify
            classified = classify_threads(threads)
            relevant = [t for t in classified if t.get("relevance") in ("relevant", "maybe")]
            result["relevant"] = len(relevant)

            # Sort by recency — newer threads get more visibility
            relevant.sort(key=lambda t: t.get("created_utc", 0), reverse=True)

            # Update learnings after classification
            if LEARNING_ENABLED:
                try:
                    update_listener_learnings(classified)
                except Exception as e:
                    logger.error(f"Listener learning update error: {e}")

            # Draft replies for relevant threads (newest first)
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
