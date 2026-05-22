from fastapi import FastAPI

from app.api import router as api_router
from app.core.config import settings
from app.core.cors import configure_cors
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(title=settings.app_name)
configure_cors(app)
app.include_router(api_router, prefix=settings.api_prefix)
