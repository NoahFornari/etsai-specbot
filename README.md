# ETSAI — AI Spec Collection Bot for Etsy Custom Order Sellers

## What It Does
After a buyer purchases a custom product (on Etsy, Shopify, anywhere), you send them a link. An AI chatbot collects every customization detail — ring sizes, engraving text, shaft flex, portrait styles — and delivers a complete spec sheet to you. No more 5-message back-and-forth per order.

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Seed demo data (works without API key)
python seed_demo.py

# Run (set API key for AI features)
export ANTHROPIC_API_KEY=your-key-here
python app.py
```

Open http://localhost:5000 → Log in with `demo@etsai.com`

## How It Works

### Seller Side
1. **Add Product** → describe what you sell, AI generates intake questions
2. **Create Order** → when a sale comes in, create an order and get an intake link
3. **Send Link** → paste the link in your Etsy/eBay message or sale confirmation
4. **Dashboard** → watch specs roll in, see conversation logs, get complete order sheets

### Buyer Side
1. Clicks the intake link from the seller's message
2. Sees a clean chat interface
3. AI asks smart, product-specific questions
4. Buyer replies naturally — "size 7, polished, script font"
5. AI extracts ALL specs from one message (no annoying one-at-a-time questions)
6. When all required specs are collected, buyer sees confirmation

## Architecture

```
etsai/
├── app.py              # Flask app (dashboard + intake pages + API)
├── ai_engine.py        # Claude AI conversation engine
├── database.py         # Multi-tenant SQLite (easy Postgres migration)
├── seed_demo.py        # Demo data for testing
├── requirements.txt
└── templates/
    ├── home.html           # Landing page + signup
    ├── dashboard.html      # Seller dashboard
    ├── add_product.html    # Add product with AI question gen
    ├── product_detail.html # View product + questions
    ├── order_detail.html   # View order specs + conversation
    ├── intake_chat.html    # BUYER-FACING chat (the product)
    ├── intake_complete.html
    └── intake_error.html
```

## API Endpoints

```
POST /api/orders              # Create order, get intake URL
GET  /api/orders/<id>         # Get order status + specs
GET  /api/orders/<id>/specs   # Get formatted spec sheet
POST /api/products/<id>/generate-questions  # Re-generate AI questions
GET  /health                  # Health check
```

## AI Cost
- ~$0.01-0.05 per conversation (Sonnet for quality, Haiku for follow-ups)
- Cost tracked per seller in dashboard

## Etsy Integration (the play)
Set your Etsy shop's "sale message" to include the intake link.
Buyer purchases → Etsy auto-sends your message → Buyer clicks link → AI collects specs.

For automation: Use Etsy API `ORDER_PAID` webhook → hit `POST /api/orders` → get intake URL → email to buyer.

## Next Steps
- [ ] Etsy OAuth integration (auto-create orders on sale)
- [ ] Email notifications (seller gets notified when specs complete)
- [ ] Shopify app version
- [ ] Stripe billing
- [ ] Multi-language support
