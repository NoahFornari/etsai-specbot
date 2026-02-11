"""
ETSAI - AI Spec Collection Bot for Etsy Custom Order Sellers
Flask app with:
  - Seller dashboard (manage products, view orders, monitor conversations)
  - Buyer intake pages (hosted forms where buyers provide specs via AI chat)
  - API endpoints (for future integrations, webhooks, etc.)
"""
import json
import os
import secrets
import logging
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash, abort, Response
from werkzeug.security import generate_password_hash, check_password_hash
from database import (
    init_db, create_seller, get_seller, get_seller_by_email,
    set_seller_password, get_seller_by_api_key,
    add_product, get_product, get_seller_products,
    create_order, get_order, get_seller_orders, update_order_specs,
    add_message, get_messages, log_ai_cost, get_seller_stats, get_recent_activity,
    save_etsy_connection, save_etsy_tokens, update_last_order_check,
    get_product_by_external_id, order_exists_by_external_id,
    update_product_notes, update_order_notes, mark_order_escalated,
    update_fulfillment_status, get_completed_orders_with_specs, get_stale_orders,
    update_seller_settings, update_seller_profile, delete_seller_account,
    update_seller_plan, set_trial_end, get_monthly_order_count, get_product_count,
    get_seller_by_stripe_customer, update_seller_brand,
    set_reset_token, get_seller_by_reset_token, clear_reset_token,
    get_all_sellers, get_admin_stats,
    generate_referral_code, set_referral_code, get_seller_by_referral_code,
    record_referral, get_referral_count, get_referrals, apply_referral_reward,
)
from ai_engine import (
    generate_greeting, process_buyer_message, generate_followup,
    generate_intake_questions, validate_answer
)
from scraper import scrape_etsy_listing, scrape_etsy_shop
from email_service import send_completion_email, send_escalation_email, send_password_reset_email
from etsy_api import (
    generate_pkce_pair, get_oauth_url, exchange_code_for_tokens,
    get_shop_for_user, get_shop_listings, get_recent_orders
)
from billing import (
    PLANS, get_plan, create_checkout_session, create_portal_session,
    handle_webhook_event, check_quota, get_usage_display,
)

# --- Sentry error monitoring (optional) ---
SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
if SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.1, profiles_sample_rate=0.1)

app = Flask(__name__)

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("etsai")

# --- Secret key ---
_debug = os.environ.get("FLASK_DEBUG", "1") == "1"
if _debug:
    app.secret_key = os.environ.get("SECRET_KEY", "etsai-dev-key-change-in-prod")
    if app.secret_key == "etsai-dev-key-change-in-prod":
        logger.warning("Using insecure default SECRET_KEY — set SECRET_KEY env var for production")
else:
    app.secret_key = os.environ.get("SECRET_KEY")
    if not app.secret_key:
        raise RuntimeError("SECRET_KEY environment variable is required in production (FLASK_DEBUG=0)")

# --- Session cookie hardening ---
if not _debug:
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# --- Rate limiting ---
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)


# --- CSRF Protection ---
def generate_csrf_token():
    if "_csrf_token" not in session:
        import secrets
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]


app.jinja_env.globals["csrf_token"] = generate_csrf_token

CSRF_EXEMPT_PREFIXES = ("/intake/", "/api/", "/auth/etsy/callback", "/health", "/billing/webhook")


@app.before_request
def check_csrf():
    if request.method not in ("POST", "PUT", "DELETE", "PATCH"):
        return
    # Exempt routes
    for prefix in CSRF_EXEMPT_PREFIXES:
        if request.path.startswith(prefix):
            return
    # JSON requests: check header
    if request.is_json:
        token = request.headers.get("X-CSRF-Token", "")
    else:
        token = request.form.get("_csrf_token", "")
    if not token or token != session.get("_csrf_token"):
        logger.warning("CSRF validation failed for %s %s", request.method, request.path)
        if request.is_json:
            return jsonify({"error": "CSRF token missing or invalid"}), 403
        flash("Session expired. Please try again.", "error")
        return redirect(request.referrer or url_for("home"))


# --- Security headers ---
@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if not _debug:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# --- HTTPS enforcement (production only) ---
@app.before_request
def enforce_https():
    if _debug:
        return
    # Trust proxy headers (Railway, Render, etc.)
    if request.headers.get("X-Forwarded-Proto", "https") != "https":
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)


# --- API Key Auth Helper ---
def require_api_key():
    api_key = request.headers.get("X-API-Key", "")
    if not api_key:
        return None, (jsonify({"error": "X-API-Key header required"}), 401)
    seller = get_seller_by_api_key(api_key)
    if not seller:
        logger.warning("Invalid API key attempt from %s", request.remote_addr)
        return None, (jsonify({"error": "Invalid API key"}), 401)
    return seller, None


# --- Stale session cleanup ---
@app.before_request
def validate_session():
    """Clear session if seller_id points to a deleted/nonexistent account."""
    seller_id = session.get("seller_id")
    if seller_id and request.endpoint not in ("logout", "home", "static"):
        seller = get_seller(seller_id)
        if not seller:
            session.clear()
            return redirect(url_for("home"))


# Initialize database on startup
init_db()


# =============================================================
# SELLER DASHBOARD
# =============================================================

@app.route("/")
def home():
    if "seller_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("home.html")


@app.route("/signup", methods=["POST"])
@limiter.limit("5 per minute")
def signup():
    email = request.form.get("email", "").strip()[:254]
    shop_name = request.form.get("shop_name", "").strip()[:100]
    password = request.form.get("password", "")
    if not email or not shop_name:
        flash("Email and shop name required.", "error")
        return redirect(url_for("home"))
    if len(password) < 8:
        flash("Password must be at least 8 characters.", "error")
        return redirect(url_for("home"))

    existing = get_seller_by_email(email)
    if existing:
        flash("Account already exists. Please log in.", "error")
        return redirect(url_for("home"))

    pw_hash = generate_password_hash(password)
    seller_id = create_seller(email, shop_name, password_hash=pw_hash)

    # Set 14-day free trial
    trial_end = (datetime.now() + timedelta(days=14)).isoformat()
    set_trial_end(seller_id, trial_end)

    # Generate unique referral code
    ref_code = generate_referral_code()
    set_referral_code(seller_id, ref_code)

    # Process referral if user came via a referral link
    # (record the relationship now; reward applied when they become a paying customer)
    referrer_id = session.pop("referral_from", None)
    if referrer_id:
        referrer = get_seller(referrer_id)
        if referrer and referrer["id"] != seller_id:
            record_referral(seller_id, referrer_id)
            logger.info("Referral recorded: %s referred by %s (reward pending paid conversion)", email, referrer_id)

    session["seller_id"] = seller_id
    logger.info("New seller signed up: %s", email)
    flash(f"Welcome to ETSAI, {shop_name}! Your 14-day free trial has started.", "success")
    return redirect(url_for("dashboard"))


@app.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    email = request.form.get("email", "").strip()[:254]
    password = request.form.get("password", "")
    seller = get_seller_by_email(email)
    if not seller:
        flash("No account found with that email.", "error")
        return redirect(url_for("home"))
    # Legacy account without password — prompt to set one
    if not seller.get("password_hash"):
        flash("Please set a password for your account.", "error")
        session["set_password_email"] = email
        return redirect(url_for("home"))
    if not check_password_hash(seller["password_hash"], password):
        flash("Incorrect password.", "error")
        return redirect(url_for("home"))
    session["seller_id"] = seller["id"]
    logger.info("Seller logged in: %s", email)
    return redirect(url_for("dashboard"))


