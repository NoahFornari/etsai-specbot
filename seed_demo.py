"""
Seed demo data for testing ETSAI without an API key.
Run: python seed_demo.py
"""
from database import init_db, create_seller, add_product, create_order, add_message, get_conn, set_trial_end, update_seller_profile
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def seed():
    init_db()

    # Create demo seller with password
    pw_hash = generate_password_hash("demo1234")
    seller_id = create_seller("demo@etsai.com", "Agora Custom Studio", password_hash=pw_hash)
    set_trial_end(seller_id, (datetime.now() + timedelta(days=14)).isoformat())
    update_seller_profile(seller_id, "Agora Custom Studio", "demo@etsai.com", display_name="Noah")
    # Set as admin
    conn = get_conn()
    conn.execute("UPDATE sellers SET is_admin = 1 WHERE id = ?", (seller_id,))
    conn.commit()
    conn.close()
    print(f"Created seller: {seller_id} (admin)")
    print(f"Login: demo@etsai.com / demo1234")

    # Product 1: Custom Golf Club
    golf_questions = [
        {
            "field_name": "shaft_flex",
            "question": "What shaft flex do you need?",
            "required": True,
            "options": ["Regular", "Stiff", "Extra Stiff", "Senior", "Ladies"],
            "example": "Regular",
            "validation_type": "select"
        },
        {
            "field_name": "hand_orientation",
            "question": "Are you right-handed or left-handed?",
            "required": True,
            "options": ["Right-handed", "Left-handed"],
            "example": "Right-handed",
            "validation_type": "select"
        },
        {
            "field_name": "grip_type",
            "question": "What grip type would you like?",
            "required": True,
            "options": ["Standard", "Midsize", "Oversize", "Jumbo"],
            "example": "Standard",
            "validation_type": "select"
        },
        {
            "field_name": "shaft_length",
            "question": "Do you need a custom shaft length? If so, what length?",
            "required": False,
            "options": [],
            "example": "Standard length is fine",
            "validation_type": "text"
        },
        {
            "field_name": "club_loft",
            "question": "Any preferred loft adjustment?",
            "required": False,
            "options": ["Standard", "+1 degree", "+2 degrees", "-1 degree", "-2 degrees"],
            "example": "Standard",
            "validation_type": "select"
        }
    ]

    p1_id = add_product(seller_id, "Custom Forged Iron Set (4-PW)", golf_questions,
                         category="Golf Equipment", price=599.99,
                         description="Hand-forged iron set with custom shaft, grip, and loft options. Available in 4-PW configuration.",
                         seller_notes="We can do custom paint fill colors (black, white, red, blue, gold). We can adjust lie angle +/- 3 degrees. Rush orders available for +$50. Standard turnaround is 2-3 weeks.")
    print(f"Created product: {p1_id} (Custom Golf Irons)")

    # Product 2: Custom Ring
    ring_questions = [
        {
            "field_name": "ring_size",
            "question": "What ring size do you need?",
            "required": True,
            "options": ["5", "6", "7", "8", "9", "10", "11", "12"],
            "example": "7",
            "validation_type": "select"
        },
        {
            "field_name": "engraving_text",
            "question": "What text would you like engraved inside the ring?",
            "required": True,
            "options": [],
            "example": "Forever Yours - J&M",
            "max_length": 25,
            "min_length": 1,
            "validation_type": "text"
        },
        {
            "field_name": "metal_finish",
            "question": "What finish do you prefer?",
            "required": True,
            "options": ["Polished", "Matte", "Brushed", "Hammered"],
            "example": "Polished",
            "validation_type": "select"
        },
        {
            "field_name": "font_style",
            "question": "What font style for the engraving?",
            "required": False,
            "options": ["Script", "Block", "Serif", "Handwritten"],
            "example": "Script",
            "validation_type": "select"
        }
    ]

    p2_id = add_product(seller_id, "Custom Engraved Sterling Silver Ring", ring_questions,
                         category="Jewelry", price=89.99,
                         description="Hand-crafted sterling silver ring with custom interior engraving. Available in multiple finishes.",
                         seller_notes="We work in sterling silver and gold vermeil only - no platinum or solid gold. Engraving limited to 25 characters. We can do symbols like hearts and infinity signs. Turnaround is 3-5 business days. Gift wrapping available free of charge.")
    print(f"Created product: {p2_id} (Custom Ring)")

    # Product 3: Custom Portrait
    portrait_questions = [
        {
            "field_name": "num_people",
            "question": "How many people/pets should be in the portrait?",
            "required": True,
            "options": ["1", "2", "3", "4", "5+"],
            "example": "2",
            "validation_type": "select"
        },
        {
            "field_name": "style",
            "question": "What art style do you prefer?",
            "required": True,
            "options": ["Realistic", "Cartoon", "Watercolor", "Minimalist", "Pop Art"],
            "example": "Watercolor",
            "validation_type": "select"
        },
        {
            "field_name": "background",
            "question": "What background would you like?",
            "required": True,
            "options": ["Plain White", "Solid Color", "Scene from Photo", "Custom Scene"],
            "example": "Scene from Photo",
            "validation_type": "select"
        },
        {
            "field_name": "canvas_size",
            "question": "What size canvas?",
            "required": True,
            "options": ["8x10", "11x14", "16x20", "24x36"],
            "example": "16x20",
            "validation_type": "select"
        },
        {
            "field_name": "special_instructions",
            "question": "Any special requests or notes for the artist?",
            "required": False,
            "options": [],
            "example": "Please include our dog in the portrait too!",
            "max_length": 200,
            "validation_type": "text"
        }
    ]

    p3_id = add_product(seller_id, "Custom Family Portrait - Digital Art", portrait_questions,
                         category="Art & Prints", price=149.99,
                         description="Custom digital family portrait in your choice of art style. Includes up to 5 subjects, additional subjects +$20 each.",
                         seller_notes="We can include pets! Additional subjects beyond 5 are +$20 each. We need a clear reference photo for each person/pet. Revisions: 2 free rounds of revisions included, additional rounds are $15 each. Turnaround is 7-10 business days. We can do holiday themes (Christmas, Halloween, etc).")
    print(f"Created product: {p3_id} (Custom Portrait)")

    # Create demo orders
    o1_id = create_order(seller_id, p1_id, buyer_name="Mike Johnson",
                          buyer_email="mike@example.com", external_order_id="ETSY-1001")
    print(f"Created order: {o1_id} (Golf Clubs for Mike)")

    o2_id = create_order(seller_id, p2_id, buyer_name="Sarah Williams",
                          buyer_email="sarah@example.com", external_order_id="ETSY-1002")
    print(f"Created order: {o2_id} (Ring for Sarah)")

    o3_id = create_order(seller_id, p3_id, buyer_name="David Chen",
                          buyer_email="david@example.com", external_order_id="ETSY-1003")
    print(f"Created order: {o3_id} (Portrait for David)")

    print(f"\n{'='*50}")
    print(f"  Demo data seeded!")
    print(f"  Login email: demo@etsai.com")
    print(f"  Seller ID: {seller_id}")
    print(f"  Products: {p1_id}, {p2_id}, {p3_id}")
    print(f"  Orders: {o1_id}, {o2_id}, {o3_id}")
    print(f"")
    print(f"  Intake URLs (buyer-facing):")
    print(f"    http://localhost:5000/intake/{o1_id}")
    print(f"    http://localhost:5000/intake/{o2_id}")
    print(f"    http://localhost:5000/intake/{o3_id}")
    print(f"{'='*50}")


if __name__ == "__main__":
    seed()
