"""
ETSAI Lead Scraper
Uses Etsy's Open API v3 to find custom order sellers, extract shop data,
score leads by custom order intensity, and output CSV for outreach tools.

Requires ETSY_API_KEY in .env (same key used for Etsy integration).

Usage:
    python lead_scraper.py                          # Default: all niches, 100 results each
    python lead_scraper.py --niches jewelry signs    # Specific niches
    python lead_scraper.py --limit 250              # More results per query
    python lead_scraper.py --output leads.csv        # Custom output file
    python lead_scraper.py --enrich                  # Also fetch full shop details
    python lead_scraper.py --dry-run                 # Preview without API calls
"""
import argparse
import csv
import json
import logging
import os
import re
import sys
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ETSY_API_BASE = "https://openapi.etsy.com/v3"
REQUEST_TIMEOUT = 20

# Etsy API rate limit: 10 requests/second for public endpoints
# We stay well under with 0.3s delay
API_DELAY = 0.3

# Search queries by niche — these target custom/personalized items
NICHE_QUERIES = {
    "jewelry": [
        "custom jewelry",
        "personalized ring",
        "custom engraved necklace",
        "made to order bracelet",
    ],
    "portraits": [
        "custom portrait",
        "personalized pet portrait",
        "custom family portrait",
        "commission portrait painting",
    ],
    "signs": [
        "custom wood sign",
        "personalized neon sign",
        "custom wedding sign",
        "made to order sign",
    ],
    "wedding": [
        "custom wedding invitations",
        "personalized wedding gift",
        "custom wedding decor",
        "made to order bridesmaid gift",
    ],
    "clothing": [
        "custom embroidered clothing",
        "personalized jacket",
        "custom printed shirt",
        "made to order dress",
    ],
    "home_decor": [
        "custom wall art",
        "personalized home decor",
        "custom doormat",
        "made to order furniture",
    ],
    "pet_products": [
        "custom pet collar",
        "personalized pet tag",
        "custom pet bed",
        "made to order pet portrait",
    ],
    "stationery": [
        "custom stationery",
        "personalized planner",
        "custom stamps",
        "made to order notebook",
    ],
    "leather": [
        "custom leather wallet",
        "personalized leather bag",
        "custom leather journal",
        "made to order leather belt",
    ],
    "kids": [
        "custom baby blanket",
        "personalized kids gift",
        "custom nursery decor",
        "made to order baby outfit",
    ],
}

# Custom order signal words — used to score listings
CUSTOM_SIGNALS = [
    "custom", "personalized", "personalised", "made to order",
    "bespoke", "commissioned", "commission", "customized", "customised",
    "your text", "your name", "your photo", "your design",
    "choose your", "select your", "pick your",
    "engraved", "engraving", "monogram", "monogrammed",
    "hand made", "handmade to order", "built to order",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("lead_scraper")


# ---------------------------------------------------------------------------
# Etsy API client (public endpoints — API key only, no OAuth)
# ---------------------------------------------------------------------------

def _get_api_key():
    key = os.getenv("ETSY_API_KEY", "")
    if not key:
        log.error("ETSY_API_KEY not found in .env — cannot use Etsy API")
        log.error("Get your key at https://www.etsy.com/developers/your-apps")
        sys.exit(1)
    return key


def _api_get(path, params=None, retries=2):
    """
    Make a GET request to Etsy's Open API v3 (public, API-key-only).
    Returns JSON response or None on failure.
    """
    api_key = _get_api_key()
    url = f"{ETSY_API_BASE}{path}"
    headers = {"x-api-key": api_key}

    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)

            if resp.status_code == 429:
                wait = 5 * (attempt + 1)
                log.warning(f"Rate limited (429). Waiting {wait}s...")
                time.sleep(wait)
                continue

            if resp.status_code == 404:
                return None

            if resp.status_code != 200:
                log.warning(f"API error {resp.status_code}: {resp.text[:200]}")
                if attempt < retries:
                    time.sleep(2)
                    continue
                return None

            return resp.json()

        except requests.exceptions.RequestException as e:
            if attempt < retries:
                log.warning(f"Request failed ({e}), retry {attempt + 1}/{retries}")
                time.sleep(3)
            else:
                log.error(f"Failed: {e}")
                return None

    return None


# ---------------------------------------------------------------------------
# Search listings via API
# ---------------------------------------------------------------------------

