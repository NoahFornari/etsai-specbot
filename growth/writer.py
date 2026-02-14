"""
ETSAI Growth Bot — Writer Agent
Multi-channel outreach: email, Reddit comments/posts, Etsy convos, DMs.
A/B testing, personalization, anti-spam safeguards, self-learning.
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
    add_growth_message, get_growth_lead, get_lead_messages,
    update_lead_status, update_message_status, get_messages_sent_today,
    log_agent_action, get_message_queue, update_campaign_stats,
    upsert_learning, get_top_learnings, get_learnings, get_conn,
)
from growth.growth_config import (
    WRITER_MAX_EMAILS_PER_DAY, WRITER_MAX_REDDIT_COMMENTS_PER_DAY,
    WRITER_MAX_DMS_PER_DAY, MIN_FOLLOWUP_GAP_DAYS, MAX_FOLLOWUPS_PER_LEAD,
    MIN_RESPONSE_RATE_PCT, REVIEW_QUEUE_REDDIT, REVIEW_QUEUE_EMAIL,
    REVIEW_QUEUE_ETSY_CONVO, CHANNEL_EMAIL, CHANNEL_REDDIT, CHANNEL_ETSY_CONVO,
    LEARNING_ENABLED,
)

logger = logging.getLogger("etsai.growth.writer")

# A/B variant styles for message testing
VARIANTS = ["question_first", "value_first", "casual", "professional"]

# =============================================================
# SYSTEM PROMPTS
# =============================================================

EMAIL_SYSTEM = """You are Noah, a fellow Etsy seller who does custom orders. You're writing a
short cold email to another seller whose shop caught your eye.

Rules:
- Reference something genuinely specific — a product, their style, a review you noticed
- Ask ONE question about how they handle custom order details from buyers
- Do NOT mention ETSAI, any tool, any product, or anything you're building. Pure conversation.
- Under 50 words total. Two sentences max.
- Casual, lowercase-okay. Like emailing someone you met at a craft fair.
- No emojis, no links, no pitch, no CTA
- Sign off as just "Noah"
- Do NOT include a subject line

Output the email body only. Nothing else."""

REDDIT_REPLY_SYSTEM = """You are writing a helpful Reddit reply as an Etsy seller community member.
You genuinely want to help, and you happen to have experience with ETSAI.

Rules:
- Lead with genuine, helpful advice about the poster's problem
- Share personal experience naturally — "I use a tool called ETSAI for this" (not salesy)
- Be specific about HOW it solves the problem they mentioned
- Match the casual tone of Reddit
- Under 120 words
- Do NOT link to ETSAI unless directly relevant
- Do NOT sound like an ad
- If the topic isn't about order management/spec collection, do NOT mention ETSAI at all

Output the Reddit comment only. Nothing else."""

REDDIT_POST_SYSTEM = """You are writing an educational Reddit post for r/EtsySellers or r/Etsy.
You're sharing genuine tips from your experience managing custom orders.

Rules:
- Title should be value-first: "How I reduced custom order back-and-forth by 80%"
- Body: share real actionable tips (not just "use ETSAI")
- Mention ETSAI naturally as ONE of your tips, not the main focus
- Include 3-5 concrete, helpful tips that don't require any tool
- Under 200 words for the body
- Casual, community tone
- No emojis

Output format:
TITLE: [post title]
BODY: [post body]"""

DM_SYSTEM = """You are writing a short Instagram/social DM to an Etsy seller.

Rules:
- Ultra short: 2-3 sentences max
- Reference their shop or what they sell
- Ask one specific question about how they handle custom order details
- Casual, friendly tone — like a fellow maker
- No emojis, no pitch, no pricing

Output the DM text only. Nothing else."""

ETSY_CONVO_SYSTEM = """You are Noah, a fellow Etsy seller. You're sending a quick message through
Etsy's messaging system to another seller whose shop you genuinely like.

Rules:
- Do NOT mention ETSAI, any tool, any product you're building, or that you're a "founder" of anything
- Reference something specific about THEIR shop — a product that caught your eye, their custom work, etc.
- Ask one genuine question about their custom order process (how they collect details, handle personalization, etc.)
- TWO sentences max. Keep it short like a real Etsy message.
- Vary your opening — don't always start with "I saw your shop" or "Hey I noticed". Be creative.
- Peer-to-peer tone, like one maker to another
- No emojis, no links, no pitch
- Sign off as just "— Noah"

Output the Etsy message only. Nothing else."""

FOLLOWUP_SYSTEM = """You are Noah, following up on a message you sent to a fellow Etsy seller.
They didn't reply to your last message.

