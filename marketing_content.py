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
    "etsy-custom-order-process": {
        "title": "How to Streamline Your Etsy Custom Order Process in 2026",
        "slug": "etsy-custom-order-process",
        "meta_description": "Step-by-step guide to building a custom order process that scales. Reduce back-and-forth messages, avoid mistakes, and handle more orders without burning out.",
        "published_date": "2026-02-20",
        "author": "Noah Fornari",
        "category": "Guides",
        "read_time": "10 min",
        "sections": [
            {
                "heading": None,
                "content": """
<p>Your custom orders are growing. That's the good news. The bad news is that your process — the one that worked when you had five orders a month — is falling apart at fifteen. Or thirty.</p>
<p>You're juggling multiple conversations. You've sent the wrong specs to the wrong buyer at least once. You've stayed up late hand-copying details from Etsy messages into your production notes. And the reviews that once said "great communication!" now say "took a while to get started."</p>
<p>This isn't a you problem. It's a process problem. And it's fixable.</p>
"""
            },
            {
                "heading": "The Three Stages of Custom Order Chaos",
                "content": """
<p><strong>Stage 1: The notebook era.</strong> You keep a notebook (physical or digital) where you write down what each buyer wants. Works until you have more than 5 active orders. Then you start mixing up who wanted the 14-inch chain vs the 16-inch chain.</p>
<p><strong>Stage 2: The spreadsheet era.</strong> You create a Google Sheet or Excel file. Columns for buyer name, order date, and every possible spec field. Works until you have 15+ active orders and the sheet becomes a wall of text you have to squint at.</p>
<p><strong>Stage 3: The "I need a system" era.</strong> You realize that the bottleneck isn't production — it's information gathering. The actual making takes you 30 minutes. Collecting specs takes 3 days.</p>
<p>If you're reading this, you're probably at Stage 3. Let's build you a real system.</p>
"""
            },
            {
                "heading": "Step 1: Standardize Your Questions",
                "content": """
<p>The biggest mistake custom order sellers make is asking different questions every time. Your message to Buyer A asks about color, size, and text. Your message to Buyer B asks about text, font, and size. Neither asks about the gift box option you just added.</p>
<p>Write down every question you could possibly need for each product type. Then rank them:</p>
<ul>
    <li><strong>Must-have:</strong> You literally cannot make the item without this info (dimensions, text, color)</li>
    <li><strong>Should-have:</strong> You'll probably need to ask later if you don't ask now (gift wrapping, rush timeline)</li>
    <li><strong>Nice-to-have:</strong> Makes the order smoother (how they found your shop, who the gift is for)</li>
</ul>
<p>Your intake template should always include must-haves, include should-haves when relevant, and skip nice-to-haves unless you're feeling conversational.</p>
"""
            },
            {
                "heading": "Step 2: Create One Intake Point",
                "content": """
<p>Right now your specs come in from everywhere. Etsy messages. Personalization boxes. Order notes. Sometimes buyers email you directly. Sometimes they DM you on Instagram about an Etsy order.</p>
<p>Pick one place where all custom order details live. Your options:</p>
<ul>
    <li><strong>Etsy messages only:</strong> Free, but relies on buyers responding in full and on time</li>
    <li><strong>Google Forms:</strong> Free, organized, but feels impersonal and breaks the Etsy trust bubble</li>
    <li><strong>A dedicated intake tool:</strong> Purpose-built for this exact problem — structured data collection with a buyer-friendly experience</li>
</ul>
<p>Whichever you choose, the rule is: if it's not in the system, it doesn't exist. No accepting specs via Instagram DM. No "oh I'll just remember what they said on the phone."</p>
"""
            },
            {
                "heading": "Step 3: Automate the Follow-Up",
                "content": """
<p>The single biggest time sink in custom orders is chasing buyers for missing info. You send your template. They respond with 3 out of 7 fields. You politely nudge them. They respond two days later with 2 more fields. You nudge again.</p>
<p>The average Etsy custom order involves <strong>4.2 messages</strong> before spec collection is complete. That's not counting the messages about shipping, timelines, and "can you also add..."</p>
<p>Automating follow-ups doesn't mean being pushy. It means:</p>
<ul>
    <li>Sending a friendly reminder 24 hours after the first message if they haven't responded</li>
    <li>Clearly highlighting which questions still need answers</li>
    <li>Making it dead simple for buyers to respond (no hunting through old messages)</li>
</ul>
<p>This is where AI-powered tools like <a href="/">ETSAI</a> shine. Instead of you manually tracking who responded and who didn't, the AI handles the conversation, asks follow-up questions in real time, and only pings you when all specs are locked in.</p>
"""
            },
            {
                "heading": "Step 4: Separate Intake from Production",
                "content": """
<p>Here's a subtle but game-changing distinction: your intake process and your production process should be separate workflows.</p>
<p>Intake = collecting all the information you need. Production = actually making the thing.</p>
<p>Many sellers blur these together. They start making the item while still collecting specs ("I'll start the base while they decide on the color"). This leads to rework, wasted materials, and frustrated buyers.</p>
<p><strong>The rule:</strong> Don't start production until intake is 100% complete. No exceptions. If a buyer hasn't provided their ring size, you don't touch silver. If they haven't confirmed the text, you don't start engraving.</p>
<p>This feels slower but it's actually faster. Zero rework means every order goes through production exactly once.</p>
"""
            },
            {
                "heading": "Step 5: Close the Loop",
                "content": """
<p>The last piece most sellers miss: confirming specs back to the buyer before starting production.</p>
<p>A simple confirmation message works wonders:</p>
<blockquote><p>"Hey [Name]! Just confirming your order: 14-inch gold chain, heart pendant, engraved with 'Mom' in script font. Everything look right?"</p></blockquote>
<p>This takes 30 seconds and prevents the single worst outcome in custom orders: making the wrong thing. A $50 remake costs you materials, time, and the customer relationship. A confirmation message costs you nothing.</p>
"""
            },
            {
                "heading": "Putting It All Together",
                "content": """
<p>Here's your streamlined custom order process in one checklist:</p>
<ol>
    <li>Buyer places order or inquires about a custom piece</li>
    <li>You send them to your single intake point (intake link, form, or template message)</li>
    <li>All specs collected in one interaction (or automatically followed up)</li>
    <li>You confirm specs back to the buyer</li>
    <li>They approve, you start production</li>
    <li>Deliver and collect that five-star review</li>
</ol>
<p>The sellers doing 50+ custom orders a month aren't working harder than you. They just have better systems. Build yours once, and it'll serve you forever — or at least until you outgrow it and need the next level.</p>
<p>If you want to skip straight to a system that handles steps 2-4 automatically, <a href="/">try ETSAI free for 14 days</a>. Your buyers chat with an AI that collects every spec, and you get a clean summary. No more message tag.</p>
"""
            },
        ],
    },

    "etsy-seller-time-management": {
        "title": "Time Management for Etsy Sellers: Where Your Hours Actually Go",
        "slug": "etsy-seller-time-management",
        "meta_description": "Etsy sellers spend 40% of their time on admin, not making. Here's a breakdown of where your hours go and how to reclaim them for production and growth.",
        "published_date": "2026-02-24",
        "author": "Noah Fornari",
        "category": "Business",
        "read_time": "7 min",
        "sections": [
            {
                "heading": None,
                "content": """
<p>You became an Etsy seller to make things. To craft, design, create. But somewhere along the way, "Etsy seller" became "Etsy message-answerer, order-tracker, photo-taker, listing-optimizer, and occasional maker."</p>
<p>If your creative time is shrinking while your admin time is growing, you're not alone. And the fix isn't "work harder" — it's understanding where the time actually goes.</p>
"""
            },
            {
                "heading": "The Time Audit No One Wants to Do",
                "content": """
<p>Track your work hours for one week. Not roughly — actually track them. Every time you switch tasks, note what you did and how long it took. Here's what most custom order sellers find:</p>
<ul>
    <li><strong>Production/creating:</strong> 30-35% of time</li>
    <li><strong>Customer messaging:</strong> 20-25% of time</li>
    <li><strong>Photography &amp; listings:</strong> 15-20% of time</li>
    <li><strong>Order management &amp; shipping:</strong> 10-15% of time</li>
    <li><strong>Marketing &amp; social media:</strong> 5-10% of time</li>
    <li><strong>Accounting &amp; admin:</strong> 5-10% of time</li>
</ul>
<p>The shock is always that first number. You're spending barely a third of your time on the thing you started this business to do.</p>
"""
            },
            {
                "heading": "The Messaging Black Hole",
                "content": """
<p>Customer messaging eats 20-25% of your working hours. But it's worse than it sounds because those hours are <em>fragmented</em>. You're not spending 2 straight hours on messages — you're checking your phone 30 times a day, breaking flow, writing quick replies, and losing 5-10 minutes of focus each time.</p>
<p>Cal Newport calls this "context switching." Each interruption costs you 15-25 minutes of productive focus, even if the reply itself only took 2 minutes to type. If you check messages 20 times a day, that's potentially 5-8 hours of lost deep work. Per day.</p>
<p>For custom order sellers, the messaging load is even heavier because each conversation requires multiple rounds:</p>
<ul>
    <li>Initial inquiry: "Can you make a custom...?"</li>
    <li>Your spec questions: "What size, color, text...?"</li>
    <li>Partial response: "Medium, blue, and..."</li>
    <li>Follow-up: "What about the engraving text?"</li>
    <li>Confirmation: "So to confirm, you want..."</li>
    <li>Revision: "Actually, can we change the color to..."</li>
</ul>
<p>That's 6 rounds minimum. Multiply by 10 active orders and you're managing 60 conversation threads simultaneously.</p>
"""
            },
            {
                "heading": "Batch Your Communication",
                "content": """
<p>The single best time management tactic for Etsy sellers: batch your messages into 2-3 dedicated windows per day.</p>
<ul>
    <li><strong>Morning (9 AM):</strong> Check and respond to overnight messages. 30 minutes max.</li>
    <li><strong>Midday (1 PM):</strong> Quick scan for urgent items. 15 minutes.</li>
    <li><strong>Evening (5 PM):</strong> End-of-day responses and follow-ups. 30 minutes max.</li>
</ul>
<p>Outside those windows? Notifications off. Phone in another room. This feels terrifying at first — "what if a buyer needs me RIGHT NOW?" — but buyers on Etsy expect handmade sellers to be busy making things. A 4-hour response time is perfectly fine. A 4-day response time (which is what happens when you're overwhelmed and avoiding your inbox) is not.</p>
"""
            },
            {
                "heading": "Automate the Repetitive Stuff",
                "content": """
<p>Look at your message history. How many of your messages are basically the same thing with minor variations?</p>
<p>If you're like most custom order sellers, at least 60% of your outgoing messages fall into a handful of categories:</p>
<ul>
    <li>Initial spec collection (same questions, different buyers)</li>
    <li>Follow-up for missing info ("Just checking in on those specs!")</li>
    <li>Order confirmation ("Here's what I have, please confirm")</li>
    <li>Production update ("Your order is in progress!")</li>
    <li>Shipping notification ("Just shipped! Here's your tracking")</li>
</ul>
<p>Templates help. Saved replies help more. But the ultimate time-saver is removing yourself from the loop entirely for the parts that don't need your creative judgment.</p>
<p>Spec collection is the biggest opportunity. It doesn't require creativity, taste, or expertise — it requires asking the right questions and recording the answers. That's exactly the kind of task an AI can handle. <a href="/">ETSAI</a> replaces the entire spec-collection conversation with a single link. You send it, the AI collects everything, you get a clean summary. One message instead of six.</p>
"""
            },
            {
                "heading": "Protect Your Maker Time",
                "content": """
<p>Once you've reduced your messaging overhead and batched your admin tasks, the final piece is treating your creative time as sacred.</p>
<p>Block out production hours on your calendar like they're meetings with your most important client — because they are. If you do your best work in the morning, that's when you make things. Messages, listings, and admin happen in the afternoon.</p>
<p>The sellers who scale past $5K/month on Etsy all have one thing in common: they protect their production time and ruthlessly eliminate anything that fragments it. Your hands should be making things, not typing messages. Build systems that make that possible, and the rest follows.</p>
"""
            },
        ],
    },

    "etsy-custom-order-mistakes": {
        "title": "7 Custom Order Mistakes That Are Costing You Etsy Sales",
        "slug": "etsy-custom-order-mistakes",
        "meta_description": "Avoid these 7 common custom order mistakes that lead to refunds, bad reviews, and buyer frustration. Practical fixes for every Etsy seller.",
        "published_date": "2026-02-28",
        "author": "Noah Fornari",
        "category": "Tips",
        "read_time": "9 min",
        "sections": [
            {
                "heading": None,
                "content": """
<p>Custom orders should be your most profitable items. Higher margins, repeat customers, word-of-mouth referrals. But for many Etsy sellers, custom orders are actually their biggest headache — and their most expensive mistakes.</p>
<p>Here are the 7 mistakes I see most often, and how to fix each one.</p>
"""
            },
            {
                "heading": "1. Not Collecting All Specs Upfront",
                "content": """
<p>This is the big one. You get excited about a custom order, start a conversation, collect most of the details... and start working. Then halfway through production, you realize you never asked about the chain length. Or the font. Or whether they wanted matte or glossy.</p>
<p>Now you're either guessing (risky), messaging the buyer mid-production (slow), or starting over (expensive).</p>
<p><strong>The fix:</strong> Create a complete spec checklist for every product type. Don't start production until every single field is filled in. Use a structured intake process — whether that's a <a href="/blog/etsy-custom-order-template">template message</a>, a form, or an <a href="/">AI-powered intake tool</a> — that ensures nothing gets missed.</p>
"""
            },
            {
                "heading": "2. Using the Personalization Box for Complex Orders",
                "content": """
<p>Etsy's personalization box has a 256-character limit. That's barely enough for a name and date, let alone the 5-10 specs a real custom order requires.</p>
<p>Yet many sellers try to squeeze everything into that tiny box: "Please enter: Name, date, font choice, ring size, metal preference, box or no box, and any special instructions."</p>
<p>Buyers see that wall of text, panic, and either skip half the fields or write something unusable like "gold ring for mom size 7 maybe 8."</p>
<p><strong>The fix:</strong> Use the personalization box only for simple items (one name, one date). For anything requiring multiple specs, direct buyers to a separate intake method where each question gets its own field and validation.</p>
"""
            },
            {
                "heading": "3. Starting Production Before Confirmation",
                "content": """
<p>You're eager. You have all the specs (you think). You start cutting, engraving, or assembling. Then the buyer messages: "Actually, can we change it to silver instead of gold?"</p>
<p>If you haven't started, no problem. If you're halfway through, you just lost materials and time.</p>
<p><strong>The fix:</strong> Always — always — send a confirmation message before starting. List every spec back to the buyer: "Just confirming: 14K gold, size 7, script font, engraved with 'Forever.' Sound right?" Wait for their thumbs up. Then and only then do you touch materials.</p>
"""
            },
            {
                "heading": "4. Not Setting Clear Timelines",
                "content": """
<p>Buyer messages: "How long will this take?"<br>You: "About a week!"<br>Buyer hears: "I'll have it in my hands in 7 days."<br>You meant: "I'll start working on it within a week, then ship it."</p>
<p>Misaligned timeline expectations are the #1 cause of negative reviews on custom orders. The buyer isn't unreasonable — they just heard something different than what you said.</p>
<p><strong>The fix:</strong> Be extremely specific. "Production takes 5-7 business days after I confirm all your specs. Shipping is an additional 3-5 business days. So from today, you're looking at about 2 weeks." Put this in your listing description AND in your first message.</p>
"""
            },
            {
                "heading": "5. Accepting Every Custom Request",
                "content": """
<p>A buyer asks for something outside your normal scope. A different material you've never worked with. A size you don't have tools for. A design that would take 10x longer than your usual items.</p>
<p>You say yes because you don't want to lose the sale. Then you spend three times as long, the result isn't your best work, and the buyer can tell.</p>
<p><strong>The fix:</strong> Define your boundaries and stick to them. "I specialize in sterling silver and 14K gold. I don't work with platinum." "My maximum ring size is 13." "I can modify existing designs but don't create fully custom designs from scratch." Saying no to the wrong orders lets you say a better yes to the right ones.</p>
"""
            },
            {
                "heading": "6. Keeping Specs in Your Head",
                "content": """
<p>You can remember the details for 3 active orders. Maybe 5 if you're good. Past that, you're relying on scrolling through Etsy message threads to find "wait, did they say emerald green or forest green?"</p>
<p>This doesn't scale. And it leads to errors that cost real money — wrong color, wrong size, wrong text. One mistake on a $150 custom piece wipes out the profit on your next 3-4 orders.</p>
<p><strong>The fix:</strong> Every order gets a written spec sheet. Whether it's a spreadsheet, a note in your phone, or a tool that auto-generates one from the intake conversation — the specs exist in one place, separate from the message thread, and you reference them during production. Not your memory.</p>
"""
            },
            {
                "heading": "7. Making Spec Collection Feel Like Homework",
                "content": """
<p>You send the buyer 12 questions. They look at it and think "this feels like a tax form." They put it off. They respond days later with incomplete answers. Or they just... don't respond at all.</p>
<p>The result: you lose the order entirely, or you spend days chasing them down.</p>
<p><strong>The fix:</strong> Make spec collection feel like a conversation, not a form. Ask one question at a time. Be friendly and specific ("What name would you like engraved?" beats "Enter personalization text"). Explain <em>why</em> you're asking ("I ask about wrist circumference so the bracelet fits perfectly — too loose and it'll snag on things").</p>
<p>This is actually one of the core ideas behind <a href="/">ETSAI</a> — instead of dumping a form on buyers, an AI has a friendly chat with them, asking one question at a time and adapting based on their answers. It feels like messaging a helpful shop assistant, not filling out a DMV form. And the completion rate is dramatically higher than forms or long template messages.</p>
"""
            },
            {
                "heading": "The Common Thread",
                "content": """
<p>All seven mistakes come down to the same root cause: an unstructured process. When spec collection is ad-hoc, communication is vague, and information lives in your head, mistakes are inevitable.</p>
<p>The sellers who avoid these mistakes don't have superhuman memory or infinite patience. They have systems. Build yours, and custom orders go from your biggest headache to your biggest profit center.</p>
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
