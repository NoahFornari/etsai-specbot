"""
ETSAI AI Engine
Handles spec collection conversations. Adapted from eBay Service 3.

Two-model routing:
  - Sonnet: Customer conversations (quality matters)
  - Haiku: Classification, follow-ups (cost matters)
"""
import json
import os

AI_MODEL_SMART = "claude-sonnet-4-5-20250929"
AI_MODEL_CHEAP = "claude-haiku-4-5-20251001"

AI_COSTS = {
    AI_MODEL_CHEAP: {"input": 0.80, "output": 4.00},
    AI_MODEL_SMART: {"input": 3.00, "output": 15.00},
}


def call_claude(prompt, model=None, max_tokens=500, system=None):
    """Call Claude API. Returns (text, cost, input_tokens, output_tokens)."""
    import anthropic

    model = model or AI_MODEL_SMART
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)

    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system

    response = client.messages.create(**kwargs)

    inp = response.usage.input_tokens
    out = response.usage.output_tokens
    rates = AI_COSTS.get(model, {"input": 3.00, "output": 15.00})
    cost = (inp * rates["input"] + out * rates["output"]) / 1_000_000

    return response.content[0].text.strip(), cost, inp, out


def generate_greeting(product_title, questions, buyer_name=None, seller_notes=None):
    """Generate first message to buyer after purchase."""
    q_text = ""
    for i, q in enumerate(questions, 1):
        req = " (required)" if q.get("required") else " (optional)"
        opts = f" Options: {', '.join(q['options'])}" if q.get("options") else ""
        constraint_parts = []
        if q.get("max_length"):
            constraint_parts.append(f"max {q['max_length']} characters")
        if q.get("min_length"):
            constraint_parts.append(f"min {q['min_length']} characters")
        constraint_note = f" [{', '.join(constraint_parts)}]" if constraint_parts else ""
        q_text += f"  {i}. {q['question']}{req}{opts}{constraint_note}\n"

    buyer_greeting = f"the buyer ({buyer_name})" if buyer_name else "the buyer"

    seller_context = ""
    if seller_notes:
        seller_context = f"""
SELLER NOTES (use this to set tone and context):
{seller_notes}
"""

    prompt = f"""You are a friendly seller messaging {buyer_greeting} who just purchased a product.
Your job: collect the customization details needed to fulfill their order.

PRODUCT THEY BOUGHT: {product_title}
{seller_context}
DETAILS YOU NEED TO COLLECT:
{q_text}

Write a SHORT, friendly first message that:
1. Thanks them for their purchase
2. Explains you need a few details to get their order started
3. Lists the questions naturally (don't number them robotically — weave them in)
4. If there are options, mention them so the buyer knows what to choose from
5. If there are character limits, mention them naturally (e.g. "up to 8 characters")
6. Keeps it under 150 words
7. Sounds human, not like a bot
8. Does NOT use the word "specifications" — say "details" or "preferences" instead

Just write the message. No subject line, no signature block."""

    text, cost, inp, out = call_claude(prompt, AI_MODEL_SMART, max_tokens=400)
    return {"response": text, "cost": cost, "input_tokens": inp, "output_tokens": out}


