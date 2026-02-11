# ETSAI Go-To-Market Strategy
## Deep Research-Backed Plan — February 2026

---

## MARKET REALITY

### The Numbers
- **5.6M active Etsy sellers**, 89.6M active buyers, $12.5B GMS
- **~30% of GMS is custom/made-to-order** = **$3.75 billion** in custom orders
- **~1.68M sellers** regularly handle custom/personalized orders
- Average custom order seller earns $1,000-5,000/mo — your ICP
- **60% of Etsy customer complaints** are communication-related
- Etsy's built-in personalization field is a single text box (1,024 chars) with known truncation bugs

### The Competitive Landscape
**There is NO direct competitor.** This is genuine whitespace.

| Tool | What It Does | Price | Why It's NOT ETSAI |
|------|-------------|-------|-------------------|
| HelloCustom | Reads Etsy personalization box, applies to POD templates | $29.99/mo + per-sale | Only works for print-on-demand. Reads existing text, doesn't collect missing specs. |
| Customily | Visual product personalizer with live preview | $49/mo + per-sale | Design tool, not spec collection. "Put my name on a mug" not "I need 8 custom specs" |
| Teeinblue | POD post-purchase personalization links | $29-49/mo | Same as Customily — visual POD personalizer |
| Google Forms | Generic form builder | Free | No AI, no Etsy integration, no conversation, no branding |
| Etsy Messages | Built-in messaging | Free | 4-8 messages per order, 2-5 days to collect specs, zero structure |

**ETSAI's position**: The only tool that uses AI conversation to intelligently collect complex custom order specs. Everyone else does visual personalization for simple POD. Nobody solves the "I need ring size, engraving text, font choice, metal type, stone preference, and turnaround priority" problem.

### What Sellers Do Today (And Why It Sucks)
1. **Etsy Messages** (90%+ of sellers) — copy-paste question lists, chase responses for days
2. **Google Forms** (power users) — no AI, breaks Etsy ecosystem, manual linking
3. **Etsy's personalization box** — single field, truncation bugs, no validation
4. **Canva order form templates** — static PDFs, not digital-first

---

## WHERE THE SELLERS ARE

### Tier 1: Highest Concentration

| Platform | Size | Notes |
|----------|------|-------|
| **Facebook: "The Etsy Sellers Group"** | ~120,000 members | Most active. Custom order complaints frequent. Limited self-promo (designated threads). |
| **Facebook: "Ecom Queens Community"** | ~50,000 | Female ecom entrepreneurs. Designated promo threads. |
| **Facebook: "The Handmade Business"** | ~43,000 | Marketing/branding focused. More professional sellers. |
| **Reddit: r/EtsySellers** | ~204,000 | Seller-only. Very active. **Strict no self-promo** — must be genuine value-add. |
| **Reddit: r/Etsy** | ~237,000 | Mixed buyer/seller. Same strict rules. |
| **YouTube: Brandon Timothy** | 161K subs | Etsy growth tips. Partnership potential. |
| **YouTube: Dylan Jahraus** | 120K subs + 111K TikTok | Multi-six-figure seller. Runs $27M+ course business. |
| **YouTube: Starla Moore** | 116K subs | SEO expert. Partners with eRank. |
| **YouTube: Kara Buntin** | 52K subs | Operations-focused. Perfect ETSAI fit. |

### Tier 2: High Value

| Platform | Size | Notes |
|----------|------|-------|
| **TikTok: Liz Fox Roseberry** | ~500K | Jewelry seller. Viral content drove 20K+ sales. |
| **TikTok: The Fast Track Girl** | ~126K | Etsy hacks, eRank tutorials. |
| **Etsy Community Hub** | 10,000+ Teams | Direct access. Requires subtlety. Search for "custom orders" tagged teams. |
| **Podcasts: Wolf Moves Only** | Top 1% seller ($600K+) | 30.8K Instagram. Guest appearance potential. |
| **Podcasts: Etsy Conversations** | 4.7/5 Apple, 408 reviews | Engaged listener base. |

### Tier 3: Supplementary
- **Discord**: ~15 Etsy servers, small but engaged
- **Twitter/X**: ~2K in Etsy sellers community, allows self-promo
- **Pinterest**: Traffic-driving, not community-building

---

## THE STRATEGY: 3 PARALLEL ATTACK VECTORS

Everything happens simultaneously. Not sequentially. Speed kills.

