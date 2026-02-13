"""
ETSAI Growth Bot — Commander Agent (The Brain)
Runs every hour. Reviews metrics, allocates budget, dispatches agents.
Uses Claude Sonnet for strategic decisions.
"""
import json
import logging
import time
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engine import call_claude, AI_MODEL_SMART, AI_MODEL_CHEAP
from growth.growth_db import (
    get_growth_overview, get_daily_metrics, save_daily_metrics,
    get_agent_stats, get_last_agent_run, get_lead_funnel,
    get_active_campaigns, log_agent_action, get_agent_log,
    get_messages_sent_today, get_lead_count_today, get_videos_published_today,
)
from growth.growth_config import (
    DAILY_BUDGET, GROWTH_ENABLED,
    CHANNEL_EMAIL, CHANNEL_REDDIT, CHANNEL_YOUTUBE, CHANNEL_ETSY_CONVO,
)

logger = logging.getLogger("etsai.growth.commander")

# Bootstrap instructions — no Claude call needed
BOOTSTRAP_INSTRUCTIONS = {
    "scout": {"run": True, "niches": ["jewelry", "portraits", "wedding"], "lead_limit": 30},
    "writer": {"run": False},
    "listener": {"run": False},
    "creator": {"run": True, "video_count": 1},
    "strategy_notes": "Bootstrap mode — discovering leads first",
}


# =============================================================
# METRICS SNAPSHOT
# =============================================================

def _collect_metrics():
    """Gather current metrics from all sources."""
    overview = get_growth_overview()
    funnel = get_lead_funnel()

    agent_stats = {}
    for agent in ["scout", "writer", "listener", "creator", "commander"]:
        agent_stats[agent] = {
            "last_24h": get_agent_stats(agent, since_hours=24),
            "last_run": get_last_agent_run(agent),
        }

    today = {
        "leads_discovered": get_lead_count_today(),
        "messages_sent": get_messages_sent_today(),
        "videos_published": get_videos_published_today(),
    }

    return {
        "overview": overview,
        "funnel": funnel,
        "agents": agent_stats,
        "today": today,
        "budget_remaining": DAILY_BUDGET - overview.get("spend_today", 0),
    }


# =============================================================
# BUDGET ALLOCATION
# =============================================================

def allocate_budget(metrics, model=None):
    """
    Use Claude to decide how to allocate today's remaining budget across agents.
    Returns JSON with per-agent instructions.
    """
    if model is None:
        model = AI_MODEL_SMART
    budget_remaining = metrics.get("budget_remaining", DAILY_BUDGET)
    overview = metrics.get("overview", {})
    today = metrics.get("today", {})

    prompt = f"""You are the growth strategist for ETSAI (an AI tool for Etsy sellers).
Review today's metrics and decide how to allocate the remaining budget across our marketing agents.

METRICS TODAY:
- Leads discovered: {today.get('leads_discovered', 0)}
- Messages sent: {today.get('messages_sent', 0)}
- Videos published: {today.get('videos_published', 0)}
- Budget remaining: ${budget_remaining:.2f} of ${DAILY_BUDGET:.2f}

ALL-TIME:
- Total leads: {overview.get('leads_total', 0)} (HOT: {overview.get('leads_hot', 0)})
- Contacted: {overview.get('leads_contacted', 0)}
- Responded: {overview.get('leads_responded', 0)}
- Converted: {overview.get('leads_converted', 0)}
- Reply rate: {overview.get('reply_rate', 0)}%
- Total messages sent: {overview.get('messages_total', 0)}
- Videos published: {overview.get('videos_total', 0)} ({overview.get('video_views', 0)} views)
- Total spend: ${overview.get('total_spend', 0):.2f}

CHANNELS ACTIVE: Email={'ON' if CHANNEL_EMAIL else 'OFF'}, Reddit={'ON' if CHANNEL_REDDIT else 'OFF'}, YouTube={'ON' if CHANNEL_YOUTUBE else 'OFF'}, Etsy Convo={'ON' if CHANNEL_ETSY_CONVO else 'OFF'}

Based on these metrics, decide:
1. Which agents should run in the next cycle?
2. What niches should Scout focus on?
3. How many emails/Reddit posts should Writer produce?
4. What video topics should Creator make?
5. Any strategy changes?

RESPOND IN JSON:
{{
    "scout": {{"run": true, "niches": ["jewelry", "wedding"], "lead_limit": 30}},
    "writer": {{"run": true, "email_count": 10, "reddit_posts": 1}},
    "listener": {{"run": true}},
    "creator": {{"run": true, "video_count": 1, "topics": ["tip about ring size collection"]}},
    "strategy_notes": "Focus on jewelry niche — highest conversion rate",
    "pause_channels": []
}}
JSON only."""

    try:
        raw, cost, inp, out = call_claude(prompt, model, max_tokens=500)
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
        instructions = json.loads(clean)

        log_agent_action("commander", "allocate_budget", True,
                         {"instructions": instructions},
                         cost=cost, tokens_used=inp + out)
        return instructions

    except Exception as e:
        logger.error(f"Commander budget allocation error: {e}")
        # Fallback: run everything with defaults
        return {
            "scout": {"run": True, "niches": ["jewelry", "portraits", "signs"], "lead_limit": 30},
            "writer": {"run": True, "email_count": 10, "reddit_posts": 0},
            "listener": {"run": True},
            "creator": {"run": True, "video_count": 1},
            "strategy_notes": "Fallback: running defaults",
        }


