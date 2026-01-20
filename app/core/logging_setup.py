from __future__ import annotations

import dataclasses
import json
import logging
from datetime import date, datetime
from logging.config import dictConfig
from typing import Any

from pydantic import BaseModel

from app.core.redaction import redact_obj
from app.core.request_context import get_request_id, get_user_id


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        rid = getattr(record, "request_id", None)
        uid = getattr(record, "user_id", None)

        if not rid:
            rid2 = get_request_id()
            if rid2:
                setattr(record, "request_id", rid2)

        if uid is None:
            uid2 = get_user_id()
            if uid2 is not None:
                setattr(record, "user_id", uid2)

        return True


_MAX_JSON_DEPTH = 6
_MAX_STR_LEN = 8192


def _safe_str(s: str) -> str:
    if not isinstance(s, str):
        s = str(s)
    if len(s) > _MAX_STR_LEN:
        return s[:_MAX_STR_LEN] + "...(truncated)"
    return s


def _bytes_to_text(b: bytes) -> str:
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return _safe_str(repr(b))


def _to_jsonable(obj: Any, *, _depth: int = 0) -> Any:
    if _depth > _MAX_JSON_DEPTH:
        return "...(max_depth)"

    if obj is None:
        return None
    if isinstance(obj, (bool, int, float)):
        return obj
    if isinstance(obj, str):
        return _safe_str(obj)
    if isinstance(obj, (bytes, bytearray, memoryview)):
        return _bytes_to_text(bytes(obj))

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    if isinstance(obj, BaseModel):
        try:
            return _to_jsonable(obj.model_dump(), _depth=_depth + 1)
        except (TypeError, ValueError):
            return _safe_str(str(obj))

    if dataclasses.is_dataclass(obj):
        try:
            return _to_jsonable(dataclasses.asdict(obj), _depth=_depth + 1)
        except (TypeError, ValueError):
            return _safe_str(str(obj))

    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            kk = _safe_str(k)
            out[kk] = _to_jsonable(v, _depth=_depth + 1)
        return out

    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(x, _depth=_depth + 1) for x in obj]
    if isinstance(obj, set):
        return [_to_jsonable(x, _depth=_depth + 1) for x in obj]

    if isinstance(obj, BaseException):
        return {"type": obj.__class__.__name__, "message": _safe_str(str(obj))}

    return _safe_str(str(obj))


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }

        rid = getattr(record, "request_id", None) or get_request_id()
        uid = getattr(record, "user_id", None)
        if uid is None:
            uid = get_user_id()

        if rid:
            payload["request_id"] = rid
        if uid is not None:
            payload["user_id"] = uid

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        for k, v in record.__dict__.items():
            if k in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
            }:
                continue
            if k in payload:
                continue
            payload[k] = v

        safe_payload = _to_jsonable(payload)
        safe_payload = redact_obj(safe_payload)

        try:
            return json.dumps(safe_payload, ensure_ascii=False)
        except (TypeError, ValueError, OverflowError):
            fallback = {
                "level": record.levelname.lower(),
                "logger": record.name,
                "message": _safe_str(record.getMessage()),
                "request_id": rid,
                "user_id": uid,
                "format_error": True,
            }
            return json.dumps(redact_obj(_to_jsonable(fallback)), ensure_ascii=False)


def setup_logging(*, level: str = "INFO") -> None:
    level = (level or "INFO").upper()

    cfg = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "context": {"()": "app.core.logging_setup.ContextFilter"},
        },
        "formatters": {
            "json": {"()": "app.core.logging_setup.JsonFormatter"},
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "filters": ["context"],
                "level": level,
            }
        },
        "root": {"handlers": ["stdout"], "level": level},
        "loggers": {
            "uvicorn": {"level": level},
            "uvicorn.error": {"level": level},
            "uvicorn.access": {"level": level, "propagate": False, "handlers": ["stdout"]},
            "access": {"level": level, "propagate": False, "handlers": ["stdout"]},
        },
    }

    dictConfig(cfg)

