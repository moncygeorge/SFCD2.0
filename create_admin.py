"""
create_admin.py
---------------
Run this ONCE after deployment to create the admin account.

    python create_admin.py

You will be prompted to set a username and password.
The password is stored as a bcrypt hash — never in plain text.
"""

import sqlite3
import getpass
from werkzeug.security import generate_password_hash

DB_FILE = 'votestack3.db'

print("=== Votestack Admin Setup ===\n")

username = input("Admin username: ").strip()
if not username:
    print("Username cannot be empty.")
    exit(1)

password = getpass.getpass("Admin password: ")
confirm  = getpass.getpass("Confirm password: ")

if password != confirm:
    print("Passwords do not match.")
    exit(1)

if len(password) < 8:
    print("Password must be at least 8 characters.")
    exit(1)

password_hash = generate_password_hash(password)

try:
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT OR REPLACE INTO admins (username, password_hash) VALUES (?, ?)",
        (username, password_hash)
    )
    conn.commit()
    conn.close()
    print(f"\nAdmin account '{username}' created successfully.")
    print("You can now log in at /admin_login")
except Exception as e:
    print(f"Error: {e}")
    exit(1)
