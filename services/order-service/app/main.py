"""Order service: validates stock with product-service before accepting an order."""
import logging
import os
import uuid

import httpx
from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Histogram, make_asgi_app
from pydantic import BaseModel, Field

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = logging.getLogger("order-service")

PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8000")

app = FastAPI(title="order-service", version=os.getenv("APP_VERSION", "dev"))
app.mount("/metrics", make_asgi_app())

ORDERS = Counter("orders_total", "Orders processed", ["status"])
UPSTREAM_LATENCY = Histogram("product_service_latency_seconds", "Latency of product-service calls")


class OrderRequest(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, le=10)


class Order(BaseModel):
    order_id: str
    product_id: int
    quantity: int
    total: float


def fetch_product(product_id: int) -> dict:
    with UPSTREAM_LATENCY.time():
        resp = httpx.get(f"{PRODUCT_SERVICE_URL}/products/{product_id}", timeout=3.0)
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="product not found")
    resp.raise_for_status()
    return resp.json()


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/orders", response_model=Order, status_code=201)
def create_order(req: OrderRequest):
    try:
        product = fetch_product(req.product_id)
    except httpx.HTTPError as exc:
        ORDERS.labels(status="upstream_error").inc()
        log.error("product-service call failed: %s", exc)
        raise HTTPException(status_code=503, detail="product-service unavailable") from exc

    if product["stock"] < req.quantity:
        ORDERS.labels(status="out_of_stock").inc()
        raise HTTPException(status_code=409, detail="not enough stock")

    ORDERS.labels(status="created").inc()
    return Order(
        order_id=str(uuid.uuid4()),
        product_id=req.product_id,
        quantity=req.quantity,
        total=round(product["price"] * req.quantity, 2),
    )
