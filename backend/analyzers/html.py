"""
HTML content analyzer for SEO.

Analyzes HTML pages for SEO factors including meta tags, headings,
images, links, and structured data.
"""

import json
import re
from dataclasses import asdict
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from models.seo import (
    Issue,
    Recommendation,
    MetaTagAnalysis,
    HeadingAnalysis,
    ImageAnalysis,
    LinkAnalysis,
)
from utils.constants import (
    TITLE_MIN_LENGTH,
    TITLE_MAX_LENGTH,
    META_DESC_MIN_LENGTH,
    META_DESC_MAX_LENGTH,
)


class HTMLAnalyzer:
    """
    Analyze HTML content for SEO factors.
    
    Features:
    - Meta tag analysis (title, description, canonical, etc.)
    - Heading structure analysis (H1-H6)
    - Image optimization checks
    - Link analysis (internal, external, nofollow)
    - Structured data detection (JSON-LD, Open Graph, Twitter)
    
    Example:
        analyzer = HTMLAnalyzer(html_content, "https://example.com")
        meta = analyzer.analyze_meta_tags()
        headings = analyzer.analyze_headings()
    """
    
    def __init__(self, html: str, base_url: str):
        """
        Initialize with HTML content and base URL.
        
        Args:
            html: Raw HTML content
            base_url: Base URL for resolving relative links
        """
        self.soup = BeautifulSoup(html, 'lxml')
        self.base_url = base_url
        self.parsed_url = urlparse(base_url)
        self.issues: list[Issue] = []
        self.recommendations: list[Recommendation] = []
        
    def analyze_meta_tags(self) -> dict:
        """
        Analyze meta tags (title, description, etc.).
        
        Returns:
            Dictionary with analysis results for each meta tag
        """
        result = {}
        
        # Title tag
        result["title"] = self._analyze_title()
        
        # Meta description
        result["description"] = self._analyze_description()
        
        # Canonical URL
        canonical = self.soup.find('link', attrs={'rel': 'canonical'})
        result["canonical"] = canonical.get('href') if canonical else None
        if not canonical:
            self.issues.append(Issue(
                "medium", "technical", "CANONICAL_MISSING",
                "No canonical URL specified"
            ))
            self.recommendations.append(Recommendation(
                3, "technical",
                "Add a canonical URL to prevent duplicate content issues"
            ))
        
        # Robots meta
        robots_meta = self.soup.find('meta', attrs={'name': 'robots'})
        result["robots_meta"] = robots_meta.get('content') if robots_meta else None
        
        # Viewport
        viewport = self.soup.find('meta', attrs={'name': 'viewport'})
        result["viewport"] = viewport.get('content') if viewport else None
        if not viewport:
            self.issues.append(Issue(
                "high", "technical", "VIEWPORT_MISSING",
                "No viewport meta tag (page may not be mobile-friendly)"
            ))
            self.recommendations.append(Recommendation(
                1, "technical",
                "Add viewport meta tag for mobile responsiveness"
            ))
        
        # Language
        html_tag = self.soup.find('html')
        result["language"] = html_tag.get('lang') if html_tag else None
        if not result["language"]:
            self.issues.append(Issue(
                "low", "on_page", "LANG_MISSING",
                "HTML lang attribute not specified"
            ))
        
        # Keywords (legacy)
        keywords_meta = self.soup.find('meta', attrs={'name': 'keywords'})
        result["keywords_meta"] = keywords_meta.get('content') if keywords_meta else None
        
        return result
    
    def _analyze_title(self) -> dict:
        """Analyze the title tag."""
        title_tag = self.soup.find('title')
        title = title_tag.get_text().strip() if title_tag else None
        
        analysis = MetaTagAnalysis(
            value=title,
            length=len(title) if title else 0
        )
        
        if not title:
            analysis.issues.append("missing")
            analysis.recommendations.append("Add a title tag")
            self.issues.append(Issue(
                "high", "on_page", "TITLE_MISSING",
                "Page is missing a title tag"
            ))
            self.recommendations.append(Recommendation(
                1, "on_page",
                "Add a descriptive title tag (50-60 characters)"
            ))
        elif len(title) < TITLE_MIN_LENGTH:
            analysis.issues.append("too_short")
            analysis.recommendations.append("Expand title to 50-60 characters")
            self.issues.append(Issue(
                "medium", "on_page", "TITLE_TOO_SHORT",
                f"Title is only {len(title)} characters (recommended: 50-60)",
                f"<title>{title}</title>"
            ))
            self.recommendations.append(Recommendation(
                2, "on_page",
                "Expand title tag to 50-60 characters with primary keyword"
            ))
        elif len(title) > TITLE_MAX_LENGTH:
            analysis.issues.append("too_long")
            analysis.recommendations.append("Shorten title to under 60 characters")
            self.issues.append(Issue(
                "low", "on_page", "TITLE_TOO_LONG",
                f"Title is {len(title)} characters (may be truncated)",
                f"<title>{title}</title>"
            ))
            
        return asdict(analysis)
    
    def _analyze_description(self) -> dict:
        """Analyze the meta description."""
        meta_desc = self.soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '').strip() if meta_desc else None
        
        analysis = MetaTagAnalysis(
            value=description,
            length=len(description) if description else 0
        )
        
        if not description:
            analysis.issues.append("missing")
            analysis.recommendations.append("Add a meta description")
            self.issues.append(Issue(
                "high", "on_page", "META_DESC_MISSING",
                "Page is missing a meta description"
            ))
            self.recommendations.append(Recommendation(
                1, "on_page",
                "Add a compelling meta description (150-160 characters)"
            ))
        elif len(description) < META_DESC_MIN_LENGTH:
            analysis.issues.append("too_short")
            analysis.recommendations.append("Expand description to 150-160 characters")
            self.issues.append(Issue(
                "medium", "on_page", "META_DESC_TOO_SHORT",
                f"Meta description is only {len(description)} characters"
            ))
        elif len(description) > META_DESC_MAX_LENGTH:
            analysis.issues.append("too_long")
            analysis.recommendations.append("Shorten description to under 160 characters")
            self.issues.append(Issue(
                "low", "on_page", "META_DESC_TOO_LONG",
                f"Meta description is {len(description)} characters (may be truncated)"
            ))
            
        return asdict(analysis)
    
    def analyze_headings(self) -> dict:
        """
        Analyze heading structure (H1-H6).
        
        Returns:
            Dictionary with analysis for each heading level
        """
        result = {}
        
        for i in range(1, 7):
            tag = f"h{i}"
            headings = self.soup.find_all(tag)
            result[tag] = HeadingAnalysis(
                count=len(headings),
                values=[h.get_text().strip()[:100] for h in headings[:10]]
            )
        
        # Check H1
        h1_count = result["h1"].count
        if h1_count == 0:
            result["h1"].issues.append("missing")
            self.issues.append(Issue(
                "high", "on_page", "H1_MISSING",
                "Page is missing an H1 tag"
            ))
            self.recommendations.append(Recommendation(
                1, "on_page",
                "Add a single H1 tag with primary keyword"
            ))
        elif h1_count > 1:
            result["h1"].issues.append("multiple")
            self.issues.append(Issue(
                "medium", "on_page", "MULTIPLE_H1",
                f"Page has {h1_count} H1 tags (should have exactly 1)"
            ))
            self.recommendations.append(Recommendation(
                2, "on_page",
                "Consolidate to a single H1 tag"
            ))
        
        # Check heading hierarchy
        result["hierarchy_valid"] = self._check_heading_hierarchy()
        if not result["hierarchy_valid"]:
            self.issues.append(Issue(
                "low", "on_page", "HEADING_HIERARCHY",
                "Heading hierarchy is not properly structured (skipped levels)"
            ))
            
        return {
            k: asdict(v) if isinstance(v, HeadingAnalysis) else v
            for k, v in result.items()
        }
    
    def _check_heading_hierarchy(self) -> bool:
        """Check if heading hierarchy is valid (no skipped levels)."""
        headings = self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if not headings:
            return True
            
        levels = [int(h.name[1]) for h in headings]
        
        for i in range(1, len(levels)):
            if levels[i] > levels[i-1] + 1:
                return False
                
        return True
    
    def analyze_images(self) -> dict:
        """
        Analyze images for alt text and optimization.
        
        Returns:
            Dictionary with image analysis results
        """
        images = self.soup.find_all('img')
        
        missing_alt = []
        lazy_count = 0
        
        for img in images:
            src = img.get('src', img.get('data-src', ''))
            alt = img.get('alt')
            
            if alt is None or alt.strip() == '':
                missing_alt.append(src[:100] if src else 'unknown')
                
            if img.get('loading') == 'lazy':
                lazy_count += 1
        
        result = ImageAnalysis(
            total=len(images),
            missing_alt=len(missing_alt),
            missing_alt_urls=missing_alt[:10],
            lazy_loading_count=lazy_count
        )
        
        if missing_alt:
            result.issues.append(f"{len(missing_alt)} images missing alt text")
            self.issues.append(Issue(
                "medium", "on_page", "MISSING_ALT",
                f"{len(missing_alt)} images are missing alt text",
                str(missing_alt[:3])
            ))
            self.recommendations.append(Recommendation(
                2, "on_page",
                f"Add descriptive alt text to {len(missing_alt)} images"
            ))
        
        return asdict(result)
    
    def analyze_links(self) -> dict:
        """
        Analyze internal and external links.
        
        Returns:
            Dictionary with link analysis results
        """
        links = self.soup.find_all('a', href=True)
        
        internal = []
        external = []
        nofollow = 0
        
        for link in links:
            href = link.get('href', '')
            rel = link.get('rel', [])
            
            if isinstance(rel, str):
                rel = [rel]
            
            # Skip anchors, javascript, mailto
            if (href.startswith('#') or 
                href.startswith('javascript:') or 
                href.startswith('mailto:')):
                continue
            
            # Determine if internal or external
            full_url = urljoin(self.base_url, href)
            parsed = urlparse(full_url)
            
            if parsed.netloc == self.parsed_url.netloc:
                internal.append(href)
            else:
                external.append(href)
                if 'nofollow' in rel:
                    nofollow += 1
        
        result = LinkAnalysis(
            internal_count=len(internal),
            external_count=len(external),
            nofollow_count=nofollow
        )
        
        if len(internal) == 0:
            self.issues.append(Issue(
                "medium", "on_page", "NO_INTERNAL_LINKS",
                "Page has no internal links"
            ))
            self.recommendations.append(Recommendation(
                3, "on_page",
                "Add internal links to related content"
            ))
        
        return asdict(result)
    
    def analyze_structured_data(self) -> dict:
        """
        Analyze Schema.org and social meta tags.
        
        Returns:
            Dictionary with structured data analysis
        """
        result = {
            "json_ld": [],
            "microdata": False,
            "rdfa": False,
            "open_graph": {},
            "twitter_card": {}
        }
        
        # JSON-LD
        scripts = self.soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                schema_type = data.get('@type', 'Unknown')
                if isinstance(schema_type, list):
                    schema_type = ', '.join(schema_type)
                result["json_ld"].append({
                    "type": schema_type,
                    "valid": True
                })
            except (json.JSONDecodeError, TypeError):
                result["json_ld"].append({"type": "Invalid JSON", "valid": False})
        
        if not result["json_ld"]:
            self.issues.append(Issue(
                "medium", "structured_data", "NO_SCHEMA",
                "No JSON-LD structured data found"
            ))
            self.recommendations.append(Recommendation(
                3, "structured_data",
                "Add Schema.org JSON-LD markup (Organization, Article, FAQ, etc.)"
            ))
        
        # Microdata
        result["microdata"] = bool(self.soup.find(attrs={'itemscope': True}))
        
        # RDFa
        result["rdfa"] = bool(self.soup.find(attrs={'typeof': True}))
        
        # Open Graph
        og_tags = self.soup.find_all('meta', property=re.compile('^og:'))
        for tag in og_tags:
            prop = tag.get('property', '').replace('og:', '')
            result["open_graph"][prop] = tag.get('content', '')[:200]
        
        if not result["open_graph"]:
            self.issues.append(Issue(
                "medium", "structured_data", "NO_OG",
                "No Open Graph tags found"
            ))
            self.recommendations.append(Recommendation(
                3, "structured_data",
                "Add Open Graph tags for better social sharing"
            ))
        elif 'image' not in result["open_graph"]:
            self.issues.append(Issue(
                "low", "structured_data", "OG_NO_IMAGE",
                "Open Graph image tag is missing"
            ))
        
        # Twitter Card
        twitter_tags = self.soup.find_all('meta', attrs={'name': re.compile('^twitter:')})
        for tag in twitter_tags:
            prop = tag.get('name', '').replace('twitter:', '')
            result["twitter_card"][prop] = tag.get('content', '')[:200]
        
        if not result["twitter_card"]:
            self.issues.append(Issue(
                "low", "structured_data", "NO_TWITTER_CARD",
                "No Twitter Card tags found"
            ))
        
        return result
    
    def extract_text_content(self) -> str:
        """
        Extract main text content from page.
        
        Returns:
            Cleaned text content from the main content area
        """
        # Create a fresh soup to avoid modifying the original
        soup_copy = BeautifulSoup(str(self.soup), 'lxml')
        
        # Remove script and style elements
        for element in soup_copy(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Try to find main content area
        main_content = (
            soup_copy.find('main') or 
            soup_copy.find('article') or 
            soup_copy.find(id='content') or
            soup_copy.find(class_='content') or
            soup_copy.find('body')
        )
        
        if main_content:
            return main_content.get_text(separator=' ', strip=True)
        
        return soup_copy.get_text(separator=' ', strip=True)
