"""Product service: serves the product catalogue used by order-service."""
import logging
import os

from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, make_asgi_app
from pydantic import BaseModel

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = logging.getLogger("product-service")

app = FastAPI(title="product-service", version=os.getenv("APP_VERSION", "dev"))
app.mount("/metrics", make_asgi_app())

LOOKUPS = Counter("product_lookups_total", "Product lookups", ["result"])


class Product(BaseModel):
    id: int
    name: str
    price: float
    stock: int


# In-memory catalogue keeps the demo self-contained. Swap for RDS in a real setup.
CATALOGUE: dict[int, Product] = {
    1: Product(id=1, name="Mechanical Keyboard", price=3499.0, stock=25),
    2: Product(id=2, name="27-inch Monitor", price=15999.0, stock=10),
    3: Product(id=3, name="USB-C Dock", price=5299.0, stock=0),
}


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    return {"status": "ready", "products": len(CATALOGUE)}


@app.get("/products", response_model=list[Product])
def list_products():
    return list(CATALOGUE.values())


@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int):
    product = CATALOGUE.get(product_id)
    if product is None:
        LOOKUPS.labels(result="not_found").inc()
        raise HTTPException(status_code=404, detail="product not found")
    LOOKUPS.labels(result="found").inc()
    return product
