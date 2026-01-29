from __future__ import annotations

from typing import Any

from fastapi import Response

from app import HDR_CACHE_CONTROL


def no_store(response: Response) -> None:
    response.headers[HDR_CACHE_CONTROL] = "no-store"


def ok_no_store(response: Response, data: Any, *, meta: Any | None = None) -> dict:
    from app import ok

    no_store(response)
    return ok(data, meta=meta)
