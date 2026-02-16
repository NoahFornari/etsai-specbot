"""
ETSAI Marketing Content — Blog posts, comparison pages, changelog, about page.
All content stored as Python dicts (no DB, no markdown library).
"""

# =============================================================
# BLOG POSTS
# =============================================================

BLOG_POSTS = {
    "etsy-custom-order-template": {
        "title": "The Only Etsy Custom Order Template You'll Ever Need",
        "slug": "etsy-custom-order-template",
        "meta_description": "Free custom order message template for Etsy sellers. Copy-paste this AI-optimized template to collect ring sizes, engraving text, colors, and every spec in one message.",
        "published_date": "2026-02-17",
        "author": "Noah Fornari",
        "category": "Templates",
        "read_time": "8 min",
        "sections": [
            {
                "heading": None,
                "content": """
<p>You just got a notification. Someone bought your custom engraved bracelet. Awesome. Now comes the part you dread.</p>
<p>You open Etsy messages, copy-paste your usual question list, and send it off. Then you wait. And wait. The buyer responds 18 hours later with half the info you need. You ask follow-up questions. They respond the next day. By the time you actually have everything you need to start working, it's been three days and six messages.</p>
<p>Sound familiar? You're not alone. Virtually every Etsy seller who does custom work goes through this exact cycle, multiple times a week. The average custom order takes 4-8 messages over 2-5 days just to collect the specs.</p>
<p>Here's a template that cuts that down significantly. And then I'll show you something that cuts it down to under 2 minutes.</p>
"""
            },
            {
                "heading": "Why Most Custom Order Templates Fail",
                "content": """
<p>Before we get to the template, let's talk about why the ones floating around Etsy forums don't work well.</p>
<p><strong>Problem 1: Wall of text.</strong> Most templates are 10-15 lines of questions crammed into one message. Buyers see that wall and either skim it or close the app and come back "later" (which means tomorrow, maybe).</p>
<p><strong>Problem 2: No structure.</strong> When buyers respond, they answer in random order, skip questions, or give partial answers. "Gold, size 7, for my mom" — but which font? What length? Do they want a box?</p>
<p><strong>Problem 3: No validation.</strong> A buyer types "size medium" for a ring. Is that a 7? An 8? You have to ask again. There's no way to enforce the right format.</p>
<p><strong>Problem 4: Copy-paste fatigue.</strong> You're sending the same message hundreds of times. It stops feeling personal. Buyers can tell it's a template, and engagement drops.</p>
<p>The template below addresses the first two problems. It's structured, scannable, and grouped logically. But it can't fix problems 3 and 4 — that requires something smarter than a text message.</p>
"""
            },
            {
                "heading": "The Template (Copy This)",
                "content": """
<p>Here's a universal template you can customize for any product. Replace the bracketed sections with your specific details.</p>
<blockquote>
<p>Hey [Buyer Name]! Thanks so much for your order — I'm excited to make this for you!</p>
<p>To get started, I need a few details. Don't worry if you're not sure about something — just let me know and I'll help you decide.</p>
<p><strong>The basics:</strong><br>
1. [Primary spec — e.g., "What name or text for the engraving?"]<br>
2. [Size/dimension — e.g., "Ring size? (If unsure, I can send a sizing guide)"]<br>
3. [Material/color — e.g., "Gold, silver, or rose gold?"]</p>
<p><strong>Style preferences:</strong><br>
4. [Style choice — e.g., "Font preference? I have script, block, and modern options"]<br>
5. [Optional add-on — e.g., "Would you like a gift box? (+$5)"]</p>
<p><strong>Logistics:</strong><br>
6. [Timeline — e.g., "Is this for a specific date? I typically ship in 5-7 business days"]</p>
<p>Feel free to answer all at once or one at a time — whatever's easiest!</p>
</blockquote>
<p><strong>Why this works better than most templates:</strong></p>
<ul>
<li>It's grouped into sections (basics, style, logistics) so it doesn't feel like a wall</li>
<li>It starts warm and personal</li>
<li>It offers help for uncertain buyers ("if unsure, I can send a sizing guide")</li>
<li>It gives permission to answer however they want</li>
<li>It's short enough that buyers actually read the whole thing</li>
</ul>
"""
            },
            {
                "heading": "Customizing It for Your Product",
                "content": """
<p>Here's how to adapt the template for common Etsy custom product categories:</p>
<p><strong>Custom jewelry (rings, necklaces, bracelets):</strong></p>
<ul>
<li>Name or text for engraving</li>
<li>Ring size / chain length / wrist size</li>
<li>Metal choice (gold, silver, rose gold, platinum)</li>
<li>Font style</li>
<li>Stone preference (if applicable)</li>
<li>Gift box or special packaging</li>
</ul>
<p><strong>Custom portraits (pet portraits, family portraits, digital art):</strong></p>
<ul>
<li>Number of subjects</li>
<li>Reference photos (ask them to attach)</li>
<li>Art style preference</li>
<li>Background preference</li>
<li>Size / dimensions</li>
<li>Special requests (clothing, accessories, text overlay)</li>
</ul>
<p><strong>Custom signs (wood signs, neon signs, wedding signs):</strong></p>
<ul>
<li>Text / wording</li>
<li>Size</li>
<li>Font choice</li>
<li>Color / finish</li>
<li>Mounting preference (hanging, stand, wall-mount)</li>
<li>Date needed by</li>
</ul>
<p><strong>Custom clothing (embroidered items, custom prints):</strong></p>
<ul>
<li>Size (with measurement guide link)</li>
<li>Text or design details</li>
<li>Placement on garment</li>
<li>Thread / print color</li>
<li>Font or design style</li>
<li>Quantity</li>
</ul>
"""
            },
            {
                "heading": "The Problem With Templates (And What Actually Works)",
                "content": """
<p>Here's the thing about templates: they're better than nothing. But they still have the same fundamental problem — you're trying to collect structured data through an unstructured medium.</p>
<p>Even with the best template in the world, you'll still deal with:</p>
<ul>
<li><strong>Partial responses.</strong> Buyers answer 3 out of 6 questions. You follow up. They answer 1 more. Repeat.</li>
<li><strong>Wrong formats.</strong> "My ring size is medium" or "I want it in the pretty gold color" — you need to translate this into actionable specs.</li>
<li><strong>Lost messages.</strong> The specs are buried in a message thread somewhere. When you're ready to start production, you're scrolling through 12 messages to find the ring size.</li>
<li><strong>Time.</strong> Even with a template, the average back-and-forth still takes 2-4 messages and 1-3 days. Multiply that by 30-50 orders a month.</li>
</ul>
<p>Templates treat the symptom. The real problem is that Etsy's messaging system was built for conversations, not data collection.</p>
"""
            },
            {
                "heading": "What If the Buyer Could Just... Talk?",
                "content": """
<p>That's why we built <a href="/" style="color: var(--brand); font-weight: 600;">ETSAI</a>. Instead of sending a template and hoping for the best, you send a single link. The buyer clicks it and has a natural conversation with an AI assistant that collects every spec you need.</p>
<p>If a buyer says "I want Sarah in gold with cursive font, size 7" — the AI extracts the name, material, font, and size all from one message. It confirms what it understood, then asks for whatever's still missing. The whole thing takes about 90 seconds.</p>
<p>You get a clean spec sheet with every answer organized and labeled. No digging through threads. No follow-up messages. No waiting days for responses.</p>
<p>The template above will help you today. ETSAI will help you every day after that.</p>
<p><a href="/#auth" class="btn-primary px-6 py-2.5 text-sm font-semibold inline-block no-underline" style="margin-top: 1rem;">Try ETSAI free for 14 days</a></p>
"""
            },
        ],
    },

    "collect-custom-order-specs-etsy": {
        "title": "5 Ways Etsy Sellers Collect Custom Order Specs (And Which One Saves 20 Hours/Month)",
        "slug": "collect-custom-order-specs-etsy",
        "meta_description": "Compare 5 methods for collecting custom order specs on Etsy: Etsy messages, Google Forms, personalization box, PDFs, and AI chat. See which saves the most time.",
        "published_date": "2026-02-19",
        "author": "Noah Fornari",
        "category": "Guides",
        "read_time": "10 min",
        "sections": [
            {
                "heading": None,
                "content": """
<p>If you sell custom products on Etsy — jewelry, portraits, signs, clothing, anything made-to-order — you know the drill. Every single order starts with the same question: "How do I get the specs I need from this buyer?"</p>
<p>Some sellers copy-paste message templates. Some use Google Forms. Some rely on Etsy's built-in personalization field. And some just wing it every time and hope for the best.</p>
<p>We looked at what sellers actually do, talked to dozens of custom order sellers, and compared every method. Here's what works, what doesn't, and which approach saves the most time.</p>
"""
            },
            {
                "heading": "Method 1: Etsy Messages (What 90% of Sellers Do)",
                "content": """
<p>This is the default. A buyer purchases your custom item, and you send them a message with your questions. Maybe you have a template saved somewhere, maybe you type it fresh every time.</p>
<p><strong>How it works:</strong> Buyer buys → you send a message with questions → buyer responds → you send follow-ups for missing info → repeat until you have everything.</p>
<p><strong>Pros:</strong></p>
<ul>
<li>Free — it's built into Etsy</li>
<li>Buyers are already familiar with Etsy messages</li>
<li>No external tools or setup required</li>
</ul>
<p><strong>Cons:</strong></p>
<ul>
<li>Takes 4-8 messages over 2-5 days per order on average</li>
<li>Buyers respond with partial info, requiring follow-ups</li>
<li>Specs are scattered across a message thread — hard to find later</li>
<li>No validation — buyers can give wrong formats or skip questions</li>
<li>At 50 orders/month, you're spending 12-25 hours just asking questions</li>
</ul>
<p><strong>Best for:</strong> Sellers doing fewer than 5 custom orders a month who don't mind the back-and-forth.</p>
"""
            },
            {
                "heading": "Method 2: Google Forms",
                "content": """
<p>Power users often level up to Google Forms. You create a form with all your questions, share the link in your Etsy message, and buyers fill it out.</p>
<p><strong>How it works:</strong> Create form once → send link after purchase → buyer fills out form → responses in Google Sheets.</p>
<p><strong>Pros:</strong></p>
<ul>
<li>Free</li>
<li>Structured — every question gets its own field</li>
<li>Responses organized in a spreadsheet</li>
<li>Can add required fields, dropdowns, file uploads</li>
</ul>
<p><strong>Cons:</strong></p>
<ul>
<li>Breaks the Etsy ecosystem — buyers click an external link, which feels weird</li>
<li>No AI — you have to write and maintain every question manually</li>
<li>Rigid format — if a buyer gives 3 answers in one response, the form can't handle it</li>
<li>No branding — looks like a generic Google form, not your shop</li>
<li>Not conversational — feels like filling out a government form</li>
<li>Buyers with multiple custom details struggle to fit into fixed fields</li>
</ul>
<p><strong>Best for:</strong> Sellers who need structured data and don't mind sending buyers off-platform.</p>
"""
            },
            {
                "heading": "Method 3: Etsy's Built-In Personalization Box",
                "content": """
<p>Etsy lets sellers add a personalization field to their listings. Buyers fill it out before purchasing.</p>
<p><strong>How it works:</strong> Enable personalization on your listing → buyer sees a text box → they type their customization details → you see it on the order.</p>
<p><strong>Pros:</strong></p>
<ul>
<li>Free and built into Etsy</li>
<li>Buyers fill it out before purchase (no follow-up needed... in theory)</li>
<li>Shows up right on the order</li>
</ul>
<p><strong>Cons:</strong></p>
<ul>
<li><strong>1,024 character limit.</strong> For products with 5+ specs, that's not enough</li>
<li><strong>Known truncation bugs.</strong> Community forums are full of reports where buyer text gets cut off</li>
<li><strong>Single text box.</strong> No separate fields, no labels, no structure. You get a blob of text</li>
<li><strong>Zero validation.</strong> Buyers type "medium" for a ring size. What does that mean?</li>
<li><strong>Buyers skip it.</strong> The personalization box is optional, and many buyers miss it entirely or write "I'll message you"</li>
<li><strong>No follow-up mechanism.</strong> If the buyer gives incomplete info, you're back to messaging anyway</li>
</ul>
<p><strong>Best for:</strong> Simple personalizations with 1-2 fields (like a name on a mug). Not for complex custom orders.</p>
"""
            },
            {
                "heading": "Method 4: PDF Order Forms",
                "content": """
<p>Some sellers create branded PDF order forms in Canva or similar tools and send them to buyers.</p>
<p><strong>How it works:</strong> Design a PDF form → send to buyer → they fill it out (somehow) → send it back.</p>
<p><strong>Pros:</strong></p>
<ul>
<li>Looks professional and branded</li>
<li>Can include visual references and examples</li>
</ul>
<p><strong>Cons:</strong></p>
<ul>
<li>Most buyers can't fill out PDFs digitally — they print, write, scan, or take a photo</li>
<li>Terrible mobile experience (most Etsy buyers are on phones)</li>
<li>No validation whatsoever</li>
<li>Adds friction — buyers are less likely to complete it</li>
<li>Still requires you to manually read and extract the specs</li>
</ul>
<p><strong>Best for:</strong> Honestly? Almost nobody in 2026. This is the fax machine of custom order collection.</p>
"""
            },
            {
                "heading": "Method 5: AI-Powered Conversation",
                "content": """
<p>This is the newest approach, and it's what we built <a href="/" style="color: var(--brand); font-weight: 600;">ETSAI</a> to do. Instead of forms or messages, you send buyers a link to a conversational AI that collects their specs through natural chat.</p>
<p><strong>How it works:</strong> Import your product → AI generates questions → create order, get link → send to buyer → buyer chats with AI → specs collected in under 2 minutes → you get an organized spec sheet.</p>
<p><strong>Pros:</strong></p>
<ul>
<li>Buyers actually enjoy it — it feels like chatting, not filling out a form</li>
<li>AI understands context — "gold cursive Sarah size 7" extracts 4 specs from one message</li>
<li>Built-in validation — AI knows that "medium" isn't a ring size and asks for clarification</li>
<li>Under 2 minutes per buyer — compared to 2-5 days with messages</li>
<li>Clean spec sheet output — organized, labeled, ready for production</li>
<li>Works on mobile perfectly</li>
</ul>
<p><strong>Cons:</strong></p>
<ul>
<li>Costs $19-79/month (depending on plan) after a free trial</li>
<li>Newer tool — smaller company, less brand recognition</li>
<li>Requires sending buyers to an external link (like Google Forms, but the experience is much better)</li>
</ul>
<p><strong>Best for:</strong> Sellers doing 10+ custom orders a month who want to save serious time and deliver a better buyer experience.</p>
<p><em>Full disclosure: we built ETSAI, so we're biased. But we built it because we saw the problem firsthand and nothing else solved it.</em></p>
"""
            },
            {
                "heading": "The Comparison",
                "content": "TABLE"
            },
            {
                "heading": "Which Should You Use?",
                "content": """
<p>Here's the honest recommendation:</p>
<ul>
<li><strong>Under 5 custom orders/month:</strong> Etsy messages with a good template are fine. Use <a href="/blog/etsy-custom-order-template" style="color: var(--brand);">our free template</a>.</li>
<li><strong>5-15 orders/month:</strong> Google Forms will save you some time, but expect friction and follow-ups.</li>
<li><strong>15+ orders/month:</strong> The time savings from AI-powered collection pay for themselves many times over. You're spending 5-15 hours/month on spec collection that could take 30 minutes.</li>
</ul>
<p>The personalization box is fine for simple stuff — a name on a mug, a color choice. But if your products need more than 2 specs, you need something better.</p>
<p><a href="/#auth" class="btn-primary px-6 py-2.5 text-sm font-semibold inline-block no-underline" style="margin-top: 1rem;">Try ETSAI free for 14 days</a></p>
"""
            },
        ],
        "comparison_table": {
            "headers": ["Method", "Cost", "Setup", "Buyer Experience", "Spec Quality", "Time Saved"],
            "rows": [
                ["Etsy Messages", "Free", "None", "Familiar but slow", "Low — scattered", "None"],
                ["Google Forms", "Free", "30 min", "OK — external link", "Medium", "Some"],
                ["Personalization Box", "Free", "2 min", "Convenient but limited", "Low — no validation", "Minimal"],
                ["PDF Forms", "Free", "1+ hour", "Poor on mobile", "Medium", "None"],
                ["AI Chat (ETSAI)", "$19/mo+", "5 min", "Great — conversational", "High — validated", "15-20 hrs/mo"],
            ]
        },
    },

    "etsy-personalization-box-broken": {
        "title": "Etsy's Personalization Box Is Broken. Here's What to Use Instead.",
        "slug": "etsy-personalization-box-broken",
        "meta_description": "Etsy's personalization field has a 1,024 character limit, truncation bugs, and zero validation. Here's why smart sellers are switching to AI-powered spec collection.",
        "published_date": "2026-02-21",
        "author": "Noah Fornari",
        "category": "Problems",
        "read_time": "7 min",
        "sections": [
            {
                "heading": None,
                "content": """
<p>You enabled personalization on your Etsy listing. Your buyer filled it out. You open the order, expecting to see all the details you need to start working. Instead, you see this:</p>
<blockquote>
<p>"Hi! I'd like the necklace in 14k gold with the name Sarah in script font. Chain length 18 inches. Can you also add a small heart charm? My ring size is 7 for the matching ring. For the engraving on the back I'd like 'Forever Yours' in bloc"</p>
</blockquote>
<p>That's it. The message just... stops. Your buyer typed more, but Etsy cut it off. Now you need to message them anyway to get the rest. The one thing the personalization box was supposed to prevent — back-and-forth messaging — is exactly what happens.</p>
"""
            },
            {
                "heading": "The 1,024 Character Limit",
                "content": """
<p>Etsy's personalization field has a hard limit of 1,024 characters. That sounds like a lot until you realize what custom order sellers actually need to collect.</p>
<p>Let's do the math for a custom engraved ring:</p>
<ul>
<li>Ring size: ~15 characters</li>
<li>Metal choice + explanation: ~40 characters</li>
<li>Engraving text: ~50 characters</li>
<li>Font preference: ~30 characters</li>
<li>Stone type and size: ~40 characters</li>
<li>Special instructions: ~100 characters</li>
</ul>
<p>That's already ~275 characters for a single ring. Now imagine a buyer ordering matching rings for a wedding party of 6. Or a custom family portrait with 5 people, each needing descriptions. Or a wedding invitation suite with ceremony details, reception details, RSVP info, and typography preferences.</p>
<p>1,024 characters isn't enough. And many sellers report that the actual limit seems to be even lower in practice.</p>
"""
            },
            {
                "heading": "The Truncation Bug",
                "content": """
<p>Search "personalization truncated" in any Etsy seller forum and you'll find dozens of threads. Buyers fill out the personalization box, but sellers receive incomplete text. Sometimes it's the character limit. Sometimes it's something else entirely.</p>
<p>The worst part? Neither the buyer nor the seller knows it happened until the seller reads the order. The buyer thinks they submitted everything. The seller sees partial data. And now you're messaging the buyer to ask for information they already provided.</p>
<p>"But I already told you my ring size" — yeah, that message never goes well.</p>
"""
            },
            {
                "heading": "Zero Validation, Zero Structure",
                "content": """
<p>The personalization field is a single text box. No separate fields. No labels. No dropdowns. No required formats. No file upload for reference photos.</p>
<p>So buyers type whatever they want, however they want:</p>
<ul>
<li>"size 7 gold cursive Sarah" — which spec is which?</li>
<li>"I want the pretty one" — which pretty one?</li>
<li>"Medium" for a ring size — what does medium mean?</li>
<li>"See attached photo" — there's no attachment feature</li>
</ul>
<p>You end up doing the same translation and follow-up work you were trying to avoid. The personalization box creates the illusion of structured collection while actually providing none of it.</p>
"""
            },
            {
                "heading": "Buyers Skip It Entirely",
                "content": """
<p>Here's the kicker: even when the personalization box is enabled and marked as required, many buyers skip it or write something unhelpful like "I'll message you the details." Some buyers genuinely don't see it during checkout. Others are on mobile and find it inconvenient to type everything in a tiny box.</p>
<p>Etsy's UI doesn't exactly make the personalization field prominent. It's a text box on a busy page full of buttons, shipping info, and payment fields. It's easy to miss, easy to rush through, and easy to write "TBD" in and move on.</p>
<p>Result: you still end up messaging the buyer. Every. Single. Time.</p>
"""
            },
            {
                "heading": "What Custom Order Sellers Actually Need",
                "content": """
<p>If you could design the perfect spec collection system from scratch, it would:</p>
<ul>
<li><strong>Have no character limit</strong> — let buyers provide as much detail as they want</li>
<li><strong>Validate answers</strong> — if someone says "medium" for a ring size, ask for the actual number</li>
<li><strong>Be structured</strong> — separate fields for separate specs, not one blob of text</li>
<li><strong>Support photos</strong> — reference images for portraits, logos for signs, inspiration boards</li>
<li><strong>Be conversational</strong> — feel like talking to a helpful person, not filling out a government form</li>
<li><strong>Work on mobile</strong> — because that's where most Etsy buyers are</li>
<li><strong>Give sellers a clean output</strong> — organized spec sheet, not a message thread to dig through</li>
</ul>
<p>Etsy's personalization box does none of these things. It's a text field from 2012 that hasn't been meaningfully updated since.</p>
"""
            },
            {
                "heading": "The Alternative: AI-Powered Spec Collection",
                "content": """
<p><a href="/" style="color: var(--brand); font-weight: 600;">ETSAI</a> replaces the personalization box (and the follow-up messages) with a single smart link. Your buyer clicks it and has a conversation with an AI assistant that collects every spec you need.</p>
<p>The AI understands natural language. If a buyer says "14k gold, script font, Sarah, 18 inch chain" — it extracts all four specs from one message, confirms them, and moves on to whatever's missing. No truncation, no character limits, no "but I already told you."</p>
<p><strong>How it works:</strong></p>
<ol>
<li>Import your product from Etsy (or describe it manually)</li>
<li>AI generates the perfect intake questions for your product</li>
<li>When you get an order, create an intake link and send it to your buyer</li>
<li>Buyer chats with the AI — takes about 90 seconds</li>
<li>You get an organized spec sheet with every answer labeled and validated</li>
</ol>
<p>No character limits. No truncation bugs. No follow-up messages. No digging through threads. Just clean specs, ready for production.</p>
<p><a href="/#auth" class="btn-primary px-6 py-2.5 text-sm font-semibold inline-block no-underline" style="margin-top: 1rem;">Replace the personalization box — try free</a></p>
"""
            },
        ],
    },
}