---

### VECTOR 1: COLD OUTREACH MACHINE (Build This Together)

This is the highest-leverage, fastest-to-revenue channel. We build an automated pipeline that finds custom order sellers and reaches them with personalized messages.

#### Step 1: Build the Etsy Seller Scraper

We already have `scraper.py`. Extend it to build a **lead generation scraper** that:

1. **Crawls Etsy search results** for shops selling custom/personalized items
   - Search queries: "custom [jewelry/portrait/engraving/ring/sign/etc.]"
   - Filter by: "Accepts custom orders" badge, 100+ sales, 4+ star rating

2. **Extracts from each shop page**:
   - Shop name, owner name
   - Shop URL
   - Social links (Instagram, website, Facebook — Etsy shows these on shop pages)
   - Number of sales, reviews, star rating
   - Product categories (jewelry, home decor, apparel, etc.)
   - Whether listings mention "custom", "personalized", "made to order"
   - Number of listings with personalization enabled

3. **Scores each lead** by likelihood of being a good ETSAI customer:
   - High score: 100+ sales + custom orders + multiple personalized listings + active social presence
   - Medium score: 50+ sales + some custom listings
   - Low score: Few sales or no custom focus

4. **Enriches with contact info**:
   - Instagram handle → DM target
   - Website → scrape for email (contact page, footer)
   - Use Hunter.io API ($49/mo) or Apollo.io ($49/mo) for email enrichment

**Output**: CSV with columns: `shop_name, owner_name, etsy_url, instagram, email, website, sales_count, custom_score, niche`

**Target**: 10,000 leads in the first week. This is achievable — Etsy has millions of shops and the data is publicly accessible.

#### Step 2: Build the AI Personalization Engine

Use Claude API (you already have it integrated) to generate personalized outreach:

```
For each lead, generate a personalized first line based on:
- Their shop name and niche
- A specific product they sell
- The custom order pain point relevant to their category
```

Example outputs:
- **Jewelry seller**: "I saw your custom engraved rings — how do you currently collect ring size, font choice, and engraving text from each buyer?"
- **Portrait artist**: "Your pet portraits are incredible. Quick question — do you collect reference photos and style preferences through Etsy messages or some other way?"
- **Sign maker**: "Love the custom wood signs. When someone orders, how many messages does it usually take to nail down the text, font, size, and finish?"

**This costs ~$0.01 per personalization** with Haiku. At 10,000 leads, that's $100.

#### Step 3: Multi-Channel Outreach Sequences

