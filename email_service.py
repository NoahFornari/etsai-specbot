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