# =============================================================
# COMPARISON PAGES
# =============================================================

COMPARISON_PAGES = {
    "google-forms": {
        "title": "ETSAI vs Google Forms for Etsy Custom Orders",
        "slug": "google-forms",
        "meta_description": "Compare ETSAI and Google Forms for collecting Etsy custom order specs. See why AI-powered chat beats generic forms for buyer experience and spec quality.",
        "competitor_name": "Google Forms",
        "competitor_tagline": "A free, generic form builder. Many Etsy sellers use it as a workaround for collecting custom order details.",
        "verdict": "Google Forms is free and decent for basic collection. But if you're doing 10+ custom orders a month, ETSAI's AI-powered approach saves you hours of follow-ups and gives buyers a dramatically better experience.",
        "features": [
            {"name": "Built for Etsy custom orders", "etsai": True, "competitor": False},
            {"name": "AI-generated questions", "etsai": True, "competitor": False},
            {"name": "Conversational (not a form)", "etsai": True, "competitor": False},
            {"name": "Understands multi-answer messages", "etsai": True, "competitor": False},
            {"name": "Smart validation (ring sizes, etc.)", "etsai": True, "competitor": "Basic"},
            {"name": "Free tier", "etsai": "14-day trial", "competitor": True},
            {"name": "Etsy product import", "etsai": True, "competitor": False},
            {"name": "Organized spec sheet output", "etsai": True, "competitor": "Spreadsheet"},
            {"name": "Mobile-friendly buyer experience", "etsai": True, "competitor": "Partial"},
            {"name": "Custom branding", "etsai": "Business plan", "competitor": False},
            {"name": "File/photo uploads", "etsai": "Coming soon", "competitor": True},
            {"name": "Requires external link", "etsai": True, "competitor": True},
        ],
        "pros_etsai": [
            "Buyers enjoy the chat experience — feels natural, not like a form",
            "AI extracts multiple specs from a single message — no rigid one-field-at-a-time",
            "Built-in validation prevents bad data (ring sizes, formats, required fields)",
            "Organized spec sheets instead of raw spreadsheet rows",
            "Import products from Etsy — AI generates the right questions automatically",
            "Under 2 minutes per buyer vs. filling out a multi-page form",
        ],
        "cons_etsai": [
            "Costs $19-79/month after free trial",
            "Newer product — smaller company",
            "Photo uploads coming soon (not yet available)",
        ],
        "pros_competitor": [
            "Completely free, forever",
            "Familiar to most people",
            "Supports file uploads and multiple question types",
            "Google Sheets integration for tracking responses",
            "Can be used for anything, not just Etsy",
        ],
        "cons_competitor": [
            "Not built for Etsy — generic tool, no product awareness",
            "Breaks the Etsy ecosystem — external link feels off-brand",
            "No AI — you write and maintain every question manually",
            "Rigid form format — buyers can't give natural multi-answer responses",
            "No validation for product-specific fields (ring sizes, font names)",
            "You still manually process every response",
            "Looks like a generic Google form, not your shop",
        ],
    },

    "etsy-messages": {
        "title": "ETSAI vs Etsy Messages for Custom Order Specs",
        "slug": "etsy-messages",
        "meta_description": "Stop spending 4-8 messages over 2-5 days collecting custom order specs. Compare ETSAI's AI chat with Etsy's built-in messaging for spec collection.",
        "competitor_name": "Etsy Messages",
        "competitor_tagline": "Etsy's built-in messaging system. It's what every seller uses by default, and it's the reason custom orders take so long.",
        "verdict": "Etsy Messages are fine for conversations. They're terrible for structured data collection. If custom orders are a meaningful part of your business, ETSAI pays for itself in the first week.",
        "features": [
            {"name": "Purpose-built for spec collection", "etsai": True, "competitor": False},
            {"name": "AI understands natural language", "etsai": True, "competitor": False},
            {"name": "Collects all specs in one session", "etsai": True, "competitor": False},
            {"name": "Validates answers in real-time", "etsai": True, "competitor": False},
            {"name": "Organized spec sheet output", "etsai": True, "competitor": False},
            {"name": "Free", "etsai": "14-day trial", "competitor": True},
            {"name": "Built into Etsy", "etsai": False, "competitor": True},
            {"name": "Works for general communication", "etsai": False, "competitor": True},
            {"name": "Average time to collect specs", "etsai": "~2 minutes", "competitor": "2-5 days"},
            {"name": "Messages per order", "etsai": "1 link", "competitor": "4-8 messages"},
            {"name": "Follow-ups needed", "etsai": "Rare", "competitor": "Almost always"},
            {"name": "Specs easy to find later", "etsai": True, "competitor": False},
        ],
        "pros_etsai": [
            "Collects every spec in under 2 minutes — not 2-5 days",
            "One link replaces 4-8 back-and-forth messages",
            "AI validates answers so you don't get 'medium' as a ring size",
            "Clean spec sheet — no digging through message threads",
            "Handles multi-answer responses intelligently",
            "Saves 15-20 hours/month at 50 orders",
        ],
        "cons_etsai": [
            "Costs $19-79/month after free trial",
            "Buyers click an external link (vs. staying in Etsy app)",
            "Not for general buyer communication — only spec collection",
        ],
        "pros_competitor": [
            "Free and built into Etsy",
            "Buyers already know how to use it",
            "Works for all communication, not just specs",
            "No external links or tools needed",
        ],
        "cons_competitor": [
            "Takes 4-8 messages and 2-5 days per order for specs",
            "Buyers give partial answers requiring follow-ups",
            "No validation — wrong formats, skipped questions",
            "Specs buried in message threads — hard to find during production",
            "At 50 orders/month: 12-25 hours wasted on messaging",
            "Copy-paste fatigue — same template, hundreds of times",
            "No structured output — you manually extract specs from chat",
        ],
    },

    "typeform": {
        "title": "ETSAI vs Typeform for Etsy Custom Orders",
        "slug": "typeform",
        "meta_description": "Compare ETSAI and Typeform for collecting custom order specs from Etsy buyers. AI chat vs. form builder — which is better for your shop?",
        "competitor_name": "Typeform",
        "competitor_tagline": "A popular form builder known for conversational-style forms. Better than Google Forms, but still fundamentally a form.",
        "verdict": "Typeform is the best form builder out there. But ETSAI isn't a form builder — it's an AI conversation. For custom order spec collection specifically, the AI approach wins on buyer experience, follow-up reduction, and time saved.",
        "features": [
            {"name": "Built for Etsy custom orders", "etsai": True, "competitor": False},
            {"name": "AI-generated questions", "etsai": True, "competitor": False},
            {"name": "True AI conversation (not a form)", "etsai": True, "competitor": False},
            {"name": "Understands multi-answer responses", "etsai": True, "competitor": False},
            {"name": "Product-specific validation", "etsai": True, "competitor": "Basic"},
            {"name": "Conversational UI", "etsai": True, "competitor": True},
            {"name": "Free tier", "etsai": "14-day trial", "competitor": "10 responses/mo"},
            {"name": "Etsy product import", "etsai": True, "competitor": False},
            {"name": "Organized spec sheet", "etsai": True, "competitor": "Responses panel"},
            {"name": "Logic jumps / conditional flow", "etsai": "AI-driven", "competitor": True},
            {"name": "File uploads", "etsai": "Coming soon", "competitor": True},
            {"name": "Integrations (Zapier, etc.)", "etsai": "API", "competitor": True},
            {"name": "Price for meaningful use", "etsai": "$19/mo", "competitor": "$25/mo+"},
        ],
        "pros_etsai": [
            "AI understands natural language — buyers talk, not fill out fields",
            "Built specifically for Etsy custom order workflows",
            "Automatically generates the right questions from your product description",
            "Handles 'gold cursive Sarah size 7' as one message — extracts all specs",
            "Cheaper than Typeform's paid plans for equivalent functionality",
            "Product-specific validation (ring sizes, chain lengths, material types)",
        ],
        "cons_etsai": [
            "Costs $19/mo+ after free trial (Typeform has a limited free tier)",
            "Newer product — fewer integrations than Typeform's ecosystem",
            "Photo uploads not yet available",
        ],
        "pros_competitor": [
            "Beautiful, well-designed forms",
            "Conversational one-question-at-a-time format",
            "Huge integration ecosystem (Zapier, Slack, Sheets, etc.)",
            "Logic jumps for conditional questions",
            "File upload support",
            "Well-established company with support resources",
        ],
        "cons_competitor": [
            "Not built for Etsy — no product awareness or import",
            "Still a form — buyers fill out fields, not have a conversation",
            "You write every question manually — no AI generation",
            "Can't handle multi-answer responses ('gold cursive Sarah' breaks into separate fields)",
            "No product-specific validation (doesn't know what a ring size is)",
            "Free tier limited to 10 responses/month — basically unusable",
            "Paid plans start at $25/month for 100 responses",
            "You still manually process responses into usable spec sheets",
        ],
    },
}


