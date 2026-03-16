"""Data quality issue injection and in-memory registry.

Tracks contract violations (DQ issues) injected into API responses and supports
resolving them by request ID.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CustomerDQIssueType(str, Enum):
    """Data quality issue types for the customers endpoint."""

    NULL_EMAIL_ON_REQUIRED = "null_email_on_required"
    DUPLICATE_ID = "duplicate_id"


@dataclass
class DQIssueRecord:
    """A single recorded data quality issue tied to a request."""

    request_id: str
    resource_type: str
    resource_id: str
    issue_type: str
    resolved: bool = False
    original_value: Any = None


class DQIssueRegistry:
    """In-memory registry of all injected data quality issues."""

    def __init__(self) -> None:
        """Initialize an empty issue registry."""
        self._issues: list[DQIssueRecord] = []

    def record_issue(
        self,
        *,
        request_id: str,
        resource_type: str,
        resource_id: str,
        issue_type: str,
        original_value: Any = None,
    ) -> DQIssueRecord:
        """Record a new data quality issue.

        Args:
            request_id: The request that caused the issue.
            resource_type: The affected resource type (e.g., "customer").
            resource_id: The affected resource's ID.
            issue_type: The type of DQ issue.
            original_value: The correct value before corruption.

        Returns:
            The newly created issue record.
        """
        issue = DQIssueRecord(
            request_id=request_id,
            resource_type=resource_type,
            resource_id=resource_id,
            issue_type=issue_type,
            original_value=original_value,
        )
        self._issues.append(issue)
        return issue

    def get_issues_by_request(self, request_id: str) -> list[DQIssueRecord]:
        """Return all unresolved issues for a given request ID."""
        return [
            i for i in self._issues if i.request_id == request_id and not i.resolved
        ]

    def resolve_issues_for_request(self, request_id: str) -> list[DQIssueRecord]:
        """Mark all issues for a request as resolved and return them."""
        resolved: list[DQIssueRecord] = []
        for issue in self._issues:
            if issue.request_id == request_id and not issue.resolved:
                issue.resolved = True
                resolved.append(issue)
        return resolved

    def get_all_unresolved(self) -> list[DQIssueRecord]:
        """Return all unresolved issues across all requests."""
        return [i for i in self._issues if not i.resolved]


dq_registry = DQIssueRegistry()
