"""
FastAPI Application - Workflow-Based SEO Analysis API

Production-ready API implementing a step-by-step workflow:
1. Overview (SEO Analysis) 
2. Parallel: Insights, Signals, Keywords, Marketing

Features:
- TaskIQ-powered async job queue with Redis
- Full caching support
- Poll/status API for job tracking
- SOLID architecture with dependency injection
- Pydantic v2 models
"""

import asyncio
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated

import taskiq_fastapi
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models.api import (
    AISummaryRequest,
    CacheClearRequest,
    CacheClearResponse,
    ErrorResponse,
    HealthResponse,
    JobStatusEnum,
    WorkflowResultResponse,
    WorkflowStartRequest,
    WorkflowStartResponse,
    WorkflowStatusResponse,
    ScoresResponse,
)
from services.cache_service import (
    CacheService,
    get_cache_service,
    shutdown_cache_service,
)
from services.workflow_service import (
    JobStatus,
    WorkflowService,
    get_workflow_service,
    shutdown_workflow_service,
)
from tasks.broker import broker
from tasks.taskiq_worker import run_workflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
API_VERSION = "2.0.0"

# Initialize TaskIQ with FastAPI
taskiq_fastapi.init(broker, "fast_api:app")


# =============================================================================
# Lifespan Context Manager
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle."""
    # Startup
    logger.info("🚀 Starting up RankOnAI Workflow API...")
    
    # Initialize cache service
    cache = await get_cache_service()
    logger.info(f"📦 Cache service: {'connected' if cache.is_connected else 'disconnected'}")
    
    # Initialize TaskIQ broker (only if not worker process)
    if not broker.is_worker_process:
        await broker.startup()
        logger.info("🔧 TaskIQ broker initialized")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    
    if not broker.is_worker_process:
        await broker.shutdown()
    
    await shutdown_cache_service()
    await shutdown_workflow_service()
    
    logger.info("✅ Shutdown complete")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="RankOnAI Workflow API",
    summary="SEO and AI Indexing Analysis with Step-by-Step Workflow",
    description="""
## Overview

Production-ready API for comprehensive website SEO and AI platform indexing analysis.

### Workflow Steps

1. **Overview** - Full SEO analysis (technical, content, structured data)
2. **Insights** - Multi-LLM AI insights (OpenAI + Grok)
3. **Signals** - AI visibility and performance signals
4. **Keywords** - Strategic keyword extraction and analysis
5. **Marketing** - Content marketing recommendations

### How to Use

1. `POST /workflow/start` - Start analysis, get `job_id`
2. `GET /workflow/{job_id}/status` - Poll for progress
3. `GET /workflow/{job_id}/result` - Get complete results

### Features

