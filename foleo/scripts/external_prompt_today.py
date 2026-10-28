"""Build the ChatGPT/Claude prompt from the same 3-month prices Foleo uses, and print Foleo's answers.

Run right after taking the Foleo screenshots (ideally after the 15:30 IST close, so prices don't move):
    python scripts/external_prompt_today.py IDEA:13 YESBANK:23 SUZLON:53
Each argument is SYMBOL:AVG_PRICE (quantity 1, NSE). Writes reports/external_prompt_today.md.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from llm_orchestrator.utils.quantitative_tools import (  # noqa: E402
    _fetch_price_histories, _holding_ticker, _run_metric,
)

PERIOD = "3mo"
holdings = []
for arg in sys.argv[1:] or ["IDEA:13", "YESBANK:23", "SUZLON:53"]:
    sym, avg = arg.split(":")
    holdings.append({"tradingsymbol": sym, "exchange": "NSE", "quantity": 1, "average_price": float(avg)})

tickers = [_holding_ticker(h) for h in holdings]
prices = _fetch_price_histories(tickers, period=PERIOD)
import pandas as pd  # noqa: E402

closes = pd.concat([prices[t].iloc[:, 0].rename(t) for t in tickers], axis=1, join="inner").dropna()
table = "date," + ",".join(tickers) + "\n" + "\n".join(
    f"{d:%Y-%m-%d}," + ",".join(f"{v:.2f}" for v in row) for d, row in zip(closes.index, closes.values))

rows = "\n".join(f"| {h['tradingsymbol']} | 1 | {h['average_price']:g} | <LTP from Foleo Holdings page> |" for h in holdings)
prompt = f"""You are a precise financial analyst. Use only the data below and compute exactly (you may run code).

My portfolio (NSE, Upstox):
| Stock | Qty | Avg price (Rs) | Last price (Rs) |
|---|---|---|---|
{rows}

Daily closing prices for the last 3 months (CSV):
{table}

Tasks:
1. For each holding and for the whole portfolio: invested value (qty x avg price), current value (qty x last price),
   profit or loss (current - invested) and percentage profit or loss (P&L / invested x 100).
2. Classify the portfolio using this rule on total P&L%: Buy if >= 10, Hold if 0 < x < 10, Trim if -10 < x <= 0, Exit if <= -10.
3. Using the daily portfolio value V_t = sum of (qty x close) over the price table, and daily returns r_t = V_t / V_(t-1) - 1:
   a. Sharpe ratio = (mean(r) - 0.05/252) / sample_std(r) x sqrt(252)
   b. 1-day 95% historical VaR (%) = -100 x 5th percentile of r (linear interpolation)
   c. Maximum drawdown (%) = 100 x min over t of (V_t / running max of V - 1)

End with these lines exactly:
FINAL invested: <number>
FINAL current: <number>
FINAL pnl: <number>
FINAL pnl_pct: <number>
FINAL decision: <Buy|Hold|Trim|Exit>
FINAL sharpe: <number, 4 decimals>
FINAL var95: <number, 2 decimals>
FINAL max_drawdown: <number, 2 decimals>
"""

out = ROOT / "reports" / "external_prompt_today.md"
out.write_text("```\n" + prompt + "```\n", encoding="utf-8")
print(prompt)
print(f"-- {len(closes)} trading days, {closes.index[0]:%d %b} to {closes.index[-1]:%d %b %Y}; saved to {out}")
print("\nFoleo's tool answers on the same window (should match the screenshots):")
for name in ("sharpe", "var", "drawdown"):
    r = _run_metric(name, {"holdings": [dict(h) for h in holdings], "period": PERIOD})
    print(" ", name, {k: v for k, v in r.items() if isinstance(v, (int, float)) and k != "period"})