def process_buyer_message(buyer_message, product_title, questions, collected_specs,
                          conversation_history, buyer_name=None, seller_notes=None):
    """
    Core AI turn. Extracts specs AND generates response in one call.
    Returns: {response, specs_extracted, is_complete, needs_clarification, should_escalate, cost}
    """
    # Check escalation triggers first (free, no API call)
    escalation = check_escalation(buyer_message, conversation_history)
    if escalation["should_escalate"]:
        return {
            "response": (
                "Thanks for your patience! I want to make sure you're taken care of properly, "
                "so I'm going to have a team member follow up with you directly. "
                "They'll be in touch shortly!"
            ),
            "specs_extracted": {},
            "is_complete": False,
            "needs_clarification": [],
            "should_escalate": True,
            "escalation_reason": escalation["reason"],
            "cost": 0.0,
        }

    # Build context
    missing_req = [q for q in questions if q.get("required") and
                   not collected_specs.get(q["field_name"])]
    missing_opt = [q for q in questions if not q.get("required") and
                   not collected_specs.get(q["field_name"])]

    hist_text = ""
    for msg in conversation_history[-10:]:
        role = "SELLER" if msg.get("direction") == "outbound" else "BUYER"
        hist_text += f"{role}: {msg['content']}\n"

    got_text = ""
    for field, value in collected_specs.items():
        if value:
            got_text += f"  - {field}: {value}\n"

    needed_text = ""
    for q in missing_req:
        opts = f" (Options: {', '.join(q['options'])})" if q.get("options") else ""
        needed_text += f"  - {q['field_name']}: {q['question']}{opts}\n"

    optional_text = ""
    for q in missing_opt:
        opts = f" (Options: {', '.join(q['options'])})" if q.get("options") else ""
        optional_text += f"  - {q['field_name']}: {q['question']}{opts}\n"

    # Build constraint info from structured fields (no more regex parsing)
    constraint_text = ""
    for q in questions:
        constraints = []
        if q.get("options"):
            constraints.append(f"Valid options: {', '.join(q['options'])}")
        if q.get("max_length"):
            constraints.append(f"Maximum {q['max_length']} characters")
        if q.get("min_length"):
            constraints.append(f"Minimum {q['min_length']} characters")
        if q.get("validation_type"):
            constraints.append(f"Type: {q['validation_type']}")
        if q.get("example"):
            constraints.append(f"Example: {q['example']}")
        if constraints:
            constraint_text += f"  - {q['field_name']}: {'; '.join(constraints)}\n"

    # Seller notes context
    seller_context = ""
    if seller_notes:
        seller_context = f"""
SELLER NOTES (what the seller can/can't do, capabilities, materials, preferences):
{seller_notes}
"""

    # Determine conversation phase
    all_required_fields = [q for q in questions if q.get("required")]
    collected_required = [q for q in all_required_fields if collected_specs.get(q["field_name"])]
    awaiting_confirmation = len(collected_required) == len(all_required_fields) and len(all_required_fields) > 0

    prompt = f"""You are a friendly seller in a conversation with a buyer.
You're collecting customization details for their order.

PRODUCT: {product_title}
{seller_context}
DETAILS ALREADY COLLECTED:
{got_text or "  (none yet)"}

DETAILS STILL NEEDED (required):
{needed_text or "  (all required details collected!)"}

OPTIONAL DETAILS (nice to have):
{optional_text or "  (none)"}

CONSTRAINTS PER FIELD:
{constraint_text or "  (none)"}

{"** ALL REQUIRED DETAILS HAVE BEEN COLLECTED. YOU ARE NOW IN CONFIRMATION PHASE. **" if awaiting_confirmation else ""}

CONVERSATION SO FAR:
{hist_text}
BUYER: {buyer_message}

YOUR TASK:
1. EXTRACT: Pull any detail answers from the buyer's message. Match them to field names.
2. VALIDATE: Check extracted answers against constraints. REJECT any that violate constraints.
3. RESPOND: Write your next message to the buyer.

RESPONSE RULES:
- If buyer answered some details: acknowledge what you got, ask for what's still missing
- If an answer violates a constraint (too many characters, not a valid option, etc.): DO NOT extract it. Tell the buyer what the constraint is and ask them to correct it.
- If an answer is ambiguous or doesn't match options: ask for clarification on JUST that field
- ONE message, capture MULTIPLE details. If they say "gold, 18 inch, heart" capture ALL THREE.
- Don't re-ask questions they already answered.
- If they seem confused, give examples.
- Keep it SHORT. Under 100 words unless presenting the order summary.
- Sound human. No "specifications", say "details" or "preferences".

CRITICAL — CAPABILITY BOUNDARIES:
- If SELLER NOTES are provided above, use them to answer buyer questions about capabilities.
  - If the seller notes address the buyer's question, respond based on the notes.
  - If the seller notes do NOT address the buyer's question, say: "That's a great question — let me flag that as a special request for the seller to review, since I'm not sure about that one."
- If NO seller notes are provided:
  - You do NOT know what the seller can or cannot do beyond the defined options.
  - If the buyer asks about special modifications or capabilities NOT listed in the options, say: "I'll note that as a special request for the seller to review — I can't confirm that one on my end."
- NEVER promise "yes we can do that" for anything you're not sure about.
- Note special requests in extracted_specs with field name "special_requests".

CRITICAL — TWO-PHASE COMPLETION:
- PHASE 1 (Summarize): When all required details are collected for the first time, present a clear summary of EVERY collected detail and ask: "Does everything look correct? Let me know if you'd like to change anything before I send this to the team."
  Set "awaiting_confirmation": true and "all_required_complete": false.
- PHASE 2 (Confirm): ONLY when the buyer explicitly confirms (e.g. "yes", "looks good", "correct", "perfect", "that's right", "send it"), THEN set "all_required_complete": true.
- If the buyer wants to change something at the confirmation step, update the spec and re-confirm with a new summary.
- NEVER set "all_required_complete": true in the same turn you first present the summary. Always wait for the buyer's response.
{"- You are currently in CONFIRMATION PHASE. If the buyer is confirming, set all_required_complete: true. If they want changes, update and re-summarize." if awaiting_confirmation else ""}

RESPOND IN THIS EXACT JSON FORMAT:
{{
  "extracted_specs": {{"field_name": "value", ...}},
  "response": "your message to the buyer",
  "all_required_complete": true/false,
  "awaiting_confirmation": true/false,
  "needs_clarification": ["field_name1", ...]
}}

JSON only. Nothing else."""

    raw_text, cost, inp, out = call_claude(prompt, AI_MODEL_SMART, max_tokens=600)

    # Parse
    try:
        clean = raw_text.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
        parsed = json.loads(clean)
    except json.JSONDecodeError:
        parsed = {
            "extracted_specs": {},
            "response": raw_text,
            "all_required_complete": False,
            "needs_clarification": [],
        }

    # Validate extracted specs
    validated = {}
    for field, value in parsed.get("extracted_specs", {}).items():
        matching_q = next((q for q in questions if q["field_name"] == field), None)
        if matching_q:
            validation = validate_answer(matching_q, value)
            if validation["valid"]:
                validated[field] = validation["value"]

    return {
        "response": parsed.get("response", raw_text),
        "specs_extracted": validated,
        "is_complete": parsed.get("all_required_complete", False),
        "needs_clarification": parsed.get("needs_clarification", []),
        "should_escalate": False,
        "escalation_reason": "",
        "cost": cost,
    }


