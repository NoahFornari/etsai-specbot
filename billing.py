"""
ETSAI Billing — Stripe integration for subscription management.

Plans:
  - free:     14-day trial, 10 orders/mo, 3 products
  - starter:  $29/mo, 50 orders/mo, 15 products
  - pro:      $59/mo, 250 orders/mo, unlimited products
  - business: $119/mo, 1000 orders/mo, unlimited products, white-label, API access
"""
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("etsai.billing")

# --- Plan definitions ---
PLANS = {
    "free": {
        "name": "Free Trial",
        "price": 0,
        "orders_per_month": 10,
        "max_products": 3,
        "white_label": False,
        "api_access": False,
        "trial_days": 14,
        "stripe_price_id": None,
    },
    "starter": {
        "name": "Starter",
        "price": 29,
        "orders_per_month": 50,
        "max_products": 15,
        "white_label": False,
        "api_access": False,
        "trial_days": 0,
        "stripe_price_id": os.environ.get("STRIPE_PRICE_STARTER"),
    },
    "pro": {
        "name": "Pro",
        "price": 59,
        "orders_per_month": 250,
        "max_products": -1,  # unlimited
        "white_label": False,
        "api_access": True,
        "trial_days": 0,
        "stripe_price_id": os.environ.get("STRIPE_PRICE_PRO"),
    },
    "business": {
        "name": "Business",
        "price": 119,
        "orders_per_month": 1000,
        "max_products": -1,  # unlimited
        "white_label": True,
        "api_access": True,
        "trial_days": 0,
        "stripe_price_id": os.environ.get("STRIPE_PRICE_BUSINESS"),
    },
}


def get_plan(plan_key):
    """Get plan config by key. Returns free plan if key is invalid."""
    if plan_key not in PLANS:
        logger.warning("Unknown plan key '%s', falling back to free", plan_key)
    return PLANS.get(plan_key, PLANS["free"])


def get_stripe():
    """Lazy-load stripe module. Returns None if not configured."""
    stripe_key = os.environ.get("STRIPE_SECRET_KEY")
    if not stripe_key:
        logger.warning("STRIPE_SECRET_KEY not set — billing disabled")
        return None
    try:
        import stripe
        stripe.api_key = stripe_key
        return stripe
    except ImportError:
        logger.error("stripe package not installed — run: pip install stripe")
        return None


def create_checkout_session(seller, plan_key, success_url, cancel_url):
    """Create a Stripe Checkout session for upgrading to a paid plan."""
    stripe = get_stripe()
    if not stripe:
        raise RuntimeError("Stripe not configured")

    plan = PLANS.get(plan_key)
    if not plan or not plan["stripe_price_id"]:
        raise ValueError(f"Invalid plan: {plan_key}")

    # Get or create Stripe customer
    customer_id = seller.get("stripe_customer_id")
    if not customer_id:
        customer = stripe.Customer.create(
            email=seller["email"],
            name=seller["shop_name"],
            metadata={"etsai_seller_id": seller["id"]},
        )
        customer_id = customer.id
        # Save customer ID (caller must persist this)

    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": plan["stripe_price_id"], "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"etsai_seller_id": seller["id"], "plan": plan_key},
        subscription_data={"metadata": {"etsai_seller_id": seller["id"], "plan": plan_key}},
    )

    return session.url, customer_id


def create_portal_session(stripe_customer_id, return_url):
    """Create a Stripe Customer Portal session for managing subscription."""
    stripe = get_stripe()
    if not stripe:
        raise RuntimeError("Stripe not configured")

    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=return_url,
    )
    return session.url


def handle_webhook_event(payload, sig_header):
    """Process a Stripe webhook event. Returns (event_type, data) or raises."""
    stripe = get_stripe()
    if not stripe:
        raise RuntimeError("Stripe not configured")

    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    if not webhook_secret:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET not set")

    event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    return event


def check_trial_active(seller):
    """Check if a free-plan seller is still within their trial period."""
    if seller.get("plan", "free") != "free":
        return True  # paid plans don't have trials

    trial_ends = seller.get("trial_ends_at")
    if not trial_ends:
        return True  # no trial end set (legacy account, treat as active)

    if isinstance(trial_ends, str):
        trial_ends = datetime.fromisoformat(trial_ends)

    return datetime.now() < trial_ends


def check_quota(seller, monthly_orders, monthly_products):
    """
    Check if seller is within their plan limits.
    Returns (allowed, reason) tuple.
    """
    plan_key = seller.get("plan", "free")
    plan = get_plan(plan_key)

    # Check trial expiry for free plan
    if plan_key == "free" and not check_trial_active(seller):
        return False, "trial_expired"

    # Check order quota
    if monthly_orders > plan["orders_per_month"]:
        return False, "order_limit"

    # Check product quota
    if plan["max_products"] != -1 and monthly_products > plan["max_products"]:
        return False, "product_limit"

    return True, None


def get_usage_display(seller, monthly_orders, monthly_products):
    """Get usage info for display on dashboard/settings."""
    plan_key = seller.get("plan", "free")
    plan = get_plan(plan_key)

    order_limit = plan["orders_per_month"]
    product_limit = plan["max_products"]

    result = {
        "plan_key": plan_key,
        "plan_name": plan["name"],
        "plan_price": plan["price"],
        "orders_used": monthly_orders,
        "orders_limit": order_limit,
        "orders_pct": min(100, int((monthly_orders / order_limit) * 100)) if order_limit > 0 else 0,
        "products_used": monthly_products,
        "products_limit": product_limit,
        "products_unlimited": product_limit == -1,
        "white_label": plan["white_label"],
        "api_access": plan["api_access"],
        "is_free": plan_key == "free",
        "trial_active": check_trial_active(seller),
    }

    # Trial days remaining
    if plan_key == "free":
        trial_ends = seller.get("trial_ends_at")
        if trial_ends:
            if isinstance(trial_ends, str):
                trial_ends = datetime.fromisoformat(trial_ends)
            days_left = max(0, (trial_ends - datetime.now()).days)
            result["trial_days_left"] = days_left
        else:
            result["trial_days_left"] = 14

    return result
