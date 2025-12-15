"""
SEO data models.

Dataclasses for structured SEO analysis data.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Issue:
    """
    Represents an SEO issue found during analysis.
    
    Attributes:
        severity: Issue severity level (high, medium, low)
        category: Issue category (technical, on_page, content, ai_indexing, structured_data)
        code: Unique issue code for programmatic handling
        message: Human-readable issue description
        element: Optional HTML element related to the issue
    """
    severity: str  # high, medium, low
    category: str  # technical, on_page, content, ai_indexing, structured_data
    code: str
    message: str
    element: Optional[str] = None


@dataclass
class Recommendation:
    """
    Represents an SEO improvement recommendation.
    
    Attributes:
        priority: Priority level (1 = highest)
        category: Recommendation category
        action: Actionable recommendation text
    """
    priority: int
    category: str
    action: str


@dataclass
class MetaTagAnalysis:
    """
    Analysis result for a meta tag.
    
    Attributes:
        value: The meta tag value (or None if missing)
        length: Character length of the value
        issues: List of issue codes
        recommendations: List of recommendation texts
    """
    value: Optional[str] = None
    length: int = 0
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class HeadingAnalysis:
    """
    Analysis result for heading tags (H1-H6).
    
    Attributes:
        count: Number of headings found
        values: List of heading text values
        issues: List of issue codes
    """
    count: int = 0
    values: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


@dataclass
class ImageAnalysis:
    """
    Analysis result for images.
    
    Attributes:
        total: Total number of images
        missing_alt: Count of images missing alt text
        missing_alt_urls: URLs of images missing alt text
        lazy_loading_count: Images with lazy loading enabled
        issues: List of issue descriptions
    """
    total: int = 0
    missing_alt: int = 0
    missing_alt_urls: list[str] = field(default_factory=list)
    lazy_loading_count: int = 0
    issues: list[str] = field(default_factory=list)


@dataclass
class LinkAnalysis:
    """
    Analysis result for page links.
    
    Attributes:
        internal_count: Number of internal links
        external_count: Number of external links
        nofollow_count: Number of nofollow links
        broken_count: Number of broken links
        broken_urls: List of broken link URLs
    """
    internal_count: int = 0
    external_count: int = 0
    nofollow_count: int = 0
    broken_count: int = 0
    broken_urls: list[str] = field(default_factory=list)
