"""Shared helpers for Pyronites table repositories."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.core.pyronites_client import get_pyronites_client

logger = logging.getLogger(__name__)


def _as_list(result: Any) -> List[Dict[str, Any]]:
    if result is None:
        return []
    if isinstance(result, list):
        return [r for r in result if isinstance(r, dict)]
    if isinstance(result, dict):
        # Common SDK shapes: {"data": [...]}, {"rows": [...]}, single row
        for key in ("data", "rows", "items", "results"):
            if key in result and isinstance(result[key], list):
                return [r for r in result[key] if isinstance(r, dict)]
        return [result]
    return []


def _as_one(result: Any) -> Optional[Dict[str, Any]]:
    rows = _as_list(result)
    return rows[0] if rows else None


def table(name: str) -> Any:
    return get_pyronites_client().table(name)


def select_eq(table_name: str, column: str, value: Any) -> List[Dict[str, Any]]:
    try:
        q = table(table_name).select()
        if hasattr(q, "eq"):
            q = q.eq(column, value)
        result = q.execute() if hasattr(q, "execute") else q
        return _as_list(result)
    except Exception as e:
        logger.error("select_eq %s.%s failed: %s", table_name, column, e)
        raise


def select_all(table_name: str) -> List[Dict[str, Any]]:
    try:
        q = table(table_name).select()
        result = q.execute() if hasattr(q, "execute") else q
        return _as_list(result)
    except Exception as e:
        logger.error("select_all %s failed: %s", table_name, e)
        raise


def get_by_id(table_name: str, row_id: str) -> Optional[Dict[str, Any]]:
    try:
        t = table(table_name)
        if hasattr(t, "get"):
            result = t.get(row_id)
            return _as_one(result)
        rows = select_eq(table_name, "id", row_id)
        return rows[0] if rows else None
    except Exception as e:
        logger.error("get_by_id %s/%s failed: %s", table_name, row_id, e)
        raise


def insert_row(table_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        t = table(table_name)
        result = t.insert(payload)
        if hasattr(result, "execute"):
            result = result.execute()
        row = _as_one(result)
        if row:
            return row
        # Some clients return the payload + id only
        if isinstance(result, dict):
            return result
        return payload
    except Exception as e:
        logger.error("insert %s failed: %s", table_name, e)
        raise


def update_eq(table_name: str, column: str, value: Any, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        t = table(table_name)
        q = t.update(payload)
        if hasattr(q, "eq"):
            q = q.eq(column, value)
        result = q.execute() if hasattr(q, "execute") else q
        return _as_one(result) or payload
    except Exception as e:
        logger.error("update %s failed: %s", table_name, e)
        raise


def delete_eq(table_name: str, column: str, value: Any) -> bool:
    try:
        t = table(table_name)
        q = t.delete()
        if hasattr(q, "eq"):
            q = q.eq(column, value)
        if hasattr(q, "execute"):
            q.execute()
        return True
    except Exception as e:
        logger.error("delete %s failed: %s", table_name, e)
        raise
