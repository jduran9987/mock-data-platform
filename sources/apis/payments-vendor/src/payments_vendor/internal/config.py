"""Simulation configuration for data generation, messy data, and DQ issues."""

from dataclasses import dataclass


@dataclass
class SimulationConfig:
    """Tunable parameters controlling data generation behavior per request."""

    min_new_records: int = 1
    max_new_records: int = 5

    min_updated_records: int = 0
    max_updated_records: int = 3

    nullable_field_null_rate: float = 0.25
    optional_nested_missing_rate: float = 0.10

    dq_issue_rate: float = 0.02

    default_page_size: int = 10
    max_page_size: int = 100


config = SimulationConfig()
