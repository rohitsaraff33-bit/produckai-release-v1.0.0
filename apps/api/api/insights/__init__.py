"""Insights API package.

Combines list, detail, prd, and ai_prompt sub-routers under a single router
that main.py mounts at /themes (URL prefix unchanged for frontend compatibility).
"""

from fastapi import APIRouter

from apps.api.api.insights.ai_prompt import router as ai_prompt_router
from apps.api.api.insights.detail import router as detail_router
from apps.api.api.insights.list import router as list_router
from apps.api.api.insights.prd import router as prd_router

router = APIRouter()

# Order matters: fixed paths before parameterised ones
router.include_router(list_router)
router.include_router(prd_router)
router.include_router(ai_prompt_router)
router.include_router(detail_router)