def search_listings(query, limit=100, offset=0):
    """
    Search Etsy active listings via API.

    GET /v3/application/listings/active
    Returns up to `limit` results (max 100 per API call).

    Each result includes: listing_id, title, description, price,
    shop_id, has_variations, is_personalizable, tags, etc.
    """
    params = {
        "keywords": query,
        "limit": min(limit, 100),
        "offset": offset,
        "sort_on": "score",  # Relevance
    }

    data = _api_get("/application/listings/active", params=params)
    if not data:
        return [], 0

    results = data.get("results", [])
    total = data.get("count", 0)

    return results, total


def search_listings_paged(query, total_results=100):
    """
    Search with pagination, collecting up to total_results listings.
    """
    all_results = []
    offset = 0
    page_size = 100  # Etsy API max

    while offset < total_results:
        batch_size = min(page_size, total_results - offset)
        results, total_available = search_listings(query, limit=batch_size, offset=offset)

        if not results:
            break

        all_results.extend(results)
        offset += len(results)

        # Stop if we've gotten all available results
        if offset >= total_available:
            break

        time.sleep(API_DELAY)

    return all_results


# ---------------------------------------------------------------------------
# Shop details via API
# ---------------------------------------------------------------------------

def get_shop_details(shop_id):
    """
    Get detailed shop info.

    GET /v3/application/shops/{shop_id}
    Returns: shop_name, title, sale_count, review_count, review_average,
    city, url, social_media, etc.
    """
    data = _api_get(f"/application/shops/{shop_id}")
    if not data:
        return None

    return {
        "shop_id": data.get("shop_id"),
        "shop_name": data.get("shop_name", ""),
        "title": data.get("title", ""),
        "sale_count": data.get("transaction_sold_count", 0),
        "review_count": data.get("review_count", 0),
        "review_average": data.get("review_average"),
        "listing_active_count": data.get("listing_active_count", 0),
        "city": data.get("city", ""),
        "url": data.get("url", ""),
        "icon_url": data.get("icon_url_fullxfull", ""),
        "is_vacation": data.get("is_vacation", False),
        "currency": data.get("currency_code", "USD"),
        "created_timestamp": data.get("create_date"),
    }


# ---------------------------------------------------------------------------
# Lead processing
# ---------------------------------------------------------------------------

def _has_custom_signals(text):
    """Check if text contains custom order signal words."""
    text_lower = text.lower()
    for signal in CUSTOM_SIGNALS:
        if signal in text_lower:
            return True
    return False


def process_search_results(results, niche):
    """
    Process raw API search results into shop-level lead data.
    Groups by shop_id, counts custom signals, collects sample listings.
    """
    shops = {}

    for listing in results:
        shop_id = listing.get("shop_id")
        if not shop_id:
            continue

        title = listing.get("title", "")
        description = listing.get("description", "")
        is_personalizable = listing.get("is_personalizable", False)
        tags = listing.get("tags", [])

        has_custom = (
            _has_custom_signals(title) or
            _has_custom_signals(description) or
            is_personalizable or
            any(_has_custom_signals(t) for t in tags)
        )

        # Price
        price_data = listing.get("price", {})
        price = None
        if price_data:
            try:
                amount = float(price_data.get("amount", 0))
                divisor = float(price_data.get("divisor", 100))
                price = amount / divisor
            except (ValueError, TypeError, ZeroDivisionError):
                pass

        if shop_id not in shops:
            shops[shop_id] = {
                "shop_id": shop_id,
                "niche": niche,
                "listings_found": [],
                "custom_listings": 0,
                "total_listings_seen": 0,
                "has_personalization": False,
                "sample_prices": [],
            }

        shop = shops[shop_id]
        shop["total_listings_seen"] += 1

        if title and title not in shop["listings_found"]:
            shop["listings_found"].append(title)

        if has_custom:
            shop["custom_listings"] += 1
            shop["has_personalization"] = True

        if is_personalizable:
            shop["has_personalization"] = True

        if price and price > 0:
            shop["sample_prices"].append(price)

    return shops


# ---------------------------------------------------------------------------
# Lead scoring
# ---------------------------------------------------------------------------

