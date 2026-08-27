"""
Run this ONCE, interactively, to log in with your Telegram account and
produce a session string. Render workers can't do interactive login,
so you generate this locally (Termux works fine) and paste the output
into the TG_SESSION_STRING env var on Render.

Usage (Termux):
    pip install telethon
    python generate_session.py
    -> enter your API_ID / API_HASH (from https://my.telegram.org)
    -> enter phone number, then the code Telegram sends you
    -> copy the printed session string into Render env vars

Do NOT commit the session string to GitHub. Treat it like a password —
it grants full access to your Telegram account.
"""
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = int(input("API ID: "))
api_hash = input("API HASH: ")

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("\nYour session string (copy this into TG_SESSION_STRING on Render):\n")
    print(client.session.save())
