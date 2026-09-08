"""
seed_users.py
Adds phone numbers from usernames.txt into the SQLite DB.
Run once after deployment if you have existing voter lists.
"""
import sqlite3

DB_FILE = 'votestack3.db'
USERNAMES_FILE = 'usernames.txt'

conn = sqlite3.connect(DB_FILE)

try:
    with open(USERNAMES_FILE, 'r') as f:
        phones = [line.strip() for line in f if line.strip()]

    conn.executemany(
        "INSERT OR IGNORE INTO users (phone_number) VALUES (?)",
        [(p,) for p in phones]
    )
    conn.commit()
    print(f"Seeded {len(phones)} users.")
except FileNotFoundError:
    print(f"{USERNAMES_FILE} not found – nothing to seed.")
finally:
    conn.close()
