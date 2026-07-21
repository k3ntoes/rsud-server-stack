from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.auth.api import router as auth_router
from app.modules.master.api import router as master_router
from app.modules.inspection.api import router as inspection_router
from app.modules.media.api import router as media_router
from app.modules.analytics.api import router as analytics_router

# Ensure all models are registered in SQLAlchemy metadata at startup
from app.modules.background.models import BackgroundJob  # noqa: F401

app = FastAPI(title="RSUD Ajibarang API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(master_router)
app.include_router(inspection_router)
app.include_router(media_router)
app.include_router(analytics_router)
