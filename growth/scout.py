"""
ETSAI Growth Bot — Scout Agent
Discovers leads from Etsy search, Reddit, and other sources.
Uses Claude Haiku for intelligent lead scoring.
"""
import json
import logging
import time
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engine import call_claude, AI_MODEL_CHEAP, AI_MODEL_SMART
from growth.growth_db import (
    add_growth_lead, lead_exists, get_lead_count_today,
    update_lead_score, log_agent_action, get_conn,
)
from growth.growth_config import SCOUT_MAX_LEADS_PER_DAY, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET

logger = logging.getLogger("etsai.growth.scout")

# Reuse niche queries from lead_scraper
NICHE_QUERIES = {
    "jewelry": ["custom jewelry", "personalized ring", "custom engraved necklace"],
    "portraits": ["custom portrait", "personalized pet portrait", "commission portrait"],
    "signs": ["custom wood sign", "personalized neon sign", "custom wedding sign"],
    "wedding": ["custom wedding invitations", "personalized wedding gift"],
    "clothing": ["custom embroidered clothing", "personalized jacket"],
    "home_decor": ["custom wall art", "personalized home decor", "custom doormat"],
    "pet_products": ["custom pet collar", "personalized pet tag"],
    "stationery": ["custom stationery", "personalized planner"],
    "leather": ["custom leather wallet", "personalized leather bag"],
    "kids": ["custom baby blanket", "personalized kids gift"],
}

CUSTOM_SIGNALS = [
    "custom", "personalized", "personalised", "made to order",
    "bespoke", "commissioned", "commission", "customized",
    "engraved", "engraving", "monogram", "your text", "your name",
]


# =============================================================
# ETSY SEARCH — API (if key available) + Web Scraping fallback
# =============================================================

def _etsy_api_get(path, params=None):
    """Etsy API GET request (public endpoints, API key only)."""
    import requests
    api_key = os.getenv("ETSY_API_KEY", "")
    if not api_key:
        return None  # Silently return None — caller will try scraping fallback

    url = f"https://openapi.etsy.com/v3{path}"
    headers = {"x-api-key": api_key}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=20)
        if resp.status_code == 429:
            logger.warning("Etsy rate limited, backing off 10s")
            time.sleep(10)
            return None
        if resp.status_code != 200:
            logger.warning(f"Etsy API {resp.status_code}: {resp.text[:200]}")
            return None
        return resp.json()
    except Exception as e:
        logger.error(f"Etsy API error: {e}")
        return None


def _scrape_etsy_search(query, limit=48):
    """Scrape Etsy search results via web (no API key needed)."""
    import requests
    from bs4 import BeautifulSoup

    results = []
    try:
        url = f"https://www.etsy.com/search?q={query.replace(' ', '+')}&explicit=1"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"Etsy scrape returned {resp.status_code}")
            return results

        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract JSON-LD structured data if available
        import json as _json
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = _json.loads(script.string)
                if isinstance(data, dict) and data.get("@type") == "ItemList":
                    for item in data.get("itemListElement", [])[:limit]:
                        listing = item.get("item", item)
                        results.append({
                            "title": listing.get("name", ""),
                            "url": listing.get("url", ""),
                            "shop_name": listing.get("brand", {}).get("name") if isinstance(listing.get("brand"), dict) else "",
                        })
            except Exception:
                continue

        # Fallback: parse listing cards from HTML
        if not results:
            for card in soup.select("div.v2-listing-card, li.wt-list-unstyled")[:limit]:
                link = card.select_one("a.listing-link, a[href*='/listing/']")
                title_el = card.select_one("h3, .v2-listing-card__title, [class*='title']")
                shop_el = card.select_one("p.shop-name, [class*='shop-name'], span[class*='shop']")
                if link:
                    results.append({
                        "title": title_el.get_text(strip=True) if title_el else "",
                        "url": link.get("href", "").split("?")[0],
                        "shop_name": shop_el.get_text(strip=True) if shop_el else "",
                    })

        logger.info(f"Scout: Scraped {len(results)} listings for '{query}'")
    except Exception as e:
        logger.error(f"Etsy scrape error: {e}")

    return results


def _get_shop_details(shop_id):
    """Fetch shop details from Etsy API."""
    data = _etsy_api_get(f"/application/shops/{shop_id}")
    if not data:
        return None
    return {
        "shop_id": data.get("shop_id"),
        "shop_name": data.get("shop_name", ""),
        "sale_count": data.get("transaction_sold_count", 0),
        "review_count": data.get("review_count", 0),
        "review_average": data.get("review_average"),
        "listing_count": data.get("listing_active_count", 0),
        "city": data.get("city", ""),
        "url": data.get("url", ""),
        "is_vacation": data.get("is_vacation", False),
    }