- 🔄 **Async Workflow** - Background processing with TaskIQ
- 📊 **Progress Tracking** - Real-time status updates
- 💾 **Caching** - Redis-backed result caching
- 🤖 **Multi-LLM** - OpenAI and Grok insights
    """,
    version=API_VERSION,
    contact={
        "name": "ConusAI Support",
        "url": "https://conusai.com",
        "email": "support@conusai.com",
    },
    license_info={
        "name": "MIT",
        "identifier": "MIT",
    },
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check and status endpoints",
        },
        {
            "name": "workflow",
            "description": "Workflow management - start, status, results",
        },
        {
            "name": "cache",
            "description": "Cache management operations",
        },
    ],
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Dependencies
# =============================================================================


async def get_current_timestamp() -> datetime:
    """Dependency for current UTC timestamp."""
    return datetime.utcnow()


CurrentTime = Annotated[datetime, Depends(get_current_timestamp)]
Cache = Annotated[CacheService, Depends(get_cache_service)]
Workflow = Annotated[WorkflowService, Depends(get_workflow_service)]


# =============================================================================
# Health Endpoints
# =============================================================================


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health Check",
    description="Check API health, Redis connection, and worker status.",
)
async def health_check(
    timestamp: CurrentTime,
    cache: Cache,
) -> HealthResponse:
    """Health check endpoint for monitoring and load balancers."""
    redis_status = "connected" if cache.is_connected else "disconnected"
    worker_status = "available" if broker.is_worker_process else "ready"
    
    return HealthResponse(
        status="healthy",
        timestamp=timestamp,
        version=API_VERSION,
        redis=redis_status,
        worker=worker_status,
    )


@app.get(
    "/",
    include_in_schema=False,
)
async def root() -> dict[str, str]:
    """Root endpoint with API info."""
    return {
        "name": "RankOnAI Workflow API",
        "version": API_VERSION,
        "docs": "/docs",
        "health": "/health",
        "workflow": "/workflow/start",
    }


# =============================================================================
# Workflow Endpoints
# =============================================================================


@app.post(
    "/workflow/start",
    response_model=WorkflowStartResponse,
    tags=["workflow"],
    summary="Start Workflow",
    description="Start a new SEO analysis workflow. Returns a job_id for tracking.",
    responses={
        200: {"description": "Workflow started or cached result available"},
        400: {"description": "Invalid URL", "model": ErrorResponse},
        503: {"description": "Service unavailable", "model": ErrorResponse},
    },
)
async def start_workflow(
    request: WorkflowStartRequest,
    workflow: Workflow,
    cache: Cache,
) -> WorkflowStartResponse:
    """
    Start a new workflow analysis.
    
    If cached results exist for this URL, returns immediately with cached=True.
    Otherwise, creates a background job and returns job_id for polling.
    """
    url = str(request.url)
    
    # Check for cached complete result
    cached_result = await workflow.get_cached_result(url)
    if cached_result:
        # Create a pseudo job for cached result
        job_state = await workflow.create_job(url)
        await workflow.update_job(
            job_state.job_id,
            status=JobStatus.COMPLETED,
            progress=100,
            step_result=("cached", cached_result),
        )
        
        return WorkflowStartResponse(
            job_id=job_state.job_id,
            url=url,
            status=JobStatusEnum.COMPLETED,
            message="Cached result available. Use /workflow/{job_id}/result to retrieve.",
            cached=True,
        )
    
    # Create new job
    job_state = await workflow.create_job(url)
    
    # Enqueue TaskIQ task
    try:
        task = await run_workflow.kiq(job_state.job_id, url)
        logger.info(f"Enqueued workflow job {job_state.job_id} for {url} (task_id: {task.task_id})")
    except Exception as e:
        logger.error(f"Failed to enqueue job: {e}")
        # Run synchronously as fallback
        await _run_workflow_sync(job_state.job_id, url, workflow, cache)
    
    return WorkflowStartResponse(
        job_id=job_state.job_id,
        url=url,
        status=JobStatusEnum.PENDING,
        message="Workflow started. Poll /workflow/{job_id}/status for updates.",
        cached=False,
    )


async def _run_workflow_sync(
    job_id: str, 
    url: str, 
    workflow: WorkflowService,
    cache: CacheService,
) -> None:
    """Run workflow synchronously as fallback when TaskIQ worker is unavailable."""
    from tasks.taskiq_worker import run_workflow as run_workflow_task
    
    # Run in background task
    asyncio.create_task(
        run_workflow_task(job_id, url)
    )


@app.get(
    "/workflow/{job_id}/status",
    response_model=WorkflowStatusResponse,
    tags=["workflow"],
    summary="Get Workflow Status",
    description="Check the status and progress of a workflow job.",
    responses={
        200: {"description": "Job status"},
        404: {"description": "Job not found", "model": ErrorResponse},
    },
)
async def get_workflow_status(
    job_id: str,
    workflow: Workflow,
) -> WorkflowStatusResponse:
    """
    Get current status of a workflow job.
    
    Poll this endpoint to track progress:
    - `pending`: Job queued, not yet started
    - `running`: Job in progress, check `progress` and `current_step`
    - `completed`: Job finished, retrieve results
    - `failed`: Job failed, check `error`
    """
    job_state = await workflow.get_job(job_id)
    
    if not job_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    
    return WorkflowStatusResponse(
        job_id=job_state.job_id,
        status=JobStatusEnum(job_state.status.value),
        progress=job_state.progress,
        current_step=job_state.current_step.value if job_state.current_step else None,
        completed_steps=job_state.completed_steps,
        error=job_state.error,
        created_at=job_state.created_at,
        updated_at=job_state.updated_at,
    )


@app.get(
    "/workflow/{job_id}/result",
    response_model=WorkflowResultResponse,
    tags=["workflow"],
    summary="Get Workflow Result",
    description="Get the complete result of a finished workflow.",
    responses={
        200: {"description": "Complete workflow result"},
        404: {"description": "Job not found", "model": ErrorResponse},
        202: {"description": "Job still in progress"},
    },
)
async def get_workflow_result(
    job_id: str,
    workflow: Workflow,
) -> WorkflowResultResponse:
    """
    Get complete workflow results.
    
    Only available when job status is `completed`.
    Returns all step results: overview, insights, signals, keywords, marketing.
    """
    job_state = await workflow.get_job(job_id)
    
    if not job_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    
    if job_state.status == JobStatus.FAILED:
        return WorkflowResultResponse(
            job_id=job_state.job_id,
            url=job_state.url,
            status=JobStatusEnum.FAILED,
            error=job_state.error,
        )
    
    if job_state.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=f"Job {job_id} is still {job_state.status.value}. Progress: {job_state.progress}%",
        )
    
    # Get result from job state
    result = job_state.result
    
    # Handle cached results
    if "cached" in result and isinstance(result.get("cached"), dict):
        result = result["cached"]
    
    # Extract scores
    scores_data = result.get("overview", {}).get("scores") or result.get("scores", {})
    scores = None
    if scores_data:
        scores = ScoresResponse(
            overall=scores_data.get("overall", 0),
            technical=scores_data.get("technical", 0),
            on_page=scores_data.get("on_page", 0),
            content=scores_data.get("content", 0),
            structured_data=scores_data.get("structured_data", 0),
            ai_readiness=scores_data.get("ai_readiness", 0),
        )
    
    return WorkflowResultResponse(
        job_id=job_state.job_id,
        url=job_state.url,
        status=JobStatusEnum.COMPLETED,
        cached=bool(result.get("cached")),
        timestamp=result.get("timestamp"),
        scores=scores,
        overview=result.get("overview", {}),
        insights=result.get("insights", {}),
        signals=result.get("signals", {}),
        keywords=result.get("keywords", {}),
        marketing=result.get("marketing", {}),
        social=result.get("social", {}),
        ai_summary=result.get("ai_summary", {}),
    )


@app.get(
    "/workflow/by-url",
    response_model=WorkflowResultResponse,
    tags=["workflow"],
    summary="Get Workflow Result by URL",
    description="Get cached workflow result for a URL. URL is normalized (www removed, trailing slash removed).",
    responses={
        200: {"description": "Cached workflow result"},
        404: {"description": "No cached result for URL", "model": ErrorResponse},
    },
)
async def get_workflow_result_by_url(
    url: str,
    workflow: Workflow,
) -> WorkflowResultResponse:
    """
    Get cached workflow results by URL.
    
    URL is normalized before lookup:
    - www. prefix is removed
    - Trailing slash is removed
    - Domain is lowercased
    
    Example: Both https://www.conusai.com/ and https://conusai.com will match.
    """
    from services.cache_service import normalize_url
    
    normalized_url = normalize_url(url)
    cached_result = await workflow.get_cached_result(normalized_url)
    
    if not cached_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No cached result for URL: {url}",
        )
    
    # Extract scores
    scores_data = cached_result.get("overview", {}).get("scores") or cached_result.get("scores", {})
    scores = None
    if scores_data:
        scores = ScoresResponse(
            overall=scores_data.get("overall", 0),
            technical=scores_data.get("technical", 0),
            on_page=scores_data.get("on_page", 0),
            content=scores_data.get("content", 0),
            structured_data=scores_data.get("structured_data", 0),
            ai_readiness=scores_data.get("ai_readiness", 0),
        )
    
    return WorkflowResultResponse(
        job_id=None,
        url=normalized_url,
        status=JobStatusEnum.COMPLETED,
        cached=True,
        timestamp=cached_result.get("timestamp"),
        scores=scores,
        overview=cached_result.get("overview", {}),
        insights=cached_result.get("insights", {}),
        signals=cached_result.get("signals", {}),
        keywords=cached_result.get("keywords", {}),
        marketing=cached_result.get("marketing", {}),
        social=cached_result.get("social", {}),
        ai_summary=cached_result.get("ai_summary", {}),
    )


@app.delete(
    "/workflow/{job_id}",
    tags=["workflow"],
    summary="Cancel Workflow",
    description="Cancel a running workflow job.",
    responses={
        200: {"description": "Job cancelled"},
        404: {"description": "Job not found"},
        400: {"description": "Cannot cancel completed job"},
    },
)
async def cancel_workflow(
    job_id: str,
    workflow: Workflow,
) -> dict:
    """Cancel a running workflow job."""
    cancelled = await workflow.cancel_job(job_id)
    
    if not cancelled:
        job_state = await workflow.get_job(job_id)
        if not job_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job in state: {job_state.status.value}",
        )
    
    return {"cancelled": True, "job_id": job_id}


# =============================================================================
# AI Summary Endpoint (Legacy compatibility)
# =============================================================================


@app.post(
    "/ai-summary",
    tags=["workflow"],
    summary="Generate AI Summary",
    description="Generate AI-powered summary from analysis data. Used by frontend for detailed reports.",
    responses={
        200: {"description": "AI summary generated"},
        400: {"description": "Invalid analysis data"},
        500: {"description": "AI generation failed"},
    },
)
async def generate_ai_summary(
    request: AISummaryRequest,
    cache: Cache,
) -> dict:
    """
    Generate AI-powered summary with improvement recommendations.
    
    This endpoint provides backwards compatibility with the frontend.
    For new integrations, use the workflow API which includes ai_summary.
    """
    import hashlib
    import json
    
    analysis = request.analysis
    if not analysis:
        raise HTTPException(status_code=400, detail="Analysis is required")
    
    # Generate cache key from analysis hash
    analysis_hash = hashlib.md5(
        json.dumps(analysis, sort_keys=True).encode()
    ).hexdigest()[:16]
    cache_key = f"ai_summary:{analysis_hash}"
    
    # Check cache first
    cached = await cache.get(cache_key)
    if cached:
        cached["cached"] = True
        return cached
    
    # Generate AI summary
    from tasks.ai_summary import AISummaryTask
    
    # Extract URL from analysis
    url = analysis.get("url", "unknown")
    
    task = AISummaryTask(url=url, overview_data=analysis)
    result = await task.run()
    
    if not result.get("success"):
        raise HTTPException(
            status_code=500, 
            detail=result.get("error", "AI summary generation failed")
        )
    
    response = {
        "success": True,
        "markdown": result.get("data", {}).get("markdown", ""),
        "structured": result.get("data", {}).get("structured", {}),
        "cached": False,
    }
    
    # Cache for 1 hour
    await cache.set(cache_key, response, ttl=3600)
    
    return response


# =============================================================================
# Generate Suggestions Endpoint
# =============================================================================


@app.post(
    "/generate-suggestions",
    tags=["workflow"],
    summary="Generate AI Suggestions",
    description="Generate AI-powered preferences or questions based on analysis data.",
    responses={
        200: {"description": "Suggestions generated"},
        400: {"description": "Invalid request"},
        500: {"description": "Generation failed"},
    },
)
async def generate_suggestions(
    request: dict,
    cache: Cache,
) -> dict:
    """
    Generate AI-powered preference options or strategic questions.
    
    Args:
        request: Contains 'analysis' (SEO data) and 'type' ('preferences' or 'questions')
    
    Returns:
        Dictionary with success status and generated data
    """
    import hashlib
    import json
    
    from services.openai_service import OpenAIService
    
    analysis = request.get("analysis")
    suggestion_type = request.get("type", "preferences")
    
    if not analysis:
        raise HTTPException(status_code=400, detail="analysis is required")
    
    if suggestion_type not in ("preferences", "questions"):
        raise HTTPException(status_code=400, detail="type must be 'preferences' or 'questions'")
    
    # Generate cache key
    analysis_hash = hashlib.md5(
        json.dumps(analysis, sort_keys=True).encode()
    ).hexdigest()[:16]
    cache_key = f"suggestions:{suggestion_type}:{analysis_hash}"
    
    # Check cache
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # Extract context from analysis
    metadata = analysis.get("metadata", {})
    content = analysis.get("content", {})
    llm_context = analysis.get("llm_context", {})
    scores = analysis.get("scores", {})
    url = analysis.get("url", "")
    
    # Get brand name
    title_data = metadata.get("title", {})
    if isinstance(title_data, dict):
        brand = title_data.get("value") or ""
    else:
        brand = str(title_data) if title_data else ""
    
    if not brand and url:
        try:
            from urllib.parse import urlparse
            brand = urlparse(url).hostname or "the brand"
        except Exception:
            brand = "the brand"
    
    # Get description
    desc_data = metadata.get("description", {})
    if isinstance(desc_data, dict):
        description = desc_data.get("value") or ""
    else:
        description = str(desc_data) if desc_data else ""
    
    # Get keywords
    keywords = llm_context.get("top_keywords", [])[:10]
    if not keywords:
        kw_freq = content.get("keywords_frequency", [])
        keywords = [k.get("keyword", "") for k in kw_freq[:10] if isinstance(k, dict)]
    
    # Build prompts
    if suggestion_type == "preferences":
        system_prompt = "You are an AI SEO expert. Generate user preference options based on SEO analysis. Return valid JSON only."
        user_prompt = f"""Based on this website analysis, generate 4 personalized preference options that users can select to focus their AI optimization efforts.

