"""
Social Task - Social Sharing Analysis & AI Recommendations

Analyzes social media sharing metadata and generates AI-powered recommendations.
"""

import json
import logging
from typing import Any

from tasks.base import WorkflowTask
from services.openai_service import OpenAIService
from utils.language import get_language_context_for_ai

logger = logging.getLogger(__name__)


class SocialTask(WorkflowTask):
    """
    Social task - analyzes social sharing readiness and generates recommendations.
    
    Provides:
    - Detailed social metadata analysis
    - Platform-specific compatibility scores
    - AI-generated improvement recommendations
    - Social image preview information
    """
    
    TASK_NAME = "social"
    REQUIRES_OVERVIEW = True
    
    async def execute(self) -> dict[str, Any]:
        """
        Analyze social sharing metadata and generate recommendations.
        
        Returns:
            Dictionary with social analysis:
            - metadata: Extracted social metadata (OG, Twitter Card)
            - images: Social sharing images with URLs
            - platforms: Platform compatibility breakdown
            - score: Overall social sharing score
            - recommendations: AI-generated improvements
        """
        social_data = self._extract_social_data()
        language_info = self._get_language_info()
        
        # Generate AI recommendations
        ai_recommendations = await self._generate_ai_recommendations(
            social_data, 
            language_info
        )
        
        return {
            "metadata": self._format_metadata(social_data),
            "images": social_data.get("social_images", []),
            "platforms": social_data.get("platform_compatibility", {}),
            "score": social_data.get("score", 0),
            "issues": self._collect_all_issues(social_data),
            "recommendations": ai_recommendations,
            "preview": self._generate_preview_data(social_data),
        }
    
    def _extract_social_data(self) -> dict:
        """Extract social metadata from overview data."""
        return self.overview_data.get("social", {})
    
    def _format_metadata(self, social_data: dict) -> dict:
        """Format social metadata for response."""
        og = social_data.get("open_graph", {})
        twitter = social_data.get("twitter_card", {})
        
        return {
            "open_graph": {
                "present": og.get("present", False),
                "title": og.get("tags", {}).get("title"),
                "description": og.get("tags", {}).get("description"),
                "image": og.get("tags", {}).get("image"),
                "url": og.get("tags", {}).get("url"),
                "type": og.get("tags", {}).get("type"),
                "site_name": og.get("tags", {}).get("site_name"),
                "locale": og.get("tags", {}).get("locale"),
                "image_dimensions": {
                    "width": og.get("tags", {}).get("image:width"),
                    "height": og.get("tags", {}).get("image:height"),
                },
                "missing_required": og.get("missing_required", []),
                "missing_recommended": og.get("missing_recommended", []),
            },
            "twitter_card": {
                "present": twitter.get("present", False),
                "card_type": twitter.get("card_type"),
                "title": twitter.get("tags", {}).get("title"),
                "description": twitter.get("tags", {}).get("description"),
                "image": twitter.get("tags", {}).get("image"),
                "site": twitter.get("tags", {}).get("site"),
                "creator": twitter.get("tags", {}).get("creator"),
                "missing_required": twitter.get("missing_required", []),
                "missing_recommended": twitter.get("missing_recommended", []),
            },
        }
    
    def _collect_all_issues(self, social_data: dict) -> list[dict]:
        """Collect all social-related issues."""
        issues = []
        
        # OG issues
        og_issues = social_data.get("open_graph", {}).get("issues", [])
        issues.extend(og_issues)
        
        # Twitter issues
        twitter_issues = social_data.get("twitter_card", {}).get("issues", [])
        issues.extend(twitter_issues)
        
        return issues
    
    def _generate_preview_data(self, social_data: dict) -> dict:
        """Generate social sharing preview data."""
        og = social_data.get("open_graph", {}).get("tags", {})
        twitter = social_data.get("twitter_card", {}).get("tags", {})
        metadata = self._extract_metadata()
        
        # Use OG data with fallbacks to Twitter Card and page metadata
        return {
            "title": (
                og.get("title") or 
                twitter.get("title") or 
                metadata.get("title", {}).get("value") or
                "No title"
            ),
            "description": (
                og.get("description") or 
                twitter.get("description") or 
                metadata.get("description", {}).get("value") or
                "No description"
            ),
            "image": og.get("image") or twitter.get("image"),
            "image_alt": og.get("image:alt") or twitter.get("image:alt"),
            "site_name": og.get("site_name") or self.url,
            "url": og.get("url") or self.url,
        }
    
    async def _generate_ai_recommendations(
        self, 
        social_data: dict,
        language_info: dict,
    ) -> dict[str, Any]:
        """Generate AI-powered social sharing recommendations."""
        openai_service = OpenAIService()
        
        if not openai_service.is_configured:
            return {
                "summary": "AI recommendations unavailable - API key not configured",
                "improvements": [],
                "best_practices": [],
            }
        
        language_context = get_language_context_for_ai(language_info)
        language_name = language_info.get("name", "English")
        
        # Prepare context
        og = social_data.get("open_graph", {})
        twitter = social_data.get("twitter_card", {})
        platforms = social_data.get("platform_compatibility", {})
        score = social_data.get("score", 0)
        images = social_data.get("social_images", [])
        
        brand = self._get_brand_name()
        description = self._get_description()
        
        system_prompt = f"""You are a social media optimization expert specializing in social sharing metadata and platform compatibility.
Analyze the provided social metadata and generate specific, actionable recommendations.
{f'Respond in {language_name}.' if language_info.get("code") and language_info.get("code") != "en" else ''}
Return valid JSON only, no markdown formatting."""

        user_prompt = f"""Analyze this website's social sharing readiness and provide recommendations:

WEBSITE: {self.url}
BRAND: {brand}
{language_context}

CURRENT SOCIAL SCORE: {score}/100

OPEN GRAPH STATUS:
- Present: {og.get('present', False)}
- Tags found: {list(og.get('tags', {}).keys())}
- Missing required: {og.get('missing_required', [])}
- Missing recommended: {og.get('missing_recommended', [])}
- Issues: {[i.get('message') for i in og.get('issues', [])]}

TWITTER CARD STATUS:
- Present: {twitter.get('present', False)}
- Card type: {twitter.get('card_type', 'none')}
- Tags found: {list(twitter.get('tags', {}).keys())}
- Missing required: {twitter.get('missing_required', [])}
- Issues: {[i.get('message') for i in twitter.get('issues', [])]}

SOCIAL IMAGES: {len(images)} found
{json.dumps(images[:3], indent=2) if images else 'No social images detected'}

PLATFORM COMPATIBILITY:
{json.dumps(platforms, indent=2)}

Generate a JSON response with:

1. "summary": A 2-3 sentence summary of the social sharing status and most critical improvements needed.

2. "improvements": Array of 5-7 specific improvements. Each with:
   - "priority": "high", "medium", or "low"
   - "category": "open_graph", "twitter_card", "image", or "general"
   - "issue": What's wrong or missing
   - "action": Specific fix with example code/tag if applicable
   - "impact": Which platforms this affects

3. "best_practices": Array of 3-4 best practice tips specific to this site's content type.

4. "sample_tags": Object with example meta tags this site should add (if missing critical ones):
   - "open_graph": Array of example og: meta tags as strings
   - "twitter_card": Array of example twitter: meta tags as strings

Return ONLY the JSON object."""

        try:
            result = await openai_service.complete_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=2500,
            )
            
            return {
                "summary": result.get("summary", ""),
                "improvements": result.get("improvements", []),
                "best_practices": result.get("best_practices", []),
                "sample_tags": result.get("sample_tags", {}),
            }
            
        except Exception as e:
            logger.warning(f"Social recommendations generation failed: {e}")
            return {
                "summary": f"Unable to generate AI recommendations: {str(e)}",
                "improvements": self._generate_fallback_improvements(social_data),
                "best_practices": [],
                "sample_tags": {},
            }
    
    def _generate_fallback_improvements(self, social_data: dict) -> list[dict]:
        """Generate basic improvements without AI."""
        improvements = []
        
        og = social_data.get("open_graph", {})
        twitter = social_data.get("twitter_card", {})
        images = social_data.get("social_images", [])
        
        if not og.get("present"):
            improvements.append({
                "priority": "high",
                "category": "open_graph",
                "issue": "Missing Open Graph tags",
                "action": "Add og:title, og:description, og:image, og:url, and og:type meta tags",
                "impact": "Facebook, LinkedIn, WhatsApp, Slack",
            })
        
        if not twitter.get("present"):
            improvements.append({
                "priority": "medium",
                "category": "twitter_card",
                "issue": "Missing Twitter Card tags",
                "action": "Add twitter:card, twitter:title, twitter:description, and twitter:image meta tags",
                "impact": "Twitter/X",
            })
        
        if not images:
            improvements.append({
                "priority": "high",
                "category": "image",
                "issue": "No social sharing image",
                "action": "Add og:image with a 1200x630 pixel image for optimal display",
                "impact": "All social platforms",
            })
        elif images and not images[0].get("width"):
            improvements.append({
                "priority": "low",
                "category": "image",
                "issue": "Social image dimensions not specified",
                "action": "Add og:image:width and og:image:height meta tags",
                "impact": "Faster image rendering on social platforms",
            })
        
        for missing in og.get("missing_required", []):
            improvements.append({
                "priority": "high",
                "category": "open_graph",
                "issue": f"Missing required og:{missing}",
                "action": f"Add <meta property=\"og:{missing}\" content=\"...\">",
                "impact": "Facebook, LinkedIn, WhatsApp",
            })
        
        return improvements
