"""
ETSAI Growth Bot — Scout Agent
Discovers leads from Etsy search, Reddit, and other sources.
Uses Claude Haiku for intelligent lead scoring.
"""
import json
import logging
import random
import time
from datetime import datetime
from pathlib import Path

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
# Explicitly load .env from project root so ETSY_API_KEY is always available
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path, override=True)

from ai_engine import call_claude, AI_MODEL_CHEAP, AI_MODEL_SMART
from growth.growth_db import (
    add_growth_lead, lead_exists, get_lead_count_today,
    update_lead_score, log_agent_action, get_conn,
    upsert_learning, get_top_learnings, get_learnings,
)
from growth.growth_config import (
    SCOUT_MAX_LEADS_PER_DAY, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET,
    LEARNING_ENABLED, LEARNING_EXPLORATION_RATE,
)

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

def _etsy_api_get(path, params=None, retries=2):
    """Etsy API GET request with retry + exponential backoff."""
    import requests
    api_key = os.getenv("ETSY_API_KEY", "")
    if not api_key:
        logger.warning("Scout: ETSY_API_KEY not found in environment")
        return None

    url = f"https://openapi.etsy.com/v3{path}"
    headers = {"x-api-key": api_key}

    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=20)
            if resp.status_code == 429:
                wait = 5 * (attempt + 1)
                logger.warning(f"Etsy rate limited (429). Waiting {wait}s...")
                time.sleep(wait)
                continue
            if resp.status_code == 404:
                return None
            if resp.status_code != 200:
                logger.warning(f"Etsy API {resp.status_code}: {resp.text[:200]}")
                if attempt < retries:
                    time.sleep(2 * (attempt + 1))
                    continue
                return None
            return resp.json()
        except Exception as e:
            if attempt < retries:
                logger.warning(f"Etsy API request failed ({e}), retry {attempt + 1}/{retries}")
                time.sleep(3 * (attempt + 1))
            else:
                logger.error(f"Etsy API error after {retries + 1} attempts: {e}")
                return None
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


def _has_custom_signals(listing):
    """Check title, description, tags, and is_personalizable for custom signals."""
    title = (listing.get("title") or "").lower()
    description = (listing.get("description") or "").lower()
    tags = listing.get("tags") or []
    tags_text = " ".join(t.lower() for t in tags)
    is_personalizable = listing.get("is_personalizable", False)

    if is_personalizable:
        return True

    combined = f"{title} {description} {tags_text}"
    return any(s in combined for s in CUSTOM_SIGNALS)


def discover_etsy_leads(niche, limit=50):
    """Search Etsy for custom order sellers in a niche. Uses API if available, scraping if not.
    Supports pagination — fetches up to 3 pages from the API."""
    start = time.time()
    queries = NICHE_QUERIES.get(niche, [f"custom {niche}"])
    shops = {}
    # TODO: Re-enable when Etsy API key is activated
    # use_api = bool(os.getenv("ETSY_API_KEY", ""))
    use_api = False

    for query in queries:
        api_worked = False
        if use_api:
            # API path — paginate up to 3 pages
            page_limit = min(limit, 100)
            for offset in range(0, min(limit, 300), page_limit):
                data = _etsy_api_get("/application/listings/active", {
                    "keywords": query, "limit": page_limit,
                    "offset": offset, "sort_on": "score",
                })
                if not data or not data.get("results"):
                    break

                api_worked = True
                for listing in data.get("results", []):
                    shop_id = listing.get("shop_id")
                    if not shop_id or shop_id in shops:
                        continue
                    if _has_custom_signals(listing):
                        shops[shop_id] = {
                            "shop_id": shop_id,
                            "sample_listing": listing.get("title", ""),
                            "is_personalizable": listing.get("is_personalizable", False),
                            "niche": niche,
                        }

                time.sleep(0.5)

        if not use_api or not api_worked:
            # Scraping fallback — API key missing, inactive, or returned errors
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

        if shop_data.get("shop_id"):
            # We got this from API — try API enrichment, fall back to scrape
            details = _get_shop_details(key)
            if details and not details.get("is_vacation"):
                shop_url = details.get("url") or f"https://www.etsy.com/shop/{details.get('shop_name', '')}"
                shop_name = details.get("shop_name", "")
                sale_count = details.get("sale_count", 0)
                review_count = details.get("review_count", 0)
                review_average = details.get("review_average")
                listing_count = details.get("listing_count", 0)
                city = details.get("city")
            elif details and details.get("is_vacation"):
                continue
            else:
                # API enrichment failed — skip enrichment, save with what we have
                shop_name = f"shop_{key}"
                shop_url = f"https://www.etsy.com/shop/{shop_name}"
                sale_count = review_count = listing_count = 0
                review_average = None
                city = None
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
# REDDIT DISCOVERY — AI-POWERED (no keyword matching)
# =============================================================

