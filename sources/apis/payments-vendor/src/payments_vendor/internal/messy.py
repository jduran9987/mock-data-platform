"""Messy data injection — randomized nulls and missing optional nested objects."""

import random
from typing import Any

from payments_vendor.internal.config import config


def maybe_null(value: Any, *, rate: float | None = None) -> Any:
    """Return None instead of the given value at the configured nullable rate.

    Args:
        value: The original value to potentially nullify.
        rate: Override for the null probability. Defaults to config rate.

    Returns:
        The original value or None.
    """
    r = rate if rate is not None else config.nullable_field_null_rate
    if random.random() < r:
        return None
    return value


def maybe_omit_nested(value: Any, *, rate: float | None = None) -> Any:
    """Return None for optional nested objects at the configured omission rate.

    Args:
        value: A sentinel value indicating the nested object should be created.
        rate: Override for the omission probability. Defaults to config rate.

    Returns:
        The original value or None.
    """
    r = rate if rate is not None else config.optional_nested_missing_rate
    if random.random() < r:
        return None
    return value
