"""Visitors without a broker get the demo portfolio only when the web app asks for it."""
import pytest
from fastapi.testclient import TestClient

from backend_api.app import app
from backend_api.database import token_store
from backend_api.routes import portfolio

DEMO = [{"tradingsymbol": "TCS", "exchange": "NSE", "quantity": 10, "average_price": 2380.0, "last_price": 2460.0, "_source": "demo"}]


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(token_store, "DB_PATH", tmp_path / "demo.db")
    token_store.init_db()
    monkeypatch.setattr(portfolio, "demo_holdings", lambda: [dict(h) for h in DEMO])
    monkeypatch.setattr(portfolio, "_sector_count_and_beta", lambda holdings: (1, 0.9))
    c = TestClient(app)
    account = {"email": "demo@example.com", "password": "secret123"}
    c.post("/api/auth/register", json=account)
    token = c.post("/api/auth/login", json=account).json()["access_token"]
    c.headers["Authorization"] = f"Bearer {token}"
    return c


def test_demo_header_serves_demo_portfolio(client):
    body = client.get("/api/portfolio/summary", headers={"X-Foleo-Demo": "1"}).json()
    assert body["data_status"] == "demo"
    assert body["total_invested"] == 23800.0
    assert body["total_current_value"] == 24600.0
    assert body["health_score"] is not None


def test_without_demo_header_user_is_asked_to_link(client):
    body = client.get("/api/portfolio/summary").json()
    assert body["linked"] is False
    assert body["data_status"] == "not_linked"