Rules:
- Keep it super casual — "hey just bumping this" energy
- If this is follow-up #1: do NOT mention ETSAI or any tool. Just re-ask your question or add a related thought.
- If this is follow-up #2+: you can briefly mention you built a tool for custom order specs, but keep it to one clause, not the focus.
- Under 40 words. One to two sentences.
- No emojis, no links, no hard pitch, no "demo" offers
- Sign off as "— Noah"

Output the follow-up message only. Nothing else."""

SUBJECT_SYSTEM = """Generate a cold email subject line for an Etsy seller.
- 4-8 words
- Feel personal and curiosity-driven
- Do NOT mention ETSAI
- NOT clickbait
- Reference their shop or custom orders naturally

Output the subject line only. No quotes."""

# Variant style instructions appended to prompts
VARIANT_INSTRUCTIONS = {
    "question_first": "Style: Lead with a curious question about their workflow before anything else.",
    "value_first": "Style: Lead with a specific insight or stat about custom order management.",
    "casual": "Style: Extra casual — like texting a friend who sells on Etsy.",
    "professional": "Style: Slightly more polished and professional, but still warm.",
}


# =============================================================
# MESSAGE DRAFTING
# =============================================================

def _build_lead_context(lead):
    """Build context string from lead data for Claude prompts."""
    parts = []
    if lead.get("shop_name"):
        parts.append(f"Shop: {lead['shop_name']}")
    if lead.get("niche"):
        parts.append(f"Niche: {lead['niche']}")
    if lead.get("sale_count"):
        parts.append(f"Sales: {lead['sale_count']:,}")
    if lead.get("city"):
        parts.append(f"Location: {lead['city']}")
    if lead.get("outreach_angle"):
        parts.append(f"Outreach angle: {lead['outreach_angle']}")

    enrichment = lead.get("enrichment_data", {})
    if isinstance(enrichment, str):
        enrichment = json.loads(enrichment)
    if enrichment.get("sample_listing"):
        parts.append(f"Sample product: {enrichment['sample_listing']}")
    if enrichment.get("post_title"):
        parts.append(f"Reddit post: {enrichment['post_title']}")

    return "\n".join(parts)


def _get_winning_examples(channel, limit=3):
    """Query best-performing messages to use as few-shot examples for Claude."""
    if not LEARNING_ENABLED:
        return ""

    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT content, variant FROM growth_messages
            WHERE channel = %s AND status = 'replied'
            ORDER BY replied_at DESC LIMIT %s
        """, (channel, limit)).fetchall()
    finally:
        conn.close()

    if not rows:
        return ""

    examples = []
    for r in rows:
        d = dict(r)
        examples.append(d["content"][:200])

    return "\n\nHere are messages that got replies — use as inspiration (but don't copy directly):\n" + "\n---\n".join(examples)


def draft_message(lead, channel, campaign_id=None, variant=None):
    """
    Draft a personalized outreach message for a lead.
    Returns message_id or None.
    """
    start = time.time()
    system_prompts = {
        "email": EMAIL_SYSTEM,
        "etsy_convo": ETSY_CONVO_SYSTEM,
        "reddit_reply": REDDIT_REPLY_SYSTEM,
        "reddit_post": REDDIT_POST_SYSTEM,
        "dm": DM_SYSTEM,
    }
    system = system_prompts.get(channel, EMAIL_SYSTEM)
    context = _build_lead_context(lead)

    user_msg = f"Write a personalized {channel} message for this seller:\n\n{context}"

    # Add variant style instruction
    if variant and variant in VARIANT_INSTRUCTIONS:
        user_msg += f"\n\n{VARIANT_INSTRUCTIONS[variant]}"

    # Add winning examples from learnings
    winning = _get_winning_examples(channel)
    if winning:
        user_msg += winning

    try:
        raw, cost, inp, out = call_claude(user_msg, AI_MODEL_CHEAP, max_tokens=300, system=system)
    except Exception as e:
        logger.error(f"Writer draft error: {e}")
        log_agent_action("writer", f"draft_{channel}", False, {"error": str(e)})
        return None

    # Generate subject for emails
    subject = None
    if channel == "email":
        try:
            subj_raw, subj_cost, _, _ = call_claude(context, AI_MODEL_CHEAP,
                                                      max_tokens=50, system=SUBJECT_SYSTEM)
            subject = subj_raw.strip().strip('"\'')
            cost += subj_cost
        except Exception:
            subject = f"Quick question about {lead.get('shop_name', 'your shop')}"

    # Determine review status
    review_needed = (
        (channel == "email" and REVIEW_QUEUE_EMAIL) or
        (channel == "etsy_convo" and REVIEW_QUEUE_ETSY_CONVO) or
        (channel.startswith("reddit") and REVIEW_QUEUE_REDDIT) or
        channel == "dm"
    )

    msg_id = add_growth_message(
        channel=channel,
        content=raw,
        lead_id=lead.get("id"),
        campaign_id=campaign_id,
        variant=variant,
        subject=subject,
        review_status="pending" if review_needed else "approved",
    )

    duration_ms = int((time.time() - start) * 1000)
    log_agent_action("writer", f"draft_{channel}", True,
                     {"lead": lead.get("shop_name"), "msg_id": msg_id, "variant": variant},
                     tokens_used=inp + out, cost=cost, duration_ms=duration_ms)

    return msg_id


