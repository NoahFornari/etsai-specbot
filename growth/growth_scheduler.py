"""
ETSAI Growth Bot — Scheduler
APScheduler integration — runs agents on cron intervals.
"""
import logging

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from growth.growth_config import (
    GROWTH_ENABLED,
    SCHEDULE_COMMANDER_MINS,
    SCHEDULE_SCOUT_MINS,
    SCHEDULE_LISTENER_MINS,
    SCHEDULE_CREATOR_MINS,
    SCHEDULE_WRITER_MINS,
)

logger = logging.getLogger("etsai.growth.scheduler")

_scheduler = None


def _safe_run(agent_name, run_func, **kwargs):
    """Wrapper that catches errors so one agent crash doesn't kill the scheduler."""
    if not GROWTH_ENABLED:
        return
    try:
        logger.info(f"Scheduler: Running {agent_name}")
        result = run_func(**kwargs)
        logger.info(f"Scheduler: {agent_name} complete — {result}")
    except Exception as e:
        logger.error(f"Scheduler: {agent_name} crashed: {e}")
        from growth.growth_db import log_agent_action
        log_agent_action(agent_name, "scheduled_run", False, {"error": str(e)})


def init_scheduler(app=None):
    """
    Initialize and start the APScheduler.
    Call this from app.py after init_db().
    """
    global _scheduler

    if not GROWTH_ENABLED:
        logger.info("Growth system disabled — scheduler not started")
        return None

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        logger.warning("APScheduler not installed — growth scheduler disabled")
        return None

    _scheduler = BackgroundScheduler(daemon=True)

    # Commander — the brain, runs everything else too
    _scheduler.add_job(
        lambda: _safe_run("commander", _run_commander),
        "interval",
        minutes=SCHEDULE_COMMANDER_MINS,
        id="growth_commander",
        replace_existing=True,
    )

    # Scout — lead discovery (also runs in Commander cycle, this is backup)
    _scheduler.add_job(
        lambda: _safe_run("scout", _run_scout),
        "interval",
        minutes=SCHEDULE_SCOUT_MINS,
        id="growth_scout",
        replace_existing=True,
    )

    # Listener — community monitoring
    _scheduler.add_job(
        lambda: _safe_run("listener", _run_listener),
        "interval",
        minutes=SCHEDULE_LISTENER_MINS,
        id="growth_listener",
        replace_existing=True,
    )

    # Creator — video production
    _scheduler.add_job(
        lambda: _safe_run("creator", _run_creator),
        "interval",
        minutes=SCHEDULE_CREATOR_MINS,
        id="growth_creator",
        replace_existing=True,
    )

    # Writer — process send queue
    _scheduler.add_job(
        lambda: _safe_run("writer", _run_writer),
        "interval",
        minutes=SCHEDULE_WRITER_MINS,
        id="growth_writer",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("Growth scheduler started — "
                f"Commander every {SCHEDULE_COMMANDER_MINS}m, "
                f"Scout every {SCHEDULE_SCOUT_MINS}m, "
                f"Listener every {SCHEDULE_LISTENER_MINS}m, "
                f"Creator every {SCHEDULE_CREATOR_MINS}m, "
                f"Writer every {SCHEDULE_WRITER_MINS}m")

    return _scheduler


def _run_commander():
    from growth.commander import run_cycle
    return run_cycle()


def _run_scout():
    from growth.scout import run as scout_run
    return scout_run()


def _run_listener():
    from growth.listener import run as listener_run
    return listener_run()


def _run_creator():
    from growth.creator import run as creator_run
    return creator_run()


def _run_writer():
    from growth.writer import run as writer_run
    return writer_run()


def shutdown_scheduler():
    """Gracefully shut down the scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        logger.info("Growth scheduler shut down")
        _scheduler = None


def get_scheduler_status():
    """Get current scheduler status for dashboard."""
    if not _scheduler:
        return {"running": False, "jobs": []}

    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name or job.id,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "interval": str(job.trigger),
        })

    return {"running": _scheduler.running, "jobs": jobs}
