from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.interview import router as interview_router

router = APIRouter()
router.include_router(health_router)
router.include_router(interview_router)
