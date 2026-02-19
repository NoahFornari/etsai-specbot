"""
ETSAI Growth Bot — Database Layer
Six growth tables using the same DB wrapper from database.py.
"""
import json
import uuid
import logging
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_conn, USE_PG, _ago, _now_expr

logger = logging.getLogger("etsai.growth_db")


# =============================================================
# SCHEMA
# =============================================================

def init_growth_tables():
    """Create growth tables. Called from init_db() in database.py."""
    conn = get_conn()
    try:
        if USE_PG:
            _init_growth_pg(conn)
        else:
            _init_growth_sqlite(conn)
        conn.commit()
    finally:
        conn.close()


def _init_growth_sqlite(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS growth_leads (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            shop_name TEXT,
            shop_url TEXT,
            email TEXT,
            social_url TEXT,
            reddit_username TEXT,
            score INTEGER DEFAULT 0,
            tier TEXT DEFAULT 'COLD',
            niche TEXT,
            contact_status TEXT DEFAULT 'new',
            outreach_angle TEXT,
            sale_count INTEGER DEFAULT 0,
            review_count INTEGER DEFAULT 0,
            review_average REAL,
            listing_count INTEGER DEFAULT 0,
            custom_pct REAL DEFAULT 0,
            city TEXT,
            enrichment_data TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_contacted_at TIMESTAMP,
            converted_at TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS growth_campaigns (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            channel TEXT NOT NULL,
            target_niche TEXT,
            status TEXT DEFAULT 'active',
            messages_sent INTEGER DEFAULT 0,
            responses INTEGER DEFAULT 0,
            conversions INTEGER DEFAULT 0,
            best_variant TEXT,
            config TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS growth_messages (
            id TEXT PRIMARY KEY,
            campaign_id TEXT,
            lead_id TEXT,
            channel TEXT NOT NULL,
            variant TEXT,
            subject TEXT,
            content TEXT NOT NULL,
            status TEXT DEFAULT 'queued',
            sent_at TIMESTAMP,
            opened_at TIMESTAMP,
            replied_at TIMESTAMP,
            review_status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES growth_campaigns(id),
            FOREIGN KEY (lead_id) REFERENCES growth_leads(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS growth_content (
            id TEXT PRIMARY KEY,
            content_type TEXT NOT NULL,
            title TEXT,
            body TEXT,
            script TEXT,
            media_path TEXT,
            thumbnail_path TEXT,
            platform TEXT,
            platform_post_id TEXT,
            platform_url TEXT,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            status TEXT DEFAULT 'draft',
            scheduled_for TIMESTAMP,
            published_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS growth_agent_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent TEXT NOT NULL,
            action TEXT NOT NULL,
            success INTEGER DEFAULT 1,
            details TEXT DEFAULT '{}',
            tokens_used INTEGER DEFAULT 0,
            cost REAL DEFAULT 0,
            duration_ms INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS growth_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            leads_discovered INTEGER DEFAULT 0,
            messages_sent INTEGER DEFAULT 0,
            messages_replied INTEGER DEFAULT 0,
            signups INTEGER DEFAULT 0,
            videos_published INTEGER DEFAULT 0,
            reddit_posts INTEGER DEFAULT 0,
            reddit_comments INTEGER DEFAULT 0,
            total_spend REAL DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS growth_learnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent TEXT NOT NULL,
            learning_type TEXT NOT NULL,
            key TEXT NOT NULL,
            value_json TEXT DEFAULT '{}',
            score REAL DEFAULT 0,
            sample_size INTEGER DEFAULT 0,
            confidence REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS growth_seen_threads (
            thread_id TEXT PRIMARY KEY,
            subreddit TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    _create_growth_indexes(conn)


def _init_growth_pg(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS growth_leads (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            shop_name TEXT,
            shop_url TEXT,
            email TEXT,
            social_url TEXT,
            reddit_username TEXT,
            score INTEGER DEFAULT 0,
            tier TEXT DEFAULT 'COLD',
            niche TEXT,
            contact_status TEXT DEFAULT 'new',
            outreach_angle TEXT,
            sale_count INTEGER DEFAULT 0,
            review_count INTEGER DEFAULT 0,
            review_average REAL,
            listing_count INTEGER DEFAULT 0,
            custom_pct REAL DEFAULT 0,
            city TEXT,
            enrichment_data TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_contacted_at TIMESTAMP,
            converted_at TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS growth_campaigns (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            channel TEXT NOT NULL,
            target_niche TEXT,
            status TEXT DEFAULT 'active',
            messages_sent INTEGER DEFAULT 0,
            responses INTEGER DEFAULT 0,
            conversions INTEGER DEFAULT 0,
            best_variant TEXT,
            config TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS growth_messages (
            id TEXT PRIMARY KEY,
            campaign_id TEXT REFERENCES growth_campaigns(id),
            lead_id TEXT REFERENCES growth_leads(id),
            channel TEXT NOT NULL,
            variant TEXT,
            subject TEXT,
            content TEXT NOT NULL,
            status TEXT DEFAULT 'queued',
            sent_at TIMESTAMP,
            opened_at TIMESTAMP,
            replied_at TIMESTAMP,
            review_status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS growth_content (
            id TEXT PRIMARY KEY,
            content_type TEXT NOT NULL,
            title TEXT,
            body TEXT,
            script TEXT,
            media_path TEXT,
            thumbnail_path TEXT,
            platform TEXT,
            platform_post_id TEXT,
            platform_url TEXT,
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,
            shares INTEGER DEFAULT 0,
            status TEXT DEFAULT 'draft',
            scheduled_for TIMESTAMP,
            published_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS growth_agent_log (
            id SERIAL PRIMARY KEY,
            agent TEXT NOT NULL,
            action TEXT NOT NULL,
            success INTEGER DEFAULT 1,
            details TEXT DEFAULT '{}',
            tokens_used INTEGER DEFAULT 0,
            cost REAL DEFAULT 0,
            duration_ms INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS growth_learnings (
            id SERIAL PRIMARY KEY,
            agent TEXT NOT NULL,
            learning_type TEXT NOT NULL,
            key TEXT NOT NULL,
            value_json TEXT DEFAULT '{}',
            score REAL DEFAULT 0,
            sample_size INTEGER DEFAULT 0,
            confidence REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS growth_metrics (
            id SERIAL PRIMARY KEY,
            date TEXT NOT NULL,
            leads_discovered INTEGER DEFAULT 0,
            messages_sent INTEGER DEFAULT 0,
            messages_replied INTEGER DEFAULT 0,
            signups INTEGER DEFAULT 0,
            videos_published INTEGER DEFAULT 0,
            reddit_posts INTEGER DEFAULT 0,
            reddit_comments INTEGER DEFAULT 0,
            total_spend REAL DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS growth_seen_threads (
            thread_id TEXT PRIMARY KEY,
            subreddit TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    _create_growth_indexes(conn)


def _create_growth_indexes(conn):
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_gl_tier ON growth_leads(tier)",
        "CREATE INDEX IF NOT EXISTS idx_gl_status ON growth_leads(contact_status)",
        "CREATE INDEX IF NOT EXISTS idx_gl_source ON growth_leads(source)",
        "CREATE INDEX IF NOT EXISTS idx_gl_niche ON growth_leads(niche)",
        "CREATE INDEX IF NOT EXISTS idx_gl_shop_url ON growth_leads(shop_url)",
        "CREATE INDEX IF NOT EXISTS idx_gm_campaign ON growth_messages(campaign_id)",
        "CREATE INDEX IF NOT EXISTS idx_gm_lead ON growth_messages(lead_id)",
        "CREATE INDEX IF NOT EXISTS idx_gm_status ON growth_messages(status)",
        "CREATE INDEX IF NOT EXISTS idx_gc_channel ON growth_campaigns(channel)",
        "CREATE INDEX IF NOT EXISTS idx_gco_platform ON growth_content(platform)",
        "CREATE INDEX IF NOT EXISTS idx_gco_status ON growth_content(status)",
        "CREATE INDEX IF NOT EXISTS idx_gal_agent ON growth_agent_log(agent)",
        "CREATE INDEX IF NOT EXISTS idx_gme_date ON growth_metrics(date)",
        "CREATE INDEX IF NOT EXISTS idx_glrn_agent ON growth_learnings(agent)",
        "CREATE INDEX IF NOT EXISTS idx_glrn_type ON growth_learnings(learning_type)",
        "CREATE INDEX IF NOT EXISTS idx_glrn_lookup ON growth_learnings(agent, learning_type, key)",
    ]
    for sql in indexes:
        conn.execute(sql)


# =============================================================
# LEAD CRUD
# =============================================================

def add_growth_lead(source, shop_name=None, shop_url=None, email=None,
                    social_url=None, reddit_username=None, score=0, tier="COLD",
                    niche=None, outreach_angle=None, sale_count=0,
                    review_count=0, review_average=None, listing_count=0,
                    custom_pct=0, city=None, enrichment_data=None):
    """Add a new growth lead. Returns lead_id or None if duplicate shop_url."""
    lead_id = str(uuid.uuid4())[:8]
    conn = get_conn()
    try:
        # Deduplicate by shop_url
        if shop_url:
            existing = conn.execute(
                "SELECT id FROM growth_leads WHERE shop_url = %s", (shop_url,)
            ).fetchone()
            if existing:
                return None

        conn.execute("""
            INSERT INTO growth_leads
            (id, source, shop_name, shop_url, email, social_url, reddit_username,
             score, tier, niche, outreach_angle, sale_count, review_count,
             review_average, listing_count, custom_pct, city, enrichment_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (lead_id, source, shop_name, shop_url, email, social_url,
              reddit_username, score, tier, niche, outreach_angle, sale_count,
              review_count, review_average, listing_count, custom_pct, city,
              json.dumps(enrichment_data or {})))
        conn.commit()
        return lead_id
    finally:
        conn.close()


def get_growth_lead(lead_id):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM growth_leads WHERE id = %s", (lead_id,)).fetchone()
        if row:
            d = dict(row)
            d["enrichment_data"] = json.loads(d.get("enrichment_data") or "{}")
            return d
        return None
    finally:
        conn.close()


def get_leads_by_tier(tier, limit=50):
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM growth_leads WHERE tier = %s ORDER BY score DESC LIMIT %s",
            (tier, limit)
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["enrichment_data"] = json.loads(d.get("enrichment_data") or "{}")
            results.append(d)
        return results
    finally:
        conn.close()


def get_leads_by_status(status, limit=50):
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM growth_leads WHERE contact_status = %s ORDER BY score DESC LIMIT %s",
            (status, limit)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_contactable_leads(limit=50):
    """Get leads that are ready for outreach (new or need follow-up)."""
    conn = get_conn()
    try:
        rows = conn.execute(f"""
            SELECT * FROM growth_leads
            WHERE contact_status IN ('new', 'contacted')
              AND (last_contacted_at IS NULL OR last_contacted_at <= {_ago('3 days')})
            ORDER BY score DESC
            LIMIT %s
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_lead_status(lead_id, status):
    """Update contact_status. Valid: new, contacted, responded, converted, dead."""
    valid = ("new", "contacted", "responded", "converted", "dead")
    if status not in valid:
        raise ValueError(f"Invalid status. Must be one of: {valid}")
    conn = get_conn()
    try:
        now = datetime.now().isoformat()
        extra = ""
        params = [status, now]
        if status == "contacted":
            extra = ", last_contacted_at = %s"
            params.append(now)
        elif status == "converted":
            extra = ", converted_at = %s"
            params.append(now)
        params.append(lead_id)
        conn.execute(
            f"UPDATE growth_leads SET contact_status = %s, updated_at = %s{extra} WHERE id = %s",
            params
        )
        conn.commit()
    finally:
        conn.close()


def update_lead_score(lead_id, score, tier, outreach_angle=None):
    conn = get_conn()
    try:
        if outreach_angle:
            conn.execute(
                "UPDATE growth_leads SET score = %s, tier = %s, outreach_angle = %s, updated_at = %s WHERE id = %s",
                (score, tier, outreach_angle, datetime.now().isoformat(), lead_id)
            )
        else:
            conn.execute(
                "UPDATE growth_leads SET score = %s, tier = %s, updated_at = %s WHERE id = %s",
                (score, tier, datetime.now().isoformat(), lead_id)
            )
        conn.commit()
    finally:
        conn.close()


def get_lead_count_today(source=None):
    """Count leads discovered today (for quota enforcement)."""
    conn = get_conn()
    try:
        if source:
            row = conn.execute(f"""
                SELECT COUNT(*) as c FROM growth_leads
                WHERE created_at >= {_ago('1 day')} AND source = %s
            """, (source,)).fetchone()
        else:
            row = conn.execute(f"""
                SELECT COUNT(*) as c FROM growth_leads
                WHERE created_at >= {_ago('1 day')}
            """).fetchone()
        return row["c"]
    finally:
        conn.close()


def lead_exists(shop_url):
    """Check if a lead already exists by shop URL."""
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id FROM growth_leads WHERE shop_url = %s", (shop_url,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


# =============================================================
# CAMPAIGN CRUD
# =============================================================

def add_campaign(name, channel, target_niche=None, config=None):
    campaign_id = str(uuid.uuid4())[:8]
    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO growth_campaigns (id, name, channel, target_niche, config)
            VALUES (%s, %s, %s, %s, %s)
        """, (campaign_id, name, channel, target_niche, json.dumps(config or {})))
        conn.commit()
        return campaign_id
    finally:
        conn.close()


def get_campaign(campaign_id):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM growth_campaigns WHERE id = %s", (campaign_id,)).fetchone()
        if row:
            d = dict(row)
            d["config"] = json.loads(d.get("config") or "{}")
            return d
        return None
    finally:
        conn.close()


def get_active_campaigns(channel=None):
    conn = get_conn()
    try:
        if channel:
            rows = conn.execute(
                "SELECT * FROM growth_campaigns WHERE status = 'active' AND channel = %s ORDER BY created_at DESC",
                (channel,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM growth_campaigns WHERE status = 'active' ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_campaign_stats(campaign_id, messages_sent=0, responses=0, conversions=0):
    conn = get_conn()
    try:
        conn.execute("""
            UPDATE growth_campaigns
            SET messages_sent = messages_sent + %s,
                responses = responses + %s,
                conversions = conversions + %s,
                updated_at = %s
            WHERE id = %s
        """, (messages_sent, responses, conversions, datetime.now().isoformat(), campaign_id))
        conn.commit()
    finally:
        conn.close()


# =============================================================
# MESSAGE CRUD
# =============================================================

def add_growth_message(channel, content, lead_id=None, campaign_id=None,
                       variant=None, subject=None, review_status="pending"):
    msg_id = str(uuid.uuid4())[:8]
    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO growth_messages
            (id, campaign_id, lead_id, channel, variant, subject, content, review_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (msg_id, campaign_id, lead_id, channel, variant, subject, content, review_status))
        conn.commit()
        return msg_id
    finally:
        conn.close()


def get_message_queue(channel=None, status="queued", limit=50):
    conn = get_conn()
    try:
        if channel:
            rows = conn.execute(
                "SELECT * FROM growth_messages WHERE status = %s AND channel = %s ORDER BY created_at ASC LIMIT %s",
                (status, channel, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM growth_messages WHERE status = %s ORDER BY created_at ASC LIMIT %s",
                (status, limit)
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_review_queue(limit=50):
    """Get messages awaiting human review (excludes etsy_convo — has its own queue)."""
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT gm.*, gl.shop_name, gl.niche, gl.tier, gl.score FROM growth_messages gm LEFT JOIN growth_leads gl ON gm.lead_id = gl.id WHERE gm.review_status = 'pending' AND gm.channel != 'etsy_convo' ORDER BY gm.created_at ASC LIMIT %s",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_etsy_outreach_queue(limit=20):
    """Get etsy_convo messages pending review, with lead info for manual sending."""
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT gm.*, gl.shop_name, gl.shop_url, gl.niche, gl.tier, gl.score
            FROM growth_messages gm
            LEFT JOIN growth_leads gl ON gm.lead_id = gl.id
            WHERE gm.channel = 'etsy_convo' AND gm.review_status = 'pending'
            ORDER BY gl.score DESC, gm.created_at ASC
            LIMIT %s
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_message_status(msg_id, status, review_status=None):
    """Update message status. status: queued, sent, opened, replied, bounced."""
    conn = get_conn()
    try:
        now = datetime.now().isoformat()
        if review_status:
            conn.execute(
                "UPDATE growth_messages SET status = %s, review_status = %s WHERE id = %s",
                (status, review_status, msg_id)
            )
        elif status == "sent":
            conn.execute(
                "UPDATE growth_messages SET status = %s, sent_at = %s WHERE id = %s",
                (status, now, msg_id)
            )
        elif status == "replied":
            conn.execute(
                "UPDATE growth_messages SET status = %s, replied_at = %s WHERE id = %s",
                (status, now, msg_id)
            )
        else:
            conn.execute(
                "UPDATE growth_messages SET status = %s WHERE id = %s", (status, msg_id)
            )
        conn.commit()
    finally:
        conn.close()


def get_messages_sent_today(channel=None):
    conn = get_conn()
    try:
        if channel:
            row = conn.execute(f"""
                SELECT COUNT(*) as c FROM growth_messages
                WHERE sent_at >= {_ago('1 day')} AND channel = %s
            """, (channel,)).fetchone()
        else:
            row = conn.execute(f"""
                SELECT COUNT(*) as c FROM growth_messages
                WHERE sent_at >= {_ago('1 day')}
            """).fetchone()
        return row["c"]
    finally:
        conn.close()


def get_lead_messages(lead_id):
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM growth_messages WHERE lead_id = %s ORDER BY created_at ASC",
            (lead_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_growth_message(msg_id):
    """Fetch a single message with its lead info (for rewrite context)."""
    conn = get_conn()
    try:
        row = conn.execute("""
            SELECT gm.*, gl.shop_name, gl.shop_url, gl.niche, gl.tier, gl.score,
                   gl.outreach_angle, gl.sale_count, gl.enrichment_data
            FROM growth_messages gm
            LEFT JOIN growth_leads gl ON gm.lead_id = gl.id
            WHERE gm.id = %s
        """, (msg_id,)).fetchone()
        if row:
            d = dict(row)
            try:
                d["enrichment_data"] = json.loads(d.get("enrichment_data") or "{}")
            except (json.JSONDecodeError, TypeError):
                d["enrichment_data"] = {}
            return d
        return None
    finally:
        conn.close()


def update_message_content(msg_id, new_content):
    """Update the content of a message (used by rewrite)."""
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE growth_messages SET content = %s WHERE id = %s",
            (new_content, msg_id)
        )
        conn.commit()
    finally:
        conn.close()


def get_followup_candidates(gap_days=3, max_followups=3, limit=10):
    """Get leads that were contacted but haven't replied, and are due for a follow-up."""
    conn = get_conn()
    try:
        rows = conn.execute(f"""
            SELECT gl.* FROM growth_leads gl
            WHERE gl.contact_status = 'contacted'
              AND gl.last_contacted_at IS NOT NULL
              AND gl.last_contacted_at <= {_ago(f'{gap_days} days')}
              AND (
                  SELECT COUNT(*) FROM growth_messages gm
                  WHERE gm.lead_id = gl.id AND gm.variant = 'followup'
              ) < %s
            ORDER BY gl.score DESC
            LIMIT %s
        """, (max_followups, limit)).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["enrichment_data"] = json.loads(d.get("enrichment_data") or "{}")
            results.append(d)
        return results
    finally:
        conn.close()


# =============================================================
# CONTENT CRUD
# =============================================================

def add_content(content_type, title=None, body=None, script=None,
                media_path=None, thumbnail_path=None, platform=None,
                status="draft", scheduled_for=None):
    content_id = str(uuid.uuid4())[:8]
    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO growth_content
            (id, content_type, title, body, script, media_path, thumbnail_path,
             platform, status, scheduled_for)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (content_id, content_type, title, body, script, media_path,
              thumbnail_path, platform, status, scheduled_for))
        conn.commit()
        return content_id
    finally:
        conn.close()


def get_content(content_id):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM growth_content WHERE id = %s", (content_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_content_by_status(status, platform=None, limit=20):
    conn = get_conn()
    try:
        if platform:
            rows = conn.execute(
                "SELECT * FROM growth_content WHERE status = %s AND platform = %s ORDER BY created_at DESC LIMIT %s",
                (status, platform, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM growth_content WHERE status = %s ORDER BY created_at DESC LIMIT %s",
                (status, limit)
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_content_status(content_id, status, platform_post_id=None, platform_url=None):
    conn = get_conn()
    try:
        now = datetime.now().isoformat()
        if status == "published":
            conn.execute("""
                UPDATE growth_content
                SET status = %s, published_at = %s, platform_post_id = %s, platform_url = %s
                WHERE id = %s
            """, (status, now, platform_post_id, platform_url, content_id))
        else:
            conn.execute(
                "UPDATE growth_content SET status = %s WHERE id = %s", (status, content_id)
            )
        conn.commit()
    finally:
        conn.close()


def update_content_metrics(content_id, views=0, likes=0, comments=0, shares=0):
    conn = get_conn()
    try:
        conn.execute("""
            UPDATE growth_content
            SET views = %s, likes = %s, comments = %s, shares = %s
            WHERE id = %s
        """, (views, likes, comments, shares, content_id))
        conn.commit()
    finally:
        conn.close()


def get_videos_published_today():
    conn = get_conn()
    try:
        row = conn.execute(f"""
            SELECT COUNT(*) as c FROM growth_content
            WHERE published_at >= {_ago('1 day')} AND content_type = 'video'
        """).fetchone()
        return row["c"]
    finally:
        conn.close()


# =============================================================
# AGENT LOG
# =============================================================

def log_agent_action(agent, action, success=True, details=None,
                     tokens_used=0, cost=0.0, duration_ms=0):
    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO growth_agent_log
            (agent, action, success, details, tokens_used, cost, duration_ms)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (agent, action, 1 if success else 0, json.dumps(details or {}),
              tokens_used, cost, duration_ms))
        conn.commit()
    finally:
        conn.close()


def get_agent_log(agent=None, limit=50):
    conn = get_conn()
    try:
        if agent:
            rows = conn.execute(
                "SELECT * FROM growth_agent_log WHERE agent = %s ORDER BY created_at DESC LIMIT %s",
                (agent, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM growth_agent_log ORDER BY created_at DESC LIMIT %s",
                (limit,)
            ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["details"] = json.loads(d.get("details") or "{}")
            results.append(d)
        return results
    finally:
        conn.close()


def get_agent_stats(agent, since_hours=24):
    """Get aggregate stats for an agent over the last N hours."""
    conn = get_conn()
    try:
        interval = f"{since_hours} hours" if USE_PG else f"{since_hours} hours"
        row = conn.execute(f"""
            SELECT COUNT(*) as actions,
                   SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                   SUM(tokens_used) as total_tokens,
                   SUM(cost) as total_cost
            FROM growth_agent_log
            WHERE agent = %s AND created_at >= {_ago(interval)}
        """, (agent,)).fetchone()
        return dict(row) if row else {"actions": 0, "successes": 0, "total_tokens": 0, "total_cost": 0}
    finally:
        conn.close()


def get_last_agent_run(agent):
    """Get the most recent log entry for an agent."""
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM growth_agent_log WHERE agent = %s ORDER BY created_at DESC LIMIT 1",
            (agent,)
        ).fetchone()
        if row:
            d = dict(row)
            d["details"] = json.loads(d.get("details") or "{}")
            return d
        return None
    finally:
        conn.close()


# =============================================================
# DAILY METRICS
# =============================================================

def save_daily_metrics(date_str=None, leads_discovered=0, messages_sent=0,
                       messages_replied=0, signups=0, videos_published=0,
                       reddit_posts=0, reddit_comments=0, total_spend=0, notes=None):
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    conn = get_conn()
    try:
        # Upsert: update existing row for today or insert new one
        existing = conn.execute(
            "SELECT id FROM growth_metrics WHERE date = %s", (date_str,)
        ).fetchone()
        if existing:
            conn.execute("""
                UPDATE growth_metrics SET
                    leads_discovered = %s, messages_sent = %s, messages_replied = %s,
                    signups = %s, videos_published = %s, reddit_posts = %s,
                    reddit_comments = %s, total_spend = %s, notes = %s
                WHERE date = %s
            """, (leads_discovered, messages_sent, messages_replied, signups,
                  videos_published, reddit_posts, reddit_comments, total_spend,
                  notes, date_str))
        else:
            conn.execute("""
                INSERT INTO growth_metrics
                (date, leads_discovered, messages_sent, messages_replied, signups,
                 videos_published, reddit_posts, reddit_comments, total_spend, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (date_str, leads_discovered, messages_sent, messages_replied,
                  signups, videos_published, reddit_posts, reddit_comments,
                  total_spend, notes))
        conn.commit()
    finally:
        conn.close()


def get_daily_metrics(date_str=None):
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM growth_metrics WHERE date = %s", (date_str,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_metrics_range(days=30):
    """Get daily metrics for the last N days."""
    conn = get_conn()
    try:
        rows = conn.execute(f"""
            SELECT * FROM growth_metrics
            WHERE created_at >= {_ago(f'{days} days')}
            ORDER BY date DESC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# =============================================================
# DASHBOARD AGGREGATES
# =============================================================

def get_growth_overview():
    """Get summary stats for the growth dashboard."""
    conn = get_conn()
    try:
        leads_total = conn.execute("SELECT COUNT(*) as c FROM growth_leads").fetchone()["c"]
        leads_hot = conn.execute("SELECT COUNT(*) as c FROM growth_leads WHERE tier = 'HOT'").fetchone()["c"]
        leads_contacted = conn.execute("SELECT COUNT(*) as c FROM growth_leads WHERE contact_status = 'contacted'").fetchone()["c"]
        leads_responded = conn.execute("SELECT COUNT(*) as c FROM growth_leads WHERE contact_status = 'responded'").fetchone()["c"]
        leads_converted = conn.execute("SELECT COUNT(*) as c FROM growth_leads WHERE contact_status = 'converted'").fetchone()["c"]

        messages_total = conn.execute("SELECT COUNT(*) as c FROM growth_messages WHERE status = 'sent'").fetchone()["c"]
        messages_replied = conn.execute("SELECT COUNT(*) as c FROM growth_messages WHERE status = 'replied'").fetchone()["c"]
        messages_pending = conn.execute("SELECT COUNT(*) as c FROM growth_messages WHERE review_status = 'pending'").fetchone()["c"]

        videos_total = conn.execute("SELECT COUNT(*) as c FROM growth_content WHERE content_type = 'video' AND status = 'published'").fetchone()["c"]
        video_views = conn.execute("SELECT COALESCE(SUM(views), 0) as c FROM growth_content WHERE content_type = 'video'").fetchone()["c"]

        # Today's numbers
        leads_today = conn.execute(f"SELECT COUNT(*) as c FROM growth_leads WHERE created_at >= {_ago('1 day')}").fetchone()["c"]
        messages_today = conn.execute(f"SELECT COUNT(*) as c FROM growth_messages WHERE sent_at >= {_ago('1 day')}").fetchone()["c"]
        replies_today = conn.execute(f"SELECT COUNT(*) as c FROM growth_messages WHERE replied_at >= {_ago('1 day')}").fetchone()["c"]

        total_spend = conn.execute("SELECT COALESCE(SUM(cost), 0) as c FROM growth_agent_log").fetchone()["c"]
        spend_today = conn.execute(f"SELECT COALESCE(SUM(cost), 0) as c FROM growth_agent_log WHERE created_at >= {_ago('1 day')}").fetchone()["c"]

        return {
            "leads_total": leads_total,
            "leads_hot": leads_hot,
            "leads_contacted": leads_contacted,
            "leads_responded": leads_responded,
            "leads_converted": leads_converted,
            "messages_total": messages_total,
            "messages_replied": messages_replied,
            "messages_pending": messages_pending,
            "videos_total": videos_total,
            "video_views": video_views,
            "leads_today": leads_today,
            "messages_today": messages_today,
            "replies_today": replies_today,
            "total_spend": round(total_spend, 2),
            "spend_today": round(spend_today, 2),
            "reply_rate": round((messages_replied / messages_total * 100), 1) if messages_total > 0 else 0,
            "conversion_rate": round((leads_converted / leads_total * 100), 1) if leads_total > 0 else 0,
        }
    finally:
        conn.close()


def get_lead_funnel():
    """Get lead counts by status for funnel visualization."""
    conn = get_conn()
    try:
        statuses = ["new", "contacted", "responded", "converted", "dead"]
        funnel = {}
        for status in statuses:
            row = conn.execute(
                "SELECT COUNT(*) as c FROM growth_leads WHERE contact_status = %s",
                (status,)
            ).fetchone()
            funnel[status] = row["c"]
        return funnel
    finally:
        conn.close()


# =============================================================
# LEARNINGS CRUD
# =============================================================

def upsert_learning(agent, learning_type, key, value_json, score=0,
                    sample_size=0, confidence=0):
    """Insert or update a learning record. Keyed on (agent, learning_type, key)."""
    conn = get_conn()
    try:
        existing = conn.execute(
            "SELECT id FROM growth_learnings WHERE agent = %s AND learning_type = %s AND key = %s",
            (agent, learning_type, key)
        ).fetchone()
        now = datetime.now().isoformat()
        if existing:
            conn.execute("""
                UPDATE growth_learnings
                SET value_json = %s, score = %s, sample_size = %s,
                    confidence = %s, updated_at = %s
                WHERE id = %s
            """, (json.dumps(value_json) if not isinstance(value_json, str) else value_json,
                  score, sample_size, confidence, now, existing["id"]))
        else:
            conn.execute("""
                INSERT INTO growth_learnings
                (agent, learning_type, key, value_json, score, sample_size, confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (agent, learning_type, key,
                  json.dumps(value_json) if not isinstance(value_json, str) else value_json,
                  score, sample_size, confidence))
        conn.commit()
    finally:
        conn.close()


def get_learnings(agent=None, learning_type=None, min_confidence=0):
    """Get learnings filtered by agent and/or type."""
    conn = get_conn()
    try:
        conditions = ["confidence >= %s"]
        params = [min_confidence]
        if agent:
            conditions.append("agent = %s")
            params.append(agent)
        if learning_type:
            conditions.append("learning_type = %s")
            params.append(learning_type)
        where = " AND ".join(conditions)
        rows = conn.execute(
            f"SELECT * FROM growth_learnings WHERE {where} ORDER BY score DESC",
            params
        ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            try:
                d["value_json"] = json.loads(d.get("value_json") or "{}")
            except (json.JSONDecodeError, TypeError):
                pass
            results.append(d)
        return results
    finally:
        conn.close()


def get_top_learnings(agent, learning_type, limit=10, min_sample=3):
    """Get top-scoring learnings for an agent/type with minimum sample size."""
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT * FROM growth_learnings
            WHERE agent = %s AND learning_type = %s AND sample_size >= %s
            ORDER BY score DESC LIMIT %s
        """, (agent, learning_type, min_sample, limit)).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            try:
                d["value_json"] = json.loads(d.get("value_json") or "{}")
            except (json.JSONDecodeError, TypeError):
                pass
            results.append(d)
        return results
    finally:
        conn.close()


# =============================================================
# SEEN THREADS (persistent dedup for Listener)
# =============================================================

def is_thread_seen(thread_id):
    """Check if a thread has already been processed."""
    conn = get_conn()
    try:
        row = conn.execute("SELECT 1 FROM growth_seen_threads WHERE thread_id = %s", (thread_id,)).fetchone()
        return row is not None
    finally:
        conn.close()


def mark_threads_seen(thread_ids, subreddit=None):
    """Mark threads as seen so they aren't re-classified after deploys."""
    if not thread_ids:
        return
    conn = get_conn()
    try:
        for tid in thread_ids:
            try:
                conn.execute(
                    "INSERT INTO growth_seen_threads (thread_id, subreddit) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (tid, subreddit)
                )
            except Exception:
                pass  # Ignore duplicates
        conn.commit()
    finally:
        conn.close()


def cleanup_old_seen_threads(days=7):
    """Remove seen threads older than N days to prevent table bloat."""
    conn = get_conn()
    try:
        conn.execute(
            "DELETE FROM growth_seen_threads WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'",
            (days,)
        )
        conn.commit()
    finally:
        conn.close()