def generate_followup(product_title, missing_questions, followup_number=1):
    """Generate a follow-up for unresponsive buyer."""
    missing_text = ", ".join(q["question"] for q in missing_questions[:3])

    prompt = f"""Write a brief, friendly follow-up message to a buyer who hasn't responded.

PRODUCT: {product_title}
WHAT WE STILL NEED: {missing_text}
THIS IS FOLLOW-UP #{followup_number}

Rules:
- Keep it under 60 words
- Don't be pushy
- Mention specifically what you still need
- If follow-up #2, add slight urgency ("want to get your order moving")
- Sound human

Just the message."""

    text, cost, inp, out = call_claude(prompt, AI_MODEL_CHEAP, max_tokens=150)
    return {"response": text, "cost": cost}


def generate_intake_questions(product_title, product_category=None, product_description=None):
    """
    AI-powered: Generate intake questions for a product the seller adds.
    This is the magic — seller adds a product, AI figures out what specs are needed.
    Now outputs structured constraint fields (max_length, min_length, validation_type).
    """
    context = f"PRODUCT: {product_title}"
    if product_category:
        context += f"\nCATEGORY: {product_category}"
    if product_description:
        context += f"\nDESCRIPTION: {product_description}"

    prompt = f"""You are an expert at custom product fulfillment. A seller has added a product
that requires customization details from buyers after purchase.

{context}

Generate the intake questions needed to fulfill this custom order.
Each question should have:
- field_name: short snake_case identifier
- question: the question to ask the buyer (do NOT embed character limits in the question text — use max_length instead)
- required: true/false
- options: array of valid options (empty array [] if free-text)
- example: example answer to help the buyer
- max_length: (optional, integer) maximum character limit for free-text fields. Use this for engraving, stamping, monograms, etc. where physical space limits text. Omit if no limit.
- min_length: (optional, integer) minimum characters required. Omit if no minimum.
- validation_type: (optional, string) one of "text", "number", "select", "email", "url". Defaults to "text" if omitted. Use "select" when options are provided, "number" for numeric fields.

Think about what ACTUALLY matters for fulfillment. Don't over-ask.
Typical custom products need 3-7 questions.

RESPOND IN THIS EXACT JSON FORMAT:
[
  {{
    "field_name": "engraving_text",
    "question": "What text would you like engraved?",
    "required": true,
    "options": [],
    "example": "EMMA",
    "max_length": 15,
    "validation_type": "text"
  }},
  {{
    "field_name": "ring_size",
    "question": "What ring size do you need?",
    "required": true,
    "options": ["5", "6", "7", "8", "9", "10", "11", "12"],
    "example": "7",
    "validation_type": "select"
  }}
]

JSON array only. Nothing else."""

    raw_text, cost, inp, out = call_claude(prompt, AI_MODEL_SMART, max_tokens=800)

    try:
        clean = raw_text.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
        questions = json.loads(clean)
        if isinstance(questions, list):
            return {"questions": questions, "cost": cost}
    except json.JSONDecodeError:
        pass

    # Fallback: return generic questions
    return {
        "questions": [
            {
                "field_name": "customization_details",
                "question": "What customization details do you need for this order?",
                "required": True,
                "options": [],
                "example": "Please describe your preferences",
                "validation_type": "text"
            }
        ],
        "cost": cost
    }