def score_lead(lead):
    """
    Score a lead from 0-100 based on likelihood of being a good ETSAI customer.
    """
    score = 0

    # Sales count (0-30 points)
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

    # Custom listing ratio (0-25 points)
    total_seen = lead.get("total_listings_seen", 0)
    custom_count = lead.get("custom_listings", 0)
    if total_seen > 0:
        custom_pct = (custom_count / total_seen) * 100
        lead["custom_listing_pct"] = round(custom_pct, 1)
        if custom_pct >= 50:
            score += 25
        elif custom_pct >= 30:
            score += 20
        elif custom_pct >= 15:
            score += 12
        elif custom_pct > 0:
            score += 5
    else:
        lead["custom_listing_pct"] = 0

    # Has personalization flag (0-15 points)
    if lead.get("has_personalization"):
        score += 15

    # Rating (0-10 points)
    rating = lead.get("review_average")
    if rating:
        if rating >= 4.8:
            score += 10
        elif rating >= 4.5:
            score += 7
        elif rating >= 4.0:
            score += 4

    # Active listing count — more listings = more serious seller (0-10 points)
    active = lead.get("listing_active_count", 0) or 0
    if active >= 100:
        score += 10
    elif active >= 50:
        score += 7
    elif active >= 20:
        score += 5
    elif active >= 5:
        score += 2

    # Review count — social proof of established business (0-10 points)
    reviews = lead.get("review_count", 0) or 0
    if reviews >= 500:
        score += 10
    elif reviews >= 100:
        score += 7
    elif reviews >= 25:
        score += 4
    elif reviews >= 5:
        score += 2

    return min(score, 100)


