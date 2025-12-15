"""
Insights Task - Multi-LLM AI Insights

Queries multiple LLM providers in parallel for diverse AI insights.
"""

import asyncio
import logging
from typing import Any

from tasks.base import WorkflowTask
from services.openai_service import OpenAIService, GrokService

logger = logging.getLogger(__name__)


class InsightsTask(WorkflowTask):
    """
    Insights task - generates AI-powered insights from multiple LLMs.
    
    Uses OpenAI and Grok in parallel for diverse perspectives.
    """
    
    TASK_NAME = "insights"
    REQUIRES_OVERVIEW = True
    
    async def execute(self) -> dict[str, Any]:
        """
        Generate AI insights about the analyzed website.
        
        Returns:
            Dictionary with insights from multiple AI models:
            - openai: GPT-4o insights
            - grok: Grok insights
            - summary: Aggregated key points
        """
        brand = self._get_brand_name()
        description = self._get_description()
        keywords = self._get_keywords(10)
        scores = self._extract_scores()
        
        # Prepare the analysis prompt
        prompt = f"""Analyze this website's AI discoverability and provide strategic insights:

WEBSITE: {self.url}
BRAND: {brand}
DESCRIPTION: {description}
TOP KEYWORDS: {', '.join(keywords)}

CURRENT SCORES:
- Overall: {scores.get('overall', 0)}/100
- AI Readiness: {scores.get('ai_readiness', 0)}/100
- Content: {scores.get('content', 0)}/100
- Technical: {scores.get('technical', 0)}/100

Provide 3-5 specific, actionable insights about:
1. How AI assistants (ChatGPT, Claude, Perplexity) would perceive this website
2. Key opportunities to improve AI discoverability
3. What makes this brand unique and recommendable

Be concise and specific to this website. Format as bullet points."""

        system_prompt = "You are an AI SEO expert specializing in AI discoverability and LLM optimization. Provide actionable, specific insights."

        # Run both LLM calls in parallel
        openai_service = OpenAIService()
        grok_service = GrokService()
        
        results = {"openai": None, "grok": None, "summary": None}
        
        tasks = []
        
        if openai_service.is_configured:
            tasks.append(self._get_openai_insights(openai_service, system_prompt, prompt))
        
        if grok_service.is_configured:
            tasks.append(self._get_grok_insights(grok_service, system_prompt, prompt))
        
        if tasks:
            completed = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in completed:
                if isinstance(result, dict):
                    results.update(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Insight generation failed: {result}")
        
        # Generate summary from available insights
        results["summary"] = self._generate_summary(results)
        
        return results
    
    async def _get_openai_insights(
        self, 
        service: OpenAIService, 
        system_prompt: str, 
        user_prompt: str,
    ) -> dict:
        """Get insights from OpenAI."""
        try:
            response = await service.complete(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=1500,
            )
            return {"openai": response}
        except Exception as e:
            logger.warning(f"OpenAI insights failed: {e}")
            return {"openai": None}
    
    async def _get_grok_insights(
        self, 
        service: GrokService, 
        system_prompt: str, 
        user_prompt: str,
    ) -> dict:
        """Get insights from Grok."""
        try:
            response = await service.complete(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=1500,
            )
            return {"grok": response}
        except Exception as e:
            logger.warning(f"Grok insights failed: {e}")
            return {"grok": None}
    
    def _generate_summary(self, results: dict) -> str:
        """Generate a summary from available insights."""
        available = []
        if results.get("openai"):
            available.append("OpenAI")
        if results.get("grok"):
            available.append("Grok")
        
        if not available:
            return "No AI insights available. Please configure API keys."
        
        return f"Insights generated from: {', '.join(available)}"