@app.route("/set-password", methods=["POST"])
def set_password():
    email = request.form.get("email", "").strip()[:254]
    password = request.form.get("password", "")
    if len(password) < 8:
        flash("Password must be at least 8 characters.", "error")
        return redirect(url_for("home"))
    seller = get_seller_by_email(email)
    if not seller:
        flash("Account not found.", "error")
        return redirect(url_for("home"))
    if seller.get("password_hash"):
        flash("Password already set. Please log in.", "error")
        return redirect(url_for("home"))
    pw_hash = generate_password_hash(password)
    set_seller_password(seller["id"], pw_hash)
    session["seller_id"] = seller["id"]
    session.pop("set_password_email", None)
    logger.info("Password set for legacy account: %s", email)
    flash("Password set! You're now logged in.", "success")
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# --- Password Reset ---

@app.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def forgot_password():
    if request.method == "GET":
        return render_template("forgot_password.html")

    email = request.form.get("email", "").strip()[:254]
    if not email:
        flash("Please enter your email address.", "error")
        return redirect(url_for("forgot_password"))

    seller = get_seller_by_email(email)
    if seller:
        token = secrets.token_urlsafe(48)
        expires = (datetime.now() + timedelta(hours=1)).isoformat()
        set_reset_token(seller["id"], token, expires)
        base_url = request.host_url.rstrip("/")
        reset_url = f"{base_url}/reset-password/{token}"
        send_password_reset_email(email, reset_url)
        logger.info("Password reset requested for %s", email)

    # Always show success (don't reveal if email exists)
    flash("If that email is registered, you'll receive a reset link shortly.", "success")
    return redirect(url_for("forgot_password"))


@app.route("/reset-password/<token>", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def reset_password(token):
    seller = get_seller_by_reset_token(token)
    if not seller:
        logger.warning("Invalid or expired password reset token attempt: %s...", token[:12])
        flash("This reset link is invalid or has expired.", "error")
        return redirect(url_for("forgot_password"))

    if request.method == "GET":
        return render_template("reset_password.html", token=token)

    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")
    if len(password) < 8:
        flash("Password must be at least 8 characters.", "error")
        return redirect(url_for("reset_password", token=token))
    if password != confirm:
        flash("Passwords do not match.", "error")
        return redirect(url_for("reset_password", token=token))

    pw_hash = generate_password_hash(password)
    set_seller_password(seller["id"], pw_hash)
    clear_reset_token(seller["id"])
    logger.info("Password reset completed for %s", seller["email"])
    flash("Password reset successfully! Please log in.", "success")
    return redirect(url_for("home"))


@app.route("/dashboard")
def dashboard():
    seller_id = session.get("seller_id")
    if not seller_id:
        return redirect(url_for("home"))

    seller = get_seller(seller_id)
    products = get_seller_products(seller_id)
    orders = get_seller_orders(seller_id)
    stats = get_seller_stats(seller_id)
    activity = get_recent_activity(seller_id)
    completed_orders = get_completed_orders_with_specs(seller_id)
    stale_order_ids = get_stale_orders(seller_id)

    # Usage/billing info
    monthly_orders = get_monthly_order_count(seller_id)
    product_count = get_product_count(seller_id)
    usage = get_usage_display(seller, monthly_orders, product_count)

    return render_template("dashboard.html",
                           seller=seller, products=products,
                           orders=orders, stats=stats, activity=activity,
                           completed_orders=completed_orders,
                           stale_order_ids=stale_order_ids,
                           usage=usage)


# === PRODUCT MANAGEMENT ===

@app.route("/products/add", methods=["GET", "POST"])
def add_product_page():
    seller_id = session.get("seller_id")
    if not seller_id:
        return redirect(url_for("home"))

    if request.method == "GET":
        seller = get_seller(seller_id)
        if not seller:
            return redirect(url_for("home"))
        try:
            seller_settings = json.loads(seller.get("settings") or "{}")
        except (json.JSONDecodeError, TypeError):
            seller_settings = {}
        default_notes = seller_settings.get("default_notes", "")
        return render_template("add_product.html", seller=seller, default_notes=default_notes)

    title = request.form.get("title", "").strip()[:200]
    category = request.form.get("category", "").strip()
    description = request.form.get("description", "").strip()
    price = request.form.get("price", "").strip()
    seller_notes = request.form.get("seller_notes", "").strip()

    if not title:
        flash("Product title required.", "error")
        return redirect(url_for("add_product_page"))

    try:
        price_val = float(price) if price else None
    except (ValueError, TypeError):
        flash("Invalid price. Please enter a number.", "error")
        return redirect(url_for("add_product_page"))

    # Product quota check
    seller = get_seller(seller_id)
    product_count = get_product_count(seller_id)
    plan = get_plan(seller.get("plan", "free"))
    if plan["max_products"] != -1 and product_count >= plan["max_products"]:
        flash(f"You've reached your {plan['name']} plan limit of {plan['max_products']} products. Upgrade for more.", "error")
        return redirect(url_for("settings_page"))

    # Option A: AI-generate questions
    if request.form.get("ai_generate") == "1":
        result = generate_intake_questions(title, category, description)
        questions = result["questions"]
        log_ai_cost(seller_id, "claude-sonnet-4-5-20250929", 0, 0, result["cost"],
                    f"Generate questions for: {title}")
    else:
        # Option B: Manual questions from form
        try:
            questions = json.loads(request.form.get("questions_json", "[]"))
        except (json.JSONDecodeError, TypeError):
            questions = []

    try:
        product_id = add_product(
            seller_id=seller_id,
            title=title,
            intake_questions=questions,
            category=category or None,
            price=price_val,
            description=description or None,
            seller_notes=seller_notes or None,
        )
    except Exception as e:
        logger.error("Failed to create product: %s", e)
        flash("Failed to create product. Please try again.", "error")
        return redirect(url_for("add_product_page"))

    flash(f"Product added! AI generated {len(questions)} intake questions.", "success")
    return redirect(url_for("product_detail", product_id=product_id))


@app.route("/products/<product_id>")
def product_detail(product_id):
    seller_id = session.get("seller_id")
    if not seller_id:
        return redirect(url_for("home"))

    product = get_product(product_id)
    if not product or product["seller_id"] != seller_id:
        flash("Product not found.", "error")
        return redirect(url_for("dashboard"))

    orders = get_seller_orders(seller_id)
    product_orders = [o for o in orders if o["product_id"] == product_id]

    seller = get_seller(seller_id)
    return render_template("product_detail.html", product=product, orders=product_orders, seller=seller)


@app.route("/products/<product_id>/edit-questions", methods=["POST"])
def edit_questions(product_id):
    seller_id = session.get("seller_id")
    if not seller_id:
        return redirect(url_for("home"))

    product = get_product(product_id)
    if not product or product["seller_id"] != seller_id:
        return jsonify({"error": "Not found"}), 404

    questions = request.json.get("questions", [])
    if not isinstance(questions, list) or len(questions) > 20:
        return jsonify({"error": "Invalid questions (max 20)"}), 400
    for q in questions:
        if not isinstance(q, dict) or "field_name" not in q or "question" not in q:
            return jsonify({"error": "Each question must have field_name and question"}), 400
    from database import get_conn
    conn = get_conn()
    try:
        conn.execute("UPDATE products SET intake_questions = %s WHERE id = %s",
                      (json.dumps(questions), product_id))
        conn.commit()
    finally:
        conn.close()

    return jsonify({"ok": True})


@app.route("/products/<product_id>/update-notes", methods=["POST"])
def update_product_notes_route(product_id):
    seller_id = session.get("seller_id")
    if not seller_id:
        return jsonify({"error": "Not logged in"}), 401

    product = get_product(product_id)
    if not product or product["seller_id"] != seller_id:
        return jsonify({"error": "Not found"}), 404

    notes = request.json.get("seller_notes", "").strip()
    update_product_notes(product_id, notes or None)
    return jsonify({"ok": True})


@app.route("/orders/<order_id>/notes", methods=["POST"])
def update_order_notes_route(order_id):
    seller_id = session.get("seller_id")
    if not seller_id:
        return jsonify({"error": "Not logged in"}), 401

    order = get_order(order_id)
    if not order or order["seller_id"] != seller_id:
        return jsonify({"error": "Not found"}), 404

    notes = request.json.get("notes", "").strip()[:5000]
    update_order_notes(order_id, notes or None)
    return jsonify({"ok": True})


@app.route("/orders/<order_id>/fulfillment", methods=["POST"])
def update_fulfillment_route(order_id):
    seller_id = session.get("seller_id")
    if not seller_id:
        return jsonify({"error": "Not logged in"}), 401

    order = get_order(order_id)
    if not order or order["seller_id"] != seller_id:
        return jsonify({"error": "Not found"}), 404

    status = request.json.get("status", "")
    try:
        update_fulfillment_status(order_id, status)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"ok": True})


