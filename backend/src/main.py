"""TradingDashboard FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import logging
import os

from .config import settings
from .api import router
from .services import (
    kitrading_service,
    coingecko_service,
    alphavantage_service,
    binance_service,
    news_service,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting TradingDashboard...")
    logger.info(f"KITradingModel API: {settings.kitrading_api_url}")

    yield

    # Cleanup
    logger.info("Shutting down TradingDashboard...")
    await kitrading_service.close()
    await coingecko_service.close()
    await alphavantage_service.close()
    await binance_service.close()
    await news_service.close()


# Create FastAPI app
app = FastAPI(
    title="TradingDashboard API",
    description="Web-based Trading Dashboard integrating KITradingModel and external market APIs",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")

# Serve static frontend files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(frontend_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_path, "assets")), name="assets")

    @app.get("/")
    async def serve_frontend():
        """Serve frontend index.html."""
        return FileResponse(os.path.join(frontend_path, "index.html"))

    @app.get("/{path:path}")
    async def serve_frontend_routes(path: str):
        """Serve frontend for all routes (SPA support)."""
        file_path = os.path.join(frontend_path, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_path, "index.html"))
else:
    @app.get("/")
    async def root():
        """Root endpoint when no frontend is built."""
        return {
            "message": "TradingDashboard API",
            "docs": "/api/docs",
            "redoc": "/api/redoc",
            "note": "Build frontend with 'npm run build' in frontend directory",
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
