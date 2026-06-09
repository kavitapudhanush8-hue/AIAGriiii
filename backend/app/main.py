"""
AI Agriculture Assistant — FastAPI Application Entry Point.

This is the main application file that initializes the FastAPI app,
registers routes, configures CORS, and creates database tables on startup.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database.database import engine, Base
from app.routes import auth, predict, weather, fertilizer, market, chat, admin

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ─── Lifespan (startup / shutdown) ───────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup and seed initial data."""
    logger.info("Creating database tables …")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready.")

    # Seed market price data
    from app.database.database import SessionLocal
    from app.services.market_service import seed_market_data
    db = SessionLocal()
    try:
        count = seed_market_data(db)
        if count > 0:
            logger.info("Seeded %d market price entries.", count)
    finally:
        db.close()

    yield
    logger.info("Shutting down AI Agriculture Assistant.")


# ─── App Instance ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="🌾 AI Agriculture Assistant",
    description=(
        "A smart agriculture platform that helps farmers detect plant diseases, "
        "receive treatment recommendations, get fertilizer suggestions, "
        "weather alerts, and track market prices."
    ),
    version="1.0.0-mvp",
    lifespan=lifespan,
)

# ─── CORS (allow Flutter app to connect) ──────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "https://*.vercel.app",   # Vercel frontend
        "https://aiagriiii-3.onrender.com",  # Render (same origin fallback)
        "*",  # Remove this in strict production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Static file serving for uploaded images ──────────────────────────────────

import os
uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(os.path.abspath(uploads_dir), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=os.path.abspath(uploads_dir)), name="uploads")

# ─── Serve Web Frontend ───────────────────────────────────────────────────────

frontend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend-web")
frontend_abs = os.path.abspath(frontend_dir)
logger.info("Looking for frontend at: %s  (exists=%s)", frontend_abs, os.path.isdir(frontend_abs))
if os.path.isdir(frontend_abs):
    app.mount("/app", StaticFiles(directory=frontend_abs, html=True), name="frontend")
    logger.info("Frontend mounted at /app")

# ─── Register Routers ────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(weather.router)
app.include_router(fertilizer.router)
app.include_router(market.router)
app.include_router(chat.router)
app.include_router(admin.router)


from fastapi.responses import RedirectResponse

# ─── Root & Health Check ──────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def root():
    """Redirect root to the frontend UI."""
    return RedirectResponse(url="/app/")

@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": "AI Agriculture Assistant",
        "version": "1.0.0-mvp",
        "modules": [
            "auth",
            "disease-detection",
            "weather-alerts",
            "fertilizer-recommendation",
            "market-prices",
            "ai-chat",
        ],
    }