# =============================================================
# AGENT DISPATCH
# =============================================================

def _dispatch_scout(instructions):
    """Run Scout agent with Commander's instructions."""
    if not instructions.get("run"):
        return {"status": "skipped"}
    try:
        from growth.scout import run as scout_run
        niches = instructions.get("niches")
        return scout_run(niches=niches)
    except Exception as e:
        logger.error(f"Commander: Scout dispatch error: {e}")
        log_agent_action("commander", "dispatch_scout", False, {"error": str(e)})
        return {"status": "error", "error": str(e)}


def _dispatch_writer(instructions):
    """Run Writer agent with Commander's instructions."""
    if not instructions.get("run"):
        return {"status": "skipped"}
    try:
        from growth.writer import run as writer_run
        return writer_run()
    except Exception as e:
        logger.error(f"Commander: Writer dispatch error: {e}")
        log_agent_action("commander", "dispatch_writer", False, {"error": str(e)})
        return {"status": "error", "error": str(e)}


def _dispatch_listener(instructions):
    """Run Listener agent with Commander's instructions."""
    if not instructions.get("run"):
        return {"status": "skipped"}
    try:
        from growth.listener import run as listener_run
        return listener_run()
    except Exception as e:
        logger.error(f"Commander: Listener dispatch error: {e}")
        log_agent_action("commander", "dispatch_listener", False, {"error": str(e)})
        return {"status": "error", "error": str(e)}


def _dispatch_creator(instructions, pain_points=None):
    """Run Creator agent with Commander's instructions."""
    if not instructions.get("run"):
        return {"status": "skipped"}
    try:
        from growth.creator import run as creator_run
        return creator_run(pain_points=pain_points)
    except Exception as e:
        logger.error(f"Commander: Creator dispatch error: {e}")
        log_agent_action("commander", "dispatch_creator", False, {"error": str(e)})
        return {"status": "error", "error": str(e)}


# =============================================================
# PERFORMANCE EVALUATION
# =============================================================

