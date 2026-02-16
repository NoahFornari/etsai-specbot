"""
ETSAI Database Layer
Dual-backend: PostgreSQL (production) / SQLite (local dev).
Set DATABASE_URL env var to use Postgres. Otherwise falls back to SQLite.
"""
import sqlite3
import json
import os
import uuid
import secrets
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("etsai.db")

# --- Backend detection ---
DATABASE_URL = os.environ.get("DATABASE_URL", "")
# Railway/Heroku provide postgres:// but psycopg2 needs postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

USE_PG = bool(DATABASE_URL)
DB_PATH = os.environ.get("ETSAI_DB", "etsai.db")

if USE_PG:
    logger.info("Using PostgreSQL: %s...%s", DATABASE_URL[:25], DATABASE_URL[-10:])
else:
    logger.info("Using SQLite: %s", DB_PATH)


class DB:
    """Thin wrapper that normalizes SQLite and PostgreSQL access.
    All queries use %%s placeholders — converted to ? for SQLite automatically.
    """

    def __init__(self):
        if USE_PG:
            import psycopg2
            import psycopg2.extras
            self.conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
            self._pg = True
        else:
            self.conn = sqlite3.connect(DB_PATH)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA foreign_keys=ON")
            self._pg = False

    def execute(self, sql, params=None):
        if not self._pg:
            sql = sql.replace('%s', '?')
        cur = self.conn.cursor()
        cur.execute(sql, params or ())
        return cur

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

    @property
    def is_pg(self):
        return self._pg


def get_conn():
    """Get a DB connection wrapper. Caller must call .close() when done."""
    return DB()


# --- SQL dialect helpers ---

def _ago(interval):
    """SQL expression for 'now minus interval'. E.g. _ago('1 day'), _ago('2 days')."""
    if USE_PG:
        return f"NOW() - INTERVAL '{interval}'"
    return f"datetime('now', '-{interval}')"


def _month_start():
    """SQL expression for first day of current month."""
    if USE_PG:
        return "date_trunc('month', NOW())"
    return "date('now', 'start of month')"


def _now_expr():
    """SQL expression for current timestamp."""
    return "NOW()" if USE_PG else "datetime('now')"


# =============================================================
# SCHEMA INITIALIZATION
# =============================================================

def init_db():
    conn = get_conn()
    try:
        if USE_PG:
            _init_pg(conn)
        else:
            _init_sqlite(conn)
        conn.commit()
    finally:
        conn.close()


