"""Aggregate router for API v1."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import breweries, discovery, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(breweries.router)
api_router.include_router(discovery.router)
