"""
TaskIQ Broker Configuration

Modern async task queue with Redis backend.
Python 3.14 compatible.

Run worker with: taskiq worker tasks.broker:broker
"""

import os
import logging

from taskiq_redis import ListQueueBroker, RedisAsyncResultBackend

logger = logging.getLogger(__name__)

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Create broker with Redis backend
broker = ListQueueBroker(
    url=REDIS_URL,
    queue_name="seo_workflow_queue",
).with_result_backend(
    RedisAsyncResultBackend(
        redis_url=REDIS_URL,
        result_ex_time=86400,  # 24 hours TTL
    )
)


# Broker lifecycle hooks
@broker.on_event("startup")
async def on_startup() -> None:
    """Called when broker starts up."""
    logger.info("🚀 TaskIQ broker starting up...")


@broker.on_event("shutdown")
async def on_shutdown() -> None:
    """Called when broker shuts down."""
    logger.info("🛑 TaskIQ broker shutting down...")
