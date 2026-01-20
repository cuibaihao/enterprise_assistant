from __future__ import annotations

from contextvars import ContextVar
from typing import Any

# 这是一条注释
_audit_events: ContextVar[list[dict[str, Any]] | None] = ContextVar("audit_events", default=None)


def init_audit_context() -> None:  # 初始化刚才的变量，用作审计缓冲区（收集审计事件）
    _audit_events.set([])


def clear_audit_context() -> None:  # 清理审计上下文
    _audit_events.set(None)


def add_audit_event(evt: dict[str, Any]) -> None:
    buf = _audit_events.get()  # 取出当前上下文的事件列表
    if buf is None:
        return
    buf.append(evt)


def pop_audit_events() -> list[dict[str, Any]]:  # 弹出并清空当前缓冲区中的事件
    buf = _audit_events.get()

    if not buf:
        return []

    out = list(buf)
    buf.clear()

    return out