def check_escalation(buyer_message, conversation_history):
    """Quick check if conversation needs human intervention."""
    msg_lower = buyer_message.lower()

    triggers = {
        "cancel": "Buyer wants to cancel",
        "refund": "Buyer requesting refund",
        "money back": "Buyer requesting refund",
        "report": "Buyer threatening to report",
        "scam": "Buyer accusing of scam",
        "fraud": "Buyer accusing of fraud",
        "lawyer": "Buyer making legal threats",
        "not as described": "Buyer claiming item not as described",
    }

    for trigger, reason in triggers.items():
        if trigger in msg_lower:
            return {"should_escalate": True, "reason": reason}

    # Too many messages without progress
    buyer_msgs = [m for m in conversation_history if m.get("direction") == "inbound"]
    if len(buyer_msgs) >= 6:
        return {"should_escalate": True, "reason": f"Long conversation ({len(buyer_msgs)} messages) without resolution"}

    return {"should_escalate": False, "reason": ""}


def validate_answer(question, answer):
    """Validate a single answer against structured question constraints."""
    answer = str(answer).strip()
    if not answer:
        return {"valid": False, "value": answer, "issue": "Empty answer"}

    # Check max_length from structured field
    max_len = question.get("max_length")
    if max_len and len(answer) > max_len:
        return {"valid": False, "value": answer, "issue": f"Too long ({len(answer)} chars). Maximum is {max_len} characters."}

    # Check min_length from structured field
    min_len = question.get("min_length")
    if min_len and len(answer) < min_len:
        return {"valid": False, "value": answer, "issue": f"Too short ({len(answer)} chars). Minimum is {min_len} characters."}

    # Type-specific validation
    validation_type = question.get("validation_type", "text")
    if validation_type == "number":
        try:
            float(answer)
        except ValueError:
            return {"valid": False, "value": answer, "issue": "Must be a number."}
    elif validation_type == "email":
        if "@" not in answer or "." not in answer:
            return {"valid": False, "value": answer, "issue": "Must be a valid email address."}

    # Check options (for select-type or any question with options)
    options = question.get("options", [])
    if options:
        options_lower = {opt.lower(): opt for opt in options}
        answer_lower = answer.lower()

        if answer_lower in options_lower:
            return {"valid": True, "value": options_lower[answer_lower], "issue": None}

        # Fuzzy match
        for opt_lower, opt_original in options_lower.items():
            if answer_lower in opt_lower or opt_lower in answer_lower:
                return {"valid": True, "value": opt_original, "issue": None}

        return {"valid": False, "value": answer, "issue": f"Not a valid option. Choose from: {', '.join(options)}"}

    return {"valid": True, "value": answer, "issue": None}
