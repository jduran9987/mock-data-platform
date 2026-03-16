"""Pydantic response and request schemas for the customer resource."""

from typing import Any, Optional

from pydantic import BaseModel


class AddressSchema(BaseModel):
    """Stripe address object shape."""

    city: Optional[str] = None
    country: Optional[str] = None
    line1: Optional[str] = None
    line2: Optional[str] = None
    postal_code: Optional[str] = None
    state: Optional[str] = None


class ShippingSchema(BaseModel):
    """Stripe shipping object with nested address."""

    address: Optional[AddressSchema] = None
    name: Optional[str] = None
    phone: Optional[str] = None


class CustomerResponse(BaseModel):
    """Stripe customer object returned in API responses."""

    id: str
    object: str = "customer"
    address: Optional[AddressSchema] = None
    balance: int = 0
    created: int
    currency: Optional[str] = None
    default_source: Optional[str] = None
    delinquent: bool = False
    description: Optional[str] = None
    email: Optional[str] = None
    invoice_prefix: Optional[str] = None
    livemode: bool = False
    metadata: dict[str, Any] = {}
    name: Optional[str] = None
    phone: Optional[str] = None
    shipping: Optional[ShippingSchema] = None
    tax_exempt: str = "none"


class CustomerListResponse(BaseModel):
    """Paginated list response wrapping customer objects."""

    object: str = "list"
    url: str = "/v1/customers"
    has_more: bool = False
    data: list[CustomerResponse] = []
    request_id: str
