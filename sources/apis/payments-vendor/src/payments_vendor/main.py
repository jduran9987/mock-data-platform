"""FastAPI application entrypoint and router registration."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from payments_vendor.api.v1.customers import router as customers_router
from payments_vendor.db.init_db import init_db
from payments_vendor.internal.fix import router as fix_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize the database on startup."""
    init_db()
    yield


app = FastAPI(
    title="Payments Vendor API",
    description="Stripe-compatible payments API for simulated e-commerce data.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(customers_router)
app.include_router(fix_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Return service health status."""
    return {"status": "ok"}
