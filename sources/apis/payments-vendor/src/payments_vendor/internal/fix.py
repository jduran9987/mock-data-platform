"""Internal endpoint for resolving data quality issues by request ID."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from payments_vendor.db.session import get_session
from payments_vendor.internal.quality_issues import CustomerDQIssueType, dq_registry

router = APIRouter(prefix="/internal", tags=["internal"])


class FixRequest(BaseModel):
    """Request body for the fix-data-quality-issues endpoint."""

    request_id: str


class FixResponse(BaseModel):
    """Response body showing how many issues were resolved."""

    request_id: str
    issues_resolved: int
    details: list[dict[str, Any]]


@router.post("/fix-data-quality-issues", response_model=FixResponse)
def fix_data_quality_issues(body: FixRequest) -> FixResponse:
    """Resolve all data quality issues tied to a specific request ID.

    Corrects affected records in the database so subsequent reads return
    clean data.
    """
    from payments_vendor.models.customer import Customer

    resolved = dq_registry.resolve_issues_for_request(body.request_id)

    details: list[dict[str, Any]] = []
    for issue in resolved:
        detail: dict[str, Any] = {
            "resource_type": issue.resource_type,
            "resource_id": issue.resource_id,
            "issue_type": issue.issue_type,
            "resolved": True,
        }

        if issue.issue_type == CustomerDQIssueType.NULL_EMAIL_ON_REQUIRED:
            session = next(get_session())
            customer = session.get(Customer, issue.resource_id)
            if customer and issue.original_value is not None:
                customer.email = issue.original_value
                session.add(customer)
                session.commit()

        details.append(detail)

    return FixResponse(
        request_id=body.request_id,
        issues_resolved=len(resolved),
        details=details,
    )