def evaluate_performance():
    """Use Claude to analyze growth performance and suggest strategy shifts."""
    metrics = _collect_metrics()
    overview = metrics.get("overview", {})

    prompt = f"""Evaluate the growth performance for ETSAI and suggest improvements.

CURRENT STATE:
- Total leads: {overview.get('leads_total', 0)} (Converted: {overview.get('leads_converted', 0)})
- Reply rate: {overview.get('reply_rate', 0)}%
- Conversion rate: {overview.get('conversion_rate', 0)}%
- Total messages: {overview.get('messages_total', 0)}
- Videos: {overview.get('videos_total', 0)} ({overview.get('video_views', 0)} views)
- Total spend: ${overview.get('total_spend', 0):.2f}

Provide:
1. What's working well (keep doing)
2. What's underperforming (change)
3. Specific tactical recommendations
4. Priority for next week

Keep it concise — under 200 words.
Just the analysis text, no JSON."""

    try:
        text, cost, inp, out = call_claude(prompt, AI_MODEL_SMART, max_tokens=400)
        log_agent_action("commander", "evaluate_performance", True,
                         {"analysis_length": len(text)}, cost=cost)
        return text
    except Exception as e:
        logger.error(f"Commander evaluation error: {e}")
        return "Evaluation failed — check logs."


# =============================================================
# WEEKLY REPORT
# =============================================================

def generate_report():
    """Generate a weekly performance summary."""
    from growth.growth_db import get_metrics_range
    metrics = get_metrics_range(days=7)
    overview = get_growth_overview()

    if not metrics:
        return "No metrics data available for the past week."

    total_leads = sum(m.get("leads_discovered", 0) for m in metrics)
    total_messages = sum(m.get("messages_sent", 0) for m in metrics)
    total_replies = sum(m.get("messages_replied", 0) for m in metrics)
    total_videos = sum(m.get("videos_published", 0) for m in metrics)
    total_spend = sum(m.get("total_spend", 0) for m in metrics)

    prompt = f"""Write a concise weekly growth report for ETSAI.

THIS WEEK:
- New leads: {total_leads}
- Messages sent: {total_messages}
- Replies received: {total_replies}
- Videos published: {total_videos}
- Spend: ${total_spend:.2f}

ALL-TIME:
- Total leads: {overview.get('leads_total', 0)}
- Conversions: {overview.get('leads_converted', 0)}
- Total video views: {overview.get('video_views', 0)}

Format as a brief report with:
1. Key metrics summary
2. What worked this week
3. Focus areas for next week

Under 150 words. Professional but friendly tone."""

    try:
        text, cost, _, _ = call_claude(prompt, AI_MODEL_SMART, max_tokens=300)
        log_agent_action("commander", "generate_report", True, cost=cost)
        return text
    except Exception as e:
        logger.error(f"Commander report error: {e}")
        return f"Report generation failed: {e}"


# =============================================================
# MAIN CYCLE
# =============================================================

def _should_skip_claude(metrics):
    """
    Determine if we can skip the expensive Claude Sonnet strategy call.
    Returns (skip: bool, reason: str, instructions: dict|None).
    """
    overview = metrics.get("overview", {})
    today = metrics.get("today", {})
    budget_remaining = metrics.get("budget_remaining", DAILY_BUDGET)
    leads_total = overview.get("leads_total", 0)

    # Case 1: No leads at all — bootstrap mode, just run Scout + Creator
    if leads_total == 0 and budget_remaining <= 0:
        return True, "bootstrap_no_budget", BOOTSTRAP_INSTRUCTIONS

    if leads_total == 0:
        return True, "bootstrap", BOOTSTRAP_INSTRUCTIONS

    # Case 2: Budget exhausted for the day
    if budget_remaining <= 0:
        return True, "budget_exhausted", {
            "scout": {"run": False},
            "writer": {"run": False},
            "listener": {"run": True},
            "creator": {"run": False},
            "strategy_notes": "Budget exhausted — only free operations",
        }

    # Case 3: Nothing new since last cycle — use Haiku instead (handled in caller)
    if today.get("leads_discovered", 0) == 0 and today.get("messages_sent", 0) == 0:
        return False, "use_haiku", None

    return False, "normal", None


