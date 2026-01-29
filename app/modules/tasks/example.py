from __future__ import annotations

from app import celery_app


@celery_app.task(name="tasks.ping")
def ping(x: int = 1) -> dict:
    return {"ok": True, "x": int(x)}