# Seller-specific subs: everyone posting here is likely a seller.
# Grab ALL posts, let Claude decide who's worth reaching out to.
SELLER_SUBREDDITS = ["EtsySellers", "Etsy", "craftit", "handmade"]
# Broader subs: lots of noise, but some sellers post here too.
GENERAL_SUBREDDITS = ["smallbusiness", "Entrepreneur", "ecommerce", "sidehustle"]
# Search queries to find sellers actively sharing their shops
SELLER_SEARCH_QUERIES = [
    "my etsy shop",
    "check out my shop",
    "just opened my etsy",
    "custom orders etsy",
    "personalized orders",
    "I make custom",
]


def _fetch_reddit_posts(subreddits, limit=25, sort="new"):
    """Fetch posts from Reddit JSON endpoints. Returns raw post dicts."""
    import requests
    headers = {"User-Agent": "ETSAI-GrowthBot/1.0"}
    all_posts = []

    for sub_name in subreddits:
        try:
            url = f"https://www.reddit.com/r/{sub_name}/{sort}.json?limit={limit}"
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                logger.warning(f"Reddit r/{sub_name} returned {resp.status_code}")
                time.sleep(2)
                continue

            data = resp.json()
            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                author = post.get("author")
                if not author or author in ("[deleted]", "AutoModerator"):
                    continue
                all_posts.append({
                    "subreddit": sub_name,
                    "author": author,
                    "title": post.get("title", ""),
                    "body": (post.get("selftext") or "")[:500],
                    "url": f"https://reddit.com{post.get('permalink', '')}",
                    "flair": post.get("link_flair_text") or post.get("author_flair_text") or "",
                    "score": post.get("score", 0),
                })
            time.sleep(2)  # Unauthenticated rate limit
        except Exception as e:
            logger.error(f"Reddit fetch error r/{sub_name}: {e}")

    return all_posts


def _search_reddit_sellers(limit=10):
    """Search Reddit for sellers actively sharing their Etsy shops."""
    import requests
    headers = {"User-Agent": "ETSAI-GrowthBot/1.0"}
    all_posts = []

    for query in SELLER_SEARCH_QUERIES:
        try:
            url = f"https://www.reddit.com/search.json?q={query.replace(' ', '+')}&sort=new&limit={limit}"
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                time.sleep(2)
                continue

            data = resp.json()
            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                author = post.get("author")
                if not author or author in ("[deleted]", "AutoModerator"):
                    continue
                all_posts.append({
                    "subreddit": post.get("subreddit", "search"),
                    "author": author,
                    "title": post.get("title", ""),
                    "body": (post.get("selftext") or "")[:500],
                    "url": f"https://reddit.com{post.get('permalink', '')}",
                    "flair": post.get("link_flair_text") or post.get("author_flair_text") or "",
                    "score": post.get("score", 0),
                })
            time.sleep(2)
        except Exception as e:
            logger.error(f"Reddit search error for '{query}': {e}")

    return all_posts


def _extract_shop_urls(text):
    """Pull Etsy shop URLs from post text."""
    import re
    patterns = [
        r'(?:https?://)?(?:www\.)?etsy\.com/shop/([\w-]+)',
        r'(?:https?://)?(?:www\.)?etsy\.com/listing/\d+',
        r'(?:https?://)?([\w-]+)\.etsy\.com',
    ]
    shops = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            shops.add(match.group(0))
    return list(shops)


