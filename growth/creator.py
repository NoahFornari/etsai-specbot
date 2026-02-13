"""
ETSAI Growth Bot — Creator Agent
Generates short-form video content featuring Hum the hummingbird.
Pipeline: topic → Claude script → Edge TTS → MoviePy → upload.
"""
import json
import logging
import time
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engine import call_claude, AI_MODEL_SMART, AI_MODEL_CHEAP
from growth.growth_db import (
    add_content, update_content_status, update_content_metrics,
    get_videos_published_today, log_agent_action,
)
from growth.growth_config import CREATOR_MAX_VIDEOS_PER_DAY, REVIEW_QUEUE_VIDEO

logger = logging.getLogger("etsai.growth.creator")

# =============================================================
# VIDEO TYPES
# =============================================================

VIDEO_STYLES = {
    "tip": {
        "system": """You write short, punchy scripts for 15-30 second vertical videos about Etsy custom order management.
Format: Hook (2s) → 3 Tips (3-5s each) → CTA (2s).
Tone: Friendly, direct, founder-sharing-tips vibe.
Each segment should be SHORT — spoken aloud in the time given.
Do NOT use emojis in the script.""",
        "template": "gradient",
        "hum_pose": "pointing",
    },
    "pain_point": {
        "system": """You write relatable, slightly humorous scripts for 15-20 second vertical videos about Etsy seller pain points.
Format: "POV:" hook (2s) → Problem description (5s) → Solution hint (3s) → CTA (2s).
Tone: "I've been there" empathy + light humor.
Keep each segment VERY short for vertical video.""",
        "template": "solid_dark",
        "hum_pose": "thinking",
    },
    "stat": {
        "system": """You write script for a 10-15 second animated stat/quote card video.
Format: Big stat or quote (5s) → Context (3s) → CTA (2s).
Tone: Authoritative but approachable.
Very minimal text per segment — it needs to be readable on a phone.""",
        "template": "gradient",
        "hum_pose": "celebrating",
    },
    "demo": {
        "system": """You write voiceover scripts for 30-45 second ETSAI product demo videos.
Format: Problem (5s) → Show the solution (15-20s) → Result (5s) → CTA (3s).
Tone: Casual walkthrough, like showing a friend.
Keep narration concise — the visuals do the heavy lifting.""",
        "template": "solid_green",
        "hum_pose": "waving",
    },
}

# Topic ideas bank
DEFAULT_TOPICS = [
    "3 signs you need an intake form for your Etsy shop",
    "POV: buyer sends a 500-word essay instead of their ring size",
    "The custom order communication hack that saves 2 hours per week",
    "Why 73% of custom order issues are just miscommunication",
    "How to stop playing message ping-pong with buyers",
    "The intake form trick that reduced my refund rate by 40%",
    "Stop asking buyers the same questions over and over",
    "Custom order sellers: are you tracking specs in spreadsheets?",
    "What if your buyers could tell you exactly what they need in 90 seconds?",
    "The #1 reason custom orders get delayed (and how to fix it)",
]


# =============================================================
# SCRIPT GENERATION
# =============================================================

def generate_script(topic, style="tip", duration_target=20):
    """
    Generate a video script using Claude.
    Returns: {segments: [{text, duration, fontsize}], title, description, tags, cost}
    """
    style_config = VIDEO_STYLES.get(style, VIDEO_STYLES["tip"])

    prompt = f"""Create a short-form vertical video script about: "{topic}"

Target duration: {duration_target} seconds total.

Output JSON with:
- title: YouTube Shorts title (under 60 chars, catchy)
- description: YouTube description (2-3 sentences, include #shorts #etsy)
- tags: array of 5-8 relevant tags
- segments: array of objects with "text" (what shows on screen), "voiceover" (what's spoken), "duration" (seconds)

Rules:
- Each segment's text should be VERY short (under 15 words) — it's on a phone screen
- Voiceover can be slightly longer but should match the duration
- Total of segment durations should be close to {duration_target}s
- Last segment should be a CTA: "Link in bio" or "Follow for more Etsy tips"
- Make it engaging from the FIRST SECOND

JSON only. No markdown."""

    try:
        raw, cost, inp, out = call_claude(prompt, AI_MODEL_SMART, max_tokens=600,
                                           system=style_config["system"])
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
        parsed = json.loads(clean)

        # Normalize segments
        segments = []
        for seg in parsed.get("segments", []):
            segments.append({
                "text": seg.get("text", ""),
                "voiceover": seg.get("voiceover", seg.get("text", "")),
                "duration": float(seg.get("duration", 3)),
                "fontsize": 48 if len(seg.get("text", "")) < 30 else 36,
            })

        result = {
            "segments": segments,
            "title": parsed.get("title", topic[:60]),
            "description": parsed.get("description", ""),
            "tags": parsed.get("tags", ["etsy", "customorders", "smallbusiness"]),
            "cost": cost,
            "style": style,
        }

        log_agent_action("creator", "generate_script", True,
                         {"topic": topic[:80], "segments": len(segments)},
                         cost=cost, tokens_used=inp + out)
        return result

    except Exception as e:
        logger.error(f"Creator script error: {e}")
        return None


# =============================================================
# FULL VIDEO PRODUCTION
# =============================================================

