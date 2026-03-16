"""Customer data generation engine.

Creates new customers and updates existing ones on each API request,
injecting messy data and data quality issues according to config.
"""

import json
import random
import string
import time

from faker import Faker
from sqlmodel import Session, select

from payments_vendor.internal.config import config
from payments_vendor.internal.messy import maybe_null, maybe_omit_nested
from payments_vendor.internal.quality_issues import CustomerDQIssueType, dq_registry
from payments_vendor.models.customer import Customer, CustomerAddress, CustomerShipping
from payments_vendor.schemas.customer import (
    AddressSchema,
    CustomerResponse,
    ShippingSchema,
)

fake = Faker()


def _generate_id(prefix: str, length: int = 14) -> str:
    """Generate a Stripe-style prefixed random ID."""
    chars = string.ascii_letters + string.digits
    return f"{prefix}{''.join(random.choices(chars, k=length))}"


def _generate_invoice_prefix() -> str:
    """Generate an 8-character alphanumeric invoice prefix."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


def _create_customer(session: Session, request_id: str) -> Customer:
    """Generate a new customer with randomized data and persist it.

    Args:
        session: Active database session.
        request_id: Current request ID for DQ issue tracking.

    Returns:
        The newly created customer record.
    """
    cus_id = _generate_id("cus_")

    customer = Customer(
        id=cus_id,
        name=maybe_null(fake.name()),
        email=fake.email(),
        phone=maybe_null(fake.phone_number()),
        description=maybe_null(fake.sentence()),
        balance=random.choice([0, 0, 0, random.randint(-10000, 50000)]),
        currency=maybe_null(random.choice(["usd", "eur", "gbp", "cad"])),
        created=int(time.time()) - random.randint(0, 86400 * 365),
        livemode=False,
        delinquent=random.random() < 0.05,
        default_source=maybe_null(_generate_id("card_")),
        invoice_prefix=_generate_invoice_prefix(),
        metadata_json=json.dumps(maybe_null({fake.word(): fake.word()}) or {}),
        tax_exempt=random.choice(["none", "none", "none", "exempt", "reverse"]),
    )

    # DQ issue: null email (email is effectively required in Stripe)
    if random.random() < config.dq_issue_rate:
        dq_registry.record_issue(
            request_id=request_id,
            resource_type="customer",
            resource_id=cus_id,
            issue_type=CustomerDQIssueType.NULL_EMAIL_ON_REQUIRED,
            original_value=customer.email,
        )
        customer.email = None

    session.add(customer)

    # Address (optional nested object)
    if maybe_omit_nested("present") is not None:
        address = CustomerAddress(
            customer_id=cus_id,
            city=maybe_null(fake.city()),
            country=maybe_null(fake.country_code()),
            line1=maybe_null(fake.street_address()),
            line2=maybe_null(fake.secondary_address()),
            postal_code=maybe_null(fake.postcode()),
            state=maybe_null(fake.state_abbr()),
        )
        session.add(address)

    # Shipping (optional nested object)
    if maybe_omit_nested("present") is not None:
        shipping = CustomerShipping(
            customer_id=cus_id,
            name=maybe_null(fake.name()),
            phone=maybe_null(fake.phone_number()),
            address_city=maybe_null(fake.city()),
            address_country=maybe_null(fake.country_code()),
            address_line1=maybe_null(fake.street_address()),
            address_line2=maybe_null(fake.secondary_address()),
            address_postal_code=maybe_null(fake.postcode()),
            address_state=maybe_null(fake.state_abbr()),
        )
        session.add(shipping)

    return customer


def _update_customer(session: Session, customer: Customer, request_id: str) -> Customer:
    """Randomly mutate fields on an existing customer to simulate updates.

    Args:
        session: Active database session.
        customer: The customer record to update.
        request_id: Current request ID for DQ issue tracking.

    Returns:
        The updated customer record.
    """
    customer.name = maybe_null(fake.name())
    customer.phone = maybe_null(fake.phone_number())
    customer.description = maybe_null(fake.sentence())
    customer.balance = random.choice(
        [0, customer.balance, random.randint(-10000, 50000)]
    )
    customer.delinquent = random.random() < 0.05
    customer.metadata_json = json.dumps(maybe_null({fake.word(): fake.word()}) or {})
    session.add(customer)
    return customer


def generate_customers(session: Session, request_id: str) -> None:
    """Create new customers and update existing ones before a list response.

    Args:
        session: Active database session.
        request_id: Current request ID for DQ issue tracking.
    """
    num_new = random.randint(config.min_new_records, config.max_new_records)
    for _ in range(num_new):
        _create_customer(session, request_id)

    existing = session.exec(select(Customer)).all()
    if existing:
        num_update = min(
            random.randint(config.min_updated_records, config.max_updated_records),
            len(existing),
        )
        to_update = random.sample(existing, num_update)
        for cust in to_update:
            _update_customer(session, cust, request_id)

    # DQ issue: duplicate ID — tracked here, injected at serialization layer
    if existing and random.random() < config.dq_issue_rate:
        source = random.choice(existing)
        dq_registry.record_issue(
            request_id=request_id,
            resource_type="customer",
            resource_id=source.id,
            issue_type=CustomerDQIssueType.DUPLICATE_ID,
        )

    session.commit()


def serialize_customer(
    session: Session, customer: Customer, request_id: str
) -> CustomerResponse:
    """Convert a Customer DB record to the API response schema.

    Args:
        session: Active database session for loading related objects.
        customer: The customer record to serialize.
        request_id: Current request ID (unused, reserved for future DQ hooks).

    Returns:
        A Stripe-shaped customer response object.
    """
    address_row = session.get(CustomerAddress, customer.id)
    address: AddressSchema | None = None
    if address_row:
        address = AddressSchema(
            city=address_row.city,
            country=address_row.country,
            line1=address_row.line1,
            line2=address_row.line2,
            postal_code=address_row.postal_code,
            state=address_row.state,
        )

    shipping_row = session.get(CustomerShipping, customer.id)
    shipping: ShippingSchema | None = None
    if shipping_row:
        shipping = ShippingSchema(
            name=shipping_row.name,
            phone=shipping_row.phone,
            address=AddressSchema(
                city=shipping_row.address_city,
                country=shipping_row.address_country,
                line1=shipping_row.address_line1,
                line2=shipping_row.address_line2,
                postal_code=shipping_row.address_postal_code,
                state=shipping_row.address_state,
            ),
        )

    metadata: dict[str, str] = (
        json.loads(customer.metadata_json) if customer.metadata_json else {}
    )

    return CustomerResponse(
        id=customer.id,
        object=customer.object,
        address=address,
        balance=customer.balance,
        created=customer.created,
        currency=customer.currency,
        default_source=customer.default_source,
        delinquent=customer.delinquent,
        description=customer.description,
        email=customer.email,
        invoice_prefix=customer.invoice_prefix,
        livemode=customer.livemode,
        metadata=metadata,
        name=customer.name,
        phone=customer.phone,
        shipping=shipping,
        tax_exempt=customer.tax_exempt,
    )