def run_cycle():
    """
    Main Commander loop:
    1. Collect metrics
    2. Ask Claude for strategy (or skip if nothing to do)
    3. Dispatch agents
    4. Save daily metrics
    5. Log results
    """
    if not GROWTH_ENABLED:
        logger.info("Commander: Growth system disabled")
        return {"status": "disabled"}

    start = time.time()
    cycle_result = {
        "timestamp": datetime.now().isoformat(),
        "agents": {},
    }

    # Step 1: Collect metrics
    metrics = _collect_metrics()
    cycle_result["metrics_snapshot"] = {
        "leads_total": metrics["overview"].get("leads_total", 0),
        "budget_remaining": metrics.get("budget_remaining", DAILY_BUDGET),
    }

    # Step 2: Smart early-exit — skip Claude when nothing actionable
    skip, reason, fallback_instructions = _should_skip_claude(metrics)

    if skip:
        instructions = fallback_instructions
        cycle_result["strategy_mode"] = reason
        log_agent_action("commander", f"skip_claude_{reason}", True,
                         {"reason": reason}, cost=0)
        logger.info(f"Commander: Skipping Claude strategy call — {reason}")
    elif reason == "use_haiku":
        # Nothing new today — use cheaper Haiku model for strategy
        instructions = allocate_budget(metrics, model=AI_MODEL_CHEAP)
        cycle_result["strategy_mode"] = "haiku_fallback"
    else:
        instructions = allocate_budget(metrics)
        cycle_result["strategy_mode"] = "normal"

    cycle_result["instructions"] = instructions

    # Step 3: Dispatch agents
    # Listener first (gathers intelligence for Creator)
    listener_result = _dispatch_listener(instructions.get("listener", {}))
    cycle_result["agents"]["listener"] = listener_result

    # Scout
    scout_result = _dispatch_scout(instructions.get("scout", {}))
    cycle_result["agents"]["scout"] = scout_result

    # Creator (uses pain points from Listener)
    pain_points = listener_result.get("pain_points") if isinstance(listener_result, dict) else None
    creator_result = _dispatch_creator(instructions.get("creator", {}), pain_points)
    cycle_result["agents"]["creator"] = creator_result

    # Writer (last — needs leads from Scout)
    writer_result = _dispatch_writer(instructions.get("writer", {}))
    cycle_result["agents"]["writer"] = writer_result

    # Step 4: Save daily metrics
    today = datetime.now().strftime("%Y-%m-%d")
    save_daily_metrics(
        date_str=today,
        leads_discovered=get_lead_count_today(),
        messages_sent=get_messages_sent_today(),
        videos_published=get_videos_published_today(),
        total_spend=metrics["overview"].get("spend_today", 0),
        notes=instructions.get("strategy_notes", ""),
    )

    # Step 5: Log
    duration_ms = int((time.time() - start) * 1000)
    cycle_result["duration_ms"] = duration_ms
    log_agent_action("commander", "run_cycle", True, cycle_result, duration_ms=duration_ms)

    logger.info(f"Commander: Cycle complete in {duration_ms}ms — "
                f"Scout: {scout_result.get('leads_added', 'N/A')}, "
                f"Writer: {writer_result.get('drafted', 'N/A')}, "
                f"Creator: {creator_result.get('videos_created', 'N/A')}")

    return cycle_result


# =============================================================
# BEST PERFORMERS
# =============================================================

def get_best_performing(channel=None, metric="replied", n=5):
    """Get top-performing messages for template replication."""
    from growth.growth_db import get_conn
    conn = get_conn()
    try:
        if channel:
            rows = conn.execute(f"""
                SELECT gm.*, gl.shop_name, gl.niche, gl.tier
                FROM growth_messages gm
                LEFT JOIN growth_leads gl ON gm.lead_id = gl.id
                WHERE gm.status = %s AND gm.channel = %s
                ORDER BY gm.replied_at DESC
                LIMIT %s
            """, (metric, channel, n)).fetchall()
        else:
            rows = conn.execute(f"""
                SELECT gm.*, gl.shop_name, gl.niche, gl.tier
                FROM growth_messages gm
                LEFT JOIN growth_leads gl ON gm.lead_id = gl.id
                WHERE gm.status = %s
                ORDER BY gm.replied_at DESC
                LIMIT %s
            """, (metric, n)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