def _init_sqlite(conn):
    """Create tables and run migrations for SQLite."""
    c = conn

    c.execute("""
        CREATE TABLE IF NOT EXISTS sellers (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            shop_name TEXT NOT NULL,
            platform TEXT DEFAULT 'etsy',
            api_key TEXT,
            webhook_secret TEXT,
            sale_message_template TEXT,
            settings TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            plan TEXT DEFAULT 'free',
            password_hash TEXT,
            stripe_customer_id TEXT,
            trial_ends_at TIMESTAMP,
            brand_color TEXT,
            brand_logo_url TEXT,
            display_name TEXT,
            phone TEXT,
            website TEXT,
            timezone TEXT,
            password_reset_token TEXT,
            password_reset_expires TIMESTAMP,
            is_admin INTEGER DEFAULT 0,
            etsy_user_id TEXT,
            etsy_shop_id TEXT,
            etsy_access_token TEXT,
            etsy_refresh_token TEXT,
            etsy_token_expires_at TIMESTAMP,
            etsy_connected_at TIMESTAMP,
            etsy_last_order_check TIMESTAMP,
            referral_code TEXT,
            referred_by TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            seller_id TEXT NOT NULL,
            external_id TEXT,
            title TEXT NOT NULL,
            category TEXT,
            price REAL,
            image_url TEXT,
            intake_questions TEXT NOT NULL,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT,
            seller_notes TEXT,
            source_url TEXT,
            FOREIGN KEY (seller_id) REFERENCES sellers(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            seller_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            external_order_id TEXT,
            buyer_name TEXT,
            buyer_email TEXT,
            buyer_identifier TEXT,
            customer_specs TEXT DEFAULT '{}',
            specs_complete INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            intake_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            seller_order_notes TEXT,
            escalated INTEGER DEFAULT 0,
            fulfillment_status TEXT DEFAULT 'pending',
            FOREIGN KEY (seller_id) REFERENCES sellers(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT NOT NULL,
            direction TEXT NOT NULL,
            sender TEXT,
            content TEXT NOT NULL,
            specs_extracted TEXT DEFAULT '{}',
            ai_generated INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS ai_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id TEXT,
            model TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            cost REAL,
            task TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Legacy migration support: add columns that may not exist yet
    # (for databases created before all columns were in CREATE TABLE)
    migrations = [
        ("products", "description", "TEXT"),
        ("products", "seller_notes", "TEXT"),
        ("products", "source_url", "TEXT"),
        ("sellers", "etsy_user_id", "TEXT"),
        ("sellers", "etsy_shop_id", "TEXT"),
        ("sellers", "etsy_access_token", "TEXT"),
        ("sellers", "etsy_refresh_token", "TEXT"),
        ("sellers", "etsy_token_expires_at", "TIMESTAMP"),
        ("sellers", "etsy_connected_at", "TIMESTAMP"),
        ("sellers", "etsy_last_order_check", "TIMESTAMP"),
        ("orders", "seller_order_notes", "TEXT"),
        ("orders", "escalated", "INTEGER DEFAULT 0"),
        ("orders", "fulfillment_status", "TEXT DEFAULT 'pending'"),
        ("sellers", "settings", "TEXT DEFAULT '{}'"),
        ("sellers", "password_hash", "TEXT"),
        ("sellers", "stripe_customer_id", "TEXT"),
        ("sellers", "trial_ends_at", "TIMESTAMP"),
        ("sellers", "brand_color", "TEXT"),
        ("sellers", "brand_logo_url", "TEXT"),
        ("sellers", "display_name", "TEXT"),
        ("sellers", "phone", "TEXT"),
        ("sellers", "website", "TEXT"),
        ("sellers", "timezone", "TEXT"),
        ("sellers", "password_reset_token", "TEXT"),
        ("sellers", "password_reset_expires", "TIMESTAMP"),
        ("sellers", "is_admin", "INTEGER DEFAULT 0"),
        ("sellers", "referral_code", "TEXT"),
        ("sellers", "referred_by", "TEXT"),
        ("sellers", "onboard_email_stage", "INTEGER DEFAULT 0"),
    ]
    for table, column, col_type in migrations:
        try:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        except sqlite3.OperationalError:
            pass

    _create_indexes(c)


def _init_pg(conn):
    """Create tables and run migrations for PostgreSQL."""
    c = conn

    c.execute("""
        CREATE TABLE IF NOT EXISTS sellers (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            shop_name TEXT NOT NULL,
            platform TEXT DEFAULT 'etsy',
            api_key TEXT,
            webhook_secret TEXT,
            sale_message_template TEXT,
            settings TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            plan TEXT DEFAULT 'free',
            password_hash TEXT,
            stripe_customer_id TEXT,
            trial_ends_at TIMESTAMP,
            brand_color TEXT,
            brand_logo_url TEXT,
            display_name TEXT,
            phone TEXT,
            website TEXT,
            timezone TEXT,
            password_reset_token TEXT,
            password_reset_expires TIMESTAMP,
            is_admin INTEGER DEFAULT 0,
            etsy_user_id TEXT,
            etsy_shop_id TEXT,
            etsy_access_token TEXT,
            etsy_refresh_token TEXT,
            etsy_token_expires_at TIMESTAMP,
            etsy_connected_at TIMESTAMP,
            etsy_last_order_check TIMESTAMP,
            referral_code TEXT,
            referred_by TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            seller_id TEXT NOT NULL REFERENCES sellers(id),
            external_id TEXT,
            title TEXT NOT NULL,
            category TEXT,
            price REAL,
            image_url TEXT,
            intake_questions TEXT NOT NULL,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            description TEXT,
            seller_notes TEXT,
            source_url TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            seller_id TEXT NOT NULL REFERENCES sellers(id),
            product_id TEXT NOT NULL REFERENCES products(id),
            external_order_id TEXT,
            buyer_name TEXT,
            buyer_email TEXT,
            buyer_identifier TEXT,
            customer_specs TEXT DEFAULT '{}',
            specs_complete INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            intake_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            seller_order_notes TEXT,
            escalated INTEGER DEFAULT 0,
            fulfillment_status TEXT DEFAULT 'pending'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            order_id TEXT NOT NULL REFERENCES orders(id),
            direction TEXT NOT NULL,
            sender TEXT,
            content TEXT NOT NULL,
            specs_extracted TEXT DEFAULT '{}',
            ai_generated INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS ai_usage (
            id SERIAL PRIMARY KEY,
            seller_id TEXT,
            model TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            cost REAL,
            task TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Postgres migrations use ADD COLUMN IF NOT EXISTS (9.6+)
    pg_migrations = [
        ("products", "description", "TEXT"),
        ("products", "seller_notes", "TEXT"),
        ("products", "source_url", "TEXT"),
        ("sellers", "etsy_user_id", "TEXT"),
        ("sellers", "etsy_shop_id", "TEXT"),
        ("sellers", "etsy_access_token", "TEXT"),
        ("sellers", "etsy_refresh_token", "TEXT"),
        ("sellers", "etsy_token_expires_at", "TIMESTAMP"),
        ("sellers", "etsy_connected_at", "TIMESTAMP"),
        ("sellers", "etsy_last_order_check", "TIMESTAMP"),
        ("orders", "seller_order_notes", "TEXT"),
        ("orders", "escalated", "INTEGER DEFAULT 0"),
        ("orders", "fulfillment_status", "TEXT DEFAULT 'pending'"),
        ("sellers", "settings", "TEXT DEFAULT '{}'"),
        ("sellers", "password_hash", "TEXT"),
        ("sellers", "stripe_customer_id", "TEXT"),
        ("sellers", "trial_ends_at", "TIMESTAMP"),
        ("sellers", "brand_color", "TEXT"),
        ("sellers", "brand_logo_url", "TEXT"),
        ("sellers", "display_name", "TEXT"),
        ("sellers", "phone", "TEXT"),
        ("sellers", "website", "TEXT"),
        ("sellers", "timezone", "TEXT"),
        ("sellers", "password_reset_token", "TEXT"),
        ("sellers", "password_reset_expires", "TIMESTAMP"),
        ("sellers", "is_admin", "INTEGER DEFAULT 0"),
        ("sellers", "referral_code", "TEXT"),
        ("sellers", "referred_by", "TEXT"),
        ("sellers", "onboard_email_stage", "INTEGER DEFAULT 0"),
    ]
    for table, column, col_type in pg_migrations:
        c.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_type}")

    _create_indexes(c)


def _create_indexes(conn):
    """Create indexes (SQL is identical for both backends)."""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_products_seller_id ON products(seller_id)",
        "CREATE INDEX IF NOT EXISTS idx_orders_seller_id ON orders(seller_id)",
        "CREATE INDEX IF NOT EXISTS idx_orders_external_order_id ON orders(external_order_id)",
        "CREATE INDEX IF NOT EXISTS idx_messages_order_id ON messages(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_products_external_id ON products(seller_id, external_id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_sellers_referral_code ON sellers(referral_code)",
    ]
    for idx_sql in indexes:
        conn.execute(idx_sql)


# =============================================================
# SELLER CRUD
# =============================================================

def create_seller(email, shop_name, platform="etsy", password_hash=None):
    seller_id = str(uuid.uuid4())[:8]
    api_key = secrets.token_urlsafe(32)
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO sellers (id, email, shop_name, platform, api_key, password_hash) VALUES (%s, %s, %s, %s, %s, %s)",
            (seller_id, email, shop_name, platform, api_key, password_hash)
        )
        conn.commit()
        return seller_id
    finally:
        conn.close()


