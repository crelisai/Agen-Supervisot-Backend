"""FastAPI application entry point.

Run locally:
    uvicorn app.main:app --reload --port 8000

Then open Swagger UI at http://127.0.0.1:8000/docs
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.data.sample_data import seed_sample_data
from app.routes import admin, chat, webhook

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Seed demo data on startup."""
    seed_sample_data()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    openapi_url=settings.OPENAPI_URL,
    lifespan=lifespan,
)

app.include_router(chat.router)
app.include_router(webhook.router)
app.include_router(admin.router)


@app.get("/", tags=["health"], summary="Health check / service info")
def root() -> dict[str, str]:
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": settings.DOCS_URL,
        "status": "ok",
    }