# === PRODUCT IMPORT (Etsy Scraper) ===

@app.route("/products/import-url", methods=["POST"])
def import_from_url():
    """Scrape a single Etsy listing URL and create a product."""
    seller_id = session.get("seller_id")
    if not seller_id:
        return redirect(url_for("home"))

    url = request.form.get("url", "").strip()
    seller_notes = request.form.get("seller_notes", "").strip()

    if not url:
        flash("Please paste an Etsy listing URL.", "error")
        return redirect(url_for("add_product_page"))

    if "etsy.com" not in url:
        flash("URL must be an Etsy listing.", "error")
        return redirect(url_for("add_product_page"))

    try:
        listing = scrape_etsy_listing(url)
    except Exception as e:
        logger.error("Scraper error for URL import: %s", e)
        flash("Could not import that listing. Please check the URL and try again.", "error")
        return redirect(url_for("add_product_page"))

    # Generate AI intake questions from scraped data
    description = listing.get("description", "")
    # Include variation info in the description for better question generation
    if listing.get("variations"):
        variation_info = ". ".join(
            f"Available {v['name']}: {', '.join(v['options'])}" for v in listing["variations"]
        )
        description = f"{description}\n\nVariations: {variation_info}" if description else variation_info

    result = generate_intake_questions(listing["title"], None, description)
    questions = result["questions"]
    log_ai_cost(seller_id, "claude-sonnet-4-5-20250929", 0, 0, result["cost"],
                f"Generate questions for imported: {listing['title']}")

    product_id = add_product(
        seller_id=seller_id,
        title=listing["title"],
        intake_questions=questions,
        category=None,
        price=listing.get("price"),
        image_url=listing["images"][0] if listing.get("images") else None,
        description=listing.get("description") or None,
        seller_notes=seller_notes or None,
        source_url=url,
    )

    flash(f"Imported \"{listing['title']}\" with {len(questions)} intake questions!", "success")
    return redirect(url_for("product_detail", product_id=product_id))


@app.route("/products/import-shop", methods=["POST"])
def import_shop_preview():
    """Scrape an Etsy shop and return listing previews as JSON."""
    seller_id = session.get("seller_id")
    if not seller_id:
        return jsonify({"error": "Not logged in"}), 401

    shop_url = request.json.get("shop_url", "").strip() if request.is_json else request.form.get("shop_url", "").strip()

    if not shop_url:
        return jsonify({"error": "Please paste an Etsy shop URL."}), 400

    try:
        listings = scrape_etsy_shop(shop_url)
    except Exception as e:
        logger.error("Scraper error for shop import: %s", e)
        return jsonify({"error": "Could not import that shop. Please check the URL and try again."}), 400

    if not listings:
        return jsonify({"error": "No listings found at that URL."}), 404

    return jsonify({"listings": listings, "count": len(listings)})


@app.route("/products/import-shop/confirm", methods=["POST"])
def import_shop_confirm():
    """Import selected listings from a shop scrape."""
    seller_id = session.get("seller_id")
    if not seller_id:
        return jsonify({"error": "Not logged in"}), 401

    data = request.json or {}
    selected_urls = data.get("urls", [])
    if len(selected_urls) > 50:
        return jsonify({"error": "Maximum 50 listings per import."}), 400
    seller_notes = data.get("seller_notes", "").strip()

    if not selected_urls:
        return jsonify({"error": "No listings selected."}), 400

    imported = []
    errors = []

    for url in selected_urls:
        try:
            listing = scrape_etsy_listing(url)

            description = listing.get("description", "")
            if listing.get("variations"):
                variation_info = ". ".join(
                    f"Available {v['name']}: {', '.join(v['options'])}" for v in listing["variations"]
                )
                description = f"{description}\n\nVariations: {variation_info}" if description else variation_info

            result = generate_intake_questions(listing["title"], None, description)
            questions = result["questions"]
            log_ai_cost(seller_id, "claude-sonnet-4-5-20250929", 0, 0, result["cost"],
                        f"Generate questions for imported: {listing['title']}")

            product_id = add_product(
                seller_id=seller_id,
                title=listing["title"],
                intake_questions=questions,
                price=listing.get("price"),
                image_url=listing["images"][0] if listing.get("images") else None,
                description=listing.get("description") or None,
                seller_notes=seller_notes or None,
                source_url=url,
            )
            imported.append({"product_id": product_id, "title": listing["title"]})
        except Exception as e:
            errors.append({"url": url, "error": str(e)})

    return jsonify({
        "imported": imported,
        "errors": errors,
        "count": len(imported),
    })


# === ORDER MANAGEMENT ===

@app.route("/orders/create", methods=["POST"])
def create_order_page():
    """Seller manually creates an order (or triggered by webhook)."""
    seller_id = session.get("seller_id")
    if not seller_id:
        return redirect(url_for("home"))

    # Quota check
    seller = get_seller(seller_id)
    monthly_orders = get_monthly_order_count(seller_id)
    product_count = get_product_count(seller_id)
    allowed, reason = check_quota(seller, monthly_orders, product_count)
    if not allowed:
        if reason == "trial_expired":
            flash("Your free trial has ended. Upgrade to keep creating orders.", "error")
        elif reason == "order_limit":
            plan = get_plan(seller.get("plan", "free"))
            flash(f"You've reached your {plan['name']} plan limit of {plan['orders_per_month']} orders this month. Upgrade for more.", "error")
        else:
            flash("Plan limit reached. Please upgrade.", "error")
        return redirect(url_for("settings_page"))

    product_id = request.form.get("product_id")
    buyer_name = request.form.get("buyer_name", "").strip()
    buyer_email = request.form.get("buyer_email", "").strip()
    external_id = request.form.get("external_order_id", "").strip()

    if not product_id:
        flash("Select a product.", "error")
        return redirect(url_for("dashboard"))

    order_id = create_order(
        seller_id=seller_id,
        product_id=product_id,
        buyer_name=buyer_name or None,
        buyer_email=buyer_email or None,
        external_order_id=external_id or None,
    )

    base_url = request.host_url.rstrip("/")
    intake_link = f"{base_url}/intake/{order_id}"

    flash(f"Order created! Intake link: {intake_link}", "success")
    return redirect(url_for("order_detail", order_id=order_id))