def get_seller(seller_id):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM sellers WHERE id = %s", (seller_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_seller_by_email(email):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM sellers WHERE email = %s", (email,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def set_seller_password(seller_id, password_hash):
    conn = get_conn()
    try:
        conn.execute("UPDATE sellers SET password_hash = %s WHERE id = %s",
                      (password_hash, seller_id))
        conn.commit()
    finally:
        conn.close()


def get_seller_by_api_key(api_key):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM sellers WHERE api_key = %s", (api_key,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# =============================================================
# PRODUCT CRUD
# =============================================================

def add_product(seller_id, title, intake_questions, category=None, price=None,
                image_url=None, external_id=None, description=None,
                seller_notes=None, source_url=None):
    product_id = str(uuid.uuid4())[:8]
    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO products (id, seller_id, external_id, title, category, price,
                                  image_url, intake_questions, description, seller_notes, source_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (product_id, seller_id, external_id, title, category, price, image_url,
              json.dumps(intake_questions), description, seller_notes, source_url))
        conn.commit()
        return product_id
    finally:
        conn.close()


def get_product(product_id):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM products WHERE id = %s", (product_id,)).fetchone()
        if row:
            p = dict(row)
            p["intake_questions"] = json.loads(p["intake_questions"])
            return p
        return None
    finally:
        conn.close()


def get_seller_products(seller_id):
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM products WHERE seller_id = %s AND active = 1 ORDER BY created_at DESC",
            (seller_id,)
        ).fetchall()
        products = []
        for r in rows:
            p = dict(r)
            p["intake_questions"] = json.loads(p["intake_questions"])
            products.append(p)
        return products
    finally:
        conn.close()


