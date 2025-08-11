from fastapi import APIRouter

from .announcement import router

announcement_router = APIRouter()
announcement_router.include_router(router, tags=["公告管理"])
