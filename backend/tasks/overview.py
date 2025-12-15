"""
Overview Task - SEO Analysis Step

First step in the workflow that performs comprehensive SEO analysis.
Results are used by subsequent parallel tasks.
"""

import logging
from typing import Any

from tasks.base import WorkflowTask

logger = logging.getLogger(__name__)


class OverviewTask(WorkflowTask):
    """
    Overview task - performs comprehensive SEO and AI indexing analysis.
    
    This is the foundation task that other tasks depend on.
    Uses SEOAnalyzer from libs/seo for analysis.
    """
    
    TASK_NAME = "overview"
    REQUIRES_OVERVIEW = False  # This task generates the overview
    
    async def execute(self) -> dict[str, Any]:
        """
        Execute SEO analysis.
        
        Returns:
            Complete SEO analysis results including:
            - scores: Overall and category scores
            - metadata: Title, description, etc.
            - content: Word count, keywords, readability
            - structured_data: JSON-LD, OpenGraph, etc.
            - ai_indexing: Robots.txt, llms.txt status
            - issues: Detected problems
            - recommendations: Suggested improvements
        """
        from libs.seo import SEOAnalyzer
        
        analyzer = SEOAnalyzer(self.url)
        result = await analyzer.analyze()
        
        if "error" in result:
            raise Exception(f"Analysis failed: {result['error']}")
        
        return result
