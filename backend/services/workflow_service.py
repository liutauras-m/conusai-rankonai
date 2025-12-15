"""
Workflow Service - Orchestrates Multi-Step Analysis Pipeline

Manages job lifecycle, status tracking, and step orchestration.
Uses Redis for job state persistence with ARQ integration.
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from services.cache_service import CacheService

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStep(str, Enum):
    """Workflow step identifiers."""
    OVERVIEW = "overview"
    INSIGHTS = "insights"
    SIGNALS = "signals"
    KEYWORDS = "keywords"
    MARKETING = "marketing"


class JobState:
    """
    Immutable job state representation.
    
    Stored in Redis as JSON for persistence.
    """
    
    def __init__(
        self,
        job_id: str,
        url: str,
        status: JobStatus = JobStatus.PENDING,
        current_step: Optional[WorkflowStep] = None,
        completed_steps: list[str] | None = None,
        progress: int = 0,
        result: dict | None = None,
        error: Optional[str] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        self.job_id = job_id
        self.url = url
        self.status = status
        self.current_step = current_step
        self.completed_steps = completed_steps or []
        self.progress = progress
        self.result = result or {}
        self.error = error
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.updated_at = updated_at or datetime.utcnow().isoformat()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "url": self.url,
            "status": self.status.value if isinstance(self.status, JobStatus) else self.status,
            "current_step": self.current_step.value if isinstance(self.current_step, WorkflowStep) else self.current_step,
            "completed_steps": self.completed_steps,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "JobState":
        """Create from dictionary."""
        return cls(
            job_id=data["job_id"],
            url=data["url"],
            status=JobStatus(data["status"]) if data.get("status") else JobStatus.PENDING,
            current_step=WorkflowStep(data["current_step"]) if data.get("current_step") else None,
            completed_steps=data.get("completed_steps", []),
            progress=data.get("progress", 0),
            result=data.get("result", {}),
            error=data.get("error"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
    
    def with_update(self, **kwargs) -> "JobState":
        """Create new state with updates (immutable pattern)."""
        data = self.to_dict()
        data.update(kwargs)
        data["updated_at"] = datetime.utcnow().isoformat()
        return JobState.from_dict(data)


class WorkflowService:
    """
    Workflow orchestration service.
    
    Manages:
    - Job creation and lifecycle
    - Step execution and ordering
    - Status tracking and persistence
    - Result aggregation
    
    Follows Single Responsibility - only handles workflow orchestration.
    """
    
    # Key prefixes for Redis storage
    JOB_KEY_PREFIX = "workflow:job"
    JOB_TTL = 86400  # 24 hours
    RESULT_TTL = 3600  # 1 hour for cached results
    
    # Workflow step configuration
    PARALLEL_STEPS = [
        WorkflowStep.INSIGHTS,
        WorkflowStep.SIGNALS,
        WorkflowStep.KEYWORDS,
        WorkflowStep.MARKETING,
    ]
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
    
    async def create_job(self, url: str) -> JobState:
        """
        Create a new workflow job.
        
        Args:
            url: The URL to analyze
        
        Returns:
            New JobState with unique ID
        """
        job_id = str(uuid.uuid4())
        state = JobState(
            job_id=job_id,
            url=url,
            status=JobStatus.PENDING,
            progress=0,
        )
        
        await self._save_state(state)
        logger.info(f"Created job {job_id} for URL: {url}")
        
        return state
    
    async def get_job(self, job_id: str) -> Optional[JobState]:
        """
        Get job state by ID.
        
        Args:
            job_id: The job identifier
        
        Returns:
            JobState if found, None otherwise
        """
        key = f"{self.JOB_KEY_PREFIX}:{job_id}"
        data = await self.cache.get(key)
        
        if data:
            return JobState.from_dict(data)
        return None
    
    async def update_job(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        current_step: Optional[WorkflowStep] = None,
        progress: Optional[int] = None,
        step_result: Optional[tuple[str, dict]] = None,
        error: Optional[str] = None,
    ) -> Optional[JobState]:
        """
        Update job state.
        
        Args:
            job_id: The job identifier
            status: New status
            current_step: Current step being executed
            progress: Progress percentage (0-100)
            step_result: Tuple of (step_name, result_dict) to add
            error: Error message if failed
        
        Returns:
            Updated JobState
        """
        state = await self.get_job(job_id)
        if not state:
            return None
        
        updates: dict[str, Any] = {}
        
        if status is not None:
            updates["status"] = status.value
        
        if current_step is not None:
            updates["current_step"] = current_step.value
        
        if progress is not None:
            updates["progress"] = progress
        
        if error is not None:
            updates["error"] = error
        
        if step_result:
            step_name, result_data = step_result
            new_result = {**state.result, step_name: result_data}
            updates["result"] = new_result
            
            # Add to completed steps
            completed = list(state.completed_steps)
            if step_name not in completed:
                completed.append(step_name)
            updates["completed_steps"] = completed
        
        new_state = state.with_update(**updates)
        await self._save_state(new_state)
        
        return new_state
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job."""
        state = await self.get_job(job_id)
        if not state:
            return False
        
        if state.status in (JobStatus.COMPLETED, JobStatus.FAILED):
            return False
        
        await self.update_job(job_id, status=JobStatus.CANCELLED)
        return True
    
    async def delete_job(self, job_id: str) -> bool:
        """Delete a job from storage."""
        key = f"{self.JOB_KEY_PREFIX}:{job_id}"
        return await self.cache.delete(key)
    
    async def _save_state(self, state: JobState) -> None:
        """Save job state to Redis."""
        key = f"{self.JOB_KEY_PREFIX}:{state.job_id}"
        await self.cache.set(key, state.to_dict(), ttl=self.JOB_TTL)
    
    # Result caching methods
    
    async def get_cached_result(self, url: str) -> Optional[dict]:
        """
        Get cached workflow result for URL.
        
        Returns full enriched result if available.
        """
        key = self.cache.generate_key("workflow:result", url)
        return await self.cache.get(key)
    
    async def cache_result(self, url: str, result: dict) -> None:
        """Cache the final workflow result."""
        key = self.cache.generate_key("workflow:result", url)
        await self.cache.set(key, result, ttl=self.RESULT_TTL)
    
    async def get_step_cache(self, url: str, step: WorkflowStep) -> Optional[dict]:
        """Get cached result for a specific step."""
        key = self.cache.generate_key(f"workflow:step:{step.value}", url)
        return await self.cache.get(key)
    
    async def cache_step_result(
        self, 
        url: str, 
        step: WorkflowStep, 
        result: dict,
    ) -> None:
        """Cache result for a specific step."""
        key = self.cache.generate_key(f"workflow:step:{step.value}", url)
        await self.cache.set(key, result, ttl=self.RESULT_TTL)
    
    def calculate_progress(self, completed_steps: list[str]) -> int:
        """
        Calculate progress percentage based on completed steps.
        
        Overview = 20%, Each parallel step = 20% (4 * 20 = 80%)
        Total = 100%
        """
        progress = 0
        
        if WorkflowStep.OVERVIEW.value in completed_steps:
            progress += 20
        
        for step in self.PARALLEL_STEPS:
            if step.value in completed_steps:
                progress += 20
        
        return min(progress, 100)


# Singleton instance
_workflow_service: Optional[WorkflowService] = None


async def get_workflow_service() -> WorkflowService:
    """Dependency injection factory for WorkflowService."""
    global _workflow_service
    
    if _workflow_service is None:
        from services.cache_service import get_cache_service
        cache = await get_cache_service()
        _workflow_service = WorkflowService(cache)
    
    return _workflow_service


async def shutdown_workflow_service() -> None:
    """Cleanup function for application shutdown."""
    global _workflow_service
    _workflow_service = None