def draft_followup(lead, previous_messages=None):
    """Draft a follow-up message based on previous outreach."""
    if not previous_messages:
        previous_messages = get_lead_messages(lead["id"])

    # Check follow-up limit
    followup_count = sum(1 for m in previous_messages if m.get("variant") == "followup")
    if followup_count >= MAX_FOLLOWUPS_PER_LEAD:
        logger.info(f"Writer: max follow-ups reached for {lead.get('shop_name')}")
        return None

    # Determine original channel
    orig_channel = "email"
    for m in previous_messages:
        if m.get("channel") and m["channel"] != "followup":
            orig_channel = m["channel"]
            break

    context = _build_lead_context(lead)
    prev_content = "\n---\n".join(m["content"][:200] for m in previous_messages[-2:])
    followup_num = followup_count + 1

    user_msg = f"""Write follow-up #{followup_num} for this seller who didn't reply:

SELLER:
{context}

PREVIOUS MESSAGE(S):
{prev_content}

This is follow-up number {followup_num}."""

    try:
        raw, cost, inp, out = call_claude(user_msg, AI_MODEL_CHEAP, max_tokens=200,
                                           system=FOLLOWUP_SYSTEM)
    except Exception as e:
        logger.error(f"Writer followup error: {e}")
        return None

    # Use same channel as original message
    review_needed = (
        (orig_channel == "email" and REVIEW_QUEUE_EMAIL) or
        (orig_channel == "etsy_convo" and REVIEW_QUEUE_ETSY_CONVO) or
        True  # follow-ups always get reviewed
    )

    msg_id = add_growth_message(
        channel=orig_channel,
        content=raw,
        lead_id=lead.get("id"),
        variant="followup",
        review_status="pending" if review_needed else "approved",
    )

    log_agent_action("writer", "draft_followup", True,
                     {"lead": lead.get("shop_name"), "followup_num": followup_num},
                     tokens_used=inp + out, cost=cost)
    return msg_id


def draft_reddit_reply(thread_data):
    """Draft a helpful Reddit reply for a relevant thread."""
    context = f"Subreddit: r/{thread_data.get('subreddit', '?')}\n"
    context += f"Post title: {thread_data.get('title', '')}\n"
    context += f"Post body: {thread_data.get('body', '')[:500]}\n"
    if thread_data.get("comment_context"):
        context += f"Comment we're replying to: {thread_data['comment_context'][:300]}\n"

    try:
        raw, cost, inp, out = call_claude(context, AI_MODEL_SMART, max_tokens=300,
                                           system=REDDIT_REPLY_SYSTEM)
    except Exception as e:
        logger.error(f"Writer Reddit reply error: {e}")
        return None

    msg_id = add_growth_message(
        channel="reddit_reply",
        content=raw,
        review_status="pending",  # Reddit replies always need review
    )

    log_agent_action("writer", "draft_reddit_reply", True,
                     {"thread": thread_data.get("title", "")[:80]},
                     tokens_used=inp + out, cost=cost)
    return msg_id


def draft_value_post(niche, topic=None):
    """Draft an educational Reddit post about custom order management."""
    user_msg = f"Niche: {niche}"
    if topic:
        user_msg += f"\nTopic: {topic}"

    try:
        raw, cost, inp, out = call_claude(user_msg, AI_MODEL_SMART, max_tokens=500,
                                           system=REDDIT_POST_SYSTEM)
    except Exception as e:
        logger.error(f"Writer value post error: {e}")
        return None

    # Parse title and body
    title = ""
    body = raw
    if "TITLE:" in raw and "BODY:" in raw:
        parts = raw.split("BODY:", 1)
        title = parts[0].replace("TITLE:", "").strip()
        body = parts[1].strip()

    msg_id = add_growth_message(
        channel="reddit_post",
        content=body,
        subject=title,
        review_status="pending",  # Posts always need review
    )

    log_agent_action("writer", "draft_value_post", True,
                     {"niche": niche, "title": title[:80]},
                     tokens_used=inp + out, cost=cost)
    return msg_id


