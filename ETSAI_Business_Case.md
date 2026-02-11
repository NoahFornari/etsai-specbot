# ETSAI — Business Case

## The One-Liner

**ETSAI automates custom order spec collection for Etsy sellers using AI-powered conversations, replacing hours of back-and-forth messaging with a single smart link.**

---

## The Problem

Every day, millions of Etsy sellers who make custom products — jewelry engravers, portrait artists, custom clothing makers, personalized gift shops — go through the same exhausting cycle:

1. Buyer purchases a custom item
2. Seller sends a message: *"Thanks for your order! I need a few details..."*
3. Buyer responds with partial info
4. Seller asks follow-up questions
5. Buyer takes hours or days to respond
6. Repeat 4-8 times over several days
7. Seller finally has what they need to start working

**This back-and-forth wastes 15-30 minutes per order.** For a seller doing 50 custom orders a month, that's **12-25 hours every month** — not making their product, not growing their business — just asking the same questions over and over in Etsy messages.

And it's not just time. When personalization setup lacks clarity or structure, it results in higher back-and-forth messages, customer frustration, and sometimes orders that get made incorrectly because the specs were unclear.

The problem is structural: Etsy's messaging system was built for simple conversations, not structured data collection. Sellers are trying to collect a form's worth of information through a chat window.

---

## The Solution

ETSAI gives every seller a smart intake link they send to their buyer. Instead of going back and forth in Etsy messages, the buyer clicks one link and has a friendly AI-guided conversation that collects every spec the seller needs — in one sitting, in under 2 minutes.

**How it works:**

1. **Seller imports their product** (from Etsy listing URL, API, or manual entry)
2. **AI generates the right questions** — "What name for the engraving?", "Ring size?", "Gold or silver?"
3. **Seller creates an order** and gets an intake link
4. **Buyer clicks the link** and chats with the AI assistant
5. **AI collects all specs**, validates answers, asks smart follow-ups
6. **Seller gets a clean spec sheet** — ready to start production

The AI understands context. If a buyer says "I want a gold necklace with my mom's name Sarah in cursive," the AI extracts the material (gold), the name (Sarah), and the font style (cursive) — all in one message. It confirms with the buyer, then delivers a structured spec sheet to the seller.

**Before ETSAI:** 4-8 messages over 2-5 days per order
**After ETSAI:** 1 link, 1 conversation, under 2 minutes

---

## The Market

### By the Numbers

| Metric | Value | Source |
|--------|-------|--------|
| Etsy active sellers | **5.4 - 8.1 million** | Etsy 2024 Annual Report |
| Etsy gross merchandise sales | **$12.5 billion** (2024) | Etsy SEC Filing |
| Custom/made-to-order as % of GMS | **30%** | Etsy Investor Relations |
| Transactions involving personalization | **33%** | Etsy Marketplace Data |
| Dollar value of custom orders on Etsy | **~$3.75 billion/year** | 30% of $12.5B GMS |
| Active buyers on Etsy | **96.5 million** (2024) | Etsy Annual Report |
| Gifting as % of Etsy sales | **44%** | Etsy Trend Reports |

### Target Customers

Our ideal customer is an Etsy seller who:
- Sells **custom or personalized** products (not digital downloads, not mass-produced)
- Does **10+ custom orders per month** (enough volume that the pain is real)
- Spends **significant time** collecting specs via Etsy messages
- Values their time and would pay to get hours back

**Primary categories:**
- Custom jewelry (name necklaces, birthstone rings, engravings) — 18% of Etsy GMS
- Personalized gifts (custom portraits, engraved items, monogrammed goods) — 44% of sales are gifts
- Custom clothing & accessories (sized items, custom embroidery)
- Made-to-order home decor (custom signs, personalized wall art)
- Custom pet products (portraits, personalized collars, tags)

### Addressable Market

- ~1.8 million sellers deal with personalization (33% of 5.4M)
- Of those, **200,000 - 500,000** do complex custom work requiring detailed specs
- Even capturing **1%** = **2,000 - 5,000** paying customers
- At an average of **$39/month**: **$78K - $195K monthly recurring revenue**
- At **5%** penetration: **$390K - $975K MRR** ($4.7M - $11.7M ARR)

### Competitive Landscape

**There is no direct competitor doing this.** The adjacent tools are:

| Tool | What it does | Price | Why it's not ETSAI |
|------|-------------|-------|--------------------|
| eRank | Etsy SEO & keywords | $5.99 - $29.99/mo | Doesn't touch order management |
| Marmalead | Etsy keyword research | $19 - $29/mo | SEO only, no buyer communication |
| Craftybase | Inventory management | $19 - $49/mo | Tracks materials, not specs |
| Typeform / JotForm | Generic form builders | $25 - $83/mo | No AI, no Etsy integration, not conversational |
| Etsy's built-in personalization | Text field on listing | Free | One static field, no validation, no follow-ups |

ETSAI creates a **new category**: AI-powered spec collection for craft sellers. No one else is doing this.

---

## The Product

### What's Built (Production-Ready)

- **Seller Dashboard** — manage products, orders, specs, fulfillment, and activity
- **AI Question Generation** — paste an Etsy URL, AI generates the right intake questions automatically
- **AI Intake Chat** — buyer-facing conversation that extracts specs, validates answers, handles edge cases
- **Etsy Integration** — OAuth connection to import products and sync orders directly from Etsy
- **Etsy Scraper** — import any Etsy listing by URL without needing API access
- **Email Notifications** — sellers get emailed when specs are complete or when an order needs attention
- **Escalation Detection** — AI flags problematic conversations (cancellation requests, angry buyers)
- **Fulfillment Tracking** — track orders from pending through shipped to delivered
- **Spec Export** — copy or download specs as formatted text
- **Settings & Account Management** — profile, notifications, default seller notes
- **White-Label Mode** — Business plan sellers can remove ETSAI branding and use their own colors/logo
- **Full API** — programmatic access for advanced integrations

