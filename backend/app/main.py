from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.auth.api import router as auth_router
from app.modules.master.api import router as master_router
from app.modules.inspection.api import router as inspection_router
from app.modules.media.api import router as media_router

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
