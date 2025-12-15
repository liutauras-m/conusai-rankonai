"""
TaskIQ Worker - Workflow Tasks

Defines task functions for the SEO analysis workflow.
Run with: taskiq worker tasks.worker:broker --fs-discover
"""

import asyncio
import logging
import os
from typing import Any

from tasks.broker import broker
from services.cache_service import CacheService
from services.workflow_service import (
    WorkflowService,
    JobStatus,
    WorkflowStep,
)

logger = logging.getLogger(__name__)

# Redis URL for services
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


@broker.task(
    task_name="run_workflow",
    timeout=300,  # 5 minutes max
    retry_on_error=True,
    max_retries=3,
)
async def run_workflow(job_id: str, url: str) -> dict[str, Any]:
    """
    Main workflow task - orchestrates the entire analysis pipeline.
    
    Steps:
    1. Run Overview (SEO analysis)
    2. Run parallel tasks: Insights, Signals, Keywords, Marketing
    3. Aggregate results and update job status
    
    Args:
        job_id: Unique job identifier
        url: URL to analyze
    
    Returns:
        Complete workflow result
    """
    # Initialize services
    cache = CacheService(redis_url=REDIS_URL)
    await cache.connect()
    
    workflow = WorkflowService(cache)
    
    try:
        # Update job status to running
        await workflow.update_job(
            job_id,
            status=JobStatus.RUNNING,
            current_step=WorkflowStep.OVERVIEW,
            progress=0,
        )
        
        # Step 1: Overview
        logger.info(f"[{job_id}] Starting overview for {url}")
        from tasks.overview import OverviewTask
        
        overview_task = OverviewTask(url=url)
        overview_result = await overview_task.run()
        
        if not overview_result.get("success"):
            raise Exception(f"Overview failed: {overview_result.get('error')}")
        
        overview_data = overview_result.get("data", {})
        
        # Cache and update progress
        await workflow.cache_step_result(url, WorkflowStep.OVERVIEW, overview_data)
        await workflow.update_job(
            job_id,
            current_step=WorkflowStep.OVERVIEW,
            progress=20,
            step_result=(WorkflowStep.OVERVIEW.value, overview_data),
        )
        
        logger.info(f"[{job_id}] Overview complete, starting parallel tasks")
        
        # Step 2: Parallel tasks (includes AI Summary and Social)
        from tasks.insights import InsightsTask
        from tasks.signals import SignalsTask
        from tasks.keywords import KeywordsTask
        from tasks.marketing import MarketingTask
        from tasks.ai_summary import AISummaryTask
        from tasks.social import SocialTask
        
        parallel_tasks = [
            (WorkflowStep.INSIGHTS, InsightsTask(url=url, overview_data=overview_data)),
            (WorkflowStep.SIGNALS, SignalsTask(url=url, overview_data=overview_data)),
            (WorkflowStep.KEYWORDS, KeywordsTask(url=url, overview_data=overview_data)),
            (WorkflowStep.MARKETING, MarketingTask(url=url, overview_data=overview_data)),
            ("ai_summary", AISummaryTask(url=url, overview_data=overview_data)),
            ("social", SocialTask(url=url, overview_data=overview_data)),
        ]
        
        # Run all parallel tasks
        async def run_parallel_task(step, task):
            result = await task.run()
            return (step, result)
        
        parallel_results = await asyncio.gather(
            *[run_parallel_task(step, task) for step, task in parallel_tasks],
            return_exceptions=True,
        )
        
        # Process results
        aggregated_results = {
            "overview": overview_data,
            "insights": {},
            "signals": {},
            "keywords": {},
            "marketing": {},
            "ai_summary": {},
            "social": {},
        }
        
        for item in parallel_results:
            if isinstance(item, Exception):
                logger.error(f"[{job_id}] Parallel task failed: {item}")
                continue
            
            step, result = item
            # Handle both WorkflowStep enum and string steps
            step_name = step.value if hasattr(step, 'value') else step
            
            if result.get("success"):
                aggregated_results[step_name] = result.get("data", {})
                # Only cache WorkflowStep types
                if hasattr(step, 'value'):
                    await workflow.cache_step_result(url, step, result.get("data", {}))
            else:
                aggregated_results[step_name] = {"error": result.get("error")}
            
            # Update progress
            state = await workflow.get_job(job_id)
            if state:
                new_progress = workflow.calculate_progress(
                    state.completed_steps + [step_name]
                )
                await workflow.update_job(
                    job_id,
                    progress=new_progress,
                    step_result=(step_name, aggregated_results[step_name]),
                )
        
        # Finalize job
        final_result = {
            "url": url,
            "timestamp": overview_data.get("timestamp"),
            "scores": overview_data.get("scores", {}),
            **aggregated_results,
        }
        
        # Cache final result
        await workflow.cache_result(url, final_result)
        
        # Mark job as completed
        await workflow.update_job(
            job_id,
            status=JobStatus.COMPLETED,
            progress=100,
        )
        
        logger.info(f"[{job_id}] Workflow completed successfully")
        
        return final_result
    
    except Exception as e:
        logger.exception(f"[{job_id}] Workflow failed: {e}")
        await workflow.update_job(
            job_id,
            status=JobStatus.FAILED,
            error=str(e),
        )
        raise
    
    finally:
        await cache.disconnect()


@broker.task(
    task_name="cleanup_old_jobs",
    timeout=60,
)
async def cleanup_old_jobs() -> None:
    """
    Periodic task to clean up old completed/failed jobs.
    
    Can be scheduled via external scheduler or cron.
    """
    logger.info("Running job cleanup task")
    # Implementation would scan and remove old job keys
    # For now, Redis TTL handles this automatically


# Re-export broker for worker CLI
__all__ = ["broker", "run_workflow", "cleanup_old_jobs"]
