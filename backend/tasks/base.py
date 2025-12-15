"""
Base Task - Abstract Interface for Workflow Tasks

Follows Open/Closed Principle - easy to add new tasks without modifying existing code.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class WorkflowTask(ABC):
    """
    Abstract base class for workflow tasks.
    
    Implements Strategy pattern - each task defines its own execution logic.
    
    To add a new task:
    1. Create a new class inheriting from WorkflowTask
    2. Implement the execute() method
    3. Register in tasks/__init__.py
    """
    
    # Task identifier (override in subclass)
    TASK_NAME: str = "base"
    
    # Whether this task requires overview results as input
    REQUIRES_OVERVIEW: bool = True
    
    def __init__(self, url: str, overview_data: dict | None = None):
        """
        Initialize task.
        
        Args:
            url: Target URL being analyzed
            overview_data: Results from overview step (if required)
        """
        self.url = url
        self.overview_data = overview_data or {}
    
    @abstractmethod
    async def execute(self) -> dict[str, Any]:
        """
        Execute the task.
        
        Returns:
            Dictionary containing task results
        
        Raises:
            Exception: If task execution fails
        """
        pass
    
    def validate_input(self) -> bool:
        """
        Validate task inputs before execution.
        
        Returns:
            True if inputs are valid
        
        Raises:
            ValueError: If validation fails
        """
        if not self.url:
            raise ValueError(f"{self.TASK_NAME}: URL is required")
        
        if self.REQUIRES_OVERVIEW and not self.overview_data:
            raise ValueError(f"{self.TASK_NAME}: Overview data is required")
        
        return True
    
    async def run(self) -> dict[str, Any]:
        """
        Run the task with validation and error handling.
        
        Returns:
            Task results with success/error status
        """
        try:
            self.validate_input()
            logger.info(f"Starting task: {self.TASK_NAME} for {self.url}")
            
            result = await self.execute()
            
            logger.info(f"Completed task: {self.TASK_NAME} for {self.url}")
            return {
                "success": True,
                "task": self.TASK_NAME,
                "data": result,
            }
        
        except Exception as e:
            logger.exception(f"Task {self.TASK_NAME} failed: {e}")
            return {
                "success": False,
                "task": self.TASK_NAME,
                "error": str(e),
            }
    
    def _extract_metadata(self) -> dict:
        """Helper to extract metadata from overview data."""
        return self.overview_data.get("metadata", {})
    
    def _extract_content(self) -> dict:
        """Helper to extract content from overview data."""
        return self.overview_data.get("content", {})
    
    def _extract_scores(self) -> dict:
        """Helper to extract scores from overview data."""
        return self.overview_data.get("scores", {})
    
    def _get_brand_name(self) -> str:
        """Helper to get brand name from overview data."""
        metadata = self._extract_metadata()
        return (
            metadata.get("title", {}).get("value") or 
            self.overview_data.get("url", "the brand")
        )
    
    def _get_description(self) -> str:
        """Helper to get description from overview data."""
        metadata = self._extract_metadata()
        return metadata.get("description", {}).get("value") or ""
    
    def _get_keywords(self, limit: int = 10) -> list[str]:
        """Helper to get top keywords from overview data."""
        content = self._extract_content()
        llm_context = self.overview_data.get("llm_context", {})
        
        # Try LLM context keywords first
        keywords = llm_context.get("top_keywords", [])[:limit]
        
        # Fall back to frequency keywords
        if not keywords:
            freq_keywords = content.get("keywords_frequency", [])
            keywords = [k.get("keyword", "") for k in freq_keywords[:limit]]
        
        return keywords
    
    def _get_language_info(self) -> dict:
        """Helper to get language detection info from overview data."""
        return self.overview_data.get("language", {})
