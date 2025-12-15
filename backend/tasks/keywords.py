"""
Keywords Task - Strategic Keyword Analysis & Extraction

Extracts and analyzes keywords for AI and SEO optimization.
"""

import json
import logging
from typing import Any

from tasks.base import WorkflowTask
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class KeywordsTask(WorkflowTask):
    """
    Keywords task - extracts and analyzes strategic keywords.
    
    Combines extracted keywords with AI-generated strategic recommendations.
    """
    
    TASK_NAME = "keywords"
    REQUIRES_OVERVIEW = True
    
    async def execute(self) -> dict[str, Any]:
        """
        Extract and analyze keywords.
        
        Returns:
            Dictionary with keyword analysis:
            - extracted: Keywords from page analysis
            - semantic: AI-recommended strategic keywords
            - opportunities: Keyword opportunities to target
        """
        # Extract keywords from overview data
        extracted = self._extract_page_keywords()
        
        # Generate AI strategic keywords
        strategic = await self._generate_strategic_keywords()
        
        return {
            "extracted": extracted,
            "strategic": strategic,
            "summary": self._generate_keyword_summary(extracted, strategic),
        }
    
    def _extract_page_keywords(self) -> dict[str, Any]:
        """Extract keywords from page analysis."""
        content = self._extract_content()
        llm_context = self.overview_data.get("llm_context", {})
        
        # Frequency-based keywords
        freq_keywords = content.get("keywords_frequency", [])
        
        # N-grams
        bigrams = content.get("top_bigrams", [])
        trigrams = content.get("top_trigrams", [])
        
        # LLM context keywords
        top_keywords = llm_context.get("top_keywords", [])
        
        return {
            "frequency": [
                {
                    "keyword": k.get("keyword", ""),
                    "count": k.get("count", 0),
                    "density": k.get("density", 0),
                }
                for k in freq_keywords[:15]
            ],
            "bigrams": [
                {
                    "phrase": b.get("phrase", ""),
                    "count": b.get("count", 0),
                }
                for b in bigrams[:10]
            ],
            "trigrams": [
                {
                    "phrase": t.get("phrase", ""),
                    "count": t.get("count", 0),
                }
                for t in trigrams[:5]
            ],
            "semantic": top_keywords[:10],
        }
    
    async def _generate_strategic_keywords(self) -> dict[str, Any]:
        """Generate AI-powered strategic keyword recommendations."""
        openai_service = OpenAIService()
        
        if not openai_service.is_configured:
            return {
                "target_keywords": [],
                "long_tail": [],
                "questions": [],
                "error": "OpenAI API key not configured",
            }
        
        brand = self._get_brand_name()
        description = self._get_description()
        keywords = self._get_keywords(15)
        
        content = self._extract_content()
        bigrams = [b.get("phrase", "") for b in content.get("top_bigrams", [])[:5]]
        
        system_prompt = """You are an SEO keyword strategist. 
Analyze the provided keywords and generate strategic recommendations.
Return valid JSON only, no markdown formatting."""

        user_prompt = f"""Based on this website's keyword profile, generate strategic keyword recommendations:

WEBSITE: {self.url}
BRAND: {brand}
DESCRIPTION: {description}

CURRENT KEYWORDS (extracted from page):
- Top keywords: {', '.join(keywords)}
- Key phrases: {', '.join(bigrams)}

Generate a JSON object with these sections:

1. "target_keywords": Array of 8 strategic keywords to target. Each with:
   - "keyword": The keyword/phrase
   - "search_intent": "informational", "transactional", "navigational", or "commercial"
   - "difficulty": "low", "medium", or "high"
   - "priority": "high", "medium", or "low"
   - "tip": Brief actionable tip

2. "long_tail": Array of 5 long-tail keyword opportunities

3. "questions": Array of 5 question-based keywords (what, how, why, etc.)

Return ONLY the JSON object."""

        try:
            result = await openai_service.complete_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=2000,
            )
            return result
        except Exception as e:
            logger.warning(f"Strategic keywords generation failed: {e}")
            return {
                "target_keywords": [],
                "long_tail": [],
                "questions": [],
                "error": str(e),
            }
    
    def _generate_keyword_summary(
        self, 
        extracted: dict, 
        strategic: dict,
    ) -> dict:
        """Generate keyword analysis summary."""
        top_extracted = [
            k["keyword"] for k in extracted.get("frequency", [])[:5]
        ]
        
        top_strategic = [
            k.get("keyword", "") 
            for k in strategic.get("target_keywords", [])[:5]
        ]
        
        return {
            "total_extracted": len(extracted.get("frequency", [])),
            "top_extracted": top_extracted,
            "strategic_recommendations": len(strategic.get("target_keywords", [])),
            "top_strategic": top_strategic,
            "long_tail_count": len(strategic.get("long_tail", [])),
            "questions_count": len(strategic.get("questions", [])),
        }
