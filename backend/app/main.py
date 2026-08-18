from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db
from app import models  # noqa: F401 — register tables
from app.routers import columns, dashboard, health, mocks, practice, questions, tracker


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="SmartDevice Interviews Tracker",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(questions.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(tracker.router, prefix="/api")
app.include_router(mocks.router, prefix="/api")
app.include_router(practice.router, prefix="/api")
app.include_router(columns.router, prefix="/api")
