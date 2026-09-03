"""Pagination-aware source API client.

Walks the `{data, next_cursor}` envelope of the FastAPI source APIs.
"""
from __future__ import annotations

import requests

from .common import API_BASE_URL


def fetch_pages(path: str, params: dict | None = None) -> list[dict]:
    """Fetch all pages of a source endpoint and return the concatenated rows."""
    params = dict(params or {})
    rows: list[dict] = []
    cursor: str | None = None
    while True:
        if cursor:
            params["cursor"] = cursor
        resp = requests.get(f"{API_BASE_URL}{path}", params=params, timeout=120)
        resp.raise_for_status()
        body = resp.json()
        rows.extend(body.get("data", []))
        cursor = body.get("next_cursor")
        if not cursor:
            break
    return rows