def batch_draft(leads, channel, campaign_id=None, variants=None):
    """Generate messages for a batch of leads. Returns list of message IDs."""
    if not variants:
        variants = [None]

    msg_ids = []
    for lead in leads:
        for variant in variants:
            msg_id = draft_message(lead, channel, campaign_id, variant)
            if msg_id:
                msg_ids.append(msg_id)
            time.sleep(0.3)  # Rate limiting

    return msg_ids


# =============================================================
# SENDING
# =============================================================

def send_email(message):
    """Send an email message using email_service."""
    lead = get_growth_lead(message["lead_id"]) if message.get("lead_id") else None
    if not lead or not lead.get("email"):
        logger.warning(f"Writer: no email for lead {message.get('lead_id')}")
        update_message_status(message["id"], "bounced")
        return False

    try:
        from email_service import _send_email, _is_configured
        if not _is_configured():
            logger.warning("Writer: SMTP not configured")
            return False

        success = _send_email(
            to_email=lead["email"],
            subject=message.get("subject", f"Quick question about {lead.get('shop_name', 'your shop')}"),
            html_body=f"<p>{message['content'].replace(chr(10), '<br>')}</p>",
        )
        if success:
            update_message_status(message["id"], "sent")
            update_lead_status(lead["id"], "contacted")
            if message.get("campaign_id"):
                update_campaign_stats(message["campaign_id"], messages_sent=1)
            return True
        else:
            update_message_status(message["id"], "bounced")
            return False
    except Exception as e:
        logger.error(f"Writer send email error: {e}")
        update_message_status(message["id"], "bounced")
        return False


def process_send_queue():
    """Process queued messages that have been approved for sending."""
    start = time.time()
    sent = {"email": 0, "etsy_convo": 0, "reddit_reply": 0, "reddit_post": 0, "dm": 0}

    # Get approved messages ready to send
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT * FROM growth_messages
            WHERE status = 'queued' AND review_status = 'approved'
            ORDER BY created_at ASC LIMIT 50
        """).fetchall()
    finally:
        conn.close()

    for row in [dict(r) for r in rows]:
        channel = row["channel"]

        # Check daily quotas
        if channel == "email" and get_messages_sent_today("email") >= WRITER_MAX_EMAILS_PER_DAY:
            logger.info("Writer: daily email quota reached")
            break
        if channel.startswith("reddit") and get_messages_sent_today("reddit_reply") + get_messages_sent_today("reddit_post") >= WRITER_MAX_REDDIT_COMMENTS_PER_DAY:
            logger.info("Writer: daily Reddit quota reached")
            continue
        if channel == "dm" and get_messages_sent_today("dm") >= WRITER_MAX_DMS_PER_DAY:
            logger.info("Writer: daily DM quota reached")
            continue

        if channel == "email":
            if send_email(row):
                sent["email"] += 1
        elif channel == "etsy_convo":
            # Etsy convos are manual — Noah sends via Etsy Messages.
            # Only mark sent when explicitly approved from dashboard.
            pass
        elif channel in ("reddit_reply", "reddit_post"):
            # Reddit posting requires PRAW — mark as sent (manual posting for now)
            update_message_status(row["id"], "sent")
            sent[channel] = sent.get(channel, 0) + 1
        elif channel == "dm":
            # DMs are manual — mark as sent when copied
            update_message_status(row["id"], "sent")
            sent["dm"] += 1

        time.sleep(0.5)

    total_sent = sum(sent.values())
    duration_ms = int((time.time() - start) * 1000)
    if total_sent > 0:
        log_agent_action("writer", "process_send_queue", True,
                         sent, duration_ms=duration_ms)
    logger.info(f"Writer: sent {total_sent} messages — {sent}")
    return sent


# =============================================================
# ANTI-SPAM CHECKS
# =============================================================

def check_channel_health(channel):
    """Check if a channel should be paused due to low response rate."""
    conn = get_conn()
    try:
        row = conn.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status = 'replied' THEN 1 ELSE 0 END) as replied
            FROM growth_messages
            WHERE channel = %s AND status IN ('sent', 'replied')
        """, (channel,)).fetchone()
    finally:
        conn.close()

    total = row["total"] if row else 0
    replied = row["replied"] if row else 0

    if total < 20:
        return True  # Not enough data yet

    rate = (replied / total * 100) if total > 0 else 0
    if rate < MIN_RESPONSE_RATE_PCT:
        logger.warning(f"Writer: {channel} response rate {rate:.1f}% below minimum {MIN_RESPONSE_RATE_PCT}%")
        return False
    return True


