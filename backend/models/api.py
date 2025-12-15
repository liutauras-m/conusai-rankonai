"""
API Models - Pydantic v2 Request/Response Models

Defines all request and response models for the workflow API.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


# =============================================================================
# Enums
# =============================================================================


class JobStatusEnum(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStepEnum(str, Enum):
    """Workflow step identifiers."""
    OVERVIEW = "overview"
    INSIGHTS = "insights"
    SIGNALS = "signals"
    KEYWORDS = "keywords"
    MARKETING = "marketing"


# =============================================================================
# Request Models
# =============================================================================


class WorkflowStartRequest(BaseModel):
    """Request to start a new workflow analysis."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://example.com",
            }
        }
    )
    
    url: HttpUrl = Field(
        description="The URL to analyze",
        examples=["https://example.com", "https://conusai.com"],
    )


class CacheClearRequest(BaseModel):
    """Request to clear cache for a URL."""
    
    url: HttpUrl = Field(description="The URL to clear cache for")


class AISummaryRequest(BaseModel):
    """Request for AI summary generation."""
    
    analysis: dict[str, Any] = Field(description="Analysis data to summarize")


# =============================================================================
# Response Models - Health
# =============================================================================


class HealthResponse(BaseModel):
    """Health check response."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "timestamp": "2025-12-15T10:30:00Z",
                "version": "2.0.0",
                "redis": "connected",
                "worker": "running",
            }
        }
    )
    
    status: str = Field(description="Service health status")
    timestamp: datetime = Field(description="Response timestamp")
    version: str = Field(description="API version")
    redis: str = Field(description="Redis connection status")
    worker: str = Field(default="unknown", description="Worker status")


# =============================================================================
# Response Models - Workflow
# =============================================================================


class WorkflowStartResponse(BaseModel):
    """Response when starting a new workflow."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "url": "https://example.com",
                "status": "pending",
                "message": "Workflow started. Poll /workflow/{job_id}/status for updates.",
            }
        }
    )
    
    job_id: str = Field(description="Unique job identifier")
    url: str = Field(description="URL being analyzed")
    status: JobStatusEnum = Field(description="Initial job status")
    message: str = Field(description="Status message")
    cached: bool = Field(default=False, description="Whether using cached result")


class WorkflowStatusResponse(BaseModel):
    """Response for workflow status check."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "running",
                "progress": 40,
                "current_step": "insights",
                "completed_steps": ["overview"],
                "created_at": "2025-12-15T10:30:00Z",
                "updated_at": "2025-12-15T10:31:00Z",
            }
        }
    )
    
    job_id: str = Field(description="Unique job identifier")
    status: JobStatusEnum = Field(description="Current job status")
    progress: int = Field(ge=0, le=100, description="Progress percentage")
    current_step: Optional[str] = Field(default=None, description="Currently executing step")
    completed_steps: list[str] = Field(default_factory=list, description="Completed step names")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    created_at: str = Field(description="Job creation timestamp")
    updated_at: str = Field(description="Last update timestamp")


class ScoresResponse(BaseModel):
    """SEO scores breakdown."""
    
    overall: int = Field(ge=0, le=100, description="Overall SEO score")
    technical: int = Field(ge=0, le=100, description="Technical SEO score")
    on_page: int = Field(ge=0, le=100, description="On-page SEO score")
    content: int = Field(ge=0, le=100, description="Content quality score")
    structured_data: int = Field(ge=0, le=100, description="Structured data score")
    ai_readiness: int = Field(ge=0, le=100, description="AI readiness score")


class WorkflowResultResponse(BaseModel):
    """Complete workflow result response."""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "url": "https://example.com",
                "status": "completed",
                "cached": False,
                "scores": {
                    "overall": 75,
                    "technical": 80,
                    "on_page": 70,
                    "content": 75,
                    "structured_data": 65,
                    "ai_readiness": 72,
                },
                "overview": {},
                "insights": {},
                "signals": {},
                "keywords": {},
                "marketing": {},
            }
        }
    )
    
    job_id: str = Field(description="Unique job identifier")
    url: str = Field(description="Analyzed URL")
    status: JobStatusEnum = Field(description="Final job status")
    cached: bool = Field(default=False, description="Whether result was from cache")
    timestamp: Optional[str] = Field(default=None, description="Analysis timestamp")
    scores: Optional[ScoresResponse] = Field(default=None, description="SEO scores")
    
    # Step results
    overview: dict[str, Any] = Field(default_factory=dict, description="SEO analysis overview")
    insights: dict[str, Any] = Field(default_factory=dict, description="AI insights")
    signals: dict[str, Any] = Field(default_factory=dict, description="Visibility signals")
    keywords: dict[str, Any] = Field(default_factory=dict, description="Keyword analysis")
    marketing: dict[str, Any] = Field(default_factory=dict, description="Marketing recommendations")
    ai_summary: dict[str, Any] = Field(default_factory=dict, description="AI-generated summary report")
    
    # Error info
    error: Optional[str] = Field(default=None, description="Error message if failed")


# =============================================================================
# Response Models - Errors
# =============================================================================


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    detail: str = Field(description="Error message")
    code: str = Field(default="error", description="Error code")
    job_id: Optional[str] = Field(default=None, description="Related job ID if applicable")


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    
    detail: list[dict[str, Any]] = Field(description="Validation error details")


# =============================================================================
# Response Models - Cache
# =============================================================================


class CacheClearResponse(BaseModel):
    """Response for cache clear operation."""
    
    cleared: bool = Field(description="Whether cache was cleared")
    url: str = Field(description="URL that was cleared")
    message: str = Field(description="Status message")
