"""
ARQ Worker Configuration

Defines the worker settings and task functions for ARQ.
Run with: arq backend.tasks.worker.WorkerSettings
"""

import asyncio
import logging
import os
from typing import Any

from arq import cron
from arq.connections import RedisSettings

from services.cache_service import CacheService
from services.workflow_service import (
    WorkflowService,
    JobStatus,
    WorkflowStep,
)

logger = logging.getLogger(__name__)

# Redis connection settings
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


def parse_redis_url(url: str) -> RedisSettings:
    """Parse Redis URL into ARQ RedisSettings."""
    # Handle redis://host:port format
    url = url.replace("redis://", "")
    
    # Check for password
    password = None
    if "@" in url:
        auth, url = url.rsplit("@", 1)
        if ":" in auth:
            _, password = auth.split(":", 1)
    
    # Parse host and port
    if ":" in url:
        host, port = url.split(":")
        port = int(port.split("/")[0])  # Handle /db suffix
    else:
        host = url.split("/")[0]
        port = 6379
    
    # Parse database
    database = 0
    if "/" in url:
        try:
            database = int(url.split("/")[1])
        except (IndexError, ValueError):
            pass
    
    return RedisSettings(
        host=host,
        port=port,
        password=password,
        database=database,
    )


async def run_workflow(ctx: dict, job_id: str, url: str) -> dict[str, Any]:
    """
    Main workflow task - orchestrates the entire analysis pipeline.
    
    Steps:
    1. Run Overview (SEO analysis)
    2. Run parallel tasks: Insights, Signals, Keywords, Marketing
    3. Aggregate results and update job status
    
    Args:
        ctx: ARQ context with Redis connection
        job_id: Unique job identifier
        url: URL to analyze
    
    Returns:
        Complete workflow result
    """
    # Initialize services
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    cache = CacheService(redis_url=redis_url)
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
        
        # Step 2: Parallel tasks
        from tasks.insights import InsightsTask
        from tasks.signals import SignalsTask
        from tasks.keywords import KeywordsTask
        from tasks.marketing import MarketingTask
        
        parallel_tasks = [
            (WorkflowStep.INSIGHTS, InsightsTask(url=url, overview_data=overview_data)),
            (WorkflowStep.SIGNALS, SignalsTask(url=url, overview_data=overview_data)),
            (WorkflowStep.KEYWORDS, KeywordsTask(url=url, overview_data=overview_data)),
            (WorkflowStep.MARKETING, MarketingTask(url=url, overview_data=overview_data)),
        ]
        
        # Run all parallel tasks
        async def run_parallel_task(step: WorkflowStep, task):
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
        }
        
        for item in parallel_results:
            if isinstance(item, Exception):
                logger.error(f"[{job_id}] Parallel task failed: {item}")
                continue
            
            step, result = item
            step_name = step.value
            
            if result.get("success"):
                aggregated_results[step_name] = result.get("data", {})
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


async def cleanup_old_jobs(ctx: dict) -> None:
    """
    Periodic task to clean up old completed/failed jobs.
    
    Runs daily to remove jobs older than 24 hours.
    """
    logger.info("Running job cleanup task")
    # Implementation would scan and remove old job keys
    # For now, Redis TTL handles this automatically


# ARQ Worker Settings
class WorkerSettings:
    """ARQ Worker configuration."""
    
    redis_settings = parse_redis_url(REDIS_URL)
    
    # Registered task functions
    functions = [
        run_workflow,
        cleanup_old_jobs,
    ]
    
    # Scheduled tasks
    cron_jobs = [
        cron(cleanup_old_jobs, hour=3, minute=0),  # Run daily at 3 AM
    ]
    
    # Worker settings
    max_jobs = int(os.getenv("MAX_CONCURRENT_ANALYSES", "5"))
    job_timeout = 300  # 5 minutes max per job
    keep_result = 86400  # Keep results for 24 hours
    
    # Retry settings
    max_tries = 3
    retry_delay = 60  # 1 minute between retries
    
    # Logging
    log_results = True
    
    @staticmethod
    async def on_startup(ctx: dict) -> None:
        """Called when worker starts."""
        logger.info("ARQ Worker starting up...")
    
    @staticmethod
    async def on_shutdown(ctx: dict) -> None:
        """Called when worker shuts down."""
        logger.info("ARQ Worker shutting down...")