# =============================================================
# ORDER CRUD
# =============================================================

def create_order(seller_id, product_id, buyer_name=None, buyer_email=None,
                 external_order_id=None, buyer_identifier=None):
    order_id = str(uuid.uuid4())[:8]
    intake_url = f"/intake/{order_id}"
    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO orders (id, seller_id, product_id, external_order_id,
                                buyer_name, buyer_email, buyer_identifier, intake_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (order_id, seller_id, product_id, external_order_id,
              buyer_name, buyer_email, buyer_identifier, intake_url))
        conn.commit()
        return order_id
    finally:
        conn.close()


def get_order(order_id):
    conn = get_conn()
    try:
        row = conn.execute("""
            SELECT o.*, p.title as product_title, p.intake_questions, p.image_url,
                   p.description as product_description, p.seller_notes,
                   s.shop_name, s.email as seller_email
            FROM orders o
            JOIN products p ON o.product_id = p.id
            JOIN sellers s ON o.seller_id = s.id
            WHERE o.id = %s
        """, (order_id,)).fetchone()
        if row:
            o = dict(row)
            o["customer_specs"] = json.loads(o["customer_specs"])
            o["intake_questions"] = json.loads(o["intake_questions"])
            return o
        return None
    finally:
        conn.close()


def get_seller_orders(seller_id, status=None):
    conn = get_conn()
    try:
        if status:
            rows = conn.execute("""
                SELECT o.*, p.title as product_title
                FROM orders o JOIN products p ON o.product_id = p.id
                WHERE o.seller_id = %s AND o.status = %s
                ORDER BY o.created_at DESC
            """, (seller_id, status)).fetchall()
        else:
            rows = conn.execute("""
                SELECT o.*, p.title as product_title
                FROM orders o JOIN products p ON o.product_id = p.id
                WHERE o.seller_id = %s
                ORDER BY o.created_at DESC
            """, (seller_id,)).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["customer_specs"] = json.loads(d["customer_specs"])
            results.append(d)
        return results
    finally:
        conn.close()


def update_order_specs(order_id, specs, complete=False):
    conn = get_conn()
    try:
        now = datetime.now().isoformat()
        status = "complete" if complete else "collecting"
        completed_at = now if complete else None
        conn.execute("""
            UPDATE orders SET customer_specs = %s, specs_complete = %s, status = %s,
                              updated_at = %s, completed_at = %s
            WHERE id = %s
        """, (json.dumps(specs), 1 if complete else 0, status, now, completed_at, order_id))
        conn.commit()
    finally:
        conn.close()


# =============================================================
# MESSAGE CRUD
# =============================================================

def add_message(order_id, direction, content, sender=None, specs_extracted=None, ai_generated=False):
    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO messages (order_id, direction, sender, content, specs_extracted, ai_generated)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (order_id, direction, sender or ("bot" if direction == "outbound" else "buyer"),
              content, json.dumps(specs_extracted or {}), 1 if ai_generated else 0))
        conn.commit()
    finally:
        conn.close()


def get_messages(order_id):
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM messages WHERE order_id = %s ORDER BY created_at ASC",
            (order_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# =============================================================
# AI COST TRACKING
# =============================================================

def log_ai_cost(seller_id, model, input_tokens, output_tokens, cost, task=""):
    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO ai_usage (seller_id, model, input_tokens, output_tokens, cost, task)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (seller_id, model, input_tokens, output_tokens, cost, task))
        conn.commit()
    finally:
        conn.close()