### Tech Stack

- **Backend:** Python/Flask, SQLite (WAL mode for concurrent access)
- **AI:** Claude API (Anthropic) — Sonnet for conversations, Haiku for classification
- **Frontend:** Tailwind CSS, vanilla JavaScript (no framework overhead)
- **Payments:** Stripe Billing (subscriptions, webhooks, customer portal)
- **Deployment:** Docker-ready, Gunicorn WSGI server

### Pricing

| Plan | Monthly | Orders/mo | Products | Key Features |
|------|---------|-----------|----------|-------------|
| **Free Trial** | $0 (14 days) | 10 | 3 | Full feature access |
| **Starter** | $29/mo | 50 | 15 | Core features |
| **Pro** | $59/mo | 250 | Unlimited | Priority + API access |
| **Business** | $119/mo | 1,000 | Unlimited | White-label + API + everything |

Annual billing available at 20% discount.

### Unit Economics

| Metric | Value |
|--------|-------|
| AI cost per order (avg 6 messages) | ~$0.04 - $0.08 |
| AI cost per order at scale | ~$0.03 (token caching) |
| Starter plan margin | ~95% ($29 revenue, ~$2 AI cost for 50 orders) |
| Pro plan margin | ~93% ($59 revenue, ~$4 AI cost for typical usage) |
| Infrastructure cost (hosting) | ~$20 - $50/mo total |
| Break-even | ~2 paying customers |

---

## Why Now

1. **AI costs just dropped dramatically.** The Claude models ETSAI uses cost 80-95% less than they did 18 months ago. This makes per-conversation AI economically viable at $29/mo.

2. **Etsy's personalization push.** Etsy is actively promoting personalized items — 33% of transactions now involve personalization, up from previous years. More personalization = more spec collection pain.

3. **Sellers are already paying for tools.** The Etsy seller tool market (eRank, Marmalead, Craftybase, etc.) proves sellers will pay $20-50/mo for tools that save them time. But nobody is solving the #1 time sink for custom sellers.

4. **No code, no setup friction.** ETSAI doesn't require sellers to build forms, write questions, or set up integrations. Paste your Etsy URL → AI does the rest. The time-to-value is under 5 minutes.

---

## Go-to-Market Strategy

### Phase 1: Validation (Month 1)
- Deploy to production (Railway + custom domain)
- Recruit 5-10 beta sellers from r/EtsySellers and Etsy forums
- Offer free Pro tier for 3 months in exchange for feedback and testimonials
- Iterate based on real usage patterns

### Phase 2: Content & Organic (Month 2-3)
- Create demo video (2 min) showing before vs. after
- Post in Etsy seller communities (Reddit, Facebook groups with 50K+ members)
- Publish YouTube tutorials: "How to automate custom order specs on Etsy"
- Short-form content on TikTok/Instagram showing the speed difference
- Launch on Product Hunt

### Phase 3: Scale (Month 4-6)
- Direct outreach to top Etsy sellers in custom categories
- Google Ads on low-competition keywords ("etsy custom order management")
- Affiliate program: sellers refer other sellers for 20% recurring commission
- Expand to Shopify custom order sellers (same problem, bigger market)

### Growth Flywheel
Every intake page has "Powered by ETSAI" at the bottom. When a buyer completes their specs, they see the ETSAI brand. Some of those buyers are also Etsy sellers. **The product markets itself through usage.**

---

## Financial Projections (Conservative)

| Month | Paying Customers | MRR | Notes |
|-------|-----------------|-----|-------|
| 1 | 5 | $0 | Beta (free) |
| 2 | 15 | $435 | First paying converts |
| 3 | 40 | $1,560 | Content push begins |
| 6 | 150 | $5,850 | Word of mouth + organic |
| 12 | 500 | $19,500 | Approaching $200K ARR |
| 18 | 1,200 | $46,800 | ~$560K ARR |
| 24 | 3,000 | $117,000 | $1.4M ARR |

**Assumptions:** 40% on Starter ($29), 45% on Pro ($59), 15% on Business ($119). 5% monthly churn. Conservative growth — no paid acquisition budget.

---

## The Vision

ETSAI starts with Etsy custom order spec collection. But the core technology — AI-powered structured data collection through conversation — applies anywhere a business needs to collect detailed information from a customer:

- **Shopify** custom order sellers (10x the market of Etsy)
- **Freelancers** collecting project briefs from clients
- **Wedding vendors** collecting event details from couples
- **Contractors** collecting project specs from homeowners
- **Healthcare** collecting patient intake forms
- **Real estate** collecting buyer preference profiles

The intake conversation is a universal SaaS primitive. ETSAI is building it for the market that needs it most right now — and the one where we can prove it works fastest.

---

## Team

**Noah** — Solo founder. Built the entire product from concept to production-ready SaaS. Full-stack development, AI integration, product design, and go-to-market strategy.

---

## Ask

ETSAI is built. The product works. The market is enormous and unserved. The next step is deployment, beta testing with real sellers, and scaling through organic content and community engagement.

**What's needed:**
- Domain registration (~$12/year)
- Hosting (~$20/month)
- Stripe account (free, they take 2.9% + $0.30 per transaction)
- Claude API credits (~$20-50/month at early scale)
- Time for beta outreach and iteration

**Total cost to launch: under $100.**

---

*Built with Claude AI. Powered by the belief that makers should spend their time making, not messaging.*