def score_tier(score):
    """Convert numeric score to tier label."""
    if score >= 60:
        return "HOT"
    elif score >= 35:
        return "WARM"
    else:
        return "COLD"


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_scraper(niches=None, results_per_query=100, enrich=True, output_file=None):
    """
    Main pipeline:
    1. Search listings via API for each niche query
    2. Group by shop_id, detect custom order signals
    3. Fetch shop details (sales, reviews, rating)
    4. Score and tier each lead
    5. Output sorted CSV
    """
    if niches is None:
        niches = list(NICHE_QUERIES.keys())

    for n in niches:
        if n not in NICHE_QUERIES:
            log.error(f"Unknown niche '{n}'. Available: {', '.join(NICHE_QUERIES.keys())}")
            sys.exit(1)

    # --- Phase 1: Search listings ---
    log.info(f"=== Phase 1: Searching {len(niches)} niches ({results_per_query} results/query) ===")
    all_shops = {}  # shop_id -> shop data

    for niche in niches:
        queries = NICHE_QUERIES[niche]
        for query in queries:
            log.info(f"  Searching: '{query}'")
            results = search_listings_paged(query, total_results=results_per_query)
            log.info(f"    Got {len(results)} listings")

            shops = process_search_results(results, niche)
            for shop_id, shop_data in shops.items():
                if shop_id not in all_shops:
                    all_shops[shop_id] = shop_data
                else:
                    # Merge: add listings, update counts
                    existing = all_shops[shop_id]
                    for title in shop_data["listings_found"]:
                        if title not in existing["listings_found"]:
                            existing["listings_found"].append(title)
                    existing["custom_listings"] += shop_data["custom_listings"]
                    existing["total_listings_seen"] += shop_data["total_listings_seen"]
                    if shop_data["has_personalization"]:
                        existing["has_personalization"] = True
                    existing["sample_prices"].extend(shop_data["sample_prices"])

            time.sleep(API_DELAY)

    log.info(f"=== Found {len(all_shops)} unique shops across all searches ===")

    if not all_shops:
        log.warning("No shops found. Check your ETSY_API_KEY and try again.")
        return None, []

    # --- Phase 2: Enrich with shop details ---
    if enrich:
        log.info(f"=== Phase 2: Fetching details for {len(all_shops)} shops ===")
        enriched = 0
        skipped = 0

        for shop_id, shop_data in all_shops.items():
            details = get_shop_details(shop_id)
            if details:
                shop_data.update(details)
                # Skip vacation shops
                if details.get("is_vacation"):
                    shop_data["_skip"] = True
                    skipped += 1
                enriched += 1
            else:
                skipped += 1

            time.sleep(API_DELAY)

            if enriched % 50 == 0 and enriched > 0:
                log.info(f"  Enriched {enriched}/{len(all_shops)} shops...")

        log.info(f"=== Enriched {enriched} shops ({skipped} skipped/failed) ===")

        # Remove vacation shops
        all_shops = {k: v for k, v in all_shops.items() if not v.get("_skip")}
        log.info(f"=== {len(all_shops)} active shops after filtering ===")

    # --- Phase 3: Score leads ---
    log.info("=== Phase 3: Scoring leads ===")
    leads = []
    for shop_id, shop_data in all_shops.items():
        shop_data["score"] = score_lead(shop_data)
        shop_data["tier"] = score_tier(shop_data["score"])
        leads.append(shop_data)

    leads.sort(key=lambda x: x["score"], reverse=True)

    # --- Phase 4: Output CSV ---
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"leads_{timestamp}.csv"

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_file)

    fieldnames = [
        "tier", "score", "shop_name", "niche", "shop_url",
        "sale_count", "review_count", "review_average",
        "listing_active_count", "custom_listings", "custom_listing_pct",
        "has_personalization", "city", "avg_price", "sample_listings",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for lead in leads:
            prices = lead.get("sample_prices", [])
            avg_price = round(sum(prices) / len(prices), 2) if prices else ""

            shop_name = lead.get("shop_name", "")
            shop_url = lead.get("url", "") or (
                f"https://www.etsy.com/shop/{shop_name}" if shop_name else ""
            )

            row = {
                "tier": lead.get("tier", "COLD"),
                "score": lead.get("score", 0),
                "shop_name": shop_name,
                "niche": lead.get("niche", ""),
                "shop_url": shop_url,
                "sale_count": lead.get("sale_count", 0),
                "review_count": lead.get("review_count", 0),
                "review_average": lead.get("review_average", ""),
                "listing_active_count": lead.get("listing_active_count", 0),
                "custom_listings": lead.get("custom_listings", 0),
                "custom_listing_pct": lead.get("custom_listing_pct", 0),
                "has_personalization": lead.get("has_personalization", False),
                "city": lead.get("city", ""),
                "avg_price": avg_price,
                "sample_listings": " | ".join(lead.get("listings_found", [])[:3]),
            }
            writer.writerow(row)

    # Summary
    hot = sum(1 for l in leads if l["tier"] == "HOT")
    warm = sum(1 for l in leads if l["tier"] == "WARM")
    cold = sum(1 for l in leads if l["tier"] == "COLD")

    log.info("=" * 60)
    log.info(f"DONE! {len(leads)} leads saved to {output_file}")
    log.info(f"  HOT:  {hot} leads (score 60+)")
    log.info(f"  WARM: {warm} leads (score 35-59)")
    log.info(f"  COLD: {cold} leads (score < 35)")

    if leads:
        top_5 = leads[:5]
        log.info(f"\nTop 5 leads:")
        for i, l in enumerate(top_5):
            log.info(f"  {i+1}. {l.get('shop_name', '?')} — "
                     f"Score: {l['score']}, "
                     f"Sales: {l.get('sale_count', 0):,}, "
                     f"Custom%: {l.get('custom_listing_pct', 0)}%")

    log.info("=" * 60)
    return output_path, leads


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ETSAI Lead Scraper — Find Etsy sellers who need custom order spec collection"
    )
    parser.add_argument(
        "--niches",
        nargs="+",
        choices=list(NICHE_QUERIES.keys()),
        default=None,
        help=f"Niches to search (default: all). Options: {', '.join(NICHE_QUERIES.keys())}",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Results per search query (default: 100, max ~250 per Etsy pagination)",
    )
    parser.add_argument(
        "--no-enrich",
        action="store_true",
        help="Skip fetching individual shop details (faster but less data)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV filename (default: leads_TIMESTAMP.csv)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be scraped without making requests",
    )

    args = parser.parse_args()

    if args.dry_run:
        niches = args.niches or list(NICHE_QUERIES.keys())
        total_queries = sum(len(NICHE_QUERIES[n]) for n in niches)
        total_api_calls = total_queries  # 1 call per query at limit=100
        if args.limit > 100:
            total_api_calls = total_queries * (args.limit // 100 + 1)

        print(f"\nDry run summary:")
        print(f"  Niches: {', '.join(niches)}")
        print(f"  Search queries: {total_queries}")
        print(f"  Results per query: {args.limit}")
        print(f"  API calls (search): ~{total_api_calls}")
        print(f"  Enrichment: {'No' if args.no_enrich else 'Yes — will also fetch each unique shop'}")
        print(f"  Est. unique shops: ~{total_queries * 30}-{total_queries * 80}")
        print(f"  Est. time: ~{total_api_calls * 0.5:.0f}s search" +
              (f" + shop enrichment" if not args.no_enrich else ""))
        print(f"\n  Requires: ETSY_API_KEY in .env")
        return

    run_scraper(
        niches=args.niches,
        results_per_query=args.limit,
        enrich=not args.no_enrich,
        output_file=args.output,
    )


if __name__ == "__main__":
    main()
