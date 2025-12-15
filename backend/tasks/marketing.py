"""
Marketing Task - AI-Powered Content Marketing Recommendations

Generates social media posts, content ideas, and marketing strategies.
"""

import json
import logging
from typing import Any

from tasks.base import WorkflowTask
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class MarketingTask(WorkflowTask):
    """
    Marketing task - generates content marketing recommendations.
    
    Uses AI to create:
    - Social media posts for multiple platforms
    - Content ideas for blog/articles
    - Brand messaging recommendations
    """
    
    TASK_NAME = "marketing"
    REQUIRES_OVERVIEW = True
    
    async def execute(self) -> dict[str, Any]:
        """
        Generate marketing recommendations.
        
        Returns:
            Dictionary with marketing content:
            - social_posts: Ready-to-use social media posts
            - content_ideas: Blog/article suggestions
            - brand_messaging: Key messaging points
        """
        openai_service = OpenAIService()
        
        if not openai_service.is_configured:
            return {
                "social_posts": [],
                "content_ideas": [],
                "brand_messaging": {},
                "error": "OpenAI API key not configured",
            }
        
        return await self._generate_marketing_content(openai_service)
    
    async def _generate_marketing_content(
        self, 
        openai_service: OpenAIService,
    ) -> dict[str, Any]:
        """Generate marketing content using AI."""
        brand = self._get_brand_name()
        description = self._get_description()
        keywords = self._get_keywords(15)
        scores = self._extract_scores()
        
        content = self._extract_content()
        bigrams = [b.get("phrase", "") for b in content.get("top_bigrams", [])[:5]]
        trigrams = [t.get("phrase", "") for t in content.get("top_trigrams", [])[:3]]
        
        system_prompt = """You are an expert content marketing strategist specializing in SEO and social media marketing. 
Generate actionable marketing recommendations based on SEO analysis data.
Return valid JSON only, no markdown formatting or code blocks."""

        user_prompt = f"""Based on this comprehensive SEO analysis, generate content marketing recommendations:

WEBSITE ANALYSIS:
- URL: {self.url}
- Brand/Title: {brand}
- Description: {description}
- Word Count: {content.get("word_count", "N/A")}
- Current SEO Scores: {json.dumps(scores)}

EXTRACTED KEYWORDS (from page analysis):
- Top keywords: {", ".join(keywords)}
- Key phrases (bigrams): {", ".join(bigrams)}
- Key phrases (trigrams): {", ".join(trigrams)}

TASK: Generate a JSON object with these sections:

1. "social_posts": Array of 3 ready-to-use social media posts (one per platform):
   - "platform": "facebook", "linkedin", or "twitter"
   - "content": The full post text (appropriate length for each platform)
   - "hashtags": Array of 3-5 relevant hashtags
   - "call_to_action": A clear CTA for the post
   - "best_time": Suggested best time to post

2. "content_ideas": Array of 5 blog post or content ideas. Each with:
   - "title": Suggested article title
   - "type": "how-to", "listicle", "guide", "case-study", or "comparison"
   - "target_keyword": Primary keyword to target
   - "description": Brief description of the content

3. "brand_messaging": Object with:
   - "value_proposition": One sentence value proposition
   - "key_differentiators": Array of 3 unique selling points
   - "tone_recommendation": Suggested brand voice/tone
   - "tagline_suggestions": Array of 2-3 tagline ideas

Return ONLY the JSON object with these three keys."""

        try:
            result = await openai_service.complete_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=2500,
            )
            
            # Ensure expected structure
            return {
                "social_posts": result.get("social_posts", []),
                "content_ideas": result.get("content_ideas", []),
                "brand_messaging": result.get("brand_messaging", {}),
            }
        
        except Exception as e:
            logger.exception(f"Marketing content generation failed: {e}")
            return {
                "social_posts": [],
                "content_ideas": [],
                "brand_messaging": {},
                "error": str(e),
            }