def get_seller_stats(seller_id):
    conn = get_conn()
    try:
        total = conn.execute("SELECT COUNT(*) as c FROM orders WHERE seller_id = %s", (seller_id,)).fetchone()["c"]
        complete = conn.execute("SELECT COUNT(*) as c FROM orders WHERE seller_id = %s AND specs_complete = 1", (seller_id,)).fetchone()["c"]
        awaiting_buyer = conn.execute("SELECT COUNT(*) as c FROM orders WHERE seller_id = %s AND specs_complete = 0 AND status != 'complete'", (seller_id,)).fetchone()["c"]
        return {
            "total_orders": total,
            "complete": complete,
            "awaiting_buyer": awaiting_buyer,
        }
    finally:
        conn.close()


def get_recent_activity(seller_id, limit=10):
    """Get recent activity feed for dashboard."""
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT 'order_created' as type,
                   'New order for ' || p.title || CASE WHEN o.buyer_name IS NOT NULL THEN ' from ' || o.buyer_name ELSE '' END as description,
                   o.created_at as timestamp
            FROM orders o JOIN products p ON o.product_id = p.id
            WHERE o.seller_id = %s
            UNION ALL
            SELECT 'order_complete' as type,
                   p.title || ' specs complete' || CASE WHEN o.buyer_name IS NOT NULL THEN ' (' || o.buyer_name || ')' ELSE '' END as description,
                   o.completed_at as timestamp
            FROM orders o JOIN products p ON o.product_id = p.id
            WHERE o.seller_id = %s AND o.specs_complete = 1 AND o.completed_at IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT %s
        """, (seller_id, seller_id, limit)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# =============================================================
# ETSY INTEGRATION
# =============================================================

def save_etsy_tokens(seller_id, access_token, refresh_token, expires_at):
    """Update Etsy tokens (used after token refresh)."""
    conn = get_conn()
    try:
        conn.execute("""
            UPDATE sellers SET etsy_access_token = %s, etsy_refresh_token = %s,
                               etsy_token_expires_at = %s
            WHERE id = %s
        """, (access_token, refresh_token, expires_at, seller_id))
        conn.commit()
    finally:
        conn.close()


def save_etsy_connection(seller_id, etsy_user_id, etsy_shop_id, access_token,
                         refresh_token, expires_at):
    """Save full Etsy connection after OAuth."""
    conn = get_conn()
    try:
        conn.execute("""
            UPDATE sellers SET etsy_user_id = %s, etsy_shop_id = %s,
                               etsy_access_token = %s, etsy_refresh_token = %s,
                               etsy_token_expires_at = %s, etsy_connected_at = %s
            WHERE id = %s
        """, (etsy_user_id, etsy_shop_id, access_token, refresh_token,
              expires_at, datetime.now().isoformat(), seller_id))
        conn.commit()
    finally:
        conn.close()


def update_last_order_check(seller_id):
    """Track when we last polled for new orders."""
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE sellers SET etsy_last_order_check = %s WHERE id = %s",
            (datetime.now().isoformat(), seller_id)
        )
        conn.commit()
    finally:
        conn.close()


def get_product_by_external_id(seller_id, external_id):
    """Find a product by its Etsy listing_id."""
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM products WHERE seller_id = %s AND external_id = %s AND active = 1",
            (seller_id, str(external_id))
        ).fetchone()
        if row:
            p = dict(row)
            p["intake_questions"] = json.loads(p["intake_questions"])
            return p
        return None
    finally:
        conn.close()


def order_exists_by_external_id(seller_id, external_order_id):
    """Check if an order already exists (prevent duplicates)."""
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id FROM orders WHERE seller_id = %s AND external_order_id = %s",
            (seller_id, str(external_order_id))
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def update_product_notes(product_id, seller_notes):
    conn = get_conn()
    try:
        conn.execute("UPDATE products SET seller_notes = %s WHERE id = %s",
                      (seller_notes, product_id))
        conn.commit()
    finally:
        conn.close()


def update_order_notes(order_id, notes):
    conn = get_conn()
    try:
        conn.execute("UPDATE orders SET seller_order_notes = %s WHERE id = %s",
                      (notes, order_id))
        conn.commit()
    finally:
        conn.close()


def mark_order_escalated(order_id):
    conn = get_conn()
    try:
        conn.execute("UPDATE orders SET escalated = 1 WHERE id = %s", (order_id,))
        conn.commit()
    finally:
        conn.close()


def update_fulfillment_status(order_id, status):
    valid = ('pending', 'in_progress', 'shipped', 'delivered')
    if status not in valid:
        raise ValueError(f"Invalid status. Must be one of: {valid}")
    conn = get_conn()
    try:
        conn.execute("UPDATE orders SET fulfillment_status = %s WHERE id = %s",
                      (status, order_id))
        conn.commit()
    finally:
        conn.close()


def get_completed_orders_with_specs(seller_id, limit=20):
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT o.*, p.title as product_title, p.intake_questions
            FROM orders o JOIN products p ON o.product_id = p.id
            WHERE o.seller_id = %s AND o.specs_complete = 1
            ORDER BY o.completed_at DESC
            LIMIT %s
        """, (seller_id, limit)).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            d["customer_specs"] = json.loads(d["customer_specs"])
            d["intake_questions"] = json.loads(d["intake_questions"])
            results.append(d)
        return results
    finally:
        conn.close()


