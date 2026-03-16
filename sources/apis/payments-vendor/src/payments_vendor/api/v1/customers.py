"""Public customer endpoints following the Stripe v1 API pattern."""

import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlmodel import Session, select

from payments_vendor.db.session import get_session
from payments_vendor.internal.generator import generate_customers, serialize_customer
from payments_vendor.internal.quality_issues import CustomerDQIssueType, dq_registry
from payments_vendor.models.customer import Customer
from payments_vendor.schemas.customer import CustomerListResponse

router = APIRouter(prefix="/v1", tags=["customers"])


@router.get("/customers", response_model=CustomerListResponse)
def list_customers(
    response: Response,
    limit: int = Query(default=10, ge=1, le=100),
    starting_after: str | None = Query(default=None),
    ending_before: str | None = Query(default=None),
    email: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> CustomerListResponse:
    """Return a paginated list of customers sorted by creation date (newest first).

    Supports cursor-based pagination via ``starting_after`` and ``ending_before``.
    """
    request_id = f"req_{uuid.uuid4().hex[:24]}"
    response.headers["Request-Id"] = request_id

    # Generate new/updated records before responding
    generate_customers(session, request_id)

    # Build query
    stmt = select(Customer).order_by(Customer.created.desc())  # type: ignore[union-attr]

    if email:
        stmt = stmt.where(Customer.email == email)

    if starting_after:
        cursor = session.get(Customer, starting_after)
        if cursor:
            stmt = stmt.where(Customer.created < cursor.created)

    if ending_before:
        cursor = session.get(Customer, ending_before)
        if cursor:
            stmt = stmt.where(Customer.created > cursor.created)

    # Fetch one extra to determine has_more
    customers = session.exec(stmt.limit(limit + 1)).all()
    has_more = len(customers) > limit
    customers = customers[:limit]

    data = [serialize_customer(session, c, request_id) for c in customers]

    # Inject duplicate ID DQ issue into response (if tracked for this request)
    for issue in dq_registry.get_issues_by_request(request_id):
        if issue.issue_type == CustomerDQIssueType.DUPLICATE_ID:
            for item in data:
                if item.id == issue.resource_id:
                    data.append(item.model_copy())
                    break

    return CustomerListResponse(
        object="list",
        url="/v1/customers",
        has_more=has_more,
        data=data,
        request_id=request_id,
    )
