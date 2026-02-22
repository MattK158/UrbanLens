from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("UrbanLens API starting up...")
    yield
    print("UrbanLens API shutting down...")

app = FastAPI(
    title="UrbanLens API",
    description="Urban data platform for Austin, TX",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
async def health():
    return {
        "status": "ok",
        "version": "1.0.0"
    }