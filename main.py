from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.routes.chat_routes import router as chat_router
from app.routes.ingestion_routes import router as ingestion_router
from app.routes.health_routes import router as health_router
from app.stores.sql_store import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup and shutdown tasks."""
    init_db()
    yield
    # teardown hooks go here


app = FastAPI(
    title="Multi-Source Document Retrieval API",
    version="0.1.0",
    description="Per-client document retrieval over structured (SQL) and semantic (vector) stores.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(PermissionError)
async def permission_error_handler(request: Request, exc: PermissionError) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc)})


app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(ingestion_router, prefix="/ingest", tags=["Ingestion"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