def _scrape_shop_details(shop_name):
    """Scrape basic shop info from Etsy shop page (no API key needed)."""
    import requests
    from bs4 import BeautifulSoup

    try:
        url = f"https://www.etsy.com/shop/{shop_name}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html",
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return {"shop_name": shop_name, "url": url}

        soup = BeautifulSoup(resp.text, "html.parser")
        sale_text = soup.select_one("[class*='sale'], [class*='transaction']")
        sale_count = 0
        if sale_text:
            import re
            m = re.search(r"([\d,]+)\s*sale", sale_text.get_text(), re.IGNORECASE)
            if m:
                sale_count = int(m.group(1).replace(",", ""))

        return {
            "shop_name": shop_name,
            "url": url,
            "sale_count": sale_count,
        }
    except Exception as e:
        logger.error(f"Shop scrape error for {shop_name}: {e}")
        return {"shop_name": shop_name, "url": f"https://www.etsy.com/shop/{shop_name}"}


def discover_etsy_leads(niche, limit=50):
    """Search Etsy for custom order sellers in a niche. Uses API if available, scraping if not."""
    start = time.time()
    queries = NICHE_QUERIES.get(niche, [f"custom {niche}"])
    shops = {}
    use_api = bool(os.getenv("ETSY_API_KEY", ""))

    for query in queries:
        if use_api:
            # API path
            data = _etsy_api_get("/application/listings/active", {
                "keywords": query, "limit": min(limit, 100), "sort_on": "score"
            })
            if data:
                for listing in data.get("results", []):
                    shop_id = listing.get("shop_id")
                    if not shop_id or shop_id in shops:
                        continue
                    title = listing.get("title", "")
                    is_personalizable = listing.get("is_personalizable", False)
                    has_custom = any(s in title.lower() for s in CUSTOM_SIGNALS) or is_personalizable
                    if has_custom:
                        shops[shop_id] = {
                            "shop_id": shop_id,
                            "sample_listing": title,
                            "is_personalizable": is_personalizable,
                            "niche": niche,
                        }
        else:
            # Scraping fallback (no API key)
            scraped = _scrape_etsy_search(query, limit=min(limit, 48))
            for item in scraped:
                title = item.get("title", "")
                shop_name = item.get("shop_name", "")
                listing_url = item.get("url", "")
                has_custom = any(s in title.lower() for s in CUSTOM_SIGNALS)
                if has_custom and shop_name and shop_name not in shops:
                    shops[shop_name] = {
                        "shop_name": shop_name,
                        "sample_listing": title,
                        "listing_url": listing_url,
                        "niche": niche,
                    }

        time.sleep(0.5)

    # Enrich and save leads
    leads_added = 0
    for key, shop_data in shops.items():
        if get_lead_count_today("etsy") >= SCOUT_MAX_LEADS_PER_DAY:
            logger.info("Scout: daily lead quota reached")
            break

        if use_api:
            details = _get_shop_details(key)
            if not details or details.get("is_vacation"):
                continue
            shop_url = details.get("url") or f"https://www.etsy.com/shop/{details.get('shop_name', '')}"
            shop_name = details.get("shop_name", "")
            sale_count = details.get("sale_count", 0)
            review_count = details.get("review_count", 0)
            review_average = details.get("review_average")
            listing_count = details.get("listing_count", 0)
            city = details.get("city")
        else:
            shop_name = shop_data.get("shop_name", key)
            shop_url = f"https://www.etsy.com/shop/{shop_name}"
            # Quick scrape for sale count
            details = _scrape_shop_details(shop_name)
            sale_count = details.get("sale_count", 0)
            review_count = 0
            review_average = None
            listing_count = 0
            city = None

        if lead_exists(shop_url):
            continue

        lead_id = add_growth_lead(
            source="etsy",
            shop_name=shop_name,
            shop_url=shop_url,
            niche=niche,
            sale_count=sale_count,
            review_count=review_count,
            review_average=review_average,
            listing_count=listing_count,
            city=city,
            enrichment_data={"sample_listing": shop_data.get("sample_listing")},
        )
        if lead_id:
            leads_added += 1

        time.sleep(0.5)

    duration_ms = int((time.time() - start) * 1000)
    log_agent_action("scout", f"discover_etsy_{niche}", True,
                     {"leads_added": leads_added, "shops_found": len(shops), "method": "api" if use_api else "scrape"},
                     duration_ms=duration_ms)
    logger.info(f"Scout: Etsy {niche} — {len(shops)} shops found, {leads_added} new leads added ({'API' if use_api else 'scrape'})")
    return leads_added


