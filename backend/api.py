"""
FastAPI Backend for SEO Analyzer
Production-ready API with caching, rate limiting, and concurrency control.
"""

import asyncio
import hashlib
import json
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import redis.asyncio as redis

from seo_analyzer import SEOAnalyzer

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT_ANALYSES", "5"))
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default

# Concurrency semaphore
analysis_semaphore = asyncio.Semaphore(MAX_CONCURRENT)

# FastAPI app
app = FastAPI(
    title="SEO Analyzer API",
    description="Production API for SEO and AI indexing analysis",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection
redis_client: Optional[redis.Redis] = None


class AnalyzeRequest(BaseModel):
    url: HttpUrl


class AnalyzeResponse(BaseModel):
    url: str
    timestamp: str
    cached: bool = False
    data: dict


@app.on_event("startup")
async def startup():
    global redis_client
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
        print(f"✓ Connected to Redis at {REDIS_URL}")
    except Exception as e:
        print(f"⚠ Redis connection failed: {e}. Running without cache.")
        redis_client = None


@app.on_event("shutdown")
async def shutdown():
    if redis_client:
        await redis_client.close()


def get_cache_key(url: str) -> str:
    """Generate a cache key for the URL."""
    return f"seo:analysis:{hashlib.sha256(url.encode()).hexdigest()[:16]}"


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    redis_status = "connected" if redis_client else "disconnected"
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "redis": redis_status,
        "concurrent_limit": MAX_CONCURRENT,
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_url(request: AnalyzeRequest, req: Request):
    """
    Analyze a URL for SEO and AI indexing factors.
    
    - Results are cached for 1 hour
    - Maximum concurrent analyses limited to prevent overload
    - Rate limiting handled by nginx
    """
    url = str(request.url)
    cache_key = get_cache_key(url)
    
    # Check cache first
    if redis_client:
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                data = json.loads(cached)
                return AnalyzeResponse(
                    url=url,
                    timestamp=data.get("timestamp", datetime.now().isoformat()),
                    cached=True,
                    data=data,
                )
        except Exception as e:
            print(f"Cache read error: {e}")
    
    # Acquire semaphore for concurrency control
    try:
        async with asyncio.timeout(5):  # Wait max 5 seconds for a slot
            await analysis_semaphore.acquire()
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=503,
            detail="Server is busy. Please try again in a few moments.",
        )
    
    try:
        # Run the analysis
        analyzer = SEOAnalyzer(url, verbose=False)
        result = await analyzer.analyze()
        
        # Cache the result
        if redis_client:
            try:
                await redis_client.setex(
                    cache_key,
                    CACHE_TTL,
                    json.dumps(result, ensure_ascii=False),
                )
            except Exception as e:
                print(f"Cache write error: {e}")
        
        return AnalyzeResponse(
            url=url,
            timestamp=result.get("timestamp", datetime.now().isoformat()),
            cached=False,
            data=result,
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        analysis_semaphore.release()


@app.delete("/cache/{url:path}")
async def clear_cache(url: str):
    """Clear cached results for a specific URL."""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Cache not available")
    
    cache_key = get_cache_key(url)
    deleted = await redis_client.delete(cache_key)
    
    return {"cleared": bool(deleted), "url": url}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
