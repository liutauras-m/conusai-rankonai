"""
Utilities package for SEO Analyzer.

Contains reusable components:
- http: Async HTTP fetcher with multiple backends
- text: Text analysis and keyword extraction
- constants: Shared constants and configurations
"""

from .http import (
    AsyncFetcher,
    FetcherBackend,
    BaseFetcher,
    AiohttpFetcher,
    HttpxFetcher,
    CurlCffiFetcher,
    PlaywrightFetcher,
    BROWSER_HEADERS,
)
from .text import ContentAnalyzer
from .constants import AI_BOTS
from .language import LanguageDetector, get_language_context_for_ai

__all__ = [
    # HTTP fetchers
    "AsyncFetcher",
    "FetcherBackend",
    "BaseFetcher",
    "AiohttpFetcher",
    "HttpxFetcher",
    "CurlCffiFetcher",
    "PlaywrightFetcher",
    "BROWSER_HEADERS",
    # Text analysis
    "ContentAnalyzer",
    # Language detection
    "LanguageDetector",
    "get_language_context_for_ai",
    # Constants
    "AI_BOTS",
]
