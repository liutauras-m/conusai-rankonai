"""
Data models package for SEO Analyzer.

Contains Pydantic-style dataclasses for structured data.
"""

from .seo import (
    Issue,
    Recommendation,
    MetaTagAnalysis,
    HeadingAnalysis,
    ImageAnalysis,
    LinkAnalysis,
)

from .api import (
    JobStatusEnum,
    WorkflowStepEnum,
    WorkflowStartRequest,
    WorkflowStartResponse,
    WorkflowStatusResponse,
    WorkflowResultResponse,
    ScoresResponse,
    HealthResponse,
    ErrorResponse,
    CacheClearRequest,
    CacheClearResponse,
)

__all__ = [
    "Issue",
    "Recommendation",
    "MetaTagAnalysis",
    "HeadingAnalysis",
    "ImageAnalysis",
    "LinkAnalysis",
]