def _classify_leads_batch(posts):
    """Use Claude to classify AND score Reddit posters in one call.
    Determines if they're sellers, what niche, and scores them 0-100.
    Returns list of posts with classification + score added."""

    classified = []
    batch_size = 6

    for i in range(0, len(posts), batch_size):
        batch = posts[i:i + batch_size]

        post_summaries = []
        for idx, p in enumerate(batch):
            shop_urls = _extract_shop_urls(f"{p['title']} {p['body']}")
            shop_str = f" | Shop: {shop_urls[0]}" if shop_urls else ""
            post_summaries.append(
                f"{idx + 1}. [r/{p['subreddit']}] u/{p['author']}: "
                f"{p['title'][:120]}\n   {p['body'][:200]}{shop_str}"
            )

        prompt = f"""Analyze these Reddit posts. For each one, classify AND score as a potential lead.

We help Etsy sellers who do custom/personalized orders. Best leads: small-medium shops (10-2000 sales) doing 50%+ custom work.

POSTS:
{chr(10).join(post_summaries)}

For each post determine:
- is_seller: yes/no/maybe
- does_custom: yes/no/unclear
- niche: jewelry/portraits/signs/wedding/clothing/home_decor/pet_products/stationery/leather/kids/other/unknown
- score: 0-100 lead quality (70+ = HOT, 35-69 = WARM, <35 = COLD)
- angle: one-sentence conversation starter about their custom order process (genuine, curious)

Scoring guide:
- Clearly does custom work + active shop = 60-80
- Maybe does custom + seller = 30-50
- Not a seller or no custom work = 0-20

RESPOND IN JSON array:
[{{"post": 1, "is_seller": "yes", "does_custom": "yes", "niche": "jewelry", "score": 65, "angle": "Love your custom rings — do buyers usually know exactly what they want?"}}]
JSON array only."""

        try:
            raw, cost, inp, out = call_claude(prompt, AI_MODEL_CHEAP, max_tokens=1000)
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            results = json.loads(clean)

            for result in results:
                idx = result.get("post", 0) - 1
                if 0 <= idx < len(batch):
                    post = batch[idx].copy()
                    post["is_seller"] = result.get("is_seller", "no")
                    post["does_custom"] = result.get("does_custom", "no")
                    score = min(max(int(result.get("score", 0)), 0), 100)
                    post["etsai_fit"] = "high" if score >= 60 else "medium" if score >= 35 else "low" if score > 0 else "none"
                    post["niche"] = result.get("niche", "unknown")
                    post["score"] = score
                    post["tier"] = "HOT" if score >= 70 else "WARM" if score >= 35 else "COLD"
                    post["outreach_angle"] = result.get("angle", "")
                    post["shop_urls"] = _extract_shop_urls(
                        f"{post['title']} {post['body']}"
                    )
                    classified.append(post)

            time.sleep(0.3)
        except Exception as e:
            logger.error(f"Scout: batch classification error: {e}")
            continue

    return classified


def _dedup_and_save_leads(classified_posts):
    """Save classified leads to DB, deduplicating by reddit username."""
    leads_added = 0

    for post in classified_posts:
        # Only save sellers with medium+ ETSAI fit
        if post.get("etsai_fit") in ("none", "low"):
            continue
        if post.get("is_seller") == "no":
            continue

        username = post["author"]
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

        if get_lead_count_today("reddit") >= SCOUT_MAX_LEADS_PER_DAY:
            logger.info("Scout: daily Reddit lead quota reached")
            break

        # Use first shop URL if found
        shop_urls = post.get("shop_urls", [])
        shop_url = shop_urls[0] if shop_urls else None

        lead_id = add_growth_lead(
            source="reddit",
            shop_name=username,
            shop_url=shop_url,
            reddit_username=username,
            niche=post.get("niche", "unknown"),
            enrichment_data={
                "subreddit": post["subreddit"],
                "post_title": post["title"][:200],
                "post_url": post["url"],
                "etsai_fit": post.get("etsai_fit"),
                "does_custom": post.get("does_custom"),
                "shop_urls": shop_urls,
                "flair": post.get("flair", ""),
            },
        )
        if lead_id:
            leads_added += 1
            # Apply pre-computed score from classification (skip separate scoring call)
            if post.get("score") and post.get("tier"):
                update_lead_score(lead_id, post["score"], post["tier"], post.get("outreach_angle", ""))

    return leads_added


