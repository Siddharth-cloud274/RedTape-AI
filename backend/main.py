from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.router import api_router
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure SQLite tables and indexes exist on startup
    init_db()
    yield


app = FastAPI(
    title="RedTape AI Backend",
    description="Agentic assistant for Indian government bureaucracy",
    version="0.1.0",
    lifespan=lifespan,
)

# Explicit CORS configuration for frontend (supporting IPv4, IPv6, and LAN loopback)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|\[::1\]|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes with /api prefix
app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    return {"message": "RedTape AI API running", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
