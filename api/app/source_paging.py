"""Generic source-API query helpers shared by all routers.

Implements the conventions from docs/source_contracts.md:
- pagination via limit + opaque cursor over the (source_updated_at, id) sort key
- updated_since incremental filtering on source_updated_at
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import Select

from .pagination import decode_cursor, encode_cursor


def parse_dt(value: str | None, name: str) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"invalid {name}: {value}")


def apply_updated_since(stmt: Select, column: Any, updated_since: str | None) -> Select:
    dt = parse_dt(updated_since, "updated_since")
    if dt is not None:
        stmt = stmt.where(column >= dt)
    return stmt


def apply_cursor(stmt: Select, order_cols: tuple[Any, Any], cursor: str | None) -> Select:
    """Applies keyset pagination over (order_cols[0], order_cols[1]) ascending.

    order_cols = (source_updated_at_col, id_col). The cursor encodes the two
    sort-key values of the last returned row; the second value is kept as a
    string (stable source ids are strings) and the first is a datetime.
    """
    if not cursor:
        return stmt
    try:
        parts = decode_cursor(cursor)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid cursor")
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="invalid cursor")

    col_ts, col_id = order_cols
    ts_str = parts[0]
    id_str = parts[1]
    # First sort key is a datetime encoded as ISO; parse it for comparison.
    ts_val = datetime.fromisoformat(ts_str)
    return stmt.where(
        (col_ts > ts_val) | ((col_ts == ts_val) & (col_id > id_str))
    )


def finish_page(rows: list, limit: int, ts_col_name: str, id_col_name: str) -> tuple[list, str | None]:
    """Trim the extra probe row and build the next cursor."""
    next_cursor = None
    if len(rows) > limit:
        rows = rows[:limit]
        last = rows[-1]
        next_cursor = encode_cursor(
            (getattr(last, ts_col_name).isoformat(), getattr(last, id_col_name))
        )
    return rows, next_cursor
