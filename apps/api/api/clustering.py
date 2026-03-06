"""Clustering endpoints."""

import json
from datetime import datetime
from typing import Optional

import redis as redis_lib
from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from apps.api.config import get_settings
from apps.api.database import get_db

router = APIRouter()

_REDIS_STATUS_KEY = "clustering:status"
_REDIS_STATUS_TTL = 86400  # 24 hours


def _get_redis() -> redis_lib.Redis:
    """Return a Redis client using the configured URL."""
    settings = get_settings()
    return redis_lib.from_url(settings.redis_url, decode_responses=True)


class ClusterResponse(BaseModel):
    """Cluster task response."""

    status: str
    message: str
    task_id: Optional[str] = None


class ClusterStatusResponse(BaseModel):
    """Cluster status response."""

    is_running: bool
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    themes_created: Optional[int] = None
    insights_created: Optional[int] = None
    error: Optional[str] = None


def get_clustering_status() -> dict:
    """Get current clustering status from Redis."""
    try:
        r = _get_redis()
        raw = r.get(_REDIS_STATUS_KEY)
        if raw:
            return json.loads(raw)
    except (redis_lib.RedisError, OSError, json.JSONDecodeError):
        # Fall back to idle if Redis is unavailable or data is corrupt
        pass
    return {"is_running": False, "status": "idle"}


def set_clustering_status(status_data: dict) -> None:
    """Persist clustering status to Redis with a 24-hour TTL."""
    try:
        r = _get_redis()
        r.set(_REDIS_STATUS_KEY, json.dumps(status_data), ex=_REDIS_STATUS_TTL)
    except (redis_lib.RedisError, OSError):
        # Best-effort write — status loss is acceptable if Redis is temporarily down
        pass


def run_clustering_task(db_url: str):
    """Background task to run clustering."""
    try:
        # Mark as running
        set_clustering_status({
            "is_running": True,
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
        })

        # Run clustering
        from apps.api.scripts.run_clustering import run_clustering_pipeline

        result = run_clustering_pipeline()

        # Mark as completed
        set_clustering_status({
            "is_running": False,
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "themes_created": result.get("themes_created", 0),
            "insights_created": result.get("insights_created", 0),
        })

    except Exception as e:
        # Mark as failed
        set_clustering_status({
            "is_running": False,
            "status": "failed",
            "completed_at": datetime.utcnow().isoformat(),
            "error": str(e),
        })
        raise


@router.post("/run", response_model=ClusterResponse)
async def trigger_clustering(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Trigger clustering pipeline.

    This runs as a background task and clusters all feedback into themes.

    Returns:
        Status of the clustering task
    """
    # Check if already running
    status = get_clustering_status()
    if status.get("is_running"):
        return ClusterResponse(
            status="already_running",
            message="Clustering task is already running",
        )

    # Add to background tasks
    background_tasks.add_task(run_clustering_task, get_settings().database_url)

    return ClusterResponse(
        status="accepted",
        message="Clustering task started in background",
    )


@router.get("/status", response_model=ClusterStatusResponse)
async def get_status():
    """
    Get current clustering pipeline status.

    Returns:
        Current status of the clustering pipeline
    """
    status = get_clustering_status()
    return ClusterStatusResponse(**status)
