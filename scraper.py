"""
ETSAI Etsy Scraper
Extracts product data from public Etsy listing and shop pages.
Uses requests + BeautifulSoup + JSON-LD structured data.
"""
import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

REQUEST_TIMEOUT = 15


def _fetch_page(url):
    """Fetch a page and return BeautifulSoup object."""
    parsed = urlparse(url)
    if parsed.hostname not in ('etsy.com', 'www.etsy.com'):
        raise ValueError("URL must be an etsy.com domain")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if resp.status_code == 403:
            raise ValueError("Access denied by Etsy. The listing may be private or the page is blocking automated access.")
        elif resp.status_code == 429:
            raise ValueError("Too many requests to Etsy. Please wait a moment and try again.")
        elif resp.status_code == 404:
            raise ValueError("Listing not found. Please check the URL and try again.")
        raise ValueError(f"Failed to fetch page (HTTP {resp.status_code})")
    except requests.exceptions.RequestException:
        raise ValueError("Could not connect to Etsy. Please check your internet connection and try again.")
    return BeautifulSoup(resp.text, "html.parser")


def _extract_json_ld(soup):
    """Extract JSON-LD structured data from page."""
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                return data
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type") == "Product":
                        return item
        except (json.JSONDecodeError, TypeError):
            continue
    return {}


def _extract_etsy_listing_id(url):
    """Extract the listing ID from an Etsy URL like /listing/123456789/..."""
    match = re.search(r"/listing/(\d+)", url)
    return match.group(1) if match else None


