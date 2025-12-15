"""
AI Summary Task - Generates AI-Powered SEO Summary Report

Produces a comprehensive markdown report with actionable insights
for improving AI discoverability across platforms.
"""

import json
import logging
from typing import Any

from tasks.base import WorkflowTask
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class AISummaryTask(WorkflowTask):
    """
    AI Summary task - generates comprehensive markdown report.
    
    Provides platform-specific insights and prioritized actions.
    """
    
    TASK_NAME = "ai_summary"
    REQUIRES_OVERVIEW = True
    
    async def execute(self) -> dict[str, Any]:
        """
        Generate AI-powered summary markdown report.
        
        Returns:
            Dictionary with:
            - markdown: Full markdown report
            - structured: JSON structured data for frontend
        """
        openai = OpenAIService()
        
        if not openai.is_configured:
            logger.warning("OpenAI not configured, using basic summary")
            return self._generate_basic_summary()
        
        # Extract comprehensive context
        scores = self._extract_scores()
        metadata = self._extract_metadata()
        content = self._extract_content()
        ai_indexing = self.overview_data.get("ai_indexing", {})
        issues = self.overview_data.get("issues", [])
        structured_data = self.overview_data.get("structured_data", {})
        
        # Format issues for prompt
        issues_text = "\n".join([
            f"- [{i.get('severity', 'unknown').upper()}] {i.get('message', '')}"
            for i in issues[:10]
        ]) or "No significant issues found."
        
        # Extract bot access
        bot_status = ai_indexing.get("robots_txt", {}).get("ai_bots_status", {})
        allowed_bots = [bot for bot, status in bot_status.items() if "allowed" in status.lower()]
        blocked_bots = [bot for bot, status in bot_status.items() if "blocked" in status.lower()]
        
        system_prompt = """You are a senior AI SEO strategist specializing in optimizing websites for AI assistant discoverability.
Your expertise spans all major AI platforms: ChatGPT/GPT-4, Claude, Gemini, Perplexity, Microsoft Copilot, Mistral, and others.
Analyze SEO reports and provide actionable, expert-level recommendations.
Return valid JSON only, no markdown formatting or code blocks."""

        keywords_list = [k.get('keyword', '') for k in content.get('keywords_frequency', [])[:8]]
        
        user_prompt = f"""Analyze this comprehensive SEO report and generate an AI discoverability improvement summary.

WEBSITE: {self.url}

CURRENT SCORES (0-100):
- Overall: {scores.get('overall', 0)}
- AI Readiness: {scores.get('ai_readiness', 0)}
- Content: {scores.get('content', 0)}
- Structured Data: {scores.get('structured_data', 0)}
- On-Page SEO: {scores.get('on_page', 0)}
- Technical: {scores.get('technical', 0)}

METADATA:
- Title: {(metadata.get('title') or {}).get('value', 'N/A')}
- Description: {(metadata.get('description') or {}).get('value', 'N/A')}
- Has Canonical: {bool(metadata.get('canonical'))}
- Language: {metadata.get('language', 'N/A')}

CONTENT ANALYSIS:
- Word Count: {content.get('word_count', 0)}
- Top Keywords: {', '.join(keywords_list)}
- Readability (Flesch): {content.get('readability', {}).get('flesch_reading_ease', 'N/A')}

STRUCTURED DATA:
- JSON-LD Schemas: {len(structured_data.get('json_ld', []))} found
- Has Open Graph: {bool(structured_data.get('open_graph'))}
- Has Twitter Card: {bool(structured_data.get('twitter_card'))}

AI BOT ACCESS:
- Has llms.txt: {ai_indexing.get('llms_txt', {}).get('present', False)}
- Has sitemap.xml: {ai_indexing.get('sitemap_xml', {}).get('present', False)}
- Allowed AI Bots: {', '.join(allowed_bots[:10]) if allowed_bots else 'None explicitly allowed'}
- Blocked AI Bots: {', '.join(blocked_bots) if blocked_bots else 'None blocked'}

CURRENT ISSUES:
{issues_text}

Generate a JSON response with this exact structure:

{{
  "overallAssessment": {{
    "rating": "Excellent|Good|Needs Improvement|Poor",
    "summary": "2-3 sentence executive summary of AI discoverability status",
    "primaryStrength": "The main thing this site does well for AI",
    "primaryWeakness": "The most critical improvement needed"
  }},
  "scoreBreakdown": [
    {{
      "category": "AI Readiness",
      "score": {scores.get('ai_readiness', 0)},
      "rating": "Excellent|Good|Fair|Poor",
      "explanation": "What this score means for AI discoverability",
      "improvement": "Specific action to improve this score"
    }},
    {{
      "category": "Content",
      "score": {scores.get('content', 0)},
      "rating": "Excellent|Good|Fair|Poor", 
      "explanation": "How content quality affects AI understanding",
      "improvement": "Content optimization suggestion"
    }},
    {{
      "category": "Rich Data",
      "score": {scores.get('structured_data', 0)},
      "rating": "Excellent|Good|Fair|Poor",
      "explanation": "Schema markup quality for AI extraction",
      "improvement": "Structured data recommendation"
    }},
    {{
      "category": "Structure",
      "score": {scores.get('on_page', 0)},
      "rating": "Excellent|Good|Fair|Poor",
      "explanation": "How headings and meta info help AI",
      "improvement": "On-page optimization tip"
    }},
    {{
      "category": "Technical",
      "score": {scores.get('technical', 0)},
      "rating": "Excellent|Good|Fair|Poor",
      "explanation": "Speed and security impact on AI crawling",
      "improvement": "Technical enhancement suggestion"
    }}
  ],
  "platformInsights": [
    {{
      "platform": "ChatGPT",
      "status": "Optimized|Partially Optimized|Needs Work",
      "tip": "Specific tip to improve discoverability on ChatGPT/OpenAI",
      "botName": "GPTBot"
    }},
    {{
      "platform": "Claude",
      "status": "Optimized|Partially Optimized|Needs Work",
      "tip": "Specific tip for Claude/Anthropic",
      "botName": "ClaudeBot"
    }},
    {{
      "platform": "Gemini",
      "status": "Optimized|Partially Optimized|Needs Work",
      "tip": "Specific tip for Google Gemini",
      "botName": "Google-Extended"
    }},
    {{
      "platform": "Perplexity",
      "status": "Optimized|Partially Optimized|Needs Work",
      "tip": "Specific tip for Perplexity AI search",
      "botName": "PerplexityBot"
    }},
    {{
      "platform": "Copilot",
      "status": "Optimized|Partially Optimized|Needs Work",
      "tip": "Specific tip for Microsoft Copilot",
      "botName": "bingbot"
    }},
    {{
      "platform": "Mistral",
      "status": "Optimized|Partially Optimized|Needs Work",
      "tip": "Specific tip for Mistral AI",
      "botName": "MistralBot"
    }}
  ],
  "prioritizedActions": [
    {{
      "priority": 1,
      "action": "Most important action to take",
      "impact": "High|Medium|Low",
      "effort": "Quick Win|Moderate|Significant",
      "category": "ai_readiness|content|structured_data|technical"
    }},
    {{
      "priority": 2,
      "action": "Second most important action",
      "impact": "High|Medium|Low",
      "effort": "Quick Win|Moderate|Significant",
      "category": "ai_readiness|content|structured_data|technical"
    }},
    {{
      "priority": 3,
      "action": "Third action",
      "impact": "High|Medium|Low",
      "effort": "Quick Win|Moderate|Significant",
      "category": "ai_readiness|content|structured_data|technical"
    }},
    {{
      "priority": 4,
      "action": "Fourth action",
      "impact": "High|Medium|Low",
      "effort": "Quick Win|Moderate|Significant",
      "category": "ai_readiness|content|structured_data|technical"
    }},
    {{
      "priority": 5,
      "action": "Fifth action",
      "impact": "High|Medium|Low",
      "effort": "Quick Win|Moderate|Significant",
      "category": "ai_readiness|content|structured_data|technical"
    }}
  ]
}}"""

        try:
            response = await openai.complete(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
            )
            
            if not response.get("success"):
                logger.error(f"OpenAI failed: {response.get('error')}")
                return self._generate_basic_summary()
            
            # Parse JSON response
            content_text = response.get("content", "{}")
            
            # Clean markdown code blocks if present
            if content_text.startswith("```"):
                lines = content_text.split("\n")
                content_text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            
            structured_data = json.loads(content_text)
            
            # Convert to markdown
            markdown = self._structured_to_markdown(structured_data)
            
            return {
                "markdown": markdown,
                "structured": structured_data,
                "success": True,
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            return self._generate_basic_summary()
        except Exception as e:
            logger.error(f"AI summary generation failed: {e}")
            return self._generate_basic_summary()
    
    def _structured_to_markdown(self, data: dict) -> str:
        """Convert structured data to markdown report."""
        lines = []
        
        # Overall Assessment
        overall = data.get("overallAssessment", {})
        rating = overall.get("rating", "Unknown")
        summary = overall.get("summary", "")
        strength = overall.get("primaryStrength", "")
        weakness = overall.get("primaryWeakness", "")
        
        lines.append(f"## AI Discoverability Report: {rating}")
        lines.append("")
        lines.append(summary)
        lines.append("")
        lines.append(f"**✅ Primary Strength:** {strength}")
        lines.append("")
        lines.append(f"**⚠️ Primary Weakness:** {weakness}")
        lines.append("")
        
        # Score Breakdown
        lines.append("## Score Breakdown")
        lines.append("")
        for score_item in data.get("scoreBreakdown", []):
            category = score_item.get("category", "")
            score = score_item.get("score", 0)
            rating = score_item.get("rating", "")
            explanation = score_item.get("explanation", "")
            improvement = score_item.get("improvement", "")
            
            lines.append(f"### {category}: {score}/100 ({rating})")
            lines.append("")
            lines.append(explanation)
            lines.append("")
            lines.append(f"**💡 Improvement:** {improvement}")
            lines.append("")
        
        # Platform Insights
        lines.append("## Platform-Specific Insights")
        lines.append("")
        for platform in data.get("platformInsights", []):
            name = platform.get("platform", "")
            status = platform.get("status", "")
            tip = platform.get("tip", "")
            
            status_emoji = "✅" if status == "Optimized" else "⚠️" if status == "Partially Optimized" else "❌"
            lines.append(f"### {name} {status_emoji}")
            lines.append("")
            lines.append(f"**Status:** {status}")
            lines.append("")
            lines.append(f"**Tip:** {tip}")
            lines.append("")
        
        # Prioritized Actions
        lines.append("## Prioritized Actions")
        lines.append("")
        for action in data.get("prioritizedActions", []):
            priority = action.get("priority", 0)
            action_text = action.get("action", "")
            impact = action.get("impact", "")
            effort = action.get("effort", "")
            
            impact_emoji = "🔥" if impact == "High" else "📈" if impact == "Medium" else "📉"
            lines.append(f"{priority}. **{action_text}**")
            lines.append(f"   - Impact: {impact_emoji} {impact}")
            lines.append(f"   - Effort: {effort}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_basic_summary(self) -> dict:
        """Generate basic summary without AI."""
        scores = self._extract_scores()
        overall = scores.get("overall", 0)
        
        rating = "Excellent" if overall >= 90 else "Good" if overall >= 70 else "Needs Improvement" if overall >= 50 else "Poor"
        
        markdown = f"""## AI Discoverability Report: {rating}

Your website scored **{overall}/100** for AI discoverability.

### Quick Summary
- **AI Readiness:** {scores.get('ai_readiness', 0)}/100
- **Content Quality:** {scores.get('content', 0)}/100
- **Structured Data:** {scores.get('structured_data', 0)}/100
- **Technical SEO:** {scores.get('technical', 0)}/100

### Next Steps
1. Review the detailed analysis
2. Focus on improving areas with lower scores
3. Implement structured data for better AI understanding
4. Create an llms.txt file for AI crawlers
"""
        
        return {
            "markdown": markdown,
            "structured": {
                "overallAssessment": {
                    "rating": rating,
                    "summary": f"Website scored {overall}/100 for AI discoverability.",
                },
                "scoreBreakdown": [],
                "platformInsights": [],
                "prioritizedActions": [],
            },
            "success": True,
        }
