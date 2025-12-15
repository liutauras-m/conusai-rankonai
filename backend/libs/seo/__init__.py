"""
SEO Analysis Library.

Provides SEO and AI indexing analysis capabilities.

Usage:
    from libs.seo import SEOAnalyzer
    
    analyzer = SEOAnalyzer("https://example.com")
    result = await analyzer.analyze()
"""

from .analyzer import SEOAnalyzer
from .scoring import ScoreCalculator

__all__ = ["SEOAnalyzer", "ScoreCalculator"]
