import time
import threading
import logging
from pybit.unified_trading import HTTP

import config
from signal_parser import ParsedSignal

log = logging.getLogger("bybit_executor")

session = HTTP(
    testnet=False,
    demo=config.BYBIT_DEMO,
    api_key=config.BYBIT_API_KEY,
    api_secret=config.BYBIT_API_SECRET,
)


def get_market_price(symbol: str) -> float:
    resp = session.get_tickers(category=config.BYBIT_CATEGORY, symbol=symbol)
    return float(resp["result"]["list"][0]["lastPrice"])


def qty_for_symbol(symbol: str, usdt_size: float, price: float) -> str:
    """
    Convert a USDT stake into a base-asset qty, rounded to the symbol's
    step size. Pulls instrument info live rather than hardcoding steps.
    """
    info = session.get_instruments_info(category=config.BYBIT_CATEGORY, symbol=symbol)
    lot = info["result"]["list"][0]["lotSizeFilter"]
    step = float(lot["qtyStep"])
    raw_qty = (usdt_size * config.LEVERAGE) / price
    steps = int(raw_qty / step)
    qty = steps * step
    decimals = len(lot["qtyStep"].split(".")[1]) if "." in lot["qtyStep"] else 0
    return f"{qty:.{decimals}f}"


def set_leverage(symbol: str):
    try:
        session.set_leverage(
            category=config.BYBIT_CATEGORY,
            symbol=symbol,
            buyLeverage=str(config.LEVERAGE),
            sellLeverage=str(config.LEVERAGE),
        )
    except Exception as e:
        # Bybit throws if leverage is already set to this value — safe to ignore
        log.info(f"set_leverage note for {symbol}: {e}")


def execute_signal(sig: ParsedSignal) -> dict:
    market_price = get_market_price(sig.symbol)
    diff_pct = abs(market_price - sig.entry) / sig.entry * 100

    order_type = "Market" if diff_pct <= config.PRICE_MATCH_THRESHOLD_PCT else "Limit"
    qty = qty_for_symbol(sig.symbol, config.POSITION_SIZE_USDT, market_price)

    order_kwargs = dict(
        category=config.BYBIT_CATEGORY,
        symbol=sig.symbol,
        side=sig.side,
        orderType=order_type,
        qty=qty,
        stopLoss=str(sig.stop_loss) if sig.stop_loss else None,
        takeProfit=str(sig.take_profits[0]) if sig.take_profits else None,
        timeInForce="GTC",
    )
    if order_type == "Limit":
        order_kwargs["price"] = str(sig.entry)

    # drop None values — pybit doesn't like them
    order_kwargs = {k: v for k, v in order_kwargs.items() if v is not None}

    log.info(f"[{'DRY RUN' if config.DRY_RUN else 'LIVE'}] {order_type} {sig.side} {qty} "
              f"{sig.symbol} @ {'market' if order_type == 'Market' else sig.entry} "
              f"(signal entry {sig.entry}, market {market_price}, diff {diff_pct:.2f}%)")

    if config.DRY_RUN:
        return {"dry_run": True, "order_type": order_type, "qty": qty,
                "symbol": sig.symbol, "diff_pct": diff_pct}

    set_leverage(sig.symbol)
    result = session.place_order(**order_kwargs)

    if order_type == "Limit":
        order_id = result["result"]["orderId"]
        _schedule_cancel_if_unfilled(sig.symbol, order_id)

    return result


def _schedule_cancel_if_unfilled(symbol: str, order_id: str):
    def cancel_if_stale():
        time.sleep(config.LIMIT_ORDER_EXPIRY_MIN * 60)
        try:
            open_orders = session.get_open_orders(category=config.BYBIT_CATEGORY, symbol=symbol)
            still_open = any(o["orderId"] == order_id for o in open_orders["result"]["list"])
            if still_open:
                session.cancel_order(category=config.BYBIT_CATEGORY, symbol=symbol, orderId=order_id)
                log.info(f"Cancelled stale limit order {order_id} for {symbol} "
                          f"after {config.LIMIT_ORDER_EXPIRY_MIN}min unfilled")
        except Exception as e:
            log.error(f"Error checking/cancelling stale order {order_id}: {e}")

    threading.Thread(target=cancel_if_stale, daemon=True).start()
