"""
Signals Task - AI Platform Visibility & Performance Metrics

Extracts and analyzes signals that affect AI discoverability:
- AI platform visibility signals (bot access, llms.txt, etc.)
- Performance metrics (load time, mobile-friendliness)
- Custom logic for AI optimization signals
"""

import logging
from typing import Any

from tasks.base import WorkflowTask

logger = logging.getLogger(__name__)


class SignalsTask(WorkflowTask):
    """
    Signals task - extracts AI visibility and performance signals.
    
    Consolidates signals from multiple sources:
    1. AI Platform Visibility - How AI bots can access the site
    2. Performance Metrics - Speed and mobile optimization
    3. Content Signals - Structured data, semantic markup
    4. Authority Signals - Domain trust indicators
    """
    
    TASK_NAME = "signals"
    REQUIRES_OVERVIEW = True
    
    async def execute(self) -> dict[str, Any]:
        """
        Extract and analyze visibility signals.
        
        Returns:
            Dictionary with categorized signals:
            - ai_visibility: AI bot access status
            - performance: Speed and mobile metrics
            - content_signals: Semantic and structural indicators
            - authority: Trust and authority signals
            - recommendations: Signal-specific improvements
        """
        return {
            "ai_visibility": self._extract_ai_visibility_signals(),
            "performance": self._extract_performance_signals(),
            "content_signals": self._extract_content_signals(),
            "authority": self._extract_authority_signals(),
            "summary": self._generate_signals_summary(),
            "recommendations": self._generate_signal_recommendations(),
        }
    
    def _extract_ai_visibility_signals(self) -> dict[str, Any]:
        """Extract AI platform visibility signals."""
        ai_indexing = self.overview_data.get("ai_indexing", {})
        robots = ai_indexing.get("robots_txt", {})
        
        # Bot status extraction
        bot_status = robots.get("ai_bots_status", {})
        
        # Categorize bots
        allowed_bots = []
        blocked_bots = []
        unknown_bots = []
        
        for bot, status in bot_status.items():
            status_lower = str(status).lower()
            if "allowed" in status_lower or "not blocked" in status_lower:
                allowed_bots.append(bot)
            elif "blocked" in status_lower or "disallowed" in status_lower:
                blocked_bots.append(bot)
            else:
                unknown_bots.append(bot)
        
        # llms.txt presence
        llms_txt = ai_indexing.get("llms_txt", {})
        llms_present = llms_txt.get("present", False)
        llms_content = llms_txt.get("content", "")
        
        # Sitemap presence
        sitemap = ai_indexing.get("sitemap_xml", {})
        sitemap_present = sitemap.get("present", False)
        sitemap_urls = sitemap.get("url_count", 0)
        
        return {
            "robots_txt": {
                "present": robots.get("present", False),
                "allows_indexing": robots.get("allows_indexing", True),
            },
            "ai_bots": {
                "allowed": allowed_bots,
                "blocked": blocked_bots,
                "unknown": unknown_bots,
                "total_checked": len(bot_status),
            },
            "llms_txt": {
                "present": llms_present,
                "has_content": bool(llms_content),
                "content_preview": llms_content[:200] if llms_content else None,
            },
            "sitemap": {
                "present": sitemap_present,
                "url_count": sitemap_urls,
            },
            "score": self._calculate_visibility_score(
                allowed_bots, blocked_bots, llms_present, sitemap_present
            ),
        }
    
    def _extract_performance_signals(self) -> dict[str, Any]:
        """Extract performance-related signals."""
        metadata = self._extract_metadata()
        content = self._extract_content()
        
        # Extract what we have from overview
        # viewport can be a string or dict depending on analyzer version
        viewport_raw = metadata.get("viewport", None)
        if isinstance(viewport_raw, dict):
            viewport_present = viewport_raw.get("present", False)
            viewport_value = viewport_raw.get("value")
        elif isinstance(viewport_raw, str):
            viewport_present = True
            viewport_value = viewport_raw
        else:
            viewport_present = False
            viewport_value = None
        
        return {
            "mobile_friendly": {
                "has_viewport": viewport_present,
                "viewport_value": viewport_value,
            },
            "content_size": {
                "word_count": content.get("word_count", 0),
                "is_substantial": content.get("word_count", 0) >= 300,
            },
            "page_structure": {
                "has_h1": bool(metadata.get("h1", {}).get("value")),
                "heading_count": len(content.get("headings", [])),
            },
            "score": self._calculate_performance_score(content, metadata),
        }
    
    def _extract_content_signals(self) -> dict[str, Any]:
        """Extract content and semantic signals."""
        content = self._extract_content()
        structured_data = self.overview_data.get("structured_data", {})
        metadata = self._extract_metadata()
        
        # JSON-LD schemas
        json_ld = structured_data.get("json_ld", [])
        schema_types = [s.get("@type", "Unknown") for s in json_ld]
        
        # OpenGraph
        og_data = structured_data.get("open_graph", {})
        
        # Twitter Card
        twitter_data = structured_data.get("twitter_card", {})
        
        # Readability
        readability = content.get("readability", {})
        
        return {
            "structured_data": {
                "json_ld_present": len(json_ld) > 0,
                "schema_types": schema_types,
                "schema_count": len(json_ld),
            },
            "social_meta": {
                "open_graph": bool(og_data),
                "twitter_card": bool(twitter_data),
                "og_type": og_data.get("og:type") if og_data else None,
            },
            "readability": {
                "flesch_score": readability.get("flesch_reading_ease"),
                "grade_level": readability.get("flesch_kincaid_grade"),
                "is_accessible": (readability.get("flesch_reading_ease") or 0) >= 60,
            },
            "semantic": {
                "has_canonical": bool((metadata.get("canonical") or {}).get("value")),
                "has_lang": bool(metadata.get("language")),
                "language": metadata.get("language"),
            },
            "score": self._calculate_content_signals_score(
                json_ld, og_data, twitter_data, readability
            ),
        }
    
    def _extract_authority_signals(self) -> dict[str, Any]:
        """Extract authority and trust signals."""
        metadata = self._extract_metadata()
        structured_data = self.overview_data.get("structured_data", {})
        
        # Check for organization schema
        json_ld = structured_data.get("json_ld", [])
        has_org_schema = any(
            s.get("@type") in ("Organization", "LocalBusiness", "Corporation")
            for s in json_ld
        )
        
        # Check for author/person schema
        has_author_schema = any(
            s.get("@type") == "Person" or s.get("author")
            for s in json_ld
        )
        
        return {
            "brand_identity": {
                "has_title": bool(metadata.get("title", {}).get("value")),
                "has_description": bool(metadata.get("description", {}).get("value")),
                "has_organization_schema": has_org_schema,
            },
            "authorship": {
                "has_author_info": has_author_schema,
            },
            "trust_indicators": {
                "uses_https": self.url.startswith("https://"),
                "has_contact_schema": any(
                    s.get("@type") == "ContactPoint" for s in json_ld
                ),
            },
            "score": self._calculate_authority_score(
                metadata, has_org_schema, has_author_schema
            ),
        }
    
    def _calculate_visibility_score(
        self, 
        allowed: list, 
        blocked: list, 
        llms: bool, 
        sitemap: bool,
    ) -> int:
        """Calculate AI visibility score (0-100)."""
        score = 50  # Base score
        
        # Penalize blocked bots
        score -= len(blocked) * 10
        
        # Reward allowed bots
        score += min(len(allowed) * 5, 20)
        
        # Reward llms.txt
        if llms:
            score += 15
        
        # Reward sitemap
        if sitemap:
            score += 10
        
        return max(0, min(100, score))
    
    def _calculate_performance_score(self, content: dict, metadata: dict) -> int:
        """Calculate performance score (0-100)."""
        score = 50
        
        word_count = content.get("word_count", 0)
        if word_count >= 1000:
            score += 20
        elif word_count >= 500:
            score += 10
        elif word_count < 200:
            score -= 10
        
        # viewport can be string or dict
        viewport = metadata.get("viewport")
        if viewport:
            score += 15
        
        if metadata.get("h1", {}).get("value"):
            score += 15
        
        return max(0, min(100, score))
    
    def _calculate_content_signals_score(
        self, 
        json_ld: list, 
        og: dict, 
        twitter: dict, 
        readability: dict,
    ) -> int:
        """Calculate content signals score (0-100)."""
        score = 40
        
        # Structured data
        score += min(len(json_ld) * 10, 25)
        
        # Social meta
        if og:
            score += 10
        if twitter:
            score += 10
        
        # Readability
        flesch = readability.get("flesch_reading_ease", 0)
        if flesch >= 60:
            score += 15
        elif flesch >= 40:
            score += 5
        
        return max(0, min(100, score))
    
    def _calculate_authority_score(
        self, 
        metadata: dict, 
        has_org: bool, 
        has_author: bool,
    ) -> int:
        """Calculate authority score (0-100)."""
        score = 30
        
        if metadata.get("title", {}).get("value"):
            score += 15
        
        if metadata.get("description", {}).get("value"):
            score += 15
        
        if has_org:
            score += 20
        
        if has_author:
            score += 10
        
        if self.url.startswith("https://"):
            score += 10
        
        return max(0, min(100, score))
    
    def _generate_signals_summary(self) -> dict:
        """Generate overall signals summary."""
        scores = self._extract_scores()
        
        return {
            "overall_ai_readiness": scores.get("ai_readiness", 0),
            "strengths": self._identify_strengths(),
            "weaknesses": self._identify_weaknesses(),
        }
    
    def _identify_strengths(self) -> list[str]:
        """Identify signal strengths."""
        strengths = []
        scores = self._extract_scores()
        
        if scores.get("technical", 0) >= 80:
            strengths.append("Strong technical SEO foundation")
        if scores.get("content", 0) >= 80:
            strengths.append("High-quality content")
        if scores.get("structured_data", 0) >= 70:
            strengths.append("Good structured data implementation")
        
        return strengths
    
    def _identify_weaknesses(self) -> list[str]:
        """Identify signal weaknesses."""
        weaknesses = []
        scores = self._extract_scores()
        
        if scores.get("ai_readiness", 0) < 50:
            weaknesses.append("Low AI readiness score")
        if scores.get("structured_data", 0) < 50:
            weaknesses.append("Missing structured data")
        if scores.get("content", 0) < 50:
            weaknesses.append("Content needs improvement")
        
        return weaknesses
    
    def _generate_signal_recommendations(self) -> list[dict]:
        """Generate signal-specific recommendations."""
        recommendations = []
        
        ai_indexing = self.overview_data.get("ai_indexing", {})
        
        # Check llms.txt
        if not ai_indexing.get("llms_txt", {}).get("present"):
            recommendations.append({
                "category": "ai_visibility",
                "priority": "high",
                "title": "Create llms.txt file",
                "description": "Add an llms.txt file to help AI assistants understand your content.",
            })
        
        # Check structured data
        structured = self.overview_data.get("structured_data", {})
        if not structured.get("json_ld"):
            recommendations.append({
                "category": "content_signals",
                "priority": "high",
                "title": "Add JSON-LD structured data",
                "description": "Implement Schema.org markup to help AI understand your content.",
            })
        
        # Check bot access
        robots = ai_indexing.get("robots_txt", {})
        bot_status = robots.get("ai_bots_status", {})
        blocked = [b for b, s in bot_status.items() if "blocked" in str(s).lower()]
        if blocked:
            recommendations.append({
                "category": "ai_visibility",
                "priority": "medium",
                "title": f"Review blocked AI bots: {', '.join(blocked)}",
                "description": "Consider allowing AI bots to improve discoverability.",
            })
        
        return recommendations