WEBSITE CONTEXT:
- Brand: {brand}
- Description: {description}
- Top Keywords: {', '.join(keywords)}
- Current Scores: {json.dumps(scores)}

Generate 4 preference options as a JSON array. Each option should be relevant to this specific website's content and goals.

Format:
[
  {{
    "id": "unique_snake_case_id",
    "label": "Short Label (2-3 words)",
    "detail": "One sentence explaining how this preference helps AI recommend this brand."
  }}
]

Return ONLY the JSON array, no markdown or explanation."""
    else:
        system_prompt = "You are an AI brand strategist. Generate questions users should answer to improve AI discoverability. Return valid JSON only."
        user_prompt = f"""Based on this website analysis, generate 5 strategic questions that will help improve how AI assistants recommend this brand.

WEBSITE CONTEXT:
- Brand: {brand}
- Description: {description}
- Top Keywords: {', '.join(keywords)}

Generate questions as a JSON array of strings. Questions should:
1. Be specific to this brand/website
2. Help craft FAQs and AI-friendly content
3. Focus on what makes this brand recommendable

Format:
["Question 1?", "Question 2?", "Question 3?", "Question 4?", "Question 5?"]

Return ONLY the JSON array, no markdown or explanation."""
    
    # Call OpenAI
    openai = OpenAIService()
    
    if not openai.is_configured:
        raise HTTPException(status_code=500, detail="OpenAI not configured")
    
    try:
        # complete_json returns parsed JSON directly (list or dict)
        data = await openai.complete_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
        )
        
        # Validate we got the expected format
        if not isinstance(data, list):
            logger.warning(f"Expected list from OpenAI, got {type(data)}")
            data = []
        
        response = {
            "success": True,
            "data": data,
            "type": suggestion_type,
        }
        
        # Cache for 1 hour
        await cache.set(cache_key, response, ttl=3600)
        
        return response
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI response: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse AI response")
    except Exception as e:
        logger.error(f"Suggestion generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Generate Files Endpoint (robots.txt & llms.txt)
# =============================================================================


class GenerateFilesRequest(BaseModel):
    """Request body for generate-files endpoint."""
    report: dict


class GenerateFilesResponse(BaseModel):
    """Response for generate-files endpoint."""
    robots_txt: str
    llms_txt: str
    ai_powered: bool


@app.post(
    "/generate-files",
    response_model=GenerateFilesResponse,
    tags=["generation"],
    summary="Generate robots.txt and llms.txt",
    description="Generate AI-optimized robots.txt and llms.txt files based on SEO report data.",
    responses={
        200: {"description": "Files generated successfully"},
        500: {"description": "Generation failed"},
    },
)
async def generate_files(
    request: GenerateFilesRequest,
) -> GenerateFilesResponse:
    """
    Generate robots.txt and llms.txt files using AI analysis.
    
    Args:
        request: Request containing the SEO report data
        
    Returns:
        Generated file contents
    """
    report = request.report
    
    if not report:
        raise HTTPException(status_code=400, detail="Report data is required")
    
    try:
        # Import generators from seo_ai_generator
        from seo_ai_generator import RobotsTxtGenerator, LlmsTxtGenerator, OpenAIClient
        
        # Create OpenAI client
        openai_client = OpenAIClient()
        ai_powered = openai_client.is_configured()
        
        # Generate robots.txt
        robots_gen = RobotsTxtGenerator(report, openai_client)
        robots_content = await robots_gen.generate()
        
        # Generate llms.txt
        llms_gen = LlmsTxtGenerator(report, openai_client)
        llms_content = await llms_gen.generate()
        
        return GenerateFilesResponse(
            robots_txt=robots_content,
            llms_txt=llms_content,
            ai_powered=ai_powered,
        )
        
    except ImportError as e:
        logger.error(f"Failed to import seo_ai_generator: {e}")
        raise HTTPException(status_code=500, detail="File generator module not available")
    except Exception as e:
        logger.error(f"File generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Cache Endpoints
# =============================================================================


@app.delete(
    "/cache",
    response_model=CacheClearResponse,
    tags=["cache"],
    summary="Clear Cache",
    description="Clear cached results for a specific URL.",
)
async def clear_cache(
    request: CacheClearRequest,
    cache: Cache,
    workflow: Workflow,
) -> CacheClearResponse:
    """Clear all cached results for a URL."""
    url = str(request.url)
    
    # Clear workflow result cache
    result_key = cache.generate_key("workflow:result", url)
    await cache.delete(result_key)
    
    # Clear step caches
    steps = ["overview", "insights", "signals", "keywords", "marketing"]
    for step in steps:
        step_key = cache.generate_key(f"workflow:step:{step}", url)
        await cache.delete(step_key)
    
    return CacheClearResponse(
        cleared=True,
        url=url,
        message=f"Cache cleared for {url}",
    )


# =============================================================================
# Development Server
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "fast_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