# =============================================================
# REDDIT DISCOVERY
# =============================================================

def _get_reddit():
    """Get a PRAW Reddit instance. Returns None if not configured."""
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        return None
    try:
        import praw
        return praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            username=os.getenv("REDDIT_USERNAME", ""),
            password=os.getenv("REDDIT_PASSWORD", ""),
            user_agent=os.getenv("REDDIT_USER_AGENT", "ETSAI-GrowthBot/1.0"),
        )
    except ImportError:
        logger.warning("PRAW not installed — skipping Reddit discovery")
        return None
    except Exception as e:
        logger.error(f"Reddit connection error: {e}")
        return None


def discover_reddit_leads(subreddits=None, limit=25):
    """Find Etsy sellers on Reddit who might need ETSAI."""
    reddit = _get_reddit()
    if not reddit:
        return 0

    start = time.time()
    if not subreddits:
        subreddits = ["EtsySellers", "Etsy"]

    leads_added = 0
    for sub_name in subreddits:
        try:
            subreddit = reddit.subreddit(sub_name)
            for post in subreddit.new(limit=limit):
                # Look for sellers talking about custom orders
                text = f"{post.title} {post.selftext}".lower()
                is_relevant = any(kw in text for kw in [
                    "custom order", "personalized", "intake form", "buyer info",
                    "collect details", "order details", "specification",
                ])
                if not is_relevant:
                    continue

                username = str(post.author) if post.author else None
                if not username:
                    continue

                # Deduplicate by reddit username
                from growth.growth_db import get_conn
                conn = get_conn()
                try:
                    existing = conn.execute(
                        "SELECT id FROM growth_leads WHERE reddit_username = %s",
                        (username,)
                    ).fetchone()
                finally:
                    conn.close()

                if existing:
                    continue

                lead_id = add_growth_lead(
                    source="reddit",
                    shop_name=username,
                    reddit_username=username,
                    niche="unknown",
                    enrichment_data={
                        "subreddit": sub_name,
                        "post_title": post.title[:200],
                        "post_url": f"https://reddit.com{post.permalink}",
                    },
                )
                if lead_id:
                    leads_added += 1

        except Exception as e:
            logger.error(f"Reddit scrape error on r/{sub_name}: {e}")

    duration_ms = int((time.time() - start) * 1000)
    log_agent_action("scout", "discover_reddit", True,
                     {"leads_added": leads_added}, duration_ms=duration_ms)
    logger.info(f"Scout: Reddit — {leads_added} new leads from {len(subreddits)} subreddits")
    return leads_added


# =============================================================
# EMAIL / SOCIAL ENRICHMENT FROM ETSY ABOUT PAGES
# =============================================================

def enrich_lead_email(lead_id):
    """
    Scrape the Etsy shop About page for email addresses and social links.
    Updates the lead record if found. Returns dict of found data.
    """
    import re
    import requests
    from bs4 import BeautifulSoup

    conn = get_conn()
    try:
        row = conn.execute("SELECT shop_url, shop_name, email, social_url FROM growth_leads WHERE id = %s", (lead_id,)).fetchone()
    finally:
        conn.close()

    if not row:
        return {}

    lead = dict(row)
    # Skip if already enriched
    if lead.get("email") and lead.get("social_url"):
        return {"email": lead["email"], "social_url": lead["social_url"]}

    shop_name = lead.get("shop_name", "")
    if not shop_name:
        return {}

    found = {}
    try:
        url = f"https://www.etsy.com/shop/{shop_name}/about"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html",
        }
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return {}

        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator=" ")

        # Extract email
        if not lead.get("email"):
            emails = re.findall(r'[\w.\-+]+@[\w.\-]+\.\w{2,}', text)
            # Filter out Etsy internal emails
            real_emails = [e for e in emails if "etsy.com" not in e.lower()]
            if real_emails:
                found["email"] = real_emails[0]

        # Extract social links
        if not lead.get("social_url"):
            social_patterns = [
                r'(https?://(?:www\.)?instagram\.com/[\w.]+)',
                r'(https?://(?:www\.)?facebook\.com/[\w.]+)',
                r'(https?://(?:www\.)?twitter\.com/[\w.]+)',
                r'(https?://(?:www\.)?tiktok\.com/@[\w.]+)',
            ]
            for link in soup.find_all("a", href=True):
                href = link["href"]
                for pattern in social_patterns:
                    match = re.match(pattern, href)
                    if match:
                        found["social_url"] = match.group(1)
                        break
                if found.get("social_url"):
                    break

        # Update DB
        if found:
            conn = get_conn()
            try:
                updates = []
                params = []
                if found.get("email"):
                    updates.append("email = %s")
                    params.append(found["email"])
                if found.get("social_url"):
                    updates.append("social_url = %s")
                    params.append(found["social_url"])
                if updates:
                    params.append(lead_id)
                    conn.execute(
                        f"UPDATE growth_leads SET {', '.join(updates)} WHERE id = %s",
                        params
                    )
                    conn.commit()
            finally:
                conn.close()

        logger.info(f"Scout: Enriched {shop_name} — found: {list(found.keys()) or 'nothing'}")
    except Exception as e:
        logger.error(f"Enrichment error for {shop_name}: {e}")

    return found