def discover_reddit_leads(limit=25):
    """AI-powered Reddit lead discovery.
    1. Fetch ALL posts from seller subs (no keyword filter)
    2. Search Reddit for sellers sharing their shops
    3. Batch-classify with Claude: who's a real custom order seller?
    4. Extract Etsy shop URLs from posts
    5. Save qualified leads
    """
    start = time.time()

    # Step 1: Fetch from seller-specific subreddits (everyone's a potential lead)
    logger.info("Scout: Fetching posts from seller subreddits...")
    seller_posts = _fetch_reddit_posts(SELLER_SUBREDDITS, limit=limit)

    # Step 2: Fetch from general subreddits (more noise, fewer posts)
    general_posts = _fetch_reddit_posts(GENERAL_SUBREDDITS, limit=max(limit // 2, 10))

    # Step 3: Search Reddit for sellers actively sharing shops
    logger.info("Scout: Searching Reddit for Etsy sellers...")
    search_posts = _search_reddit_sellers(limit=8)

    # Deduplicate by author before classification
    seen_authors = set()
    unique_posts = []
    for post in seller_posts + general_posts + search_posts:
        if post["author"] not in seen_authors:
            seen_authors.add(post["author"])
            unique_posts.append(post)

    logger.info(f"Scout: {len(unique_posts)} unique posts to classify")

    if not unique_posts:
        duration_ms = int((time.time() - start) * 1000)
        log_agent_action("scout", "discover_reddit", True,
                         {"leads_added": 0, "posts_found": 0}, duration_ms=duration_ms)
        return 0

    # Step 4: AI classification — Claude decides who's a real lead
    logger.info("Scout: Classifying posts with Claude...")
    classified = _classify_leads_batch(unique_posts)

    qualified = [p for p in classified if p.get("etsai_fit") in ("high", "medium")]
    logger.info(f"Scout: {len(qualified)}/{len(classified)} posts qualified as leads")

    # Step 5: Save to DB
    leads_added = _dedup_and_save_leads(classified)

    duration_ms = int((time.time() - start) * 1000)
    log_agent_action("scout", "discover_reddit", True, {
        "leads_added": leads_added,
        "posts_fetched": len(unique_posts),
        "posts_classified": len(classified),
        "qualified": len(qualified),
        "method": "ai_classification",
    }, duration_ms=duration_ms)
    logger.info(f"Scout: Reddit — {leads_added} new leads from {len(unique_posts)} posts (AI classified)")
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

    prompt = f"""Score this Etsy seller as a potential lead for outreach (we help sellers who do custom/personalized orders).

LEAD DATA:
{chr(10).join(context_parts)}

Score 0-100 based on:
- Custom order focus (sellers doing mostly custom/personalized work score highest)
- Active and engaged (good reviews, active listings)
- Sweet spot: 10-5000 sales. Small shops doing 80%+ custom = best leads. Big shops with low custom % = worse.
- Shops with 10-100 sales doing mostly custom work should score 50-70 (they need help the most)

Also suggest a conversation starter — a short, genuine compliment about their shop + one simple question about how they handle custom orders. Keep it natural, like one seller talking to another. No jargon.

RESPOND IN JSON:
{{"score": 65, "tier": "WARM", "angle": "Love your custom jewelry work — do your buyers usually know exactly what they want or do you have to walk them through it?"}}

Tier rules: HOT (70+), WARM (35-69), COLD (<35).
JSON only."""

    try:
        raw, cost, inp, out = call_claude(prompt, AI_MODEL_CHEAP, max_tokens=200)
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
        parsed = json.loads(clean)

        try:
            score = min(max(int(parsed.get("score", 0)), 0), 100)
        except (ValueError, TypeError):
            score = 0
        tier = parsed.get("tier", "COLD")
        if tier not in ("HOT", "WARM", "COLD"):
            tier = "HOT" if score >= 70 else "WARM" if score >= 35 else "COLD"
        angle = parsed.get("angle", "")

        return score, tier, angle, cost
    except Exception as e:
        logger.error(f"Lead scoring error: {e}")
        # Fallback to basic scoring
        score = _basic_score(lead_data)
        tier = "HOT" if score >= 70 else "WARM" if score >= 35 else "COLD"
        return score, tier, "", 0


def _basic_score(lead):
    """Fallback scoring without AI. Favors custom focus over raw sales volume."""
    score = 0
    sales = lead.get("sale_count", 0) or 0

    # Sales: sweet spot is 10-2000. Small active shops score well.
    if 10 <= sales <= 100:
        score += 20  # Small but active — most likely to need help
    elif 100 < sales <= 500:
        score += 25
    elif 500 < sales <= 2000:
        score += 20
    elif 2000 < sales <= 5000:
        score += 15
    elif sales > 5000:
        score += 8   # Probably has their own systems already

    # Custom percentage: THIS is the most important signal
    custom_pct = lead.get("custom_pct", 0) or 0
    if custom_pct >= 80:
        score += 35
    elif custom_pct >= 50:
        score += 28
    elif custom_pct >= 30:
        score += 20
    elif custom_pct >= 10:
        score += 10

    # Good reviews = active and cares about quality
    rating = lead.get("review_average")
    if rating and rating >= 4.5:
        score += 10

    # Active listings
    if (lead.get("listing_count") or 0) >= 10:
        score += 5

    return min(score, 100)


def score_unscored_leads(limit=50):
    """Score leads that haven't been AI-scored yet (score == 0).
    Reddit leads are pre-scored during classification, so this mainly catches Etsy leads."""
    from growth.growth_db import get_conn
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM growth_leads WHERE score = 0 AND source != 'reddit' ORDER BY created_at ASC LIMIT %s",
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
# SELF-LEARNING — NICHE PERFORMANCE
# =============================================================

def update_scout_learnings():
    """Analyze which niches produce HOT leads and update learnings."""
    if not LEARNING_ENABLED:
        return

    conn = get_conn()
    try:
        # Get niche stats
        rows = conn.execute("""
            SELECT niche,
                   COUNT(*) as total,
                   SUM(CASE WHEN tier = 'HOT' THEN 1 ELSE 0 END) as hot,
                   SUM(CASE WHEN tier = 'WARM' THEN 1 ELSE 0 END) as warm,
                   SUM(CASE WHEN contact_status = 'responded' THEN 1 ELSE 0 END) as responded,
                   SUM(CASE WHEN contact_status = 'converted' THEN 1 ELSE 0 END) as converted
            FROM growth_leads
            WHERE niche IS NOT NULL
            GROUP BY niche
        """).fetchall()
    finally:
        conn.close()

    for row in rows:
        r = dict(row)
        niche = r["niche"]
        total = r["total"]
        if total == 0:
            continue

        hot_rate = (r["hot"] / total) * 100
        response_rate = (r["responded"] / total) * 100 if total > 0 else 0
        conversion_rate = (r["converted"] / total) * 100 if total > 0 else 0

        # Score = weighted combination of hot rate and response rate
        score = hot_rate * 0.5 + response_rate * 0.3 + conversion_rate * 0.2
        confidence = min(total / 20, 1.0)  # Full confidence at 20 samples

        upsert_learning(
            agent="scout",
            learning_type="niche_performance",
            key=niche,
            value_json={
                "hot_rate": round(hot_rate, 1),
                "response_rate": round(response_rate, 1),
                "conversion_rate": round(conversion_rate, 1),
                "total_leads": total,
            },
            score=round(score, 2),
            sample_size=total,
            confidence=round(confidence, 2),
        )

    logger.info(f"Scout: Updated learnings for {len(rows)} niches")


def get_smart_niches(max_niches=3):
    """Pick niches based on learnings: top performers + 1 untested for exploration."""
    if not LEARNING_ENABLED:
        return list(NICHE_QUERIES.keys())[:max_niches]

    top = get_top_learnings("scout", "niche_performance", limit=max_niches, min_sample=3)
    tested_niches = {l["key"] for l in get_learnings(agent="scout", learning_type="niche_performance")}

    # Top performers
    smart_niches = [l["key"] for l in top if l["key"] in NICHE_QUERIES]

    # Add exploration niche(s)
    untested = [n for n in NICHE_QUERIES if n not in tested_niches]
    explore_count = max(1, int(max_niches * LEARNING_EXPLORATION_RATE))

    if untested:
        explore_picks = random.sample(untested, min(explore_count, len(untested)))
        smart_niches.extend(explore_picks)

    # Fill remaining slots with defaults if needed
    if len(smart_niches) < max_niches:
        remaining = [n for n in NICHE_QUERIES if n not in smart_niches]
        smart_niches.extend(remaining[:max_niches - len(smart_niches)])

    return smart_niches[:max_niches]


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
        niches = get_smart_niches(max_niches=3)

    etsy_leads = 0
    reddit_leads = 0

    # Etsy discovery — skip if API key isn't active (scraping gets 403)
    etsy_api_key = os.getenv("ETSY_API_KEY", "")
    if etsy_api_key:
        for niche in niches:
            etsy_leads += discover_etsy_leads(niche, limit=30)
    else:
        logger.info("Scout: Skipping Etsy discovery — no active API key")

    # Reddit discovery
    reddit_leads += discover_reddit_leads()

    total_leads = etsy_leads + reddit_leads

    # Score unscored leads
    scored = score_unscored_leads(limit=30)

    # Update learnings after discovery
    if LEARNING_ENABLED:
        try:
            update_scout_learnings()
        except Exception as e:
            logger.error(f"Scout learning update error: {e}")

    duration_ms = int((time.time() - start) * 1000)
    result = {
        "status": "ok",
        "total_leads": total_leads,
        "etsy_leads": etsy_leads,
        "reddit_leads": reddit_leads,
        "leads_scored": scored,
        "niches_searched": niches,
        "duration_ms": duration_ms,
    }
    log_agent_action("scout", "run", True, result, duration_ms=duration_ms)
    return result