def get_stale_orders(seller_id):
    """Returns set of order IDs needing follow-up:
    - Created >24h ago with no buyer messages (never opened link)
    - Last buyer message >48h ago with specs still incomplete
    """
    conn = get_conn()
    try:
        never_opened = conn.execute(f"""
            SELECT o.id FROM orders o
            WHERE o.seller_id = %s AND o.specs_complete = 0
              AND o.created_at <= {_ago('1 day')}
              AND NOT EXISTS (
                  SELECT 1 FROM messages m WHERE m.order_id = o.id AND m.direction = 'inbound'
              )
        """, (seller_id,)).fetchall()

        stale_convos = conn.execute(f"""
            SELECT o.id FROM orders o
            WHERE o.seller_id = %s AND o.specs_complete = 0
              AND EXISTS (
                  SELECT 1 FROM messages m WHERE m.order_id = o.id AND m.direction = 'inbound'
              )
              AND (
                  SELECT MAX(m.created_at) FROM messages m
                  WHERE m.order_id = o.id AND m.direction = 'inbound'
              ) <= {_ago('2 days')}
        """, (seller_id,)).fetchall()

        return set(r["id"] for r in never_opened) | set(r["id"] for r in stale_convos)
    finally:
        conn.close()


# =============================================================
# SETTINGS & PROFILE
# =============================================================

def update_seller_settings(seller_id, settings_dict):
    """Merge settings into the seller's settings JSON."""
    conn = get_conn()
    try:
        row = conn.execute("SELECT settings FROM sellers WHERE id = %s", (seller_id,)).fetchone()
        current = json.loads(row["settings"]) if row and row["settings"] else {}
        current.update(settings_dict)
        conn.execute("UPDATE sellers SET settings = %s WHERE id = %s",
                      (json.dumps(current), seller_id))
        conn.commit()
    finally:
        conn.close()


def update_seller_profile(seller_id, shop_name, email, display_name=None,
                          phone=None, website=None, timezone=None):
    """Update seller's profile fields."""
    conn = get_conn()
    try:
        conn.execute("""UPDATE sellers SET shop_name = %s, email = %s, display_name = %s,
                        phone = %s, website = %s, timezone = %s WHERE id = %s""",
                      (shop_name, email, display_name, phone, website, timezone, seller_id))
        conn.commit()
    finally:
        conn.close()


def delete_seller_account(seller_id):
    """Cascade delete: messages -> orders -> products -> ai_usage -> seller."""
    conn = get_conn()
    try:
        conn.execute("""
            DELETE FROM messages WHERE order_id IN (
                SELECT id FROM orders WHERE seller_id = %s
            )
        """, (seller_id,))
        conn.execute("DELETE FROM orders WHERE seller_id = %s", (seller_id,))
        conn.execute("DELETE FROM products WHERE seller_id = %s", (seller_id,))
        conn.execute("DELETE FROM ai_usage WHERE seller_id = %s", (seller_id,))
        conn.execute("DELETE FROM sellers WHERE id = %s", (seller_id,))
        conn.commit()
    finally:
        conn.close()