def enrich_scored_leads(limit=20):
    """Enrich HOT/WARM leads that haven't been enriched yet."""
    conn = get_conn()
    try:
        rows = conn.execute("""
            SELECT id FROM growth_leads
            WHERE tier IN ('HOT', 'WARM')
              AND email IS NULL AND social_url IS NULL
            ORDER BY score DESC LIMIT %s
        """, (limit,)).fetchall()
    finally:
        conn.close()

    enriched = 0
    for row in rows:
        result = enrich_lead_email(row["id"])
        if result:
            enriched += 1
        time.sleep(1)  # Rate limit: 1 req/sec

    if enriched:
        log_agent_action("scout", "enrich_leads", True, {"enriched": enriched, "checked": len(rows)})
        logger.info(f"Scout: Enriched {enriched}/{len(rows)} leads")
    return enriched


# =============================================================
# CLAUDE-POWERED LEAD SCORING
# =============================================================

def score_lead(lead_data):
    """
    Use Claude Haiku to score a lead 0-100 and generate an outreach angle.
    Returns (score, tier, outreach_angle, cost).
    """
    context_parts = []
    if lead_data.get("shop_name"):
        context_parts.append(f"Shop: {lead_data['shop_name']}")
    if lead_data.get("niche"):
        context_parts.append(f"Niche: {lead_data['niche']}")
    if lead_data.get("sale_count"):
        context_parts.append(f"Sales: {lead_data['sale_count']:,}")
    if lead_data.get("review_count"):
        context_parts.append(f"Reviews: {lead_data['review_count']} (avg: {lead_data.get('review_average', 'N/A')})")
    if lead_data.get("listing_count"):
        context_parts.append(f"Active listings: {lead_data['listing_count']}")
    if lead_data.get("custom_pct"):
        context_parts.append(f"Custom listing %: {lead_data['custom_pct']}%")
    if lead_data.get("city"):
        context_parts.append(f"Location: {lead_data['city']}")

    enrichment = lead_data.get("enrichment_data", {})
    if isinstance(enrichment, str):
        enrichment = json.loads(enrichment)
    if enrichment.get("sample_listing"):
        context_parts.append(f"Sample product: {enrichment['sample_listing']}")

    prompt = f"""Score this Etsy seller as a potential customer for ETSAI (an AI tool that collects custom order specs from buyers via a smart chat link).

LEAD DATA:
{chr(10).join(context_parts)}

Score 0-100 based on:
- Custom order volume (sellers with many custom/personalized items need ETSAI more)
- Business maturity (enough sales to benefit from automation, but not so big they have their own systems)
- Sweet spot: 50-5000 sales, high custom %, active shop

Also suggest a personalized outreach angle — one sentence about why ETSAI would help THIS specific seller.

RESPOND IN JSON:
{{"score": 72, "tier": "HOT", "angle": "With 200+ custom jewelry orders, you're probably spending hours just collecting ring sizes and engraving text — that's exactly what ETSAI automates."}}

Tier rules: HOT (70+), WARM (40-69), COLD (<40).
JSON only."""

    try:
        raw, cost, inp, out = call_claude(prompt, AI_MODEL_CHEAP, max_tokens=200)
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
        parsed = json.loads(clean)

        score = min(max(int(parsed.get("score", 0)), 0), 100)
        tier = parsed.get("tier", "COLD")
        if tier not in ("HOT", "WARM", "COLD"):
            tier = "HOT" if score >= 70 else "WARM" if score >= 40 else "COLD"
        angle = parsed.get("angle", "")

        return score, tier, angle, cost
    except Exception as e:
        logger.error(f"Lead scoring error: {e}")
        # Fallback to basic scoring
        score = _basic_score(lead_data)
        tier = "HOT" if score >= 70 else "WARM" if score >= 40 else "COLD"
        return score, tier, "", 0


