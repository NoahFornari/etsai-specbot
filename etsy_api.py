"""
ETSAI Etsy API Module
OAuth 2.0 with PKCE + Etsy v3 API helpers.
Raw requests-based — no extra library needed.
"""
import os
import hashlib
import base64
import secrets
import time
import requests
from datetime import datetime, timedelta
from urllib.parse import urlencode

ETSY_API_BASE = "https://openapi.etsy.com/v3"
ETSY_AUTH_URL = "https://www.etsy.com/oauth/connect"
ETSY_TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"

REQUEST_TIMEOUT = 15


# === PKCE Helpers ===

def generate_pkce_pair():
    """Generate code_verifier and code_challenge for PKCE OAuth."""
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode("ascii")
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge


# === OAuth Flow ===

def get_oauth_url(state, code_challenge):
    """Build the Etsy OAuth authorization URL."""
    api_key = os.environ.get("ETSY_API_KEY", "")
    redirect_uri = os.environ.get("ETSY_REDIRECT_URI", "")

    params = {
        "response_type": "code",
        "client_id": api_key,
        "redirect_uri": redirect_uri,
        "scope": "transactions_r listings_r shops_r",
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{ETSY_AUTH_URL}?{urlencode(params)}"


def exchange_code_for_tokens(auth_code, code_verifier):
    """Exchange authorization code for access + refresh tokens."""
    api_key = os.environ.get("ETSY_API_KEY", "")
    redirect_uri = os.environ.get("ETSY_REDIRECT_URI", "")

    try:
        resp = requests.post(ETSY_TOKEN_URL, json={
            "grant_type": "authorization_code",
            "client_id": api_key,
            "redirect_uri": redirect_uri,
            "code": auth_code,
            "code_verifier": code_verifier,
        }, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException:
        raise Exception("Could not connect to Etsy. Please try again.")

    if resp.status_code != 200:
        raise Exception(f"Token exchange failed: {resp.status_code} {resp.text}")

    data = resp.json()
    expires_at = (datetime.now() + timedelta(seconds=data["expires_in"])).isoformat()

    return {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "expires_at": expires_at,
    }


def refresh_access_token(refresh_token):
    """Refresh an expired access token."""
    api_key = os.environ.get("ETSY_API_KEY", "")

    try:
        resp = requests.post(ETSY_TOKEN_URL, json={
            "grant_type": "refresh_token",
            "client_id": api_key,
            "refresh_token": refresh_token,
        }, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException:
        raise Exception("Could not connect to Etsy. Please try again.")

    if resp.status_code != 200:
        raise Exception(f"Token refresh failed: {resp.status_code} {resp.text}")

    data = resp.json()
    expires_at = (datetime.now() + timedelta(seconds=data["expires_in"])).isoformat()

    return {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "expires_at": expires_at,
    }


# === Authenticated API Helper ===

def etsy_request(method, path, seller, params=None, _retried=False):
    """
    Make an authenticated Etsy API request.
    Auto-refreshes token if expired.
    `seller` is a dict from get_seller() with etsy_* fields.
    Returns (response_json, updated_seller_or_None).
    """
    from database import save_etsy_tokens

    access_token = seller.get("etsy_access_token")
    refresh_token_val = seller.get("etsy_refresh_token")
    expires_at = seller.get("etsy_token_expires_at")
    updated_seller = None

    # Check if token needs refresh (with 5-minute buffer)
    if expires_at:
        try:
            exp_time = datetime.fromisoformat(expires_at)
            if datetime.now() >= exp_time - timedelta(minutes=5):
                tokens = refresh_access_token(refresh_token_val)
                access_token = tokens["access_token"]
                save_etsy_tokens(
                    seller["id"],
                    tokens["access_token"],
                    tokens["refresh_token"],
                    tokens["expires_at"],
                )
                updated_seller = True
        except (ValueError, TypeError):
            pass

    api_key = os.environ.get("ETSY_API_KEY", "")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "x-api-key": api_key,
    }

    url = f"{ETSY_API_BASE}{path}"

    if method.upper() == "GET":
        resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
    else:
        resp = requests.post(url, headers=headers, json=params, timeout=REQUEST_TIMEOUT)

    if resp.status_code == 401 and refresh_token_val and not _retried:
        # Token might have been invalidated; try one refresh
        tokens = refresh_access_token(refresh_token_val)
        headers["Authorization"] = f"Bearer {tokens['access_token']}"
        save_etsy_tokens(
            seller["id"],
            tokens["access_token"],
            tokens["refresh_token"],
            tokens["expires_at"],
        )
        if method.upper() == "GET":
            resp = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        else:
            resp = requests.post(url, headers=headers, json=params, timeout=REQUEST_TIMEOUT)

    resp.raise_for_status()
    return resp.json()


# === Etsy API Endpoints ===

def get_shop_for_user(seller):
    """Get the seller's Etsy shop after OAuth. Returns shop_id and shop_name."""
    etsy_user_id = seller.get("etsy_user_id")
    if not etsy_user_id:
        # Get user ID from token info
        data = etsy_request("GET", "/application/users/me", seller)
        etsy_user_id = data.get("user_id")

    # User might own multiple shops, get the first
    data = etsy_request("GET", f"/application/users/{etsy_user_id}/shops", seller)

    if isinstance(data, list) and data:
        shop = data[0]
    elif isinstance(data, dict):
        # Could be the shop directly or wrapped
        results = data.get("results", [data])
        shop = results[0] if results else None
    else:
        shop = None

    if not shop:
        raise Exception("No Etsy shop found for this account")

    return {
        "shop_id": shop.get("shop_id"),
        "shop_name": shop.get("shop_name"),
        "user_id": etsy_user_id,
    }


def get_shop_listings(seller, limit=25):
    """Fetch active listings from the seller's Etsy shop."""
    shop_id = seller.get("etsy_shop_id")
    if not shop_id:
        raise Exception("No Etsy shop connected")

    data = etsy_request("GET", f"/application/shops/{shop_id}/listings/active", seller,
                        params={"limit": limit, "includes": "Images"})

    listings = []
    for item in data.get("results", []):
        images = []
        if item.get("images"):
            images = [img.get("url_570xN", "") for img in item["images"][:3]]

        listings.append({
            "listing_id": item.get("listing_id"),
            "title": item.get("title", ""),
            "description": item.get("description", ""),
            "price": float(item.get("price", {}).get("amount", 0)) / item.get("price", {}).get("divisor", 100) if item.get("price") else None,
            "image_url": images[0] if images else None,
            "url": item.get("url", ""),
        })

    return listings


def get_recent_orders(seller, min_created=None):
    """
    Poll for recent receipts (orders) from the seller's shop.
    Returns list of receipt dicts with transaction info.
    """
    shop_id = seller.get("etsy_shop_id")
    if not shop_id:
        raise Exception("No Etsy shop connected")

    params = {"limit": 25, "sort_on": "created", "sort_order": "desc"}

    # Filter by timestamp if provided
    if min_created:
        try:
            ts = int(datetime.fromisoformat(min_created).timestamp())
            params["min_created"] = ts
        except (ValueError, TypeError):
            pass

    data = etsy_request("GET", f"/application/shops/{shop_id}/receipts", seller, params=params)

    orders = []
    for receipt in data.get("results", []):
        # Get buyer info from shipping address
        buyer_name = ""
        if receipt.get("name"):
            buyer_name = receipt["name"]

        orders.append({
            "receipt_id": receipt.get("receipt_id"),
            "buyer_name": buyer_name,
            "buyer_email": receipt.get("buyer_email", ""),
            "created_timestamp": receipt.get("create_timestamp"),
            "transactions": receipt.get("transactions", []),
        })

    return orders


def get_receipt_transactions(seller, receipt_id):
    """Get line items (transactions) for a specific receipt."""
    shop_id = seller.get("etsy_shop_id")
    data = etsy_request("GET", f"/application/shops/{shop_id}/receipts/{receipt_id}/transactions", seller)
    return data.get("results", [])