**Email (via Instantly.ai — $30/mo)**:
- Warm up 3 email domains ($10/year each via Namecheap)
- 50 emails/day per domain = 150/day = 4,500/month
- Sequence: 3 emails over 10 days
- Expected response rate: 3-8% (industry average for cold B2B email is 1-5%; we'll beat it with personalization)

**Instagram DMs (manual + semi-automated)**:
- 20-30 DMs/day (stay under Instagram's limits)
- Use the personalized first lines from Step 2
- DMs convert 2-3x higher than email because they feel more personal
- Target: sellers who have Instagram linked on their Etsy shop

**Sequence Framework**:

| Day | Channel | Message |
|-----|---------|---------|
| 1 | Email or DM | Personalized question about their custom order workflow. No pitch. |
| 3 | Same channel | If they respond: share the tool. If no response: follow-up with value (link to a blog post about custom order tips). |
| 7 | Same channel | Final touch: 30-second demo video link + free trial offer. |

**Projected numbers at steady state (Month 1)**:
- 4,500 email touches + 600 DMs = 5,100 outreach/month
- 3-5% response rate = 150-255 conversations
- 20-30% of conversations → trial signup = 30-75 trials
- 25-40% trial → paid = 8-30 paying customers
- At $29-59/mo average = **$230 - $1,770 MRR from outreach alone**

#### Step 4: Build a CRM Dashboard (Optional, Week 2)

Simple internal tool to track:
- Leads scraped, contacted, responded, signed up, converted
- Which niches convert best
- Which message templates get the highest response rates

We can build this as a simple page in the ETSAI admin panel.

---

### VECTOR 2: CONTENT ENGINE (SEO + Social)

#### Short-Form Video (Start Day 1)

This is the fastest organic channel. TikTok's algorithm gives new accounts reach.

**Content formula** (record these on your phone/screen):

| # | Video Concept | Hook | Length |
|---|--------------|------|--------|
| 1 | Side-by-side: Etsy messages chaos vs. ETSAI clean spec sheet | "This is what custom orders look like vs. what they could look like" | 30s |
| 2 | Screen recording of buyer completing intake in real-time | "My buyer just filled out every spec in 90 seconds" | 45s |
| 3 | Timer challenge: buyer completes full intake | "Can my buyer give me a complete spec sheet in under 2 minutes?" | 60s |
| 4 | "Day in my life" as a custom order seller, featuring the link | "The one tool that changed my Etsy workflow" | 45s |
| 5 | Scrolling through 15 Etsy messages vs. 1 clean spec sheet | "15 messages. 4 days. For ONE order. Never again." | 20s |
| 6 | "If you make custom orders on Etsy, stop doing this" | Call out the Google Forms / message copy-paste workflow | 30s |
| 7 | Reaction to Etsy's personalization box character limit bug | "Etsy literally cuts off your buyer's customization text" | 30s |

**Posting schedule**: 1-2 videos/day across TikTok, Instagram Reels, YouTube Shorts. Same video, all 3 platforms. This is 15-30 minutes of work per day.

**Hashtags**: #EtsySeller #EtsyTips #CustomOrders #SmallBusinessTikTok #HandmadeBusiness #EtsyShop #EtsySuccess

#### SEO Blog Content (Start Week 1)

**High-intent keywords to target** (low competition, high purchase intent):

| Keyword Cluster | Article Title | Funnel Stage |
|----------------|---------------|--------------|
| "etsy custom order message template" | "The Only Etsy Custom Order Template You'll Ever Need (Free Download)" | Top — capture leads with free template, upsell ETSAI |
| "how to collect custom order specs etsy" | "5 Ways Etsy Sellers Collect Custom Order Specs (And Which One Saves 20 Hours/Month)" | Mid — comparison article, ETSAI wins |
| "etsy personalization character limit" | "Etsy's Personalization Box Is Broken. Here's What to Use Instead." | Mid — problem-aware searchers |
| "etsy buyer not responding custom order" | "What to Do When Your Etsy Buyer Ghosts You on Custom Details" | Top — pain point, introduce automation |
| "etsy seller tools 2026" | "The 15 Best Etsy Seller Tools in 2026 (Honest Reviews)" | Top — listicle, include ETSAI |
| "etsy custom order management" | "The Complete Guide to Managing Custom Orders on Etsy" | Mid — comprehensive guide |
| "how to offer custom orders on etsy" | "How to Offer Custom Orders on Etsy Without Losing Your Mind" | Top — new sellers learning |
| "etsy order form template" | "Free Etsy Order Form Template (Better Than Google Forms)" | Top — lead magnet |

**Content velocity**: 2 articles/week. Each article: 1,500-2,500 words, SEO-optimized, includes a CTA to try ETSAI free.

**Lead magnet**: "Free Etsy Custom Order Message Template Pack" — downloadable PDF with pre-written question templates for 10 product categories. Captures email → nurture sequence → ETSAI trial.

#### Programmatic SEO (Week 2-3)

Build landing pages at scale:
- `/for/jewelry-sellers` — "AI Spec Collection for Custom Jewelry Orders"
- `/for/portrait-artists` — "AI Spec Collection for Custom Portrait Orders"
- `/for/sign-makers` — "AI Spec Collection for Custom Sign Orders"
- `/for/wedding-vendors` — "AI Spec Collection for Wedding Custom Orders"
- `/for/pet-products` — "AI Spec Collection for Custom Pet Products"

Each page: same template, niche-specific copy, relevant example questions, category-specific demo. **We can build this together** — a simple template system that generates these pages from a config file.

#### Directory Listings (Day 1 — Takes 30 Minutes)

Submit ETSAI to:
- **Product Hunt** — prep a launch (we'll schedule this for max impact)
- **SaaSHub** — free listing
- **AlternativeTo** — list as alternative to Google Forms, Etsy Messages
- **G2** — free listing, start collecting reviews
- **Capterra** — free listing
- **AppSumo** — consider a lifetime deal for early traction
- **BetaList** — pre-launch/early product listing
- **Indie Hackers** — community post + product listing
- **Hacker News** — "Show HN" post

---

### VECTOR 3: COMMUNITY INFILTRATION (Organic Presence)

This isn't about spamming groups. It's about becoming the known expert on custom order management in every community where Etsy sellers hang out.

#### Facebook Groups — Systematic Approach

**Week 1**: Join these 5 groups:
1. The Etsy Sellers Group (120K)
2. Ecom Queens Community (50K)
3. The Handmade Business (43K)
4. Etsy Elite (11K)
5. Craftsposure (30K)

**Daily routine (15 min/day)**:
- Search each group for "custom order" posts from the last 24 hours
- Leave a genuinely helpful comment with a specific tip
- Once per week, post a valuable tip about custom order management (no link, no pitch)
- When someone specifically asks "how do you handle custom order specs?", describe ETSAI naturally

**Week 3**: Post a "before/after" showing the difference. Something like:
> "I was spending 20 minutes per custom order collecting specs through messages. Built a tool that does it in 2 minutes. Would anyone want to try it free? Not trying to sell anything — genuinely want feedback from other custom order sellers."

This "building in public" / feedback-seeking approach is welcomed in most groups.

#### Reddit — Long Game, Big Payoff

**Strategy**: Build karma on r/EtsySellers by being genuinely helpful for 2 weeks before ever mentioning ETSAI.

- Answer 2-3 questions per day about custom order management
- Share tips about managing buyer communication
- When the moment is right (someone asks "what tools do you use?"), mention ETSAI naturally
- Eventually post: "I built a tool that collects custom order specs via AI chat — looking for beta testers"

**r/SideProject, r/SaaS, r/IndieBiz** — these subs are more open to self-promotion and "I built this" posts.

#### Podcast Outreach

**Target these 3 podcasts for guest appearances**:
1. **Wolf Moves Only** (Brittany Lewis) — she's a top 1% seller, would understand the pain
2. **Etsy Conversations** — general Etsy topics, custom orders are always relevant
3. **How to Sell Your Stuff** — practical tips focus, perfect for a tool demo

**Pitch angle**: "I'm an Etsy seller who built an AI tool to solve the custom order messaging problem. I can share the data on how much time sellers waste on spec collection and what an automated approach looks like."

---

## WHAT WE BUILD TOGETHER

These are tools/features we code to accelerate the GTM:

### 1. Etsy Lead Scraper (`lead_scraper.py`)
- Crawl Etsy search results for custom order shops
- Extract shop data + social links + contact info
- Score leads by custom order intensity
- Output clean CSV for outreach tools
- **Build time**: 1-2 sessions

### 2. AI Outreach Personalizer (`outreach_engine.py`)
- Takes lead CSV as input
- Uses Claude Haiku to generate personalized first lines
- Outputs enriched CSV ready for Instantly.ai import
- **Build time**: 1 session

### 3. Programmatic Landing Pages
- Niche-specific pages (`/for/jewelry`, `/for/portraits`, etc.)
- Template system with category-specific copy, example questions, and demo
- SEO-optimized with structured data
- **Build time**: 1 session

### 4. Free Lead Magnet Tool
- Standalone page: "Etsy Custom Order Message Generator"
- Seller enters product type → AI generates a message template they can copy-paste
- Captures email before showing result → nurture to ETSAI trial
- Lives at something like `/tools/message-generator`
- **Build time**: 1 session

### 5. Viral Loop: Buyer → Seller Lead
- When a buyer completes an ETSAI intake, they see "Powered by ETSAI"
- Other sellers see this when buyers tell them about the experience
- Add "Are you an Etsy seller? Try ETSAI free" link on the intake completion page
- **Build time**: 30 minutes (template edit)

### 6. Referral System
- Give existing sellers a referral code
- "Refer a seller, get 1 month free"
- Track referrals in the sellers table
- **Build time**: 1 session

### 7. Outreach CRM Dashboard
- Admin page showing: leads scraped, contacted, responded, signed up, converted
- Track which niches and message templates perform best
- **Build time**: 1 session

---

## THE AGGRESSIVE TIMELINE

### Day 1 (Today)
- [ ] Record first 3 short-form videos (screen recordings of ETSAI in action)
- [ ] Post on TikTok, Reels, Shorts
- [ ] Submit to 5 directories (SaaSHub, AlternativeTo, BetaList, Indie Hackers, SaaS listings)
- [ ] Join 5 Facebook groups
- [ ] Start building lead scraper together

### Day 2-3
- [ ] Finish lead scraper, run first batch (1,000 leads)
- [ ] Build AI outreach personalizer
- [ ] Set up Instantly.ai + warm up email domains
- [ ] Write first 2 SEO blog posts
- [ ] Post 2 more videos
- [ ] Leave 10 helpful comments in Facebook groups

### Day 4-5
- [ ] First cold email batch goes out (100 emails)
- [ ] Start Instagram DM outreach (20/day)
- [ ] Build programmatic landing pages (`/for/jewelry`, etc.)
- [ ] Post 2 more videos
- [ ] First Reddit comments on r/EtsySellers

### Day 6-7
- [ ] Build free lead magnet tool (message generator)
- [ ] Publish 2 blog posts
- [ ] Continue outreach (150/day email + 30/day DM)
- [ ] Post 2 more videos
- [ ] Implement viral buyer → seller loop

### Week 2
- [ ] Scale outreach to 200/day
- [ ] 4 more videos posted
- [ ] 2 more blog posts
- [ ] Product Hunt launch prep
- [ ] Reach out to 3 micro-influencers (Kara Buntin, smaller YouTubers)
- [ ] Build referral system
- [ ] First paying customers from outreach

### Week 3
- [ ] Product Hunt launch day
- [ ] 2 more blog posts (8 total)
- [ ] Continue daily outreach + video
- [ ] First podcast pitch sent
- [ ] Analyze: which niche converts best? Double down.

### Week 4
- [ ] First influencer video goes live
- [ ] 10+ blog posts live and indexing
- [ ] Outreach machine at steady state
- [ ] Referral system active
- [ ] Review metrics: MRR, CAC, conversion rates by channel

**Week 4 Target**: 50-100 trial signups, 15-30 paying customers, $500-1,500 MRR

---

## METRICS THAT MATTER

| Metric | Day 7 Target | Day 14 Target | Day 30 Target |
|--------|-------------|---------------|---------------|
| Leads scraped | 2,000 | 5,000 | 10,000 |
| Outreach sent | 500 | 2,000 | 5,000 |
| Response rate | 3% | 4% | 5%+ |
| Trial signups | 10 | 30 | 75 |
| Paid conversions | 2 | 8 | 20 |
| MRR | $58 | $350 | $800+ |
| Videos posted | 7 | 14 | 28 |
| Blog posts live | 2 | 6 | 10 |
| SEO traffic | 0 | 50/mo | 200/mo |

---

## BUDGET (Month 1)

| Item | Cost | Notes |
|------|------|-------|
| Instantly.ai | $30/mo | Cold email automation |
| 3 email domains | $30/year | Namecheap, for email warm-up |
| Hunter.io | $49/mo | Email enrichment (can use free tier first: 25 searches/mo) |
| Claude API (outreach personalization) | ~$50 | 10K personalizations at $0.005 each |
| Domain for lead magnet | $0 | Use etsai.com subdomain |
| TikTok/Reels/Shorts | $0 | Organic, screen recordings |
| Facebook Groups | $0 | Organic participation |
| Reddit | $0 | Organic participation |
| **Total Month 1** | **~$130-160** | |

Everything else is sweat equity and code we build together.

---

## THE UNFAIR ADVANTAGE: WHAT ONLY ETSAI CAN DO

1. **The product IS the marketing.** Every buyer who uses the intake chat sees ETSAI in action. Every completed spec sheet is a proof point. The intake experience itself is a demo.

2. **Built-in viral loop.** Buyers talk to sellers. "That spec collection thing was cool, what was that?" Sellers hear about ETSAI from buyers who experienced it.

3. **AI-native positioning.** You're not retrofitting AI onto an existing tool. ETSAI was built AI-first. The conversation quality IS the moat. No form builder or visual personalizer can replicate an intelligent conversation that adapts to what the buyer says.

4. **Etsy's brokenness is your tailwind.** Etsy's personalization box has known bugs (truncation, character limit not enforced). Their AI investment is in search/discovery and seller reply assistance — they have shown zero indication of building structured spec collection. Every month Etsy doesn't fix this, ETSAI's value grows.

5. **Data flywheel.** Every conversation teaches you which questions work for which product categories. Over time, your AI-generated questions get better than anything a human could write. This compounds and becomes impossible to replicate.

---

## NEXT STEP

**Let's build the lead scraper right now.** That's the highest-leverage code we can write today. 10,000 qualified leads in your pipeline by tomorrow, outreach starts Day 2.

Say the word and we start coding `lead_scraper.py`.