# =============================================================
# SELF-LEARNING — REPLY RATES & VARIANT PERFORMANCE
# =============================================================

def update_writer_learnings():
    """Track reply rates per channel + variant to learn what works."""
    if not LEARNING_ENABLED:
        return

    conn = get_conn()
    try:
        # Per channel + variant stats
        rows = conn.execute("""
            SELECT channel, variant,
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
                   SUM(CASE WHEN status = 'replied' THEN 1 ELSE 0 END) as replied
            FROM growth_messages
            WHERE status IN ('sent', 'replied')
            GROUP BY channel, variant
        """).fetchall()
    finally:
        conn.close()

    for row in rows:
        r = dict(row)
        channel = r["channel"]
        variant = r["variant"] or "default"
        sent = r["sent"] + r["replied"]  # replied is also sent
        replied = r["replied"]

        if sent == 0:
            continue

        reply_rate = (replied / sent) * 100
        confidence = min(sent / 15, 1.0)
        key = f"{channel}:{variant}"

        upsert_learning(
            agent="writer",
            learning_type="variant_performance",
            key=key,
            value_json={
                "channel": channel,
                "variant": variant,
                "reply_rate": round(reply_rate, 1),
                "sent": sent,
                "replied": replied,
            },
            score=round(reply_rate, 2),
            sample_size=sent,
            confidence=round(confidence, 2),
        )

    logger.info(f"Writer: Updated learnings for {len(rows)} channel/variant combos")


def _pick_variant():
    """Pick a variant for A/B testing. Prefers high-performing variants but explores."""
    if not LEARNING_ENABLED:
        return random.choice(VARIANTS)

    top = get_top_learnings("writer", "variant_performance", limit=4, min_sample=5)
    if not top:
        return random.choice(VARIANTS)

    # 80% exploit best, 20% explore random
    if random.random() < 0.2:
        return random.choice(VARIANTS)

    best_key = top[0]["key"]
    # key format is "channel:variant"
    variant = best_key.split(":")[-1] if ":" in best_key else best_key
    if variant in VARIANTS:
        return variant
    return random.choice(VARIANTS)


# =============================================================
# MAIN RUN
# =============================================================

def run():
    """Main writer run — draft new messages and process send queue."""
    from growth.growth_config import GROWTH_ENABLED
    if not GROWTH_ENABLED:
        return {"status": "disabled"}

    start = time.time()
    result = {"drafted": 0, "sent": {}}

    # Draft new messages for contactable leads — smart channel selection
    from growth.scout import get_daily_targets
    targets = get_daily_targets()
    for lead in targets[:10]:
        existing = get_lead_messages(lead["id"])
        if existing:
            continue

        # Pick channel: email if lead has one, otherwise etsy_convo
        if lead.get("email") and CHANNEL_EMAIL and check_channel_health("email"):
            if get_messages_sent_today("email") >= WRITER_MAX_EMAILS_PER_DAY:
                continue
            channel = "email"
        elif CHANNEL_ETSY_CONVO:
            channel = "etsy_convo"
        else:
            continue

        # A/B variant assignment
        variant = _pick_variant()
        msg_id = draft_message(lead, channel, variant=variant)
        if msg_id:
            result["drafted"] += 1
        time.sleep(0.3)

    # Draft follow-ups for contacted leads that haven't replied
    from growth.growth_db import get_followup_candidates
    followup_leads = get_followup_candidates(
        gap_days=MIN_FOLLOWUP_GAP_DAYS,
        max_followups=MAX_FOLLOWUPS_PER_LEAD,
        limit=5,
    )
    followups_drafted = 0
    for lead in followup_leads:
        msg_id = draft_followup(lead)
        if msg_id:
            followups_drafted += 1
        time.sleep(0.3)
    result["followups_drafted"] = followups_drafted

    # Process send queue
    result["sent"] = process_send_queue()

    # Update learnings
    if LEARNING_ENABLED:
        try:
            update_writer_learnings()
        except Exception as e:
            logger.error(f"Writer learning update error: {e}")

    duration_ms = int((time.time() - start) * 1000)
    log_agent_action("writer", "run", True, result, duration_ms=duration_ms)
    return result
