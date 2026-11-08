import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import AsyncSessionLocal, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure invoice storage directory structure exists on startup
    os.makedirs(os.path.join(settings.STORAGE_DIR, "invoices"), exist_ok=True)
    yield
    # Safely close persistent database engine pool on shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Explicit permitted origin domains (local development + production)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "https://swayambhuinfo.com",
    "https://www.swayambhuinfo.com",
    "https://app.swayambhuinfo.com",
    "https://swayambhu-innovative-solutions.vercel.app",
]

# CORS Middleware with regex coverage for dynamic Vercel preview environments
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https:\/\/([a-zA-Z0-9_-]+\.)?(swayambhuinfo\.com|vercel\.app|onrender\.com)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# Mount API V1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Crash guard: Catches unhandled errors to keep the ASGI worker healthy."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "Internal processing failure. Transaction safely aborted.",
            "detail": str(exc) if settings.ENVIRONMENT == "development" else None,
        },
    )


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


@app.get("/db-check", tags=["System"])
async def db_check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        return {"database": "connected", "result": result.scalar()}