import os

# --- Telegram (userbot, NOT a bot token) ---
TG_API_ID = int(os.getenv("TG_API_ID", "0"))
TG_API_HASH = os.getenv("TG_API_HASH", "")
TG_SESSION_STRING = os.getenv("TG_SESSION_STRING", "")  # generated once, see generate_session.py
TG_SOURCE_CHANNEL = os.getenv("TG_SOURCE_CHANNEL", "")  # e.g. "@somechannel" or numeric chat id
TG_ALERT_CHAT_ID = os.getenv("TG_ALERT_CHAT_ID", "")     # where the bot DMs you on parse failures / fills

# --- Bybit (DEMO account keys) ---
BYBIT_API_KEY = os.getenv("BYBIT_DEMO_API_KEY", "")
BYBIT_API_SECRET = os.getenv("BYBIT_DEMO_API_SECRET", "")
BYBIT_DEMO = True          # keep True until you've watched it run clean for a while
BYBIT_CATEGORY = "linear"  # USDT perpetuals

# --- Execution behavior ---
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"   # log only, place nothing
PRICE_MATCH_THRESHOLD_PCT = float(os.getenv("PRICE_MATCH_THRESHOLD_PCT", "0.3"))  # market vs limit cutoff
LIMIT_ORDER_EXPIRY_MIN = int(os.getenv("LIMIT_ORDER_EXPIRY_MIN", "30"))  # auto-cancel stale limits
POSITION_SIZE_USDT = float(os.getenv("POSITION_SIZE_USDT", "10"))  # per-trade stake
LEVERAGE = int(os.getenv("LEVERAGE", "10"))
MAX_OPEN_POSITIONS = int(os.getenv("MAX_OPEN_POSITIONS", "5"))
