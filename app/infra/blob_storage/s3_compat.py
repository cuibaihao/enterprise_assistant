
from __future__ import annotations

from dataclasses import dataclass

from app.infra.blob_storage.interface import StorageBackend, StoredObject

@dataclass(frozen=True)
class S3CompatStorage(StorageBackend):
    endpoint_url: str
    bucket: str
    access_key_id: str
    secret_access_key: str
    region: str | None = None

    async def put_bytes(self, *, key: str, data: bytes, content_type: str | None = None) -> StoredObject:
        raise NotImplementedError("s3_storage_not_configured")

    async def get_bytes(self, *, key: str) -> bytes:
        raise NotImplementedError("s3_storage_not_configured")

    async def exists(self, *, key: str) -> bool:
        raise NotImplementedError("s3_storage_not_configured")

    async def delete(self, *, key: str) -> None:
        raise NotImplementedError("s3_storage_not_configured")
