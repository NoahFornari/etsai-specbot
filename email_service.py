"""
ETSAI Email Service
Sends notifications to sellers via SMTP. Fails silently if not configured.
"""
import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "")


def _is_configured():
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASS and SMTP_FROM)


def _send_email(to_email, subject, html_body):
    if not _is_configured():
        logger.warning("SMTP not configured — skipping email to %s", to_email)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"ETSAI <{SMTP_FROM}>"
    msg["To"] = to_email
    msg["Reply-To"] = os.environ.get("SMTP_REPLY_TO", SMTP_FROM)
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_FROM, to_email, msg.as_string())
        logger.info("Email sent to %s: %s", to_email, subject)
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, e)
        return False


def send_completion_email(order, base_url):
    """Send spec completion summary to the seller."""
    to_email = order.get("seller_email")
    if not to_email:
        return False

    product = order.get("product_title", "Unknown product")
    buyer = order.get("buyer_name") or order.get("buyer_email") or "A buyer"
    order_url = f"{base_url}/orders/{order['id']}"

    specs_html = ""
    for q in order.get("intake_questions", []):
        field = q.get("field_name", "unknown")
        answer = order.get("customer_specs", {}).get(field, "")
        if answer:
            specs_html += f"<tr><td style='padding:6px 12px;color:#78716c;font-size:13px;'>{q['question']}</td><td style='padding:6px 12px;font-weight:600;font-size:13px;'>{answer}</td></tr>"

    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:520px;margin:0 auto;color:#2c1810;">
        <div style="background:linear-gradient(135deg,#4a6741,#5c7d52);padding:20px 24px;border-radius:12px 12px 0 0;">
            <h1 style="color:white;font-size:18px;margin:0;">Specs Complete!</h1>
        </div>
        <div style="border:1px solid #e6dfd6;border-top:none;border-radius:0 0 12px 12px;padding:20px 24px;">
            <p style="margin:0 0 8px;font-size:14px;"><strong>{buyer}</strong> finished their specs for <strong>{product}</strong>.</p>
            <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                {specs_html}
            </table>
            <a href="{order_url}" style="display:inline-block;background:#4a6741;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;font-size:14px;font-weight:600;">View Order</a>
        </div>
    </div>
    """

    return _send_email(to_email, f"Specs complete: {product} — {buyer}", html)


def send_escalation_email(order, reason, base_url):
    """Alert seller that an order needs human attention."""
    to_email = order.get("seller_email")
    if not to_email:
        return False

    product = order.get("product_title", "Unknown product")
    buyer = order.get("buyer_name") or order.get("buyer_email") or "A buyer"
    order_url = f"{base_url}/orders/{order['id']}"

    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:520px;margin:0 auto;color:#2c1810;">
        <div style="background:#dc2626;padding:20px 24px;border-radius:12px 12px 0 0;">
            <h1 style="color:white;font-size:18px;margin:0;">Order Needs Attention</h1>
        </div>
        <div style="border:1px solid #e6dfd6;border-top:none;border-radius:0 0 12px 12px;padding:20px 24px;">
            <p style="margin:0 0 8px;font-size:14px;">The conversation with <strong>{buyer}</strong> about <strong>{product}</strong> has been escalated.</p>
            <p style="margin:0 0 16px;font-size:13px;color:#78716c;"><strong>Reason:</strong> {reason}</p>
            <a href="{order_url}" style="display:inline-block;background:#dc2626;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;font-size:14px;font-weight:600;">View Order</a>
        </div>
    </div>
    """

    return _send_email(to_email, f"Escalated: {product} — {buyer}", html)


def send_welcome_email(to_email, shop_name, base_url):
    """Send immediately on signup."""
    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:520px;margin:0 auto;color:#2c1810;">
        <div style="background:linear-gradient(135deg,#4a6741,#5c7d52);padding:20px 24px;border-radius:12px 12px 0 0;">
            <h1 style="color:white;font-size:18px;margin:0;">Welcome to ETSAI, {shop_name}!</h1>
        </div>
        <div style="border:1px solid #e6dfd6;border-top:none;border-radius:0 0 12px 12px;padding:20px 24px;">
            <p style="margin:0 0 12px;font-size:14px;">You're in. Your 14-day free trial just started.</p>
            <p style="margin:0 0 12px;font-size:14px;">ETSAI replaces back-and-forth Etsy messages with a single AI-powered intake link. Your buyers chat with the AI, it collects every spec, and you get a clean summary.</p>
            <p style="margin:0 0 4px;font-size:14px;font-weight:600;">Here's how to get started:</p>
            <ol style="margin:0 0 16px;padding-left:20px;font-size:14px;color:#78716c;">
                <li style="margin-bottom:6px;">Create your first product with intake questions</li>
                <li style="margin-bottom:6px;">Copy the intake link</li>
                <li style="margin-bottom:6px;">Paste it in your Etsy listing or send it to buyers</li>
            </ol>
            <a href="{base_url}/dashboard" style="display:inline-block;background:#4a6741;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;font-size:14px;font-weight:600;">Go to Dashboard</a>
            <p style="margin:16px 0 0;font-size:12px;color:#78716c;">Questions? Just reply to this email.</p>
        </div>
    </div>
    """
    return _send_email(to_email, f"Welcome to ETSAI, {shop_name}!", html)


def send_product_reminder_email(to_email, shop_name, base_url):
    """Day 2 — remind them to create their first product."""
    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:520px;margin:0 auto;color:#2c1810;">
        <div style="background:linear-gradient(135deg,#4a6741,#5c7d52);padding:20px 24px;border-radius:12px 12px 0 0;">
            <h1 style="color:white;font-size:18px;margin:0;">Set up your first product</h1>
        </div>
        <div style="border:1px solid #e6dfd6;border-top:none;border-radius:0 0 12px 12px;padding:20px 24px;">
            <p style="margin:0 0 12px;font-size:14px;">Hey {shop_name} — just checking in.</p>
            <p style="margin:0 0 12px;font-size:14px;">The fastest way to see ETSAI in action is to create a product with 3-5 intake questions. Things like size, color, engraving text — whatever you normally ask buyers.</p>
            <p style="margin:0 0 16px;font-size:14px;">Once you create it, you'll get an intake link you can paste right into your Etsy listings. Buyers click it, chat with the AI, and you get clean specs without the back-and-forth.</p>
            <a href="{base_url}/products/new" style="display:inline-block;background:#4a6741;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;font-size:14px;font-weight:600;">Create a Product</a>
        </div>
    </div>
    """
    return _send_email(to_email, f"{shop_name}, create your first intake link", html)


