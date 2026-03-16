"""Payments Vendor API — simulated Stripe-compatible payment processor."""


def main() -> None:
    """Start the uvicorn server for the payments vendor API."""
    import uvicorn

    uvicorn.run("payments_vendor.main:app", host="0.0.0.0", port=8000)