def create_video(topic, style="tip", auto_upload=False):
    """
    Full pipeline: script → voiceover → assembly → (optional) upload.
    Returns content_id or None.
    """
    start = time.time()

    # Check quota
    if get_videos_published_today() >= CREATOR_MAX_VIDEOS_PER_DAY:
        logger.info("Creator: daily video quota reached")
        return None

    # Step 1: Generate script
    script = generate_script(topic, style)
    if not script or not script.get("segments"):
        logger.error("Creator: failed to generate script")
        return None

    # Step 2: Generate voiceover
    from growth.video_engine import generate_voiceover
    voiceover_text = " ".join(s.get("voiceover", s.get("text", "")) for s in script["segments"])
    voiceover_path = generate_voiceover(voiceover_text)

    # Step 3: Assemble video
    from growth.video_engine import assemble_video, create_thumbnail
    style_config = VIDEO_STYLES.get(style, VIDEO_STYLES["tip"])

    video_path = assemble_video(
        script_segments=script["segments"],
        voiceover_path=voiceover_path,
        template=style_config["template"],
        hum_pose=style_config["hum_pose"],
    )

    if not video_path:
        logger.error("Creator: video assembly failed")
        return None

    # Step 4: Create thumbnail
    thumbnail_path = create_thumbnail(script["title"], style_config["hum_pose"])

    # Step 5: Save to DB
    content_id = add_content(
        content_type="video",
        title=script["title"],
        body=script["description"],
        script=json.dumps(script["segments"]),
        media_path=video_path,
        thumbnail_path=thumbnail_path,
        platform="youtube",
        status="review" if REVIEW_QUEUE_VIDEO else "ready",
    )

    # Step 6: Upload if auto-enabled and approved
    upload_result = None
    if auto_upload and not REVIEW_QUEUE_VIDEO:
        from growth.video_engine import upload_to_youtube
        upload_result = upload_to_youtube(
            video_path=video_path,
            title=script["title"],
            description=script["description"],
            tags=script.get("tags"),
        )
        if upload_result:
            update_content_status(
                content_id, "published",
                platform_post_id=upload_result.get("video_id"),
                platform_url=upload_result.get("url"),
            )

    duration_ms = int((time.time() - start) * 1000)
    log_agent_action("creator", "create_video", True, {
        "topic": topic[:80],
        "style": style,
        "content_id": content_id,
        "uploaded": bool(upload_result),
    }, cost=script.get("cost", 0), duration_ms=duration_ms)

    logger.info(f"Creator: Video created — {script['title']} (content_id: {content_id})")
    return content_id


def batch_create(topics, style="tip", count=None):
    """Create multiple videos from a topic list."""
    if count:
        topics = topics[:count]

    content_ids = []
    for topic in topics:
        if get_videos_published_today() >= CREATOR_MAX_VIDEOS_PER_DAY:
            break
        content_id = create_video(topic, style)
        if content_id:
            content_ids.append(content_id)
        time.sleep(1)

    return content_ids


# =============================================================
# TOPIC GENERATION
# =============================================================

def generate_topics(pain_points=None, count=5):
    """Generate video topic ideas, optionally based on listener pain points."""
    context = ""
    if pain_points:
        context = "Recent seller pain points from Reddit:\n"
        for pp in pain_points[:5]:
            context += f"- {pp.get('theme', '')}: {pp.get('description', '')}\n"

    prompt = f"""Generate {count} short-form video topic ideas for ETSAI's YouTube Shorts / TikTok.

ETSAI helps Etsy sellers collect custom order specs from buyers via an AI chat link.

{context}

Each topic should be:
- Specific and actionable (not vague)
- Appealing to Etsy sellers who do custom/personalized orders
- Suitable for 15-30 second vertical video
- Mix of: tips, pain points, stats, relatable moments

RESPOND IN JSON:
[{{"topic": "...", "style": "tip|pain_point|stat|demo", "priority": 1-5}}]
JSON array only."""

    try:
        raw, cost, inp, out = call_claude(prompt, AI_MODEL_CHEAP, max_tokens=400)
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
        topics = json.loads(clean)
        topics.sort(key=lambda t: t.get("priority", 5))
        return topics
    except Exception as e:
        logger.error(f"Creator topic generation error: {e}")
        # Return default topics
        return [{"topic": t, "style": "tip", "priority": 3} for t in DEFAULT_TOPICS[:count]]


# =============================================================
# MAIN RUN
# =============================================================

def run(pain_points=None):
    """Main creator run — generate topics, produce videos."""
    from growth.growth_config import GROWTH_ENABLED
    if not GROWTH_ENABLED:
        return {"status": "disabled"}

    start = time.time()
    result = {"videos_created": 0, "topics_generated": 0}

    # Generate topics
    topics = generate_topics(pain_points, count=3)
    result["topics_generated"] = len(topics)

    # Create videos — auto-upload when review queue is off
    for topic_data in topics:
        if get_videos_published_today() >= CREATOR_MAX_VIDEOS_PER_DAY:
            break
        content_id = create_video(
            topic=topic_data.get("topic", ""),
            style=topic_data.get("style", "tip"),
            auto_upload=not REVIEW_QUEUE_VIDEO,
        )
        if content_id:
            result["videos_created"] += 1

    duration_ms = int((time.time() - start) * 1000)
    log_agent_action("creator", "run", True, result, duration_ms=duration_ms)
    return result
