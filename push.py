"""
push.py
-------
Minimal Web Push (VAPID) helper for sending browser notifications to
subscribed members. Uses pywebpush under the hood.

Setup:
  1. Run `python generate_vapid_keys.py` once to create a key pair.
  2. Set these environment variables (Heroku config vars / .env):
       VAPID_PUBLIC_KEY
       VAPID_PRIVATE_KEY
       VAPID_CLAIM_EMAIL   (e.g. mailto:admin@yourchurch.org)
"""

import os
import json
import sqlite3
from pywebpush import webpush, WebPushException

VAPID_PUBLIC_KEY  = os.environ.get('VAPID_PUBLIC_KEY', '')
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '')
VAPID_CLAIM_EMAIL = os.environ.get('VAPID_CLAIM_EMAIL', 'mailto:admin@example.org')


def push_configured():
    return bool(VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY)


def save_subscription(db_file, subscription, username=None):
    """Store (or update) a browser's push subscription."""
    endpoint = subscription.get('endpoint')
    keys     = subscription.get('keys', {})
    p256dh   = keys.get('p256dh')
    auth     = keys.get('auth')
    if not (endpoint and p256dh and auth):
        return False

    conn = sqlite3.connect(db_file)
    conn.execute(
        """INSERT INTO push_subscriptions (username, endpoint, p256dh, auth)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(endpoint) DO UPDATE SET username=excluded.username""",
        (username, endpoint, p256dh, auth)
    )
    conn.commit()
    conn.close()
    return True


def send_push_to_all(db_file, title, body, url='/'):
    """Send a notification to every stored subscription. Prunes dead ones."""
    if not push_configured():
        print("[push] VAPID keys not set — skipping push send.")
        return {"sent": 0, "failed": 0, "skipped": True}

    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM push_subscriptions").fetchall()

    sent, failed, dead_endpoints = 0, 0, []

    payload = json.dumps({"title": title, "body": body, "url": url})

    for row in rows:
        subscription_info = {
            "endpoint": row["endpoint"],
            "keys": {"p256dh": row["p256dh"], "auth": row["auth"]},
        }
        try:
            webpush(
                subscription_info=subscription_info,
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub": VAPID_CLAIM_EMAIL},
            )
            sent += 1
        except WebPushException as ex:
            failed += 1
            # 404/410 = subscription expired or unsubscribed — clean it up
            status = getattr(ex.response, 'status_code', None)
            if status in (404, 410):
                dead_endpoints.append(row["endpoint"])

    if dead_endpoints:
        conn.executemany(
            "DELETE FROM push_subscriptions WHERE endpoint=?",
            [(e,) for e in dead_endpoints]
        )
        conn.commit()

    conn.close()
    return {"sent": sent, "failed": failed, "skipped": False}
