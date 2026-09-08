# SFCD

A community app for the church: online voting, announcements, an events
calendar, a photo gallery, and push notifications — installable on members'
phones as a PWA. Built on Flask, fully unified on SQLite, with the DB schema
created automatically on startup.

## Features

- **Voting** — phone-number login for members, admin sets the role/choices, live tally.
- **Announcements** — admin posts updates; members see a feed.
- **Events** — admin posts date/time/location; members see upcoming & past events.
- **Gallery** — admin uploads photos from services/events; members browse them.
- **Push notifications** — members who grant permission get a phone notification
  whenever the admin posts a new announcement or event.
- **Installable app** — the PWA manifest + service worker let members "Add to
  Home Screen" on iOS/Android so it behaves like a native app.

## Setting up push notifications

Push notifications need a VAPID key pair (this proves your server's identity
to Apple/Google's push services — it's free, no account needed).

```bash
pip install -r requirements.txt
python generate_vapid_keys.py
```

This prints three values. Set them as environment variables (locally in a
`.env` file, or as Render/Heroku config vars):

```
VAPID_PUBLIC_KEY=...
VAPID_PRIVATE_KEY=...
VAPID_CLAIM_EMAIL=mailto:admin@yourchurch.org
```

Restart the app after setting these. Until they're set, announcements and
events still post normally — push notifications are just skipped (you'll see
a note in the admin dashboard flash message).

**Note on iOS:** push notifications for installed web apps require iOS 16.4+,
and the member must first "Add to Home Screen" and open the app from there
(Safari itself doesn't support web push) before their browser will prompt for
notification permission.

## What changed from Votestack2

| Issue | Fix |
|---|---|
| `no such table: settings` on every cold start | `app.py` now calls `create_tables()` + `migrate_files_to_db()` inside `with app.app_context()` before the first request |
| `load_role()` read from a flat file while `get_current_role()` queried SQLite | Removed the flat-file path; everything reads/writes the `settings` table |
| `Procfile` said `gunicorn app` (no `:app`) | Fixed to `gunicorn app:app` |
| Voters stored only in `usernames.txt` | All voter CRUD goes through the `users` table |

## Local development

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Deploy on Render

1. Push this repo to GitHub.
2. Create a new **Web Service** on Render, connect the repo.
3. Set **Build Command**: `pip install -r requirements.txt`
4. Set **Start Command**: `gunicorn app:app`
5. Add a **Persistent Disk** (mount path `/data`, any size) and set the
   environment variable `DB_PATH=/data/votestack3.db` if you want data to
   survive restarts (otherwise the DB resets on each deploy on the free tier).
6. Optionally set `SECRET_KEY` to a long random string in Render environment vars.

## Notes on Render's ephemeral filesystem

On Render's free tier, the disk resets on every redeploy. To keep voter
registrations, votes, announcements, events, and uploaded photos across
deploys, add a **Persistent Disk** in the Render dashboard, mount it (e.g.
at `/data`), and:

- set `DB_PATH=/data/votestack3.db`
- symlink or move `static/uploads` onto the persistent disk too, since
  uploaded photos are saved there and will otherwise be wiped on redeploy.
