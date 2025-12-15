"""
Result Builder for SEO Analysis.

Assembles the final analysis result dictionary.
"""

from dataclasses import asdict
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from analyzers import HTMLAnalyzer, RobotsParser
    from utils import ContentAnalyzer


class ResultBuilder:
    """
    Build the final analysis result dictionary.
    
    Assembles data from various analyzers into a structured result.
    """
    
    def __init__(self, url: str, parsed_url):
        """
        Initialize the builder.
        
        Args:
            url: The analyzed URL
            parsed_url: Parsed URL object
        """
        self.url = url
        self.parsed_url = parsed_url
    
    def build(
        self,
        html_analyzer: "HTMLAnalyzer",
        content_analyzer: "ContentAnalyzer",
        robots_parser: "RobotsParser",
        main_response: dict,
        robots_response: dict,
        llms_response: dict,
        sitemap_response: dict,
        scores: dict,
        start_time: datetime,
    ) -> dict:
        """
        Build the complete analysis result.
        
        Returns:
            Complete analysis result dictionary
        """
        # Get Content-Language header for language detection
        content_language = main_response["headers"].get("Content-Language")
        
        return {
            "url": self.url,
            "timestamp": datetime.now().isoformat(),
            "crawl_time_ms": round(
                (datetime.now() - start_time).total_seconds() * 1000
            ),
            "scores": scores,
            "metadata": html_analyzer.analyze_meta_tags(),
            "language": html_analyzer.analyze_language(content_language),
            "headings": html_analyzer.analyze_headings(),
            "images": html_analyzer.analyze_images(),
            "links": html_analyzer.analyze_links(),
            "content": self._build_content_section(content_analyzer),
            "structured_data": html_analyzer.analyze_structured_data(),
            "social": html_analyzer.analyze_social_metadata(),
            "technical": self._build_technical_section(main_response),
            "ai_indexing": self._build_ai_indexing_section(
                robots_parser, robots_response, llms_response, sitemap_response
            ),
            "issues": [asdict(issue) for issue in html_analyzer.issues],
            "recommendations": [
                asdict(rec) 
                for rec in sorted(
                    html_analyzer.recommendations, 
                    key=lambda x: x.priority
                )
            ],
        }
    
    def _build_content_section(self, content_analyzer: "ContentAnalyzer") -> dict:
        """Build the content analysis section."""
        return {
            "word_count": content_analyzer.get_word_count(),
            "readability": content_analyzer.get_readability(),
            "keywords_tfidf": content_analyzer.extract_keywords_tfidf(top_n=15),
            "keywords_frequency": content_analyzer.extract_keywords_simple(top_n=15),
            "top_bigrams": content_analyzer.extract_phrases(n=2, top_k=10),
            "top_trigrams": content_analyzer.extract_phrases(n=3, top_k=10),
        }
    
    def _build_technical_section(self, main_response: dict) -> dict:
        """Build the technical analysis section."""
        return {
            "https": self.parsed_url.scheme == 'https',
            "response_time_ms": round(main_response["response_time_ms"]),
            "content_type": main_response["headers"].get("Content-Type", ""),
            "content_encoding": main_response["headers"].get("Content-Encoding", "none"),
            "server": main_response["headers"].get("Server", ""),
            "x_frame_options": main_response["headers"].get("X-Frame-Options", ""),
            "content_security_policy": "Content-Security-Policy" in main_response["headers"],
        }
    
    def _build_ai_indexing_section(
        self,
        robots_parser: "RobotsParser",
        robots_response: dict,
        llms_response: dict,
        sitemap_response: dict,
    ) -> dict:
        """Build the AI indexing section."""
        return {
            "robots_txt": {
                "present": robots_response.get("status") == 200,
                "ai_bots_status": robots_parser.get_ai_bot_status(),
                "sitemaps_declared": robots_parser.get_sitemap_urls(),
            },
            "llms_txt": {
                "present": llms_response.get("status") == 200,
                "content_preview": (
                    (llms_response["content"][:500] + "...") 
                    if llms_response.get("content") else None
                ),
            },
            "sitemap_xml": {
                "present": sitemap_response.get("status") == 200,
            },
        }
