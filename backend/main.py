"""FastAPI application entry point."""

import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import analysis, auth, resume
from app.services import engine


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # load the models in the background so the first request doesn't wait ~1 minute
    if os.getenv("RESUME_ANALYSER_NO_WARMUP") != "1":
        def warm():
            try:
                engine.get_engine()
            except engine.EngineUnavailable as e:
                print(f"[matcher] unavailable: {e}")

        threading.Thread(target=warm, daemon=True).start()
    yield


app = FastAPI(title="Resume Analyser API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(resume.router)
app.include_router(analysis.router)