def _clean_text(text):
    """Clean whitespace from extracted text."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def scrape_etsy_listing(url):
    """
    Scrape a single Etsy listing page.

    Returns dict:
    {
        "title": str,
        "description": str,
        "price": float or None,
        "currency": str,
        "images": [str, ...],
        "variations": [{"name": str, "options": [str, ...]}, ...],
        "materials": [str, ...],
        "tags": [str, ...],
        "source_url": str,
        "listing_id": str or None,
        "shop_name": str,
    }
    """
    soup = _fetch_page(url)
    json_ld = _extract_json_ld(soup)

    # Title: prefer JSON-LD, fallback to meta/h1
    title = json_ld.get("name", "")
    if not title:
        og_title = soup.find("meta", property="og:title")
        if og_title:
            title = og_title.get("content", "")
    if not title:
        h1 = soup.find("h1")
        title = h1.get_text() if h1 else ""
    title = _clean_text(title)

    # Description: prefer JSON-LD, fallback to meta og:description,
    # then look for the listing description div
    description = json_ld.get("description", "")
    if not description:
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            description = og_desc.get("content", "")
    if not description:
        desc_div = (
            soup.find("div", {"data-id": "description-text"})
            or soup.find("div", class_=re.compile(r"listing-page-description"))
            or soup.find("p", class_=re.compile(r"wt-text-body"))
        )
        if desc_div:
            description = desc_div.get_text(separator="\n")
    description = _clean_text(description)

    # Price from JSON-LD offers
    price = None
    currency = "USD"
    offers = json_ld.get("offers", {})
    if isinstance(offers, list) and offers:
        offers = offers[0]
    if isinstance(offers, dict):
        try:
            price = float(offers.get("price", 0))
        except (ValueError, TypeError):
            price = None
        currency = offers.get("priceCurrency", "USD")

    # Fallback price from meta
    if not price:
        price_meta = soup.find("meta", property="product:price:amount")
        if price_meta:
            try:
                price = float(price_meta.get("content", 0))
            except (ValueError, TypeError):
                pass
        currency_meta = soup.find("meta", property="product:price:currency")
        if currency_meta:
            currency = currency_meta.get("content", "USD")

    # Images from JSON-LD
    images = []
    ld_images = json_ld.get("image", [])
    if isinstance(ld_images, str):
        images = [ld_images]
    elif isinstance(ld_images, list):
        images = [img if isinstance(img, str) else img.get("url", "") for img in ld_images]
    images = [img for img in images if img]

    # Fallback images from og:image
    if not images:
        for meta in soup.find_all("meta", property="og:image"):
            img_url = meta.get("content", "")
            if img_url:
                images.append(img_url)

    # Variations (size, color, etc.) from select elements
    variations = []
    for select in soup.find_all("select", id=re.compile(r"variation")):
        label_el = soup.find("label", {"for": select.get("id", "")})
        var_name = _clean_text(label_el.get_text()) if label_el else select.get("id", "")
        options = []
        for opt in select.find_all("option"):
            val = _clean_text(opt.get_text())
            if val and val.lower() not in ("select an option", "select", "choose", ""):
                options.append(val)
        if options:
            variations.append({"name": var_name, "options": options})

    # Also try to find variation data in script tags (Etsy embeds it as JS)
    if not variations:
        for script in soup.find_all("script"):
            if script.string and "variations" in (script.string or ""):
                # Try to find JSON objects with variation data
                var_matches = re.findall(
                    r'"variation_label"\s*:\s*"([^"]+)".*?"options"\s*:\s*\[([^\]]+)\]',
                    script.string, re.DOTALL
                )
                for label, opts_str in var_matches:
                    opts = re.findall(r'"value"\s*:\s*"([^"]+)"', opts_str)
                    if opts:
                        variations.append({"name": label, "options": opts})

    # Materials
    materials = []
    mat_section = soup.find("span", string=re.compile(r"Materials?:", re.I))
    if mat_section:
        parent = mat_section.parent
        if parent:
            mat_text = parent.get_text().replace("Materials:", "").replace("Material:", "")
            materials = [_clean_text(m) for m in mat_text.split(",") if _clean_text(m)]

    # Tags from meta keywords
    tags = []
    kw_meta = soup.find("meta", attrs={"name": "keywords"})
    if kw_meta:
        tags = [_clean_text(t) for t in kw_meta.get("content", "").split(",") if _clean_text(t)]

    # Shop name
    shop_name = ""
    shop_link = soup.find("a", href=re.compile(r"etsy\.com/shop/"))
    if shop_link:
        shop_name = _clean_text(shop_link.get_text())
    if not shop_name:
        # Try from JSON-LD brand
        brand = json_ld.get("brand", {})
        if isinstance(brand, dict):
            shop_name = brand.get("name", "")
        elif isinstance(brand, str):
            shop_name = brand

    return {
        "title": title,
        "description": description,
        "price": price,
        "currency": currency,
        "images": images[:5],  # Cap at 5
        "variations": variations,
        "materials": materials,
        "tags": tags[:15],  # Cap at 15
        "source_url": url,
        "listing_id": _extract_etsy_listing_id(url),
        "shop_name": shop_name,
    }


def scrape_etsy_shop(shop_url):
    """
    Scrape an Etsy shop page to get all active listing URLs.

    Accepts URLs like:
    - https://www.etsy.com/shop/ShopName
    - https://www.etsy.com/shop/ShopName?section_id=...

    Returns list of dicts:
    [
        {
            "url": "https://www.etsy.com/listing/123456789/...",
            "title": "Product Title",
            "price": "$59.99" or None,
            "thumbnail": "https://..." or None,
            "listing_id": "123456789",
        },
        ...
    ]
    """
    soup = _fetch_page(shop_url)

    listings = []
    seen_ids = set()

    # Find listing links - Etsy uses various patterns
    listing_links = soup.find_all("a", href=re.compile(r"/listing/\d+"))

    for link in listing_links:
        href = link.get("href", "")
        listing_id = _extract_etsy_listing_id(href)
        if not listing_id or listing_id in seen_ids:
            continue
        seen_ids.add(listing_id)

        # Build full URL
        parsed = urlparse(href)
        if not parsed.scheme:
            full_url = f"https://www.etsy.com{href}"
        else:
            full_url = href
        # Strip query params for clean URL
        full_url = full_url.split("?")[0]

        # Try to get title from the link or nearby elements
        title = ""
        # Check for title in the link's text or children
        title_el = link.find("h3") or link.find("h2") or link.find("span")
        if title_el:
            title = _clean_text(title_el.get_text())
        if not title:
            title = _clean_text(link.get("title", ""))
        if not title:
            title = _clean_text(link.get_text())
        # Truncate very long extracted text (likely got too much DOM)
        if len(title) > 200:
            title = title[:200].rsplit(" ", 1)[0] + "..."

        # Try to get price
        price_text = None
        parent = link.parent
        if parent:
            price_el = parent.find("span", class_=re.compile(r"currency"))
            if not price_el:
                price_el = parent.find(string=re.compile(r"\$\d+"))
            if price_el:
                price_text = _clean_text(str(price_el) if isinstance(price_el, str) else price_el.get_text())

        # Try to get thumbnail
        thumbnail = None
        img = link.find("img")
        if img:
            thumbnail = img.get("src") or img.get("data-src")

        listings.append({
            "url": full_url,
            "title": title or f"Listing {listing_id}",
            "price": price_text,
            "thumbnail": thumbnail,
            "listing_id": listing_id,
        })

    return listings
