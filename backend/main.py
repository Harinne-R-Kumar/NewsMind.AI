import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.config import settings
from backend.utils.logging import setup_logger
from backend.database.connection import init_db
from backend.api.auth import router as auth_router
from backend.api.preferences import router as preferences_router
from backend.api.schedules import router as schedules_router
from backend.api.feedback import router as feedback_router
from backend.api.reports import router as reports_router
from fastapi.routing import APIRoute

# Initialize logger
logger = setup_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"NewsMind AI Backend starting up in {settings.ENV} mode...")
    logger.info(f"Ollama Endpoint: {settings.OLLAMA_URL}")
    logger.info(f"Default LLM Model: {settings.DEFAULT_LLM_MODEL}")
    
    # Initialize SQLite Database tables
    try:
        await init_db()
    except Exception as e:
        logger.error(f"Critical error on database bootstrap: {e}")
    
    # Start scheduler
    try:
        from backend.scheduler.tasks import start_scheduler
        start_scheduler()
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        
    yield
    
    # Stop scheduler on shutdown
    try:
        from backend.scheduler.tasks import stop_scheduler
        stop_scheduler()
    except Exception:
        pass
    
    logger.info("NewsMind AI Backend shutting down...")


app = FastAPI(
    title="NewsMind AI API",
    description="Backend API for NewsMind AI - Personal News Intelligence Agent",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)
print("Reached before root route")
@app.get("/")
async def root():
    print("Root endpoint called")

    return {
        "message": "Welcome to NewsMind AI Backend",
        "docs": "/docs",
        "health": "/api/health"
    }
print("Reached after root route")

# Register Routers
app.include_router(auth_router)
app.include_router(preferences_router)
app.include_router(schedules_router)
app.include_router(feedback_router)
app.include_router(reports_router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing and logging middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.4f}s"
    )
    return response


# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception caught on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please check logs for details."}
    )


# Health Check Endpoint
@app.get("/api/health")
async def health_check():
    """Application health status."""
    chromadb_status = "unknown"
    try:
        import chromadb
        from backend.config import settings as cfg
        client = chromadb.PersistentClient(path=cfg.CHROMA_DB_PATH)
        chromadb_status = "connected" if client else "error"
    except Exception:
        chromadb_status = "unavailable"

    sources_status = "unknown"
    try:
        from backend.mcp.source_registry import load_sources_config
        cfg = load_sources_config()
        sources_status = f"{len(cfg.get('sources', []))} sources loaded"
    except Exception:
        sources_status = "error"

    return {
        "status": "healthy",
        "env": settings.ENV,
        "debug": settings.DEBUG,
        "database": "sqlite",
        "chromadb": chromadb_status,
        "sources": sources_status,
    }
print("\n========== REGISTERED ROUTES ==========")

for route in app.routes:
    if isinstance(route, APIRoute):
        print(f"{route.path} -> {route.methods}")

print("=======================================\n")



