"""
Analyzers package for SEO Analyzer.

Contains specialized analyzers:
- robots: Robots.txt parsing and AI bot detection
- html: HTML content and SEO analysis
"""

from .robots import RobotsParser
from .html import HTMLAnalyzer

__all__ = ["RobotsParser", "HTMLAnalyzer"]
