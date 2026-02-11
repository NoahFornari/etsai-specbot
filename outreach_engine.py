"""
ETSAI Outreach Personalizer
Takes a lead CSV from lead_scraper.py, uses Claude Haiku to generate
personalized outreach messages, and outputs an enriched CSV ready for
import into Instantly.ai or other email outreach tools.

Usage:
    python outreach_engine.py leads.csv                     # Default: email sequence
    python outreach_engine.py leads.csv --channel dm        # Instagram DM style
    python outreach_engine.py leads.csv --tier HOT          # Only HOT leads
    python outreach_engine.py leads.csv --limit 100         # First 100 leads
    python outreach_engine.py leads.csv --preview 5         # Preview 5 messages, no CSV
"""
import argparse
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("outreach_engine")

# ---------------------------------------------------------------------------
# Claude client
# ---------------------------------------------------------------------------

client = None


def _get_client():
    global client
    if client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            log.error("ANTHROPIC_API_KEY not set in environment or .env")
            sys.exit(1)
        client = Anthropic(api_key=api_key)
    return client


# ---------------------------------------------------------------------------
# Message templates (system prompts by channel)
# ---------------------------------------------------------------------------

EMAIL_SYSTEM = """You are a cold email copywriter for ETSAI, an AI tool that helps Etsy sellers collect custom order specifications from buyers through an intelligent chat interface (instead of messy Etsy messages back-and-forth).

Your job: write a short, personalized cold email to an Etsy seller. The email should feel like it's from a fellow Etsy seller / small business owner, NOT a salesperson.

Rules:
- First line must reference something specific about their shop (name, niche, a product)
- Ask a genuine question about their custom order workflow — don't pitch yet
- Keep it under 80 words total
- Conversational, lowercase-okay tone. No corporate speak.
- No emojis
- Sign off as "Noah" (founder of ETSAI)
- Do NOT include a subject line
- Do NOT mention pricing or plans
- The goal is to start a conversation, not close a sale

Output format: Just the email body text. Nothing else."""

DM_SYSTEM = """You are writing a short Instagram/social DM to an Etsy seller for ETSAI, an AI tool that helps Etsy sellers collect custom order specs from buyers through a smart chat link.

Rules:
- Ultra short: 2-3 sentences max
- Reference their shop or what they sell
- Ask one specific question about how they handle custom order details
- Casual, friendly tone — like a fellow maker reaching out
- No emojis
- Do NOT pitch the product in the first message
- Do NOT mention pricing

Output format: Just the DM text. Nothing else."""

FOLLOWUP_SYSTEM = """You are writing a follow-up email for ETSAI outreach. The prospect didn't reply to the first email.

Rules:
- Reference the first email briefly ("I reached out last week about...")
- Share one specific value point: "I built a tool that turns the spec collection for custom orders into a 90-second AI chat link"
- Include a soft CTA: "happy to show you a 30-second demo if you're curious"
- Under 60 words
- Sign off as "Noah"

Output format: Just the email body text. Nothing else."""


# ---------------------------------------------------------------------------
# Personalization generation
# ---------------------------------------------------------------------------

def generate_personalization(lead, channel="email"):
    """
    Generate a personalized outreach message for a lead.

    Args:
        lead: dict with shop_name, niche, sample_listings, etc.
        channel: "email", "dm", or "followup"

    Returns:
        str: The personalized message
    """
    system_prompt = {
        "email": EMAIL_SYSTEM,
        "dm": DM_SYSTEM,
        "followup": FOLLOWUP_SYSTEM,
    }.get(channel, EMAIL_SYSTEM)

    # Build context about the lead
    context_parts = [f"Shop: {lead.get('shop_name', 'Unknown')}"]

    if lead.get("niche"):
        context_parts.append(f"Niche: {lead['niche']}")

    if lead.get("sample_listings"):
        context_parts.append(f"Products they sell: {lead['sample_listings']}")

    if lead.get("sales_count"):
        sales = lead["sales_count"]
        if isinstance(sales, str):
            try:
                sales = int(sales)
            except ValueError:
                sales = 0
        if sales > 0:
            context_parts.append(f"Sales count: {sales:,}")

    if lead.get("owner_name"):
        context_parts.append(f"Owner name: {lead['owner_name']}")

    if lead.get("location"):
        context_parts.append(f"Location: {lead['location']}")

    if lead.get("custom_listing_pct"):
        pct = lead["custom_listing_pct"]
        if isinstance(pct, str):
            try:
                pct = float(pct)
            except ValueError:
                pct = 0
        if pct > 0:
            context_parts.append(f"~{pct:.0f}% of their listings are custom/personalized")

    user_msg = "Write a personalized message for this Etsy seller:\n\n" + "\n".join(context_parts)

    try:
        response = _get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=system_prompt,
            messages=[{"role": "user", "content": user_msg}],
        )
        return response.content[0].text.strip()
    except Exception as e:
        log.error(f"API error for {lead.get('shop_name', '?')}: {e}")
        return ""


# ---------------------------------------------------------------------------
# Subject line generation
# ---------------------------------------------------------------------------

SUBJECT_SYSTEM = """Generate a cold email subject line for an Etsy seller. The subject should:
- Be 4-8 words
- Feel personal and curiosity-driven
- NOT mention the product name (ETSAI)
- NOT be clickbait
- Reference their shop or custom orders naturally

Output format: Just the subject line. Nothing else. No quotes."""


