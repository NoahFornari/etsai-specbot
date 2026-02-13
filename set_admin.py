"""One-time script to set a seller as admin. Run on Railway: railway run python set_admin.py"""
import sys
from database import get_conn

email = sys.argv[1] if len(sys.argv) > 1 else "noahfornari@gmail.com"

conn = get_conn()
try:
    row = conn.execute("SELECT id, email, shop_name, is_admin FROM sellers WHERE email = %s", (email,)).fetchone()
    if not row:
        print(f"No account found for {email}")
        sys.exit(1)
    print(f"Found: {dict(row)}")
    conn.execute("UPDATE sellers SET is_admin = 1 WHERE email = %s", (email,))
    conn.commit()
    print(f"Admin flag set for {email}!")
finally:
    conn.close()