@app.route("/orders/<order_id>")
def order_detail(order_id):
    seller_id = session.get("seller_id")
    if not seller_id:
        return redirect(url_for("home"))

    order = get_order(order_id)
    if not order or order["seller_id"] != seller_id:
        flash("Order not found.", "error")
        return redirect(url_for("dashboard"))

    messages = get_messages(order_id)

    # Compute spec progress
    questions = order["intake_questions"]
    collected = order["customer_specs"]
    required = [q for q in questions if q.get("required")]
    filled_required = [q for q in required if collected.get(q["field_name"])]
    progress = len(filled_required) / len(required) if required else 1.0

    seller = get_seller(seller_id)
    return render_template("order_detail.html",
                           order=order, messages=messages,
                           progress=progress, seller=seller)


# =============================================================
# BUYER INTAKE PAGE (the product — hosted spec collection)
# =============================================================

@app.route("/intake/<order_id>")
def intake_page(order_id):
    """The buyer-facing page. This is what the Etsy sale_message links to."""
    order = get_order(order_id)
    if not order:
        return render_template("intake_error.html", message="Order not found."), 404

    if order["specs_complete"]:
        seller = get_seller(order["seller_id"])
        wl = seller.get("plan") == "business"
        return render_template("intake_complete.html", order=order,
                               white_label=wl,
                               brand_color=seller.get("brand_color") if wl else None,
                               brand_logo_url=seller.get("brand_logo_url") if wl else None)

    messages = get_messages(order_id)

    # If no messages yet, generate greeting
    if not messages:
        try:
            greeting = generate_greeting(
                order["product_title"],
                order["intake_questions"],
                order.get("buyer_name"),
                seller_notes=order.get("seller_notes")
            )
            greeting_text = greeting["response"]
            log_ai_cost(order["seller_id"], "claude-sonnet-4-5-20250929", 0, 0,
                        greeting["cost"], f"Greeting for order {order_id}")
        except Exception:
            logger.exception("AI error generating greeting for order %s", order_id)
            buyer = order.get("buyer_name") or "there"
            greeting_text = (
                f"Hi {buyer}! Thanks for your order of {order['product_title']}. "
                "I'll help collect a few details to get your custom order started. "
                "What details would you like to share?"
            )
        add_message(order_id, "outbound", greeting_text, ai_generated=True)
        messages = get_messages(order_id)

    # White-label: check if seller is on Business plan
    seller = get_seller(order["seller_id"])
    white_label = seller.get("plan") == "business"
    brand_color = seller.get("brand_color") if white_label else None
    brand_logo_url = seller.get("brand_logo_url") if white_label else None

    return render_template("intake_chat.html", order=order, messages=messages,
                           white_label=white_label, brand_color=brand_color,
                           brand_logo_url=brand_logo_url)


