from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from app import install_exception_handlers
from app import router as health_router
from app import install_cors
from app import RequestContextMiddleware
from app import SecurityHeadersMiddleware
from app import TenantContextMiddleware
from app import install_openapi
from app import run_startup_checks
from app import settings
from app import setup_logging
from app import create_engine
from app import create_session_maker
from app import create_es_client
from app import router as admin_router
from app import router as auth_router
from app import sync_authz


@asynccontextmanager
async def lifespan(application: FastAPI):
    setup_logging(level=settings.log_level)

    engine = create_engine()
    application.state.db_engine = engine
    application.state.db_session_maker = create_session_maker(engine)

    redis = Redis.from_url(
        settings.redis_url,
        decode_responses=False,
        max_connections=settings.redis_max_connections,
        socket_connect_timeout=settings.redis_socket_connect_timeout,
        socket_timeout=settings.redis_socket_timeout,
        retry_on_timeout=True,
        health_check_interval=settings.redis_health_check_interval,
    )
    application.state.redis = redis

    application.state.es = create_es_client()

    await run_startup_checks(application)

    if settings.auto_sync_authz:
        async with application.state.db_session_maker() as db:
            await sync_authz(db)

    yield

    try:
        await application.state.es.close()
    except Exception:
        pass

    try:
        aclose = getattr(application.state.redis, "aclose", None)
        if callable(aclose):
            await aclose()
        else:
            await application.state.redis.close()
    except Exception:
        pass

    try:
        await application.state.db_engine.dispose()
    except Exception:
        pass


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(RequestContextMiddleware)
# app.add_middleware(TenantContextMiddleware)

install_exception_handlers(app)

install_cors(
    app,
    allow_origins=settings.cors_origins_list(),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_methods_list(),
    allow_headers=settings.cors_headers_list(),
)

if settings.security_headers_enabled:
    app.add_middleware(SecurityHeadersMiddleware, content_security_policy=settings.csp)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(admin_router)

install_openapi(app)
