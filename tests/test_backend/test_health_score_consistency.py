"""The chat must report the same portfolio health score as the dashboard."""
from backend_api.routes import portfolio
from backend_api.services import chat_service
from llm_orchestrator.context.context_builder import build_portfolio_context

HOLDINGS = [
    {"tradingsymbol": "IDEA", "exchange": "NSE", "quantity": 1, "average_price": 13.34, "last_price": 11.53},
    {"tradingsymbol": "YESBANK", "exchange": "NSE", "quantity": 1, "average_price": 23.14, "last_price": 16.05},
    {"tradingsymbol": "SUZLON", "exchange": "NSE", "quantity": 1, "average_price": 52.99, "last_price": 38.57},
]


def test_chat_health_matches_dashboard(monkeypatch):
    monkeypatch.setattr(portfolio, "_get_live_holdings", lambda user_id: (HOLDINGS, None))
    monkeypatch.setattr(portfolio, "_sector_count_and_beta", lambda holdings: (3, 0.66))

    dashboard_score, _ = portfolio._compute_health_score(HOLDINGS, portfolio._aggregate_holdings(HOLDINGS))

    summary = chat_service._fetch_portfolio_summary("u1")
    # What the LLM sees: the context built by the chat pipeline from that summary.
    chat_score = build_portfolio_context(
        user_id="u1",
        holdings=summary["holdings"],
        total_invested=summary["total_invested"],
        total_current_value=summary["total_current_value"],
        total_pnl=summary["total_pnl"],
        total_pnl_pct=summary["total_pnl_pct"],
        sector_count=summary["sector_count"],
        portfolio_beta=summary["portfolio_beta"],
    )["analytics"]["portfolio_health"]["score"]

    assert round(chat_score) == round(dashboard_score)
