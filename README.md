# Phoenix Signal Bot — Telegram → Bybit automation

Listens to a Telegram channel you're a member of, parses trading signals,
and auto-places orders on Bybit (demo account to start). Market order if
signal price is still close to current market price, otherwise a limit
order at the signal's entry price with an auto-cancel if it never fills.

## 1. Get Telegram API credentials
Go to https://my.telegram.org → API Development Tools → create an app.
You'll get `api_id` and `api_hash`.

## 2. Generate a session string (one-time, do this locally in Termux)