def generate_subject(lead):
    """Generate a personalized email subject line."""
    context = f"Shop: {lead.get('shop_name', '')}, Niche: {lead.get('niche', '')}"
    if lead.get("sample_listings"):
        context += f", Products: {lead['sample_listings']}"

    try:
        response = _get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=50,
            system=SUBJECT_SYSTEM,
            messages=[{"role": "user", "content": context}],
        )
        return response.content[0].text.strip().strip('"\'')
    except Exception as e:
        log.error(f"Subject gen error: {e}")
        return f"Quick question about {lead.get('shop_name', 'your shop')}"


# ---------------------------------------------------------------------------
# Batch processing
# ---------------------------------------------------------------------------

def process_leads(input_csv, channel="email", tier_filter=None, limit=None,
                  preview=None, output_file=None):
    """
    Process a lead CSV and generate personalized outreach messages.
    """
    # Read leads
    leads = []
    with open(input_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if tier_filter and row.get("tier") != tier_filter:
                continue
            leads.append(row)

    if limit:
        leads = leads[:limit]

    if not leads:
        log.error("No leads found matching criteria")
        return

    log.info(f"Processing {len(leads)} leads (channel: {channel})")

    # Preview mode
    if preview:
        leads = leads[:preview]
        log.info(f"\n{'='*60}")
        log.info(f"PREVIEW MODE — Generating {len(leads)} sample messages")
        log.info(f"{'='*60}\n")

        for i, lead in enumerate(leads):
            msg = generate_personalization(lead, channel)
            subject = generate_subject(lead) if channel == "email" else ""

            print(f"\n--- Lead {i+1}: {lead.get('shop_name', '?')} ({lead.get('niche', '?')}) ---")
            print(f"Score: {lead.get('score', '?')} | Tier: {lead.get('tier', '?')}")
            if subject:
                print(f"Subject: {subject}")
            print(f"\n{msg}\n")

            if i < len(leads) - 1:
                time.sleep(0.5)  # Small delay between API calls

        return

    # Full processing
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"outreach_{channel}_{timestamp}.csv"

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_file)

    # Determine output fields based on channel
    if channel == "email":
        fieldnames = [
            "shop_name", "niche", "tier", "score", "email",
            "owner_name", "subject_line", "email_body", "followup_body",
            "shop_url", "instagram",
        ]
    elif channel == "dm":
        fieldnames = [
            "shop_name", "niche", "tier", "score",
            "instagram", "owner_name", "dm_message",
            "shop_url",
        ]
    else:
        fieldnames = [
            "shop_name", "niche", "tier", "score",
            "message", "shop_url",
        ]

    generated = 0
    errors = 0

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for i, lead in enumerate(leads):
            try:
                # Generate primary message
                msg = generate_personalization(lead, channel)
                if not msg:
                    errors += 1
                    continue

                row = {
                    "shop_name": lead.get("shop_name", ""),
                    "niche": lead.get("niche", ""),
                    "tier": lead.get("tier", ""),
                    "score": lead.get("score", ""),
                    "owner_name": lead.get("owner_name", ""),
                    "shop_url": lead.get("shop_url", ""),
                    "instagram": lead.get("instagram", ""),
                    "email": lead.get("email", ""),
                }

                if channel == "email":
                    row["subject_line"] = generate_subject(lead)
                    row["email_body"] = msg
                    # Generate follow-up
                    followup = generate_personalization(lead, "followup")
                    row["followup_body"] = followup
                elif channel == "dm":
                    row["dm_message"] = msg
                else:
                    row["message"] = msg

                writer.writerow(row)
                generated += 1

                # Progress logging
                if generated % 10 == 0:
                    log.info(f"  Generated {generated}/{len(leads)} messages...")

                # Rate limiting — don't hammer the API
                time.sleep(0.3)

            except Exception as e:
                log.error(f"Error processing {lead.get('shop_name', '?')}: {e}")
                errors += 1

    # Summary
    log.info("=" * 60)
    log.info(f"DONE! {generated} messages saved to {output_file}")
    if errors > 0:
        log.info(f"  Errors: {errors}")
    log.info(f"  Channel: {channel}")

    # Cost estimate
    # Haiku: ~$0.001 per 1K input tokens, ~$0.005 per 1K output tokens
    # Rough estimate: ~300 input + 150 output tokens per message
    est_cost = generated * 0.001  # Very rough
    if channel == "email":
        est_cost *= 3  # Subject + body + followup
    log.info(f"  Est. API cost: ~${est_cost:.2f}")
    log.info("=" * 60)

    return output_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ETSAI Outreach Personalizer — Generate personalized messages for Etsy seller leads"
    )
    parser.add_argument(
        "input_csv",
        help="Path to lead CSV from lead_scraper.py",
    )
    parser.add_argument(
        "--channel",
        choices=["email", "dm", "followup"],
        default="email",
        help="Message channel/style (default: email)",
    )
    parser.add_argument(
        "--tier",
        choices=["HOT", "WARM", "COLD"],
        default=None,
        help="Only process leads of this tier",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max number of leads to process",
    )
    parser.add_argument(
        "--preview",
        type=int,
        default=None,
        help="Preview N messages without saving (prints to console)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV filename",
    )

    args = parser.parse_args()

    if not os.path.exists(args.input_csv):
        log.error(f"Input file not found: {args.input_csv}")
        sys.exit(1)

    process_leads(
        input_csv=args.input_csv,
        channel=args.channel,
        tier_filter=args.tier,
        limit=args.limit,
        preview=args.preview,
        output_file=args.output,
    )


if __name__ == "__main__":
    main()