# =============================================================
# BILLING & USAGE
# =============================================================

def update_seller_plan(seller_id, plan, stripe_customer_id=None):
    """Update seller's plan (called after Stripe webhook confirms payment)."""
    conn = get_conn()
    try:
        if stripe_customer_id:
            conn.execute(
                "UPDATE sellers SET plan = %s, stripe_customer_id = %s WHERE id = %s",
                (plan, stripe_customer_id, seller_id))
        else:
            conn.execute("UPDATE sellers SET plan = %s WHERE id = %s", (plan, seller_id))
        conn.commit()
    finally:
        conn.close()


def set_trial_end(seller_id, trial_ends_at):
    """Set the trial expiry date for a new free-plan seller."""
    conn = get_conn()
    try:
        conn.execute("UPDATE sellers SET trial_ends_at = %s WHERE id = %s",
                      (trial_ends_at, seller_id))
        conn.commit()
    finally:
        conn.close()


def get_monthly_order_count(seller_id):
    """Count orders created this calendar month for quota enforcement."""
    conn = get_conn()
    try:
        row = conn.execute(f"""
            SELECT COUNT(*) as c FROM orders
            WHERE seller_id = %s
              AND created_at >= {_month_start()}
        """, (seller_id,)).fetchone()
        return row["c"]
    finally:
        conn.close()


def get_product_count(seller_id):
    """Count active products for quota enforcement."""
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT COUNT(*) as c FROM products WHERE seller_id = %s AND active = 1",
            (seller_id,)).fetchone()
        return row["c"]
    finally:
        conn.close()


def get_seller_by_stripe_customer(stripe_customer_id):
    """Find seller by Stripe customer ID (for webhook processing)."""
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM sellers WHERE stripe_customer_id = %s",
            (stripe_customer_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_seller_brand(seller_id, brand_color=None, brand_logo_url=None):
    """Update white-label branding settings."""
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE sellers SET brand_color = %s, brand_logo_url = %s WHERE id = %s",
            (brand_color, brand_logo_url, seller_id))
        conn.commit()
    finally:
        conn.close()


def set_reset_token(seller_id, token, expires_at):
    """Store a password reset token with expiry."""
    conn = get_conn()
    try:
        conn.execute("UPDATE sellers SET password_reset_token = %s, password_reset_expires = %s WHERE id = %s",
                      (token, expires_at, seller_id))
        conn.commit()
    finally:
        conn.close()


def get_seller_by_reset_token(token):
    """Find seller by password reset token (returns None if expired)."""
    conn = get_conn()
    try:
        if USE_PG:
            row = conn.execute(
                "SELECT * FROM sellers WHERE password_reset_token = %s AND password_reset_expires > NOW()",
                (token,)).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM sellers WHERE password_reset_token = %s AND password_reset_expires > %s",
                (token, datetime.now().isoformat())).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def clear_reset_token(seller_id):
    """Clear password reset token after use."""
    conn = get_conn()
    try:
        conn.execute("UPDATE sellers SET password_reset_token = NULL, password_reset_expires = NULL WHERE id = %s",
                      (seller_id,))
        conn.commit()
    finally:
        conn.close()


# =============================================================
# ADMIN
# =============================================================

def get_all_sellers():
    """Get all sellers for admin panel."""
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT s.*,
                   (SELECT COUNT(*) FROM products WHERE seller_id = s.id AND active = 1) as product_count,
                   (SELECT COUNT(*) FROM orders WHERE seller_id = s.id) as order_count,
                   (SELECT COUNT(*) FROM orders WHERE seller_id = s.id AND specs_complete = 1) as completed_count
            FROM sellers s ORDER BY s.created_at DESC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_admin_stats():
    """Get system-wide stats for admin panel."""
    conn = get_conn()
    try:
        sellers = conn.execute("SELECT COUNT(*) as c FROM sellers").fetchone()["c"]
        products = conn.execute("SELECT COUNT(*) as c FROM products WHERE active = 1").fetchone()["c"]
        orders = conn.execute("SELECT COUNT(*) as c FROM orders").fetchone()["c"]
        completed = conn.execute("SELECT COUNT(*) as c FROM orders WHERE specs_complete = 1").fetchone()["c"]
        messages = conn.execute("SELECT COUNT(*) as c FROM messages").fetchone()["c"]
        return {
            "total_sellers": sellers,
            "total_products": products,
            "total_orders": orders,
            "completed_orders": completed,
            "total_messages": messages,
        }
    finally:
        conn.close()