# =============================================================
# CHANGELOG
# =============================================================

CHANGELOG_ENTRIES = [
    {
        "date": "2026-02-16",
        "title": "Custom Domain + Email Outreach",
        "items": [
            "ETSAI is now live at etsai.io",
            "Email outreach via Resend SMTP",
            "Professional sender identity with Reply-To support",
            "Updated all references to etsai.io domain",
        ]
    },
    {
        "date": "2026-02-14",
        "title": "Review Queue + Etsy Outreach Improvements",
        "items": [
            "Review queue with approve/reject/rewrite for outreach messages",
            "Separated Etsy outreach into its own queue with click-to-copy",
            "More human outreach messages — no product mentions, 2 sentences max",
            "Follow-up system for unresponsive leads",
            "Error visibility on growth dashboard",
        ]
    },
    {
        "date": "2026-02-13",
        "title": "Autonomous Growth Engine",
        "items": [
            "5-agent growth system: Commander, Scout, Writer, Listener, Creator",
            "Lead discovery via Reddit and Etsy scraping",
            "AI-personalized outreach message drafting",
            "Growth dashboard with stats, lead funnel, and activity feed",
            "Reddit monitoring and pain point extraction",
            "Self-learning system for message optimization",
        ]
    },
    {
        "date": "2026-02-11",
        "title": "Etsy Integration + Billing",
        "items": [
            "Etsy OAuth — connect your shop and import products",
            "Stripe billing with Free, Starter, Pro, and Business plans",
            "Bulk product import from Etsy shop",
            "Lead scraper for discovering custom order sellers",
        ]
    },
    {
        "date": "2026-02-01",
        "title": "Launch",
        "items": [
            "AI-powered spec collection for Etsy custom orders",
            "Seller dashboard with product and order management",
            "Buyer intake chat with smart question extraction",
            "Email notifications for completed specs and escalations",
            "Dark mode support across the entire app",
            "Fulfillment tracking from pending to delivered",
        ]
    },
]


