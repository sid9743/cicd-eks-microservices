from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/healthz").json() == {"status": "ok"}


def test_list_products():
    resp = client.get("/products")
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_get_product():
    resp = client.get("/products/1")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Mechanical Keyboard"


def test_missing_product_returns_404():
    assert client.get("/products/999").status_code == 404


def test_metrics_exposed():
    client.get("/products/1")
    body = client.get("/metrics/").text
    assert "product_lookups_total" in body
