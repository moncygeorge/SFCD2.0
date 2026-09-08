"""
init_db.py
----------
Creates all tables and (once) migrates legacy flat-file data into SQLite.
Called automatically by app.py on every startup – safe to run repeatedly
because every CREATE TABLE uses IF NOT EXISTS.
"""

import os
import sqlite3


# ── schema ─────────────────────────────────────────────────────────────────────

def get_db_connection(db_file):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables(db_file='votestack3.db'):
    conn = get_db_connection(db_file)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT UNIQUE NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS choices (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            role   TEXT NOT NULL,
            choice TEXT NOT NULL,
            UNIQUE(role, choice)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT NOT NULL,
            role       TEXT NOT NULL,
            choice     TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(username, role)
        )
    ''')

    # ── SFCD community features ──────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS announcements (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT NOT NULL,
            body       TEXT NOT NULL,
            image_path TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            description TEXT,
            location    TEXT,
            event_date  TEXT NOT NULL,
            event_time  TEXT,
            image_path  TEXT,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gallery (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            caption    TEXT,
            image_path TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rsvps (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL COLLATE NOCASE UNIQUE,
            attending  INTEGER NOT NULL CHECK(attending IN (0,1)),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS push_subscriptions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT,
            endpoint   TEXT UNIQUE NOT NULL,
            p256dh     TEXT NOT NULL,
            auth       TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print(f"[init_db] Tables ready in {db_file}")


# ── one-time file → DB migration ───────────────────────────────────────────────

def _set_current_role(conn, role):
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        ('current_role', role)
    )


def _migrate_role(conn, role_file):
    if not os.path.exists(role_file):
        return None
    with open(role_file, 'r', encoding='utf-8') as f:
        role = f.read().strip()
    if role:
        _set_current_role(conn, role)
        print(f"[init_db] Migrated role: {role}")
        return role
    return None


def _migrate_choices(conn, choices_file, role):
    if not role or not os.path.exists(choices_file):
        return
    with open(choices_file, 'r', encoding='utf-8') as f:
        choices = [line.strip() for line in f if line.strip()]
    if not choices:
        return
    conn.execute("DELETE FROM choices WHERE role=?", (role,))
    conn.executemany(
        "INSERT OR IGNORE INTO choices (role, choice) VALUES (?, ?)",
        [(role, c) for c in choices]
    )
    print(f"[init_db] Migrated {len(choices)} choices for role '{role}'")


def _migrate_votes(conn, votes_file):
    if not os.path.exists(votes_file):
        return
    with open(votes_file, 'r', encoding='utf-8') as f:
        rows = [line.strip() for line in f if line.strip()]
    migrated = 0
    for row in rows:
        parts = row.split(':')
        if len(parts) != 3:
            continue
        username, role, choice = parts
        try:
            conn.execute(
                "INSERT OR IGNORE INTO votes (username, role, choice) VALUES (?, ?, ?)",
                (username, role, choice)
            )
            migrated += 1
        except sqlite3.DatabaseError:
            continue
    if migrated:
        print(f"[init_db] Migrated {migrated} votes from file")


def migrate_files_to_db(
    db_file='votestack3.db',
    role_file='roles.txt',
    choices_file='choices.txt',
    votes_file='votes.txt',
):
    """
    Runs migration only if the DB doesn't already have a current_role set
    (so it's safe to call on every startup without duplicating data).
    """
    conn = get_db_connection(db_file)

    existing_role_row = conn.execute(
        "SELECT value FROM settings WHERE key='current_role'"
    ).fetchone()

    if existing_role_row:
        role = existing_role_row['value']
        print(f"[init_db] DB already initialised, current role: {role}")
    else:
        role = _migrate_role(conn, role_file)
        if role:
            _migrate_choices(conn, choices_file, role)
            _migrate_votes(conn, votes_file)

    conn.commit()
    conn.close()


# ── standalone usage ───────────────────────────────────────────────────────────

if __name__ == '__main__':
    create_tables()
    migrate_files_to_db()
    print('[init_db] Done.')