# =============================================================
# REFERRAL SYSTEM
# =============================================================

def generate_referral_code():
    """Generate a short, unique referral code (8 chars, URL-safe)."""
    return secrets.token_urlsafe(6)


def set_referral_code(seller_id, code):
    """Set the referral code for a seller."""
    conn = get_conn()
    try:
        conn.execute("UPDATE sellers SET referral_code = %s WHERE id = %s",
                      (code, seller_id))
        conn.commit()
    finally:
        conn.close()


def get_seller_by_referral_code(code):
    """Find a seller by their referral code."""
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM sellers WHERE referral_code = %s",
                           (code,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def record_referral(new_seller_id, referrer_seller_id):
    """Record that new_seller was referred by referrer_seller."""
    conn = get_conn()
    try:
        conn.execute("UPDATE sellers SET referred_by = %s WHERE id = %s",
                      (referrer_seller_id, new_seller_id))
        conn.commit()
    finally:
        conn.close()


def get_referral_count(seller_id):
    """Count how many sellers were referred by this seller."""
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT COUNT(*) as c FROM sellers WHERE referred_by = %s",
            (seller_id,)).fetchone()
        return row["c"]
    finally:
        conn.close()


def get_referrals(seller_id, limit=50):
    """Get list of referred sellers with basic info."""
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT id, shop_name, plan, created_at FROM sellers
            WHERE referred_by = %s
            ORDER BY created_at DESC LIMIT %s
        """, (seller_id, limit)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def apply_referral_reward(referrer_seller_id):
    """
    Extend referrer's trial by 30 days as reward for a successful referral.
    Capped at 180 days (6 months) total earned from referrals.
    Only triggers when the referred seller is on a paying plan.
    """
    MAX_REFERRAL_DAYS = 180
    conn = get_conn()
    try:
        row = conn.execute("SELECT trial_ends_at, plan, settings FROM sellers WHERE id = %s",
                           (referrer_seller_id,)).fetchone()
        if not row:
            return

        current_settings = json.loads(row["settings"]) if row and row["settings"] else {}
        days_already_earned = current_settings.get("referral_days_earned", 0)

        if days_already_earned >= MAX_REFERRAL_DAYS:
            return

        days_to_add = min(30, MAX_REFERRAL_DAYS - days_already_earned)

        if row["plan"] == "free" or not row["plan"]:
            current_end = row["trial_ends_at"]
            if current_end:
                if isinstance(current_end, str):
                    current_end = datetime.fromisoformat(current_end)
                base = max(current_end, datetime.now())
            else:
                base = datetime.now()
            new_end = (base + timedelta(days=days_to_add)).isoformat()
            conn.execute("UPDATE sellers SET trial_ends_at = %s WHERE id = %s",
                          (new_end, referrer_seller_id))
        else:
            current_settings["referral_credits"] = current_settings.get("referral_credits", 0) + 1

        current_settings["referral_days_earned"] = days_already_earned + days_to_add
        conn.execute("UPDATE sellers SET settings = %s WHERE id = %s",
                      (json.dumps(current_settings), referrer_seller_id))
        conn.commit()
    finally:
        conn.close()


def get_sellers_needing_onboard_email(stage, min_days_ago):
    """Get sellers at a specific onboard stage whose account is old enough for the next email."""
    conn = get_conn()
    try:
        rows = conn.execute(f"""
            SELECT id, email, shop_name FROM sellers
            WHERE onboard_email_stage = %s
              AND created_at <= {_ago(f'{min_days_ago} days')}
        """, (stage,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def set_onboard_email_stage(seller_id, stage):
    """Update the onboard email stage for a seller."""
    conn = get_conn()
    try:
        conn.execute("UPDATE sellers SET onboard_email_stage = %s WHERE id = %s",
                      (stage, seller_id))
        conn.commit()
    finally:
        conn.close()


# =============================================================

if __name__ == "__main__":
    init_db()
    if USE_PG:
        print(f"Database initialized: PostgreSQL")
    else:
        print(f"Database initialized: {os.path.abspath(DB_PATH)}")
