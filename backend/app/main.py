from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from app.api import neighborhoods, map, trends, scores
from app.database import SessionLocal
from app.ingestion.crime import ingest_crime
from app.ingestion.traffic import ingest_traffic
from app.ingestion.permits import ingest_permits
from app.ingestion.code_complaints import ingest_code_complaints
from app.scoring.engine import compute_all_scores
import os
from datetime import datetime, timezone
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


load_dotenv()

def run_ingestion():
    """Runs incremental ingestion for all datasets then recomputes scores."""
    print(f"[{datetime.now(timezone.utc)}] Starting scheduled ingestion...")
    db = SessionLocal()
    try:
        from sqlalchemy import text
        result = db.execute(text("""
            SELECT MAX(occurred_at) FROM crime_incidents
        """)).scalar()
        
        since = result.strftime('%Y-%m-%d') if result else "2025-01-01"
        print(f"Ingesting since: {since}")
        
        ingest_crime(db, since=since, max_pages=10)
        ingest_traffic(db, since=since, max_pages=10)
        ingest_permits(db, since=since, max_pages=10)
        ingest_code_complaints(db, since=since, max_pages=10)
        compute_all_scores(db)
        print(f"[{datetime.now(timezone.utc)}] Scheduled ingestion complete.")
    except Exception as e:
        print(f"Scheduled ingestion failed: {e}")
    finally:
        db.close()

scheduler = BackgroundScheduler()
scheduler.add_job(run_ingestion, "interval", hours=6)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("UrbanLens API starting up...")
    scheduler.start()
    print("Scheduler started - ingestion runs every 6 hours")
    yield
    scheduler.shutdown()
    print("UrbanLens API shutting down...")

app = FastAPI(
    title="UrbanLens API",
    description="Urban data platform for Austin, TX",
    version="1.0.0",
    lifespan=lifespan
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
		   "http://urbanlensatx.com",
		   "https://urbanlensatx.com", 
		   "http://www.urbanlensatx.com",
		   "https://www.urbanlensatx.com", 
		   "http://18.191.233.243"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(neighborhoods.router, prefix="/api/v1")
app.include_router(map.router, prefix="/api/v1")
app.include_router(trends.router, prefix="/api/v1")
app.include_router(scores.router, prefix="/api/v1")

@app.get("/api/v1/health")
async def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "scheduler": "running" if scheduler.running else "stopped"
    }