def _basic_score(lead):
    """Fallback scoring without AI (same logic as lead_scraper.py)."""
    score = 0
    sales = lead.get("sale_count", 0) or 0
    if sales >= 1000:
        score += 30
    elif sales >= 500:
        score += 25
    elif sales >= 100:
        score += 20
    elif sales >= 50:
        score += 15
    elif sales >= 10:
        score += 8

    if lead.get("custom_pct", 0) >= 50:
        score += 25
    elif lead.get("custom_pct", 0) >= 30:
        score += 20

    rating = lead.get("review_average")
    if rating and rating >= 4.5:
        score += 10

    if (lead.get("listing_count") or 0) >= 50:
        score += 10

    return min(score, 100)


def score_unscored_leads(limit=50):
    """Score leads that haven't been AI-scored yet (score == 0)."""
    from growth.growth_db import get_conn
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM growth_leads WHERE score = 0 ORDER BY created_at ASC LIMIT %s",
            (limit,)
        ).fetchall()
    finally:
        conn.close()

    total_cost = 0
    scored = 0
    hot_warm_ids = []
    for row in rows:
        lead = dict(row)
        lead["enrichment_data"] = json.loads(lead.get("enrichment_data") or "{}")
        score, tier, angle, cost = score_lead(lead)
        update_lead_score(lead["id"], score, tier, angle)
        total_cost += cost
        scored += 1
        if tier in ("HOT", "WARM"):
            hot_warm_ids.append(lead["id"])
        time.sleep(0.2)

    if scored:
        log_agent_action("scout", "score_leads", True,
                         {"scored": scored}, cost=total_cost)
        logger.info(f"Scout: Scored {scored} leads (${total_cost:.4f})")

    # Enrich HOT/WARM leads with email/social data
    if hot_warm_ids:
        enriched = 0
        for lead_id in hot_warm_ids:
            result = enrich_lead_email(lead_id)
            if result:
                enriched += 1
            time.sleep(1)
        if enriched:
            logger.info(f"Scout: Enriched {enriched}/{len(hot_warm_ids)} newly scored leads")

    return scored


# =============================================================
# NICHE TREND ANALYSIS
# =============================================================

def find_trending_niches():
    """Use Claude to analyze what's trending on Etsy for custom orders."""
    prompt = """Based on your knowledge of Etsy trends, what are the TOP 5 trending niches for custom/personalized products right now?

For each niche, provide:
- name: short niche name
- search_queries: 2-3 Etsy search queries to find sellers in this niche
- reasoning: why it's trending

RESPOND IN JSON:
[{"name": "niche", "search_queries": ["query1", "query2"], "reasoning": "why"}]
JSON array only."""

    try:
        raw, cost, inp, out = call_claude(prompt, AI_MODEL_CHEAP, max_tokens=500)
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
        niches = json.loads(clean)
        log_agent_action("scout", "find_trending_niches", True,
                         {"niches_found": len(niches)}, cost=cost)
        return niches
    except Exception as e:
        logger.error(f"Trending niche error: {e}")
        return []


# =============================================================
# DAILY TARGET SELECTION
# =============================================================

def get_daily_targets(budget=None):
    """Get prioritized leads to contact today, respecting budget."""
    from growth.growth_db import get_contactable_leads
    from growth.growth_config import DAILY_BUDGET, WRITER_MAX_EMAILS_PER_DAY

    if budget is None:
        budget = DAILY_BUDGET

    leads = get_contactable_leads(limit=WRITER_MAX_EMAILS_PER_DAY)

    # Prioritize: HOT first, then WARM, then by score
    leads.sort(key=lambda l: (
        0 if l.get("tier") == "HOT" else 1 if l.get("tier") == "WARM" else 2,
        -l.get("score", 0)
    ))

    return leads


# =============================================================
# MAIN RUN
# =============================================================

def run(niches=None):
    """Main scout run — called by Commander or scheduler."""
    from growth.growth_config import GROWTH_ENABLED
    if not GROWTH_ENABLED:
        return {"status": "disabled"}

    start = time.time()
    if niches is None:
        niches = list(NICHE_QUERIES.keys())[:3]  # Top 3 niches per run

    total_leads = 0

    # Etsy discovery
    for niche in niches:
        total_leads += discover_etsy_leads(niche, limit=30)

    # Reddit discovery
    total_leads += discover_reddit_leads()

    # Score unscored leads
    scored = score_unscored_leads(limit=30)

    duration_ms = int((time.time() - start) * 1000)
    result = {
        "status": "ok",
        "leads_added": total_leads,
        "leads_scored": scored,
        "niches_searched": niches,
        "duration_ms": duration_ms,
    }
    log_agent_action("scout", "run", True, result, duration_ms=duration_ms)
    return result
