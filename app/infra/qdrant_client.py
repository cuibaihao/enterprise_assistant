from __future__ import annotations

from qdrant_client import AsyncQdrantClient

from app.core.config import Settings


def create_qdrant_client() -> AsyncQdrantClient:
    url = str(Settings.qdrant_url).strip()
    api_key = (Settings.qdrant_api_key or "").strip() or None
    return AsyncQdrantClient(url=url, api_key=api_key, timeout=float(Settings.qdrant_timeout_seconds))


async def qdrant_ping(client: AsyncQdrantClient) -> bool:
    try:
        await client.get_collections()
        return True
    except Exception:
        return False