@app.route("/intake/<order_id>/message", methods=["POST"])
@limiter.limit("20 per minute")
def intake_message(order_id):
    """Buyer sends a message via the intake chat."""
    order = get_order(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if order["specs_complete"]:
        return jsonify({"error": "Specs already complete", "complete": True})

    buyer_message = request.json.get("message", "").strip()[:2000]
    if not buyer_message:
        return jsonify({"error": "Empty message"}), 400

    # Save buyer message
    add_message(order_id, "inbound", buyer_message)

    # Get conversation history
    messages = get_messages(order_id)
    history = [{"direction": m["direction"], "content": m["content"]} for m in messages]

    # Process with AI
    try:
        result = process_buyer_message(
            buyer_message=buyer_message,
            product_title=order["product_title"],
            questions=order["intake_questions"],
            collected_specs=order["customer_specs"],
            conversation_history=history,
            buyer_name=order.get("buyer_name"),
            seller_notes=order.get("seller_notes"),
        )
    except Exception:
        logger.exception("AI error processing message for order %s", order_id)
        return jsonify({
            "response": "I'm sorry, I'm having a little trouble right now. Could you try sending that again?",
            "specs_extracted": {},
            "is_complete": False,
            "should_escalate": False,
        })

    # Update specs
    if result["specs_extracted"]:
        updated_specs = order["customer_specs"].copy()
        # Filter out special_requests from normal specs — store separately
        extracted = result["specs_extracted"].copy()
        extracted.pop("special_requests", None)
        updated_specs.update(extracted)

        # Only mark complete when AI confirms buyer explicitly approved
        # (two-phase: AI summarizes first, buyer confirms, THEN all_required_complete=true)
        buyer_confirmed = result.get("is_complete", False)

        update_order_specs(order_id, updated_specs, complete=buyer_confirmed)
        result["is_complete"] = buyer_confirmed
    else:
        # Even without new specs, the AI might signal completion (buyer confirming summary)
        buyer_confirmed = result.get("is_complete", False)
        if buyer_confirmed:
            update_order_specs(order_id, order["customer_specs"], complete=True)
            result["is_complete"] = True

    # Save bot response
    add_message(order_id, "outbound", result["response"],
                specs_extracted=result["specs_extracted"], ai_generated=True)

    # Log cost
    log_ai_cost(order["seller_id"], "claude-sonnet-4-5-20250929", 0, 0,
                result["cost"], f"Conversation turn for order {order_id}")

    # Load seller notification settings
    seller = get_seller(order["seller_id"])
    try:
        seller_settings = json.loads(seller.get("settings") or "{}")
    except (json.JSONDecodeError, TypeError):
        seller_settings = {}

    # Handle escalation
    should_escalate = result.get("should_escalate", False)
    if should_escalate:
        mark_order_escalated(order_id)
        if seller_settings.get("email_on_escalation", True):
            base_url = request.host_url.rstrip("/")
            send_escalation_email(order, result.get("escalation_reason", ""), base_url)

    # Handle completion email
    if result["is_complete"]:
        if seller_settings.get("email_on_complete", True):
            base_url = request.host_url.rstrip("/")
            refreshed_order = get_order(order_id)
            if refreshed_order:
                send_completion_email(refreshed_order, base_url)

    return jsonify({
        "response": result["response"],
        "specs_extracted": result["specs_extracted"],
        "is_complete": result["is_complete"],
        "should_escalate": should_escalate,
    })


# =============================================================
# ETSY API INTEGRATION
# =============================================================

@app.route("/auth/etsy")
def etsy_auth_start():
    """Start Etsy OAuth — redirect seller to Etsy login."""
    seller_id = session.get("seller_id")
    if not seller_id:
        return redirect(url_for("home"))

    code_verifier, code_challenge = generate_pkce_pair()
    state = os.urandom(16).hex()

    # Store in session for callback verification
    session["etsy_code_verifier"] = code_verifier
    session["etsy_oauth_state"] = state

    auth_url = get_oauth_url(state, code_challenge)
    return redirect(auth_url)


@app.route("/auth/etsy/callback")
@limiter.limit("10 per minute")
def etsy_auth_callback():
    """Etsy redirects back here after OAuth approval."""
    seller_id = session.get("seller_id")
    if not seller_id:
        return redirect(url_for("home"))

    # Verify state
    state = request.args.get("state", "")
    expected_state = session.get("etsy_oauth_state", "")
    if state != expected_state:
        flash("OAuth state mismatch. Please try again.", "error")
        return redirect(url_for("dashboard"))
    session.pop("etsy_oauth_state", "")

    error = request.args.get("error")
    if error:
        if error == "access_denied":
            flash("You declined the Etsy connection. Connect anytime from your dashboard.", "error")
        else:
            flash("Etsy authorization failed. Please try again.", "error")
        return redirect(url_for("dashboard"))

    auth_code = request.args.get("code", "")
    code_verifier = session.pop("etsy_code_verifier", "")

    if not auth_code or not code_verifier:
        flash("Missing authorization code. Please try again.", "error")
        return redirect(url_for("dashboard"))

    try:
        tokens = exchange_code_for_tokens(auth_code, code_verifier)

        # Get seller object with new tokens temporarily set
        seller = get_seller(seller_id)
        seller["etsy_access_token"] = tokens["access_token"]
        seller["etsy_refresh_token"] = tokens["refresh_token"]
        seller["etsy_token_expires_at"] = tokens["expires_at"]

        # Get shop info
        shop_info = get_shop_for_user(seller)

        # Save everything
        save_etsy_connection(
            seller_id,
            etsy_user_id=str(shop_info["user_id"]),
            etsy_shop_id=str(shop_info["shop_id"]),
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_at=tokens["expires_at"],
        )

        flash(f"Connected to Etsy shop: {shop_info['shop_name']}!", "success")
    except Exception as e:
        logger.error("Etsy OAuth error: %s", e)
        flash("Failed to connect to Etsy. Please try again.", "error")

    return redirect(url_for("dashboard"))


@app.route("/auth/etsy/disconnect", methods=["POST"])
def etsy_disconnect():
    """Clear Etsy tokens — disconnect integration."""
    seller_id = session.get("seller_id")
    if not seller_id:
        return redirect(url_for("home"))

    from database import get_conn
    conn = get_conn()
    try:
        conn.execute("""
            UPDATE sellers SET etsy_user_id = NULL, etsy_shop_id = NULL,
                               etsy_access_token = NULL, etsy_refresh_token = NULL,
                               etsy_token_expires_at = NULL, etsy_connected_at = NULL,
                               etsy_last_order_check = NULL
            WHERE id = %s
        """, (seller_id,))
        conn.commit()
    finally:
        conn.close()

    flash("Etsy disconnected.", "success")
    return redirect(url_for("dashboard"))


@app.route("/etsy/import-products", methods=["POST"])
@limiter.limit("5 per minute")
def etsy_import_products():
    """Pull active listings from Etsy API and create products with AI questions."""
    seller_id = session.get("seller_id")
    if not seller_id:
        return redirect(url_for("home"))

    seller = get_seller(seller_id)
    if not seller.get("etsy_access_token"):
        flash("Connect Etsy first.", "error")
        return redirect(url_for("dashboard"))

    try:
        listings = get_shop_listings(seller)
    except Exception as e:
        logger.error("Etsy listing fetch error: %s", e)
        flash("Could not fetch your Etsy listings. Please try again.", "error")
        return redirect(url_for("dashboard"))

    if not listings:
        flash("No active listings found in your Etsy shop.", "error")
        return redirect(url_for("dashboard"))

    imported = 0
    skipped = 0

    # Check product quota
    product_count = get_product_count(seller_id)
    plan = get_plan(seller.get("plan", "free"))

    for listing in listings:
        # Skip if already imported
        existing = get_product_by_external_id(seller_id, str(listing["listing_id"]))
        if existing:
            skipped += 1
            continue

        if plan["max_products"] != -1 and product_count >= plan["max_products"]:
            logger.info("Product quota reached during Etsy import for seller %s", seller_id)
            break

        # Generate AI intake questions
        try:
            result = generate_intake_questions(
                listing["title"], None, listing.get("description", "")
            )
            questions = result["questions"]
            log_ai_cost(seller_id, "claude-sonnet-4-5-20250929", 0, 0, result["cost"],
                        f"Generate questions for Etsy import: {listing['title']}")

            add_product(
                seller_id=seller_id,
                title=listing["title"],
                intake_questions=questions,
                price=listing.get("price"),
                image_url=listing.get("image_url"),
                external_id=str(listing["listing_id"]),
                description=listing.get("description") or None,
                source_url=listing.get("url") or None,
            )
            imported += 1
            product_count += 1
        except Exception as e:
            logger.error("Failed to import listing %s: %s", listing['listing_id'], e)

    msg = f"Imported {imported} products from Etsy."
    if skipped:
        msg += f" ({skipped} already existed)"
    flash(msg, "success")
    return redirect(url_for("dashboard"))


@app.route("/etsy/check-orders", methods=["POST"])
@limiter.limit("5 per minute")
def etsy_check_orders():
    """Poll Etsy for new orders and auto-create ETSAI orders."""
    seller_id = session.get("seller_id")
    if not seller_id:
        return redirect(url_for("home"))

    seller = get_seller(seller_id)
    if not seller.get("etsy_access_token"):
        flash("Connect Etsy first.", "error")
        return redirect(url_for("dashboard"))

    try:
        receipts = get_recent_orders(seller, min_created=seller.get("etsy_last_order_check"))
    except Exception as e:
        logger.error("Etsy order check error: %s", e)
        flash("Could not check Etsy orders. Please try again.", "error")
        return redirect(url_for("dashboard"))

    created = 0
    skipped = 0
    no_product = 0

    # Check order quota
    monthly_orders = get_monthly_order_count(seller_id)
    plan = get_plan(seller.get("plan", "free"))

    for receipt in receipts:
        receipt_id = str(receipt["receipt_id"])

        # Skip if order already exists
        if order_exists_by_external_id(seller_id, receipt_id):
            skipped += 1
            continue

        # Match transactions to products
        for txn in receipt.get("transactions", []):
            try:
                listing_id = str(txn.get("listing_id", ""))
                product = get_product_by_external_id(seller_id, listing_id)

                if not product:
                    no_product += 1
                    continue

                allowed, reason = check_quota(seller, monthly_orders, 0)
                if not allowed:
                    logger.info("Order quota reached during Etsy order sync for seller %s", seller_id)
                    break

                order_id = create_order(
                    seller_id=seller_id,
                    product_id=product["id"],
                    buyer_name=receipt.get("buyer_name") or None,
                    external_order_id=receipt_id,
                )
                created += 1
                monthly_orders += 1
            except Exception as e:
                logger.error("Error processing transaction in receipt %s: %s", receipt_id, e)
                continue

    update_last_order_check(seller_id)

    msg = f"Found {created} new orders."
    if skipped:
        msg += f" ({skipped} already imported)"
    if no_product:
        msg += f" ({no_product} had no matching product — import products first)"
    flash(msg, "success")
    return redirect(url_for("dashboard"))


# =============================================================
# API ENDPOINTS (for integrations / webhooks)
# =============================================================

@app.route("/api/orders", methods=["POST"])
def api_create_order():
    """
    Create an order via API. Returns the intake URL.
    Requires X-API-Key header.

    POST /api/orders
    {
        "product_id": "def456",
        "buyer_name": "John",
        "buyer_email": "john@example.com",
        "external_order_id": "ETSY-12345"
    }
    """
    seller, err = require_api_key()
    if err:
        return err

    data = request.json or {}
    product_id = data.get("product_id")

    if not product_id:
        return jsonify({"error": "product_id required"}), 400

    product = get_product(product_id)
    if not product or product["seller_id"] != seller["id"]:
        return jsonify({"error": "Product not found"}), 404

    order_id = create_order(
        seller_id=seller["id"],
        product_id=product_id,
        buyer_name=data.get("buyer_name"),
        buyer_email=data.get("buyer_email"),
        external_order_id=data.get("external_order_id"),
    )

    base_url = request.host_url.rstrip("/")
    intake_url = f"{base_url}/intake/{order_id}"

    return jsonify({
        "order_id": order_id,
        "intake_url": intake_url,
        "status": "pending",
    }), 201


@app.route("/api/orders/<order_id>", methods=["GET"])
def api_get_order(order_id):
    """Get order status and collected specs. Requires X-API-Key header."""
    seller, err = require_api_key()
    if err:
        return err

    order = get_order(order_id)
    if not order or order["seller_id"] != seller["id"]:
        return jsonify({"error": "Not found"}), 404

    return jsonify({
        "order_id": order["id"],
        "product_title": order["product_title"],
        "status": order["status"],
        "specs_complete": bool(order["specs_complete"]),
        "customer_specs": order["customer_specs"],
        "intake_url": f"{request.host_url.rstrip('/')}/intake/{order_id}",
    })


@app.route("/api/orders/<order_id>/specs", methods=["GET"])
def api_get_specs(order_id):
    """Get just the collected specs (for supplier ordering). Requires X-API-Key header."""
    seller, err = require_api_key()
    if err:
        return err

    order = get_order(order_id)
    if not order or order["seller_id"] != seller["id"]:
        return jsonify({"error": "Not found"}), 404

    questions = order["intake_questions"]
    specs = order["customer_specs"]

    formatted = []
    for q in questions:
        field = q["field_name"]
        formatted.append({
            "field": field,
            "question": q["question"],
            "answer": specs.get(field, ""),
            "required": q.get("required", False),
            "filled": bool(specs.get(field)),
        })

    return jsonify({
        "order_id": order_id,
        "product": order["product_title"],
        "complete": bool(order["specs_complete"]),
        "specs": formatted,
    })


@app.route("/api/products/<product_id>/generate-questions", methods=["POST"])
def api_generate_questions(product_id):
    """Re-generate intake questions for a product. Requires X-API-Key header."""
    seller, err = require_api_key()
    if err:
        return err

    product = get_product(product_id)
    if not product or product["seller_id"] != seller["id"]:
        return jsonify({"error": "Not found"}), 404

    data = request.json or {}
    result = generate_intake_questions(
        product["title"],
        data.get("category", product.get("category")),
        data.get("description"),
    )

    return jsonify(result)


# =============================================================
# SETTINGS
# =============================================================

@app.route("/settings", methods=["GET", "POST"])
def settings_page():
    seller_id = session.get("seller_id")
    if not seller_id:
        return redirect(url_for("home"))

    seller = get_seller(seller_id)
    if not seller:
        return redirect(url_for("home"))
    try:
        settings = json.loads(seller.get("settings") or "{}")
    except (json.JSONDecodeError, TypeError):
        settings = {}

    if request.method == "POST":
        action = request.form.get("action")

        if action == "profile":
            shop_name = request.form.get("shop_name", "").strip()[:100]
            email = request.form.get("email", "").strip()[:254]
            display_name = request.form.get("display_name", "").strip()[:100] or None
            phone = request.form.get("phone", "").strip()[:20] or None
            website = request.form.get("website", "").strip()[:200] or None
            timezone = request.form.get("timezone", "").strip()[:50] or None
            if shop_name and email:
                update_seller_profile(seller_id, shop_name, email, display_name,
                                      phone, website, timezone)
                flash("Profile updated.", "success")
            else:
                flash("Shop name and email are required.", "error")

        elif action == "change_password":
            current_pw = request.form.get("current_password", "")
            new_pw = request.form.get("new_password", "")
            confirm_pw = request.form.get("confirm_password", "")
            if not check_password_hash(seller.get("password_hash", ""), current_pw):
                flash("Current password is incorrect.", "error")
            elif len(new_pw) < 8:
                flash("New password must be at least 8 characters.", "error")
            elif new_pw != confirm_pw:
                flash("New passwords do not match.", "error")
            else:
                set_seller_password(seller_id, generate_password_hash(new_pw))
                flash("Password changed successfully.", "success")

        elif action == "notifications":
            update_seller_settings(seller_id, {
                "email_on_complete": "email_on_complete" in request.form,
                "email_on_escalation": "email_on_escalation" in request.form,
            })
            flash("Notification preferences saved.", "success")

        elif action == "default_notes":
            update_seller_settings(seller_id, {
                "default_notes": request.form.get("default_notes", "").strip(),
            })
            flash("Default notes saved.", "success")

        elif action == "branding":
            brand_color = request.form.get("brand_color", "").strip()[:7]
            brand_logo_url = request.form.get("brand_logo_url", "").strip()[:500]
            update_seller_brand(seller_id, brand_color or None, brand_logo_url or None)
            flash("Branding updated.", "success")

        elif action == "regenerate_referral":
            new_code = generate_referral_code()
            set_referral_code(seller_id, new_code)
            flash("Referral code regenerated.", "success")

        elif action == "delete_account":
            delete_seller_account(seller_id)
            session.clear()
            flash("Account deleted.", "success")
            return redirect(url_for("home"))

        return redirect(url_for("settings_page"))

    # Billing/usage data
    monthly_orders = get_monthly_order_count(seller_id)
    product_count = get_product_count(seller_id)
    usage = get_usage_display(seller, monthly_orders, product_count)

    # Referral data
    referral_count = get_referral_count(seller_id)
    referrals = get_referrals(seller_id)

    # Ensure seller has a referral code (backfill for existing accounts)
    if not seller.get("referral_code"):
        ref_code = generate_referral_code()
        set_referral_code(seller_id, ref_code)
        seller["referral_code"] = ref_code

    return render_template("settings.html", seller=seller, settings=settings,
                           usage=usage, plans=PLANS,
                           referral_count=referral_count, referrals=referrals)


# =============================================================
# BILLING
# =============================================================

@app.route("/billing/checkout", methods=["POST"])
def billing_checkout():
    """Start a Stripe Checkout session for upgrading plan."""
    seller_id = session.get("seller_id")
    if not seller_id:
        return redirect(url_for("home"))

    seller = get_seller(seller_id)
    plan_key = request.form.get("plan", "starter")

    if plan_key not in ("starter", "pro", "business"):
        flash("Invalid plan.", "error")
        return redirect(url_for("settings_page"))

    base_url = request.host_url.rstrip("/")
    try:
        checkout_url, customer_id = create_checkout_session(
            seller, plan_key,
            success_url=f"{base_url}/settings?billing=success",
            cancel_url=f"{base_url}/settings?billing=cancelled",
        )
        # Save Stripe customer ID if newly created
        if not seller.get("stripe_customer_id") and customer_id:
            update_seller_plan(seller_id, seller.get("plan", "free"), stripe_customer_id=customer_id)
        return redirect(checkout_url)
    except Exception as e:
        logger.error("Stripe checkout error: %s", e)
        flash("Could not start checkout. Please try again.", "error")
        return redirect(url_for("settings_page"))


@app.route("/billing/portal", methods=["POST"])
def billing_portal():
    """Redirect to Stripe Customer Portal for managing subscription."""
    seller_id = session.get("seller_id")
    if not seller_id:
        return redirect(url_for("home"))

    seller = get_seller(seller_id)
    if not seller.get("stripe_customer_id"):
        flash("No billing account found.", "error")
        return redirect(url_for("settings_page"))

    base_url = request.host_url.rstrip("/")
    try:
        portal_url = create_portal_session(
            seller["stripe_customer_id"],
            return_url=f"{base_url}/settings",
        )
        return redirect(portal_url)
    except Exception as e:
        logger.error("Stripe portal error: %s", e)
        flash("Could not open billing portal.", "error")
        return redirect(url_for("settings_page"))


@app.route("/billing/webhook", methods=["POST"])
def billing_webhook():
    """Stripe webhook endpoint — updates plan on payment events."""
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        event = handle_webhook_event(payload, sig_header)
    except Exception as e:
        logger.error("Stripe webhook error: %s", e)
        return jsonify({"error": str(e)}), 400

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        # Subscription just started
        seller_id = data.get("metadata", {}).get("etsai_seller_id")
        plan_key = data.get("metadata", {}).get("plan", "starter")
        customer_id = data.get("customer")
        if seller_id:
            update_seller_plan(seller_id, plan_key, stripe_customer_id=customer_id)
            logger.info("Seller %s upgraded to %s", seller_id, plan_key)

            # Referral reward: if this seller was referred, reward the referrer
            new_seller = get_seller(seller_id)
            if new_seller and new_seller.get("referred_by"):
                apply_referral_reward(new_seller["referred_by"])
                logger.info("Referral reward applied for referrer %s (referred seller %s paid)",
                           new_seller["referred_by"], seller_id)

    elif event_type == "customer.subscription.updated":
        # Plan changed (upgrade/downgrade)
        customer_id = data.get("customer")
        plan_key = data.get("metadata", {}).get("plan")
        if customer_id and plan_key:
            seller = get_seller_by_stripe_customer(customer_id)
            if seller:
                update_seller_plan(seller["id"], plan_key)
                logger.info("Seller %s plan updated to %s", seller["id"], plan_key)

    elif event_type == "customer.subscription.deleted":
        # Subscription cancelled — downgrade to free
        customer_id = data.get("customer")
        if customer_id:
            seller = get_seller_by_stripe_customer(customer_id)
            if seller:
                update_seller_plan(seller["id"], "free")
                logger.info("Seller %s subscription cancelled, downgraded to free", seller["id"])

    elif event_type == "invoice.payment_failed":
        customer_id = data.get("customer")
        logger.warning("Payment failed for Stripe customer %s", customer_id)
        if customer_id:
            seller = get_seller_by_stripe_customer(customer_id)
            if seller:
                update_seller_plan(seller["id"], "free")
                logger.warning("Seller %s downgraded to free due to payment failure", seller["id"])

    return jsonify({"received": True}), 200


# =============================================================
# ADMIN PANEL
# =============================================================

@app.route("/admin")
def admin_panel():
    seller_id = session.get("seller_id")
    if not seller_id:
        return redirect(url_for("home"))
    seller = get_seller(seller_id)
    if not seller or not seller.get("is_admin"):
        abort(404)
    sellers = get_all_sellers()
    stats = get_admin_stats()
    return render_template("admin.html", seller=seller, sellers=sellers, admin_stats=stats)


# =============================================================
# SEO
# =============================================================

@app.route("/robots.txt")
def robots_txt():
    content = "User-agent: *\nAllow: /\nAllow: /for/\nAllow: /tools/\nDisallow: /dashboard\nDisallow: /settings\nDisallow: /admin\nDisallow: /intake/\nDisallow: /api/\nSitemap: " + request.host_url.rstrip("/") + "/sitemap.xml\n"
    return Response(content, mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap_xml():
    base = request.host_url.rstrip("/")
    urls = [
        (base + "/", "1.0"),
        (base + "/privacy", "0.3"),
        (base + "/terms", "0.3"),
        (base + "/support", "0.5"),
        (base + "/tools/message-generator", "0.7"),
    ]
    for niche_slug in NICHE_PAGES:
        urls.append((base + f"/for/{niche_slug}", "0.8"))
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url, priority in urls:
        xml += f"  <url><loc>{url}</loc><priority>{priority}</priority></url>\n"
    xml += "</urlset>"
    return Response(xml, mimetype="application/xml")


# =============================================================
# STATIC PAGES
# =============================================================

@app.route("/pitch")
def pitch_page():
    return render_template("pitch.html")


@app.route("/privacy")
def privacy_page():
    return render_template("privacy.html")


@app.route("/terms")
def terms_page():
    return render_template("terms.html")


@app.route("/support")
def support_page():
    return render_template("support.html")


# =============================================================
# REFERRAL SYSTEM
# =============================================================

@app.route("/refer/<code>")
def referral_landing(code):
    """Referral link — sets session cookie and redirects to signup."""
    referrer = get_seller_by_referral_code(code)
    if not referrer:
        flash("Invalid referral link.", "error")
        return redirect(url_for("home"))

    # If already logged in, no need for referral
    if "seller_id" in session:
        return redirect(url_for("dashboard"))

    # Store referrer in session for signup to pick up
    session["referral_from"] = referrer["id"]
    session["referral_shop"] = referrer["shop_name"]
    flash(f"You were referred by {referrer['shop_name']}! Sign up to get started.", "success")
    return redirect(url_for("home"))


# =============================================================
# PROGRAMMATIC SEO LANDING PAGES
# =============================================================

NICHE_PAGES = {
    "jewelry-sellers": {
        "title": "AI Spec Collection for Custom Jewelry Orders",
        "headline": "Stop chasing buyers for ring sizes and engraving text.",
        "subheadline": "ETSAI collects every jewelry spec — ring size, metal type, font choice, engraving text, stone preference — through a friendly AI chat. Your buyer gets a link. You get a complete spec sheet.",
        "category": "Jewelry",
        "pain_points": [
            "Buyers forget to include their ring size",
            "Engraving text gets mangled in Etsy's personalization box",
            "3-4 messages just to confirm metal type and finish",
            "Font choices lost in long message threads",
        ],
        "example_questions": [
            "What ring size do you need?",
            "Which metal would you prefer? (Gold, Silver, Rose Gold, Platinum)",
            "What text would you like engraved?",
            "Do you have a font preference? (Script, Block, Serif)",
            "Any stone or gemstone preference?",
            "Is this for a specific date or occasion?",
        ],
        "meta_description": "Automate custom jewelry order spec collection. ETSAI uses AI to collect ring sizes, engraving text, metal preferences, and more from your Etsy buyers in under 2 minutes.",
    },
    "portrait-artists": {
        "title": "AI Spec Collection for Custom Portrait Orders",
        "headline": "Get reference photos and style preferences in one conversation.",
        "subheadline": "ETSAI collects everything your portrait commissions need — reference photos, style preferences, size, medium, background choices — through AI chat. No more chasing buyers for that one missing photo.",
        "category": "Portraits",
        "pain_points": [
            "Buyers send blurry reference photos days later",
            "Style preferences unclear until you've already started",
            "Background and size details missing from initial order",
            "Multiple rounds of 'can you also include...' messages",
        ],
        "example_questions": [
            "Please share 2-3 clear reference photos",
            "What style are you looking for? (Realistic, Watercolor, Digital, Cartoon)",
            "What size canvas/print do you want?",
            "Any specific background preference?",
            "How many subjects should be included?",
            "Is there a deadline for this portrait?",
        ],
        "meta_description": "Automate custom portrait commission spec collection. ETSAI uses AI to collect reference photos, style preferences, and sizing from your buyers in under 2 minutes.",
    },
    "sign-makers": {
        "title": "AI Spec Collection for Custom Sign Orders",
        "headline": "Nail down text, font, size, and finish in 90 seconds.",
        "subheadline": "ETSAI collects every sign spec — exact text, font choice, dimensions, wood type, paint colors, mounting preference — through a single AI chat link. One link, zero back-and-forth.",
        "category": "Signs",
        "pain_points": [
            "Text mistakes caught only after production starts",
            "Font and color combos need 3+ messages to confirm",
            "Custom dimensions missing from personalization box",
            "Mounting preferences forgotten until shipping",
        ],
        "example_questions": [
            "What text would you like on your sign? (Please double-check spelling)",
            "What font style? (Farmhouse Script, Modern Sans, Bold Block)",
            "What dimensions do you need?",
            "Preferred wood type? (Pine, Oak, Walnut, Birch)",
            "What paint colors for text and background?",
            "How will you mount this? (Sawtooth hanger, Stand, Rope)",
        ],
        "meta_description": "Automate custom sign order spec collection. ETSAI uses AI to collect text, fonts, dimensions, and finish preferences from your Etsy buyers in under 2 minutes.",
    },
    "wedding-vendors": {
        "title": "AI Spec Collection for Wedding Custom Orders",
        "headline": "Collect every wedding detail before the deadline hits.",
        "subheadline": "Wedding orders have the most specs and the tightest deadlines. ETSAI collects names, dates, colors, quantities, and every personalization detail through AI chat — so nothing gets missed.",
        "category": "Wedding",
        "pain_points": [
            "Name spellings wrong on invitations",
            "Date and venue details arrive last minute",
            "Color swatches exchanged over 5+ messages",
            "Quantity changes after production started",
        ],
        "example_questions": [
            "Names of the couple (exact spelling for printing)",
            "Wedding date and venue name",
            "Color palette / theme",
            "Quantity needed",
            "Any specific text or wording to include?",
            "When do you need this by?",
        ],
        "meta_description": "Automate wedding custom order spec collection. ETSAI uses AI to collect names, dates, color palettes, and personalization details from your clients in under 2 minutes.",
    },
    "pet-products": {
        "title": "AI Spec Collection for Custom Pet Product Orders",
        "headline": "Get pet names, breeds, and sizing without the runaround.",
        "subheadline": "Custom pet products need specific details — pet name, breed, collar size, reference photos, color preferences. ETSAI collects it all through a quick AI chat so you can start creating immediately.",
        "category": "Pet Products",
        "pain_points": [
            "Collar sizes not provided until after production",
            "Pet name spelling needs confirmation",
            "Reference photos for pet portraits arrive late",
            "Breed-specific sizing details missing",
        ],
        "example_questions": [
            "What is your pet's name? (Exact spelling)",
            "What breed is your pet?",
            "Pet's neck/collar measurement in inches",
            "Please share 2-3 clear photos of your pet",
            "Preferred color scheme",
            "Any specific details you'd like included?",
        ],
        "meta_description": "Automate custom pet product spec collection. ETSAI uses AI to collect pet names, sizes, breed details, and reference photos from your Etsy buyers in under 2 minutes.",
    },
    "clothing-sellers": {
        "title": "AI Spec Collection for Custom Clothing Orders",
        "headline": "Sizes, colors, and customization details — collected automatically.",
        "subheadline": "Custom clothing orders need precise measurements, fabric choices, and personalization details. ETSAI collects everything through AI chat — no more size chart confusion or missing embroidery text.",
        "category": "Clothing",
        "pain_points": [
            "Buyers pick wrong size from confusing size charts",
            "Embroidery text and font not specified clearly",
            "Color preferences don't match available options",
            "Custom measurements arrive in wrong format",
        ],
        "example_questions": [
            "What size? (S/M/L/XL or exact measurements)",
            "Preferred color",
            "Text for embroidery/print (exact spelling)",
            "Font style preference",
            "Placement preference (front, back, sleeve)",
            "Any special sizing notes?",
        ],
        "meta_description": "Automate custom clothing order spec collection. ETSAI uses AI to collect sizes, embroidery text, color choices, and measurements from your Etsy buyers in under 2 minutes.",
    },
}


@app.route("/for/<niche>")
def niche_landing(niche):
    """Programmatic SEO landing pages for specific seller niches."""
    page = NICHE_PAGES.get(niche)
    if not page:
        abort(404)
    return render_template("niche_landing.html", page=page, niche=niche)


# =============================================================
# FREE TOOLS (Lead Magnets)
# =============================================================

@app.route("/tools/message-generator", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def message_generator():
    """
    Free tool: generate a custom order message template.
    Seller enters product type → AI generates a copy-paste message template.
    """
    if request.method == "GET":
        return render_template("message_generator.html", result=None)

    product_type = request.form.get("product_type", "").strip()[:200]
    if not product_type:
        flash("Please describe your product.", "error")
        return redirect(url_for("message_generator"))

    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            system="""You generate Etsy seller message templates for collecting custom order specs from buyers.

Given a product type, output a ready-to-paste message template that an Etsy seller can send to buyers after a custom order purchase. The template should:
- Be warm and professional
- List the specific specs/details needed for that product type
- Use [brackets] for fields the seller should customize
- Be under 300 words
- Include a brief greeting and sign-off

Output ONLY the message template text. No explanation, no markdown formatting.""",
            messages=[{"role": "user", "content": f"Generate a custom order spec collection message template for: {product_type}"}],
        )
        result = response.content[0].text.strip()
    except Exception as e:
        logger.error("Message generator AI error: %s", e)
        result = None
        flash("Could not generate template right now. Please try again.", "error")

    return render_template("message_generator.html", result=result, product_type=product_type)


# =============================================================
# ERROR HANDLERS
# =============================================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500


# =============================================================
# HEALTH CHECK
# =============================================================

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "etsai"})


# =============================================================
# RUN
# =============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    logger.info("ETSAI — AI Spec Collection for Etsy Sellers")
    logger.info("http://localhost:%d", port)
    app.run(host="0.0.0.0", port=port, debug=debug)
