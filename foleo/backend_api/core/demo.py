"""Demo portfolio for visitors who have not linked a broker.

The web app sends `X-Foleo-Demo: 1` while demo mode is on; middleware in app.py stores it in
`demo_requested`. Users with a linked broker always get their real holdings.
"""
from __future__ import annotations

from contextvars import ContextVar

demo_requested: ContextVar[bool] = ContextVar("demo_requested", default=False)

# (symbol, quantity, average buy price). Last prices are filled from the market at request time.
_DEMO_POSITIONS = [
    ("TCS", 10, 2380.0),
    ("HDFCBANK", 40, 720.0),
    ("RELIANCE", 20, 1090.0),
    ("INFY", 15, 1180.0),
    ("ITC", 60, 245.0),
    ("SUNPHARMA", 8, 1620.0),
]


def demo_holdings() -> list[dict]:
    """Demo positions priced at the latest NSE close (falls back to the buy price if prices are unavailable)."""
    from llm_orchestrator.utils.quantitative_tools import _fetch_price_histories

    tickers = [f"{symbol}.NS" for symbol, _, _ in _DEMO_POSITIONS]
    try:
        prices = _fetch_price_histories(tickers, period="5d")
    except Exception:
        prices = {}

    holdings = []
    for symbol, quantity, average_price in _DEMO_POSITIONS:
        frame = prices.get(f"{symbol}.NS")
        last_price = float(frame.iloc[-1, 0]) if frame is not None and len(frame) else average_price
        holdings.append({
            "tradingsymbol": symbol,
            "exchange": "NSE",
            "quantity": quantity,
            "average_price": average_price,
            "last_price": round(last_price, 2),
            "_source": "demo",
        })
    return holdings
