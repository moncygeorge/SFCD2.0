"""
reset_admin.py
---------------
Recover admin access when the username/password has been forgotten.

Usage:

  # 1. See what admin username(s) already exist
  python reset_admin.py --list

  # 2. Set a new password for an existing admin username
  python reset_admin.py --reset --username admin --password NewPass123

  # 3. Or, if you don't remember the username either, just wipe all
  #    admin accounts and create a fresh one in one step:
  python reset_admin.py --recreate --username admin --password NewPass123

Set DB_PATH as an environment variable first if your deployment uses a
non-default database path (e.g. on Render with a persistent disk):

  export DB_PATH=/data/votestack3.db
"""

import argparse
import os
import sqlite3
from werkzeug.security import generate_password_hash

DB_FILE = os.environ.get('DB_PATH', 'votestack3.db')


def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def list_admins():
    conn = get_conn()
    rows = conn.execute("SELECT id, username FROM admins").fetchall()
    conn.close()
    if not rows:
        print(f"No admin accounts found in {DB_FILE}.")
        print("Run with --recreate --username ... --password ... to create one.")
    else:
        print(f"Admin accounts in {DB_FILE}:")
        for r in rows:
            print(f"  id={r['id']}  username={r['username']}")


def reset_password(username, password):
    if len(password) < 8:
        print("Password must be at least 8 characters.")
        return
    conn = get_conn()
    existing = conn.execute("SELECT id FROM admins WHERE username=?", (username,)).fetchone()
    if not existing:
        print(f"No admin found with username '{username}'. Use --list to see existing usernames,")
        print("or --recreate to wipe and start fresh.")
        conn.close()
        return
    conn.execute(
        "UPDATE admins SET password_hash=? WHERE username=?",
        (generate_password_hash(password), username)
    )
    conn.commit()
    conn.close()
    print(f"Password updated for admin '{username}'. You can log in now.")


def recreate_admin(username, password):
    if len(password) < 8:
        print("Password must be at least 8 characters.")
        return
    conn = get_conn()
    conn.execute("DELETE FROM admins")
    conn.execute(
        "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
        (username, generate_password_hash(password))
    )
    conn.commit()
    conn.close()
    print(f"All previous admin accounts removed. New admin '{username}' created. You can log in now.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Recover or reset SFCD admin access.")
    parser.add_argument('--list', action='store_true', help="List existing admin usernames")
    parser.add_argument('--reset', action='store_true', help="Reset the password for an existing username")
    parser.add_argument('--recreate', action='store_true', help="Wipe all admins and create a new one")
    parser.add_argument('--username', help="Admin username")
    parser.add_argument('--password', help="New password (min 8 characters)")
    args = parser.parse_args()

    if args.list:
        list_admins()
    elif args.reset:
        if not args.username or not args.password:
            print("--reset requires --username and --password")
        else:
            reset_password(args.username, args.password)
    elif args.recreate:
        if not args.username or not args.password:
            print("--recreate requires --username and --password")
        else:
            recreate_admin(args.username, args.password)
    else:
        parser.print_help()
