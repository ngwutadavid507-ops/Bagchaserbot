import os
import logging
import threading
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession

import config
from signal_parser import parse_signal
from bybit_executor import execute_signal

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("signal-bot")

open_position_count = 0  # naive local counter; for real accuracy, query Bybit positions instead

client = TelegramClient(
    StringSession(config.TG_SESSION_STRING),
    config.TG_API_ID,
    config.TG_API_HASH,
)

# --- Tiny health-check web server, so UptimeRobot has something to ping ---
# This is what lets us deploy as a free Render Web Service instead of a
# paid Background Worker: UptimeRobot pings this every few minutes, which
# keeps the whole process (including the Telegram listener below) awake.
app = Flask(__name__)


@app.route("/")
def health():
    return "Signal bot is running", 200


def run_health_server():
    port = int(os.getenv("PORT", "10000"))  # Render sets PORT automatically
    app.run(host="0.0.0.0", port=port)


async def send_alert(text: str):
    if config.TG_ALERT_CHAT_ID:
        try:
            await client.send_message(config.TG_ALERT_CHAT_ID, text)
        except Exception as e:
            log.error(f"Failed to send alert: {e}")


@client.on(events.NewMessage(chats=config.TG_SOURCE_CHANNEL))
async def on_signal(event):
    global open_position_count
    text = event.raw_text
    log.info(f"New message: {text[:200]}")

    sig = parse_signal(text)
    if sig is None:
        log.warning("Could not parse message as a signal — skipping")
        await send_alert(f"⚠️ Couldn't parse a signal from:\n\n{text[:300]}")
        return

    if open_position_count >= config.MAX_OPEN_POSITIONS:
        log.warning(f"Max open positions ({config.MAX_OPEN_POSITIONS}) reached — skipping {sig.symbol}")
        await send_alert(f"⚠️ Skipped {sig.symbol} signal — max open positions reached")
        return

    try:
        result = execute_signal(sig)
        open_position_count += 1
        await send_alert(
            f"✅ {sig.side} {sig.symbol} executed\n"
            f"Entry: {sig.entry} | SL: {sig.stop_loss} | TP: {sig.take_profits}\n"
            f"Result: {result}"
        )
    except Exception as e:
        log.error(f"Order execution failed for {sig.symbol}: {e}")
        await send_alert(f"❌ Failed to execute {sig.symbol} signal: {e}")


def main():
    log.info(f"Starting signal bot | DRY_RUN={config.DRY_RUN} | "
              f"watching {config.TG_SOURCE_CHANNEL}")

    # Run the health-check server in a background thread so it doesn't
    # block the Telegram client's event loop
    threading.Thread(target=run_health_server, daemon=True).start()

    client.start()
    client.run_until_disconnected()


if __name__ == "__main__":
    main()
