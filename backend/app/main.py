import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.api.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="NEXUS Cognitive Supply Chain Twin - API Orchestration Control Plane",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits access from local Vite servers (typically http://localhost:5173)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP middleware to calculate API response durations
@app.middleware("http")
async def api_latency_logging_middleware(request: Request, call_next):
    start_time = time.perf_counter()
    
    response = await call_next(request)
    
    duration_ms = (time.perf_counter() - start_time) * 1000.0
    # Output the structured API logging format requested
    logger.info(f"[API] Response generated for {request.method} {request.url.path} in {duration_ms:.2f} ms")
    
    response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
    return response

# Register API Router
app.include_router(api_router, prefix="/api")

@app.get("/health", tags=["System Utility"])
def health_check():
    """Simple status check endpoint."""
    return {"status": "healthy", "service": settings.PROJECT_NAME, "time": time.time()}
