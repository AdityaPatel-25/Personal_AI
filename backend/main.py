import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Enable flexible imports whether running from root or from within backend/
try:
    from backend.chat import router as chat_router
except ImportError:
    from chat import router as chat_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Personal AI - Competitive Programming & DSA Coach",
    description="Backend API with real-time streaming chat powered by Gemini.",
    version="0.1.0",
)

# CORS configuration for frontend clients (e.g., Vite/React on localhost:5173)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route handlers
app.include_router(chat_router)


@app.get("/")
async def root():
    """Health and status endpoint."""
    return {
        "status": "online",
        "service": "Personal AI - DSA Coach API",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "chat": "POST /chat",
        },
    }
