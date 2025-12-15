"""
Insights Task - Multi-LLM AI Insights

Queries multiple LLM providers in parallel for diverse AI insights.
"""

import asyncio
import logging
from typing import Any

from tasks.base import WorkflowTask
from services.openai_service import OpenAIService, GrokService
from utils.language import get_language_context_for_ai

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
            - executive_summary: Quick overview with key metrics
        """
        brand = self._get_brand_name()
        description = self._get_description()
        keywords = self._get_keywords(10)
        scores = self._extract_scores()
        language_info = self._get_language_info()
        language_context = get_language_context_for_ai(language_info)
        
        # Build executive summary from analyzer data
        executive_summary = self._build_executive_summary(brand, scores)
        
        # Prepare the analysis prompt with language context
        prompt = f"""Analyze this website's AI discoverability and provide strategic insights:

WEBSITE: {self.url}
BRAND: {brand}
DESCRIPTION: {description}
{language_context}
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
4. Language/localization considerations for AI visibility

Be concise and specific to this website. Format as bullet points.
{f'Respond in {language_info.get("name", "English")} if the website is not in English.' if language_info.get("code") and language_info.get("code") != "en" else ''}"""

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
        
        # Add executive summary as markdown
        results["executive_summary"] = executive_summary
        results["executive_summary_md"] = self._build_executive_summary_md(executive_summary)
        
        return results
    
    def _build_executive_summary(self, brand: str, scores: dict) -> dict:
        """Build executive summary from analyzer data."""
        overall = scores.get("overall", 0)
        ai_readiness = scores.get("ai_readiness", 0)
        content = scores.get("content", 0)
        technical = scores.get("technical", 0)
        structured_data = scores.get("structured_data", 0)
        
        # Determine rating
        if overall >= 80:
            rating = "Excellent"
            rating_color = "green"
        elif overall >= 60:
            rating = "Good"
            rating_color = "blue"
        elif overall >= 40:
            rating = "Needs Work"
            rating_color = "yellow"
        else:
            rating = "Poor"
            rating_color = "red"
        
        # Identify strengths and weaknesses
        score_items = [
            ("AI Readiness", ai_readiness),
            ("Content", content),
            ("Technical", technical),
            ("Structured Data", structured_data),
        ]
        sorted_scores = sorted(score_items, key=lambda x: x[1], reverse=True)
        primary_strength = sorted_scores[0][0] if sorted_scores[0][1] >= 50 else None
        primary_weakness = sorted_scores[-1][0] if sorted_scores[-1][1] < 70 else None
        
        # Get additional context
        metadata = self._extract_metadata()
        ai_indexing = self.overview_data.get("ai_indexing", {})
        issues = self.overview_data.get("issues", [])
        
        # Count critical issues
        critical_issues = len([i for i in issues if i.get("severity") == "high"])
        
        # Check AI bot access
        bot_status = ai_indexing.get("robots_txt", {}).get("ai_bots_status", {})
        allowed_bots = [bot for bot, status in bot_status.items() if "allowed" in status.lower()]
        blocked_bots = [bot for bot, status in bot_status.items() if "blocked" in status.lower()]
        
        has_llms_txt = ai_indexing.get("llms_txt", {}).get("present", False)
        has_sitemap = ai_indexing.get("sitemap_xml", {}).get("present", False)
        
        return {
            "brand": brand,
            "rating": rating,
            "rating_color": rating_color,
            "overall_score": overall,
            "scores": {
                "ai_readiness": ai_readiness,
                "content": content,
                "technical": technical,
                "structured_data": structured_data,
            },
            "primary_strength": primary_strength,
            "primary_weakness": primary_weakness,
            "critical_issues_count": critical_issues,
            "total_issues_count": len(issues),
            "ai_access": {
                "has_llms_txt": has_llms_txt,
                "has_sitemap": has_sitemap,
                "allowed_bots_count": len(allowed_bots),
                "blocked_bots_count": len(blocked_bots),
                "allowed_bots": allowed_bots[:5],
                "blocked_bots": blocked_bots[:5],
            },
            "metadata": {
                "title": (metadata.get("title") or {}).get("value"),
                "description": (metadata.get("description") or {}).get("value"),
                "language": metadata.get("language", "en"),
            },
        }
    
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

    def _build_executive_summary_md(self, summary: dict) -> str:
        """Build executive summary as markdown."""
        brand = summary.get("brand", "Website")
        rating = summary.get("rating", "Unknown")
        overall = summary.get("overall_score", 0)
        scores = summary.get("scores", {})
        strength = summary.get("primary_strength")
        weakness = summary.get("primary_weakness")
        ai_access = summary.get("ai_access", {})
        critical_issues = summary.get("critical_issues_count", 0)
        total_issues = summary.get("total_issues_count", 0)
        
        # Rating emoji
        rating_emoji = {
            "Excellent": "🟢",
            "Good": "🔵", 
            "Needs Work": "🟡",
            "Poor": "🔴"
        }.get(rating, "⚪")
        
        lines = [
            f"## {rating_emoji} {rating} - {overall}/100",
            "",
            f"**{brand}** AI discoverability assessment.",
            "",
            "### Score Breakdown",
            "",
            f"| Category | Score |",
            f"|----------|-------|",
            f"| AI Readiness | {scores.get('ai_readiness', 0)}/100 |",
            f"| Content | {scores.get('content', 0)}/100 |",
            f"| Technical | {scores.get('technical', 0)}/100 |",
            f"| Structured Data | {scores.get('structured_data', 0)}/100 |",
            "",
        ]
        
        if strength or weakness:
            lines.append("### Key Findings")
            lines.append("")
            if strength:
                lines.append(f"✅ **Strength:** {strength}")
            if weakness:
                lines.append(f"⚠️ **Needs Improvement:** {weakness}")
            lines.append("")
        
        lines.append("### AI Crawler Access")
        lines.append("")
        llms_status = "✅ Present" if ai_access.get("has_llms_txt") else "❌ Missing"
        sitemap_status = "✅ Present" if ai_access.get("has_sitemap") else "❌ Missing"
        lines.append(f"- **llms.txt:** {llms_status}")
        lines.append(f"- **Sitemap:** {sitemap_status}")
        lines.append(f"- **AI Bots Allowed:** {ai_access.get('allowed_bots_count', 0)}")
        
        if ai_access.get("blocked_bots_count", 0) > 0:
            lines.append(f"- **AI Bots Blocked:** {ai_access.get('blocked_bots_count', 0)}")
        
        if ai_access.get("allowed_bots"):
            bots = ", ".join(ai_access.get("allowed_bots", [])[:5])
            lines.append(f"- **Allowed:** {bots}")
        
        lines.append("")
        
        if critical_issues > 0:
            lines.append(f"### ⚠️ Issues")
            lines.append("")
            lines.append(f"**{critical_issues} critical** issue{'s' if critical_issues != 1 else ''} out of {total_issues} total.")
            lines.append("")
        
        return "\n".join(lines)
