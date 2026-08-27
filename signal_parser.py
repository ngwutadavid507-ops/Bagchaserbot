import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedSignal:
    symbol: str          # e.g. "BTCUSDT"
    side: str            # "Buy" or "Sell"
    entry: float
    stop_loss: Optional[float]
    take_profits: list   # can be one or several TP levels
    raw_text: str


# Matches things like: BTC/USDT, BTCUSDT, $BTC, BTC-USDT
_SYMBOL_RE = re.compile(r"\b([A-Z]{2,10})[\/\-]?(USDT|USD|BUSD)?\b")
_SIDE_RE = re.compile(r"\b(long|buy|short|sell)\b", re.IGNORECASE)
_ENTRY_RE = re.compile(r"entry[:\s]*\$?([\d,]+\.?\d*)", re.IGNORECASE)
_SL_RE = re.compile(r"(?:stop\s?loss|sl)[:\s]*\$?([\d,]+\.?\d*)", re.IGNORECASE)
_TP_RE = re.compile(r"(?:take\s?profit|tp)\s?\d?[:\s]*\$?([\d,]+\.?\d*)", re.IGNORECASE)


def parse_signal(text: str) -> Optional[ParsedSignal]:
    """
    Best-effort regex parse of a signal message. Returns None if it can't
    confidently extract symbol + side + entry — caller should treat that
    as 'not a signal' or route to a fallback (e.g. LLM parse), never guess.
    """
    if not text:
        return None

    side_match = _SIDE_RE.search(text)
    entry_match = _ENTRY_RE.search(text)
    symbol_match = _SYMBOL_RE.search(text.upper())

    if not (side_match and entry_match and symbol_match):
        return None

    side_word = side_match.group(1).lower()
    side = "Buy" if side_word in ("long", "buy") else "Sell"

    base = symbol_match.group(1)
    quote = symbol_match.group(2) or "USDT"
    symbol = f"{base}{quote}"

    entry = float(entry_match.group(1).replace(",", ""))

    sl_match = _SL_RE.search(text)
    stop_loss = float(sl_match.group(1).replace(",", "")) if sl_match else None

    take_profits = [float(m.group(1).replace(",", "")) for m in _TP_RE.finditer(text)]

    return ParsedSignal(
        symbol=symbol,
        side=side,
        entry=entry,
        stop_loss=stop_loss,
        take_profits=take_profits,
        raw_text=text,
    )
