"""FastAPI application entrypoint."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select

from app.api.v1 import admin, auth, jobs, recommendations, users
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal, init_db
from app.models.job import Job
from app.services import engine_service

settings = get_settings()

app = FastAPI(title=settings.app_name, version="1.0.0", openapi_url="/api/v1/openapi.json")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.cors_origins] or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        result = await session.exec(select(Job))
        jobs = result.all()
        if jobs:
            engine_service.ingest_jobs(jobs)
