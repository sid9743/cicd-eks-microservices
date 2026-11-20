from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from app import main

client = TestClient(main.app)

KEYBOARD = {"id": 1, "name": "Mechanical Keyboard", "price": 3499.0, "stock": 25}
DOCK = {"id": 3, "name": "USB-C Dock", "price": 5299.0, "stock": 0}


def test_health():
    assert client.get("/healthz").status_code == 200


@patch.object(main, "fetch_product", return_value=KEYBOARD)
def test_create_order(_):
    resp = client.post("/orders", json={"product_id": 1, "quantity": 2})
    assert resp.status_code == 201
    assert resp.json()["total"] == 6998.0


@patch.object(main, "fetch_product", return_value=DOCK)
def test_out_of_stock(_):
    resp = client.post("/orders", json={"product_id": 3, "quantity": 1})
    assert resp.status_code == 409


def test_invalid_quantity():
    resp = client.post("/orders", json={"product_id": 1, "quantity": 0})
    assert resp.status_code == 422


@patch.object(main, "fetch_product", side_effect=httpx.ConnectError("down"))
def test_upstream_down_returns_503(_):
    resp = client.post("/orders", json={"product_id": 1, "quantity": 1})
    assert resp.status_code == 503
