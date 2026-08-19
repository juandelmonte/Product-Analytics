"""Shared source-API conventions: pagination envelope and cursor helpers.

Matches docs/source_contracts.md:
- Response envelope: {"data": [...], "next_cursor": "opaque-or-null"}
- Stable ordering: (source_updated_at, id) ascending.
"""
from __future__ import annotations

import base64
import json
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


def encode_cursor(order_key: tuple[Any, ...]) -> str:
    """Encode a row's sort key into an opaque cursor string."""
    raw = json.dumps([str(part) for part in order_key])
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(cursor: str) -> tuple[Any, ...]:
    """Decode an opaque cursor back into its sort-key parts."""
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    return tuple(json.loads(raw))


class Page(BaseModel, Generic[T]):
    """The standard source-API response envelope."""

    data: list[T]
    next_cursor: str | None = None
