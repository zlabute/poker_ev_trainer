"""
Poker EV Trainer - FastAPI Backend
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import game

app = FastAPI(
    title="Poker EV Trainer",
    description="API for poker training with EV evaluation",
    version="1.0.0"
)

# Configure CORS - allow localhost for dev, Render URL for production
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Add production frontend URL if set
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(game.router, prefix="/api/game", tags=["game"])


@app.get("/")
async def root():
    return {"message": "Poker EV Trainer API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