def send_tips_email(to_email, shop_name, base_url):
    """Day 5 — tips for getting the most out of intake links."""
    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:520px;margin:0 auto;color:#2c1810;">
        <div style="background:linear-gradient(135deg,#4a6741,#5c7d52);padding:20px 24px;border-radius:12px 12px 0 0;">
            <h1 style="color:white;font-size:18px;margin:0;">3 tips from top sellers</h1>
        </div>
        <div style="border:1px solid #e6dfd6;border-top:none;border-radius:0 0 12px 12px;padding:20px 24px;">
            <p style="margin:0 0 12px;font-size:14px;">Hey {shop_name} — here's what sellers getting the best results do:</p>
            <p style="margin:0 0 4px;font-size:14px;font-weight:600;">1. Put the link in your listing description</p>
            <p style="margin:0 0 12px;font-size:13px;color:#78716c;">Add something like "Click here to submit your custom order details" right above your FAQ section.</p>
            <p style="margin:0 0 4px;font-size:14px;font-weight:600;">2. Use it in your first message to buyers</p>
            <p style="margin:0 0 12px;font-size:13px;color:#78716c;">When someone messages about a custom order, send the link. The AI handles the rest.</p>
            <p style="margin:0 0 4px;font-size:14px;font-weight:600;">3. Add seller notes for context</p>
            <p style="margin:0 0 16px;font-size:13px;color:#78716c;">Tell the AI what materials you work with, typical turnaround times, etc. It'll give better answers.</p>
            <a href="{base_url}/dashboard" style="display:inline-block;background:#4a6741;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;font-size:14px;font-weight:600;">Open Dashboard</a>
        </div>
    </div>
    """
    return _send_email(to_email, "3 tips to get more from ETSAI", html)


def send_trial_expiring_email(to_email, shop_name, base_url):
    """Day 12 — trial expiring in 2 days."""
    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:520px;margin:0 auto;color:#2c1810;">
        <div style="background:#dc7a2e;padding:20px 24px;border-radius:12px 12px 0 0;">
            <h1 style="color:white;font-size:18px;margin:0;">Your trial ends in 2 days</h1>
        </div>
        <div style="border:1px solid #e6dfd6;border-top:none;border-radius:0 0 12px 12px;padding:20px 24px;">
            <p style="margin:0 0 12px;font-size:14px;">Hey {shop_name} — your 14-day ETSAI trial wraps up in 2 days.</p>
            <p style="margin:0 0 12px;font-size:14px;">After that, your intake links will stop working and buyers won't be able to submit specs.</p>
            <p style="margin:0 0 16px;font-size:14px;">Plans start at $19/mo. Pick one to keep your links live and your orders flowing.</p>
            <a href="{base_url}/billing" style="display:inline-block;background:#4a6741;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;font-size:14px;font-weight:600;">Choose a Plan</a>
            <p style="margin:16px 0 0;font-size:12px;color:#78716c;">Not ready? No worries — reply and let us know what's holding you back.</p>
        </div>
    </div>
    """
    return _send_email(to_email, f"{shop_name}, your ETSAI trial ends in 2 days", html)


def send_password_reset_email(to_email, reset_url):
    """Send password reset link to seller."""
    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:520px;margin:0 auto;color:#2c1810;">
        <div style="background:linear-gradient(135deg,#4a6741,#5c7d52);padding:20px 24px;border-radius:12px 12px 0 0;">
            <h1 style="color:white;font-size:18px;margin:0;">Reset Your Password</h1>
        </div>
        <div style="border:1px solid #e6dfd6;border-top:none;border-radius:0 0 12px 12px;padding:20px 24px;">
            <p style="margin:0 0 16px;font-size:14px;">We received a request to reset your ETSAI password. Click the button below to set a new one.</p>
            <a href="{reset_url}" style="display:inline-block;background:#4a6741;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;font-size:14px;font-weight:600;">Reset Password</a>
            <p style="margin:16px 0 0;font-size:12px;color:#78716c;">This link expires in 1 hour. If you didn't request this, you can safely ignore this email.</p>
        </div>
    </div>
    """
    return _send_email(to_email, "Reset your ETSAI password", html)
