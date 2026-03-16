"""SQLModel database models for the customer resource and related objects."""

import time
from typing import Optional

from sqlmodel import Field, SQLModel


class CustomerAddress(SQLModel, table=True):
    """Billing address associated with a customer."""

    __tablename__ = "customer_addresses"

    customer_id: str = Field(primary_key=True, foreign_key="customers.id")
    city: Optional[str] = None
    country: Optional[str] = None
    line1: Optional[str] = None
    line2: Optional[str] = None
    postal_code: Optional[str] = None
    state: Optional[str] = None


class CustomerShipping(SQLModel, table=True):
    """Shipping details associated with a customer, with a flattened address."""

    __tablename__ = "customer_shipping"

    customer_id: str = Field(primary_key=True, foreign_key="customers.id")
    name: Optional[str] = None
    phone: Optional[str] = None
    address_city: Optional[str] = None
    address_country: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_state: Optional[str] = None


class Customer(SQLModel, table=True):
    """Core customer record mirroring the Stripe customer object."""

    __tablename__ = "customers"

    id: str = Field(primary_key=True)
    object: str = Field(default="customer")
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    balance: int = Field(default=0)
    currency: Optional[str] = None
    created: int = Field(default_factory=lambda: int(time.time()))
    livemode: bool = Field(default=False)
    delinquent: bool = Field(default=False)
    default_source: Optional[str] = None
    invoice_prefix: Optional[str] = None
    metadata_json: str = Field(default="{}")
    tax_exempt: str = Field(default="none")