# =============================================================
# ABOUT PAGE
# =============================================================

ABOUT_PAGE = {
    "title": "About ETSAI",
    "meta_description": "ETSAI was built to solve the custom order messaging nightmare on Etsy. One link, one conversation, every spec collected. Here's the story.",
    "sections": [
        {
            "heading": "The problem I couldn't ignore",
            "content": """
<p>Every day, millions of Etsy sellers who make custom products go through the same exhausting cycle: buyer purchases a custom item, seller sends a list of questions, buyer responds with half the info, seller follows up, buyer takes a day to respond. Repeat 4-8 times over several days.</p>
<p>For a seller doing 50 custom orders a month, that's 20+ hours every month — not making their product, not growing their business — just asking the same questions over and over in Etsy messages.</p>
<p>The problem isn't the sellers. The problem is that Etsy's messaging system was built for conversations, not structured data collection. Sellers are trying to collect a form's worth of information through a chat window.</p>
"""
        },
        {
            "heading": "What if it was just... a conversation?",
            "content": """
<p>Forms are structured but rigid. Messages are natural but unstructured. What if you could have both?</p>
<p>That's the idea behind ETSAI. Instead of a form or a message template, you send your buyer a link to an AI assistant that collects their specs through natural conversation. The AI understands context — if a buyer says "gold cursive Sarah size 7," it extracts all four specs from one message. It validates answers, asks smart follow-ups, and delivers a clean spec sheet when it's done.</p>
<p>The whole thing takes about 90 seconds. Not 90 minutes. Not 3 days. Ninety seconds.</p>
"""
        },
        {
            "heading": "Built for sellers who make things",
            "content": """
<p>I'm Noah. I built ETSAI because I saw how much time custom order sellers waste on spec collection and knew AI could fix it. Not with another form builder. Not with another template. With something that actually understands what the buyer is saying and gets you the information you need to start making.</p>
<p>ETSAI is a solo project right now, which means it moves fast, listens to feedback immediately, and doesn't have a committee deciding what to build next. If something's broken, I fix it today. If you have an idea, I probably ship it this week.</p>
"""
        },
        {
            "heading": "Where we're going",
            "content": """
<p>ETSAI starts with Etsy custom order spec collection. But the core technology — AI-powered structured data collection through conversation — works everywhere a business needs to collect detailed information from a customer.</p>
<p>Shopify sellers. Freelancers collecting project briefs. Wedding vendors collecting event details. The intake conversation is a universal tool. We're building it for the market that needs it most right now — Etsy custom order sellers — and expanding from there.</p>
<p>If you sell custom products and you're tired of the back-and-forth, <a href="/#auth" style="color: var(--brand); font-weight: 600;">try ETSAI free for 14 days</a>. Set up takes 5 minutes. Your first buyer will probably finish faster than it took you to read this page.</p>
"""
        },
    ],
}
