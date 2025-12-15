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
from utils.language import LanguageDetector


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
            result["open_graph"][prop] = tag.get('content', '')[:500]
        
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
            result["twitter_card"][prop] = tag.get('content', '')[:500]
        
        if not result["twitter_card"]:
            self.issues.append(Issue(
                "low", "structured_data", "NO_TWITTER_CARD",
                "No Twitter Card tags found"
            ))
        
        return result
    
    def analyze_social_metadata(self) -> dict:
        """
        Comprehensive social sharing metadata analysis.
        
        Extracts and validates all social sharing metadata including:
        - Open Graph (Facebook, LinkedIn, WhatsApp)
        - Twitter Card
        - Social images with dimensions
        - Platform-specific requirements
        
        Returns:
            Dictionary with detailed social metadata analysis:
            - open_graph: Full OG tag analysis with validation
            - twitter_card: Twitter Card analysis with validation
            - social_images: List of detected social images
            - platform_compatibility: Compatibility scores per platform
            - issues: Social-specific SEO issues
            - score: Overall social sharing readiness score
        """
        result = {
            "open_graph": self._analyze_open_graph_detailed(),
            "twitter_card": self._analyze_twitter_card_detailed(),
            "social_images": [],
            "platform_compatibility": {},
            "issues": [],
            "score": 100,
        }
        
        # Collect all social images
        result["social_images"] = self._collect_social_images(result)
        
        # Calculate platform compatibility
        result["platform_compatibility"] = self._calculate_platform_compatibility(result)
        
        # Calculate overall score
        result["score"] = self._calculate_social_score(result)
        
        return result
    
    def _analyze_open_graph_detailed(self) -> dict:
        """Analyze Open Graph tags in detail."""
        og_data = {
            "present": False,
            "tags": {},
            "missing_required": [],
            "missing_recommended": [],
            "issues": [],
        }
        
        # Required OG tags
        required_tags = ["title", "type", "url", "image"]
        # Recommended OG tags
        recommended_tags = ["description", "site_name", "locale"]
        # Image-related tags
        image_tags = ["image:width", "image:height", "image:alt", "image:type"]
        
        # Extract all OG tags
        og_meta = self.soup.find_all('meta', property=re.compile('^og:'))
        for tag in og_meta:
            prop = tag.get('property', '').replace('og:', '')
            content = tag.get('content', '')
            og_data["tags"][prop] = content
        
        og_data["present"] = len(og_data["tags"]) > 0
        
        # Check required tags
        for req in required_tags:
            if req not in og_data["tags"] or not og_data["tags"][req]:
                og_data["missing_required"].append(req)
                og_data["issues"].append({
                    "code": f"OG_MISSING_{req.upper()}",
                    "severity": "high" if req in ["title", "image"] else "medium",
                    "message": f"Missing required Open Graph tag: og:{req}",
                })
        
        # Check recommended tags
        for rec in recommended_tags:
            if rec not in og_data["tags"] or not og_data["tags"][rec]:
                og_data["missing_recommended"].append(rec)
        
        # Validate og:title length (should be 40-60 chars)
        if "title" in og_data["tags"]:
            title_len = len(og_data["tags"]["title"])
            if title_len > 90:
                og_data["issues"].append({
                    "code": "OG_TITLE_TOO_LONG",
                    "severity": "low",
                    "message": f"og:title is {title_len} chars (recommended: under 60)",
                })
        
        # Validate og:description length (should be 100-200 chars)
        if "description" in og_data["tags"]:
            desc_len = len(og_data["tags"]["description"])
            if desc_len > 300:
                og_data["issues"].append({
                    "code": "OG_DESC_TOO_LONG",
                    "severity": "low",
                    "message": f"og:description is {desc_len} chars (recommended: under 200)",
                })
        
        # Check image dimensions
        has_image_dimensions = (
            "image:width" in og_data["tags"] and 
            "image:height" in og_data["tags"]
        )
        if "image" in og_data["tags"] and not has_image_dimensions:
            og_data["issues"].append({
                "code": "OG_IMAGE_NO_DIMENSIONS",
                "severity": "low",
                "message": "og:image dimensions not specified (add og:image:width and og:image:height)",
            })
        
        return og_data
    
    def _analyze_twitter_card_detailed(self) -> dict:
        """Analyze Twitter Card tags in detail."""
        twitter_data = {
            "present": False,
            "card_type": None,
            "tags": {},
            "missing_required": [],
            "missing_recommended": [],
            "issues": [],
        }
        
        # Required tags (depends on card type)
        base_required = ["card", "title"]
        recommended_tags = ["description", "image", "site", "creator"]
        
        # Extract all Twitter tags
        twitter_meta = self.soup.find_all('meta', attrs={'name': re.compile('^twitter:')})
        for tag in twitter_meta:
            prop = tag.get('name', '').replace('twitter:', '')
            content = tag.get('content', '')
            twitter_data["tags"][prop] = content
        
        twitter_data["present"] = len(twitter_data["tags"]) > 0
        twitter_data["card_type"] = twitter_data["tags"].get("card", "summary")
        
        # Check required tags
        for req in base_required:
            if req not in twitter_data["tags"] or not twitter_data["tags"][req]:
                twitter_data["missing_required"].append(req)
                twitter_data["issues"].append({
                    "code": f"TWITTER_MISSING_{req.upper()}",
                    "severity": "medium",
                    "message": f"Missing Twitter Card tag: twitter:{req}",
                })
        
        # For summary_large_image, image is required
        if twitter_data["card_type"] == "summary_large_image":
            if "image" not in twitter_data["tags"]:
                twitter_data["missing_required"].append("image")
                twitter_data["issues"].append({
                    "code": "TWITTER_LARGE_IMAGE_MISSING",
                    "severity": "high",
                    "message": "summary_large_image card requires twitter:image",
                })
        
        # Check recommended tags
        for rec in recommended_tags:
            if rec not in twitter_data["tags"] or not twitter_data["tags"][rec]:
                twitter_data["missing_recommended"].append(rec)
        
        # Validate title length (should be under 70 chars)
        if "title" in twitter_data["tags"]:
            title_len = len(twitter_data["tags"]["title"])
            if title_len > 70:
                twitter_data["issues"].append({
                    "code": "TWITTER_TITLE_TOO_LONG",
                    "severity": "low",
                    "message": f"twitter:title is {title_len} chars (max: 70)",
                })
        
        # Validate description length (should be under 200 chars)
        if "description" in twitter_data["tags"]:
            desc_len = len(twitter_data["tags"]["description"])
            if desc_len > 200:
                twitter_data["issues"].append({
                    "code": "TWITTER_DESC_TOO_LONG",
                    "severity": "low",
                    "message": f"twitter:description is {desc_len} chars (max: 200)",
                })
        
        return twitter_data
    
    def _collect_social_images(self, social_data: dict) -> list[dict]:
        """Collect all social sharing images."""
        images = []
        seen_urls = set()
        
        # OG image
        og_image = social_data["open_graph"]["tags"].get("image")
        if og_image and og_image not in seen_urls:
            seen_urls.add(og_image)
            images.append({
                "url": og_image,
                "source": "og:image",
                "width": social_data["open_graph"]["tags"].get("image:width"),
                "height": social_data["open_graph"]["tags"].get("image:height"),
                "alt": social_data["open_graph"]["tags"].get("image:alt"),
                "type": social_data["open_graph"]["tags"].get("image:type"),
            })
        
        # Additional OG images (og:image can appear multiple times)
        for i in range(1, 5):
            key = f"image:{i}" if i > 0 else "image"
            # Check for numbered images in tags
            pass  # OG typically uses same key for multiple images
        
        # Twitter image
        twitter_image = social_data["twitter_card"]["tags"].get("image")
        if twitter_image and twitter_image not in seen_urls:
            seen_urls.add(twitter_image)
            images.append({
                "url": twitter_image,
                "source": "twitter:image",
                "width": social_data["twitter_card"]["tags"].get("image:width"),
                "height": social_data["twitter_card"]["tags"].get("image:height"),
                "alt": social_data["twitter_card"]["tags"].get("image:alt"),
            })
        
        return images
    
    def _calculate_platform_compatibility(self, social_data: dict) -> dict:
        """Calculate compatibility scores for each platform."""
        og = social_data["open_graph"]
        twitter = social_data["twitter_card"]
        
        platforms = {
            "facebook": {
                "score": 100,
                "status": "optimal",
                "issues": [],
            },
            "twitter": {
                "score": 100,
                "status": "optimal",
                "issues": [],
            },
            "linkedin": {
                "score": 100,
                "status": "optimal",
                "issues": [],
            },
            "whatsapp": {
                "score": 100,
                "status": "optimal",
                "issues": [],
            },
            "slack": {
                "score": 100,
                "status": "optimal",
                "issues": [],
            },
        }
        
        # Facebook - requires OG tags
        if not og["present"]:
            platforms["facebook"]["score"] -= 50
            platforms["facebook"]["issues"].append("Missing Open Graph tags")
        else:
            platforms["facebook"]["score"] -= len(og["missing_required"]) * 15
            if "image" not in og["tags"]:
                platforms["facebook"]["issues"].append("No share image")
        
        # Twitter - prefers Twitter Card, falls back to OG
        if not twitter["present"] and not og["present"]:
            platforms["twitter"]["score"] -= 50
            platforms["twitter"]["issues"].append("No Twitter Card or OG tags")
        elif not twitter["present"]:
            platforms["twitter"]["score"] -= 10
            platforms["twitter"]["issues"].append("Using OG fallback (add Twitter Card)")
        else:
            platforms["twitter"]["score"] -= len(twitter["missing_required"]) * 15
        
        # LinkedIn - uses OG tags
        if not og["present"]:
            platforms["linkedin"]["score"] -= 50
            platforms["linkedin"]["issues"].append("Missing Open Graph tags")
        else:
            platforms["linkedin"]["score"] -= len(og["missing_required"]) * 10
            if "image" not in og["tags"]:
                platforms["linkedin"]["issues"].append("No share image - LinkedIn strongly prefers images")
                platforms["linkedin"]["score"] -= 20
        
        # WhatsApp - uses OG tags
        if not og["present"]:
            platforms["whatsapp"]["score"] -= 40
            platforms["whatsapp"]["issues"].append("Missing Open Graph tags")
        else:
            if "image" not in og["tags"]:
                platforms["whatsapp"]["issues"].append("No preview image")
                platforms["whatsapp"]["score"] -= 15
        
        # Slack - uses OG tags
        if not og["present"]:
            platforms["slack"]["score"] -= 40
            platforms["slack"]["issues"].append("Missing Open Graph tags")
        
        # Update status based on score
        for platform in platforms:
            score = platforms[platform]["score"]
            if score >= 80:
                platforms[platform]["status"] = "optimal"
            elif score >= 60:
                platforms[platform]["status"] = "good"
            elif score >= 40:
                platforms[platform]["status"] = "needs_improvement"
            else:
                platforms[platform]["status"] = "poor"
            
            # Ensure non-negative
            platforms[platform]["score"] = max(0, platforms[platform]["score"])
        
        return platforms
    
    def _calculate_social_score(self, social_data: dict) -> int:
        """Calculate overall social sharing readiness score."""
        score = 100
        
        og = social_data["open_graph"]
        twitter = social_data["twitter_card"]
        
        # OG presence and completeness (50 points max)
        if not og["present"]:
            score -= 30
        else:
            score -= len(og["missing_required"]) * 8
            score -= len(og["missing_recommended"]) * 3
            for issue in og["issues"]:
                if issue["severity"] == "high":
                    score -= 10
                elif issue["severity"] == "medium":
                    score -= 5
                else:
                    score -= 2
        
        # Twitter Card (25 points max)
        if not twitter["present"]:
            score -= 15
        else:
            score -= len(twitter["missing_required"]) * 5
            for issue in twitter["issues"]:
                if issue["severity"] == "high":
                    score -= 8
                elif issue["severity"] == "medium":
                    score -= 4
                else:
                    score -= 2
        
        # Social images (25 points)
        if not social_data["social_images"]:
            score -= 20
        elif len(social_data["social_images"]) == 1:
            # Check if image has dimensions
            img = social_data["social_images"][0]
            if not img.get("width") or not img.get("height"):
                score -= 5
        
        return max(0, score)
    
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
    
    def analyze_language(self, content_language_header: Optional[str] = None) -> dict:
        """
        Analyze page language using multiple detection methods.
        
        Detects language from:
        - HTML lang attribute (highest priority)
        - Content-Language HTTP header
        - og:locale meta tag
        - hreflang link tags
        - Content analysis (fallback)
        
        Args:
            content_language_header: Content-Language HTTP header value
            
        Returns:
            Dictionary with language detection results:
            - code: ISO 639-1 language code
            - region: Region code if available
            - name: Full language name
            - confidence: Detection confidence level
            - source: Detection method used
            - alternatives: Other available languages (from hreflang)
            - issues: Language-related SEO issues
        """
        detector = LanguageDetector()
        
        # Get HTML lang attribute
        html_tag = self.soup.find('html')
        html_lang = html_tag.get('lang') if html_tag else None
        
        # Get og:locale
        og_locale_tag = self.soup.find('meta', property='og:locale')
        og_locale = og_locale_tag.get('content') if og_locale_tag else None
        
        # Get hreflang tags
        hreflang_links = self.soup.find_all('link', attrs={'hreflang': True})
        hreflang_tags = [
            {"hreflang": link.get('hreflang'), "href": link.get('href', '')}
            for link in hreflang_links
        ]
        
        # Get text content for fallback detection
        text_content = self.extract_text_content()
        
        # Detect language
        result = detector.detect(
            html_lang=html_lang,
            content_language=content_language_header,
            og_locale=og_locale,
            hreflang_tags=hreflang_tags if hreflang_tags else None,
            text_content=text_content,
        )
        
        # Add any language issues to the analyzer's issue list
        for issue in result.get("issues", []):
            self.issues.append(Issue(
                issue["severity"],
                "on_page",
                issue["code"],
                issue["message"]
            ))
            self.recommendations.append(Recommendation(
                2 if issue["severity"] == "medium" else 3,
                "on_page",
                issue["recommendation"]
            ))
        
        return result
