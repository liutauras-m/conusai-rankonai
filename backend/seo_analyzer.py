#!/usr/bin/env python3
"""
SEO & AI Indexing Analyzer
A comprehensive tool to analyze web pages for SEO and AI model indexing improvements.
Outputs structured JSON with issues, recommendations, and extracted data for LLM guidance.

Usage:
    python seo_analyzer.py https://example.com
    python seo_analyzer.py https://example.com --output report.json
    python seo_analyzer.py https://example.com --verbose
"""

import asyncio
import json
import re
import sys
import argparse
from datetime import datetime
from urllib.parse import urljoin, urlparse
from collections import Counter
from typing import Optional
from dataclasses import dataclass, field, asdict

# Third-party imports
try:
    import aiohttp
    from bs4 import BeautifulSoup
    import textstat
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install required packages: pip install aiohttp beautifulsoup4 lxml textstat")
    sys.exit(1)

# Optional: scikit-learn for TF-IDF (fallback to simple extraction if not available)
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


# ============================================================================
# Data Classes for Structured Output
# ============================================================================

@dataclass
class MetaTagAnalysis:
    value: Optional[str] = None
    length: int = 0
    issues: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)


@dataclass
class HeadingAnalysis:
    count: int = 0
    values: list = field(default_factory=list)
    issues: list = field(default_factory=list)


@dataclass
class ImageAnalysis:
    total: int = 0
    missing_alt: int = 0
    missing_alt_urls: list = field(default_factory=list)
    lazy_loading_count: int = 0
    issues: list = field(default_factory=list)


@dataclass
class LinkAnalysis:
    internal_count: int = 0
    external_count: int = 0
    nofollow_count: int = 0
    broken_count: int = 0
    broken_urls: list = field(default_factory=list)


@dataclass 
class Issue:
    severity: str  # high, medium, low
    category: str  # technical, on_page, content, ai_indexing, structured_data
    code: str
    message: str
    element: Optional[str] = None


@dataclass
class Recommendation:
    priority: int
    category: str
    action: str


# ============================================================================
# AI Crawler Bot Definitions
# ============================================================================

AI_BOTS = {
    # OpenAI
    "GPTBot": "OpenAI training crawler",
    "OAI-SearchBot": "ChatGPT search feature",
    "ChatGPT-User": "ChatGPT user browsing actions",
    
    # Anthropic
    "ClaudeBot": "Anthropic training crawler",
    "Claude-Web": "Claude web access",
    "anthropic-ai": "Anthropic AI crawler",
    
    # Google
    "Google-Extended": "Google Gemini/Bard training",
    "GoogleOther": "Google other services",
    
    # Others
    "PerplexityBot": "Perplexity AI search",
    "Bytespider": "ByteDance/TikTok crawler",
    "CCBot": "Common Crawl (used by many AI)",
    "Amazonbot": "Amazon Alexa/AI services",
    "Applebot-Extended": "Apple AI features",
    "cohere-ai": "Cohere AI training",
    "Diffbot": "Diffbot knowledge graph",
    "FacebookBot": "Meta AI training",
    "Meta-ExternalAgent": "Meta external AI agent",
    "omgili": "Webz.io data for AI",
    "Timpibot": "Timpi search engine",
}


# ============================================================================
# Async Fetcher - Parallel URL Fetching
# ============================================================================

class AsyncFetcher:
    """Async HTTP fetcher for parallel requests."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.headers = {
            "User-Agent": "SEO-AI-Analyzer/1.0 (https://github.com/seo-analyzer)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
    
    async def fetch(self, session: aiohttp.ClientSession, url: str) -> dict:
        """Fetch a single URL and return response data."""
        start_time = datetime.now()
        result = {
            "url": url,
            "status": None,
            "content": None,
            "headers": {},
            "error": None,
            "response_time_ms": 0,
        }
        
        try:
            async with session.get(url, headers=self.headers, ssl=False) as response:
                result["status"] = response.status
                result["headers"] = dict(response.headers)
                
                if response.status == 200:
                    result["content"] = await response.text()
                    
                result["response_time_ms"] = (datetime.now() - start_time).total_seconds() * 1000
                
        except asyncio.TimeoutError:
            result["error"] = "Timeout"
        except aiohttp.ClientError as e:
            result["error"] = str(e)
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
            
        return result
    
    async def fetch_all(self, urls: list[str]) -> dict[str, dict]:
        """Fetch multiple URLs in parallel."""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            tasks = [self.fetch(session, url) for url in urls]
            results = await asyncio.gather(*tasks)
            return {r["url"]: r for r in results}


# ============================================================================
# Robots.txt Parser
# ============================================================================

class RobotsParser:
    """Parse robots.txt and check AI bot permissions."""
    
    def __init__(self, content: Optional[str]):
        self.content = content or ""
        self.rules = self._parse()
    
    def _parse(self) -> dict:
        """Parse robots.txt into structured rules."""
        rules = {"*": {"allow": [], "disallow": []}}
        current_agent = "*"
        
        for line in self.content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
                
            if ":" not in line:
                continue
                
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            
            if key == "user-agent":
                current_agent = value
                if current_agent not in rules:
                    rules[current_agent] = {"allow": [], "disallow": []}
            elif key == "allow":
                rules[current_agent]["allow"].append(value)
            elif key == "disallow":
                rules[current_agent]["disallow"].append(value)
                
        return rules
    
    def get_ai_bot_status(self) -> dict:
        """Check status of each AI bot."""
        status = {}
        
        for bot_name in AI_BOTS.keys():
            if bot_name in self.rules:
                # Bot has specific rules
                bot_rules = self.rules[bot_name]
                if "/" in bot_rules["disallow"]:
                    status[bot_name] = "blocked"
                elif bot_rules["allow"] or not bot_rules["disallow"]:
                    status[bot_name] = "allowed"
                else:
                    status[bot_name] = "partially_blocked"
            elif "*" in self.rules:
                # Fall back to wildcard rules
                wildcard = self.rules["*"]
                if "/" in wildcard["disallow"]:
                    status[bot_name] = "blocked_by_wildcard"
                else:
                    status[bot_name] = "allowed_by_default"
            else:
                status[bot_name] = "not_specified"
                
        return status
    
    def get_sitemap_urls(self) -> list:
        """Extract sitemap URLs from robots.txt."""
        sitemaps = []
        for line in self.content.split("\n"):
            if line.lower().startswith("sitemap:"):
                sitemaps.append(line.split(":", 1)[1].strip())
        return sitemaps


# ============================================================================
# Content Analyzer - Keywords, Readability
# ============================================================================

class ContentAnalyzer:
    """Analyze page content for keywords, readability, and structure."""
    
    def __init__(self, text: str):
        self.text = text
        self.words = self._extract_words()
        
    def _extract_words(self) -> list:
        """Extract clean words from text."""
        # Remove extra whitespace and convert to lowercase
        clean_text = re.sub(r'\s+', ' ', self.text.lower())
        # Extract words (letters and numbers only)
        words = re.findall(r'\b[a-z]{3,}\b', clean_text)
        return words
    
    def get_word_count(self) -> int:
        """Get total word count."""
        return len(self.words)
    
    def get_readability(self) -> dict:
        """Calculate readability scores."""
        if not self.text.strip():
            return {"score": 0, "grade": "N/A", "reading_ease": 0}
            
        return {
            "flesch_reading_ease": round(textstat.flesch_reading_ease(self.text), 1),
            "flesch_kincaid_grade": round(textstat.flesch_kincaid_grade(self.text), 1),
            "gunning_fog": round(textstat.gunning_fog(self.text), 1),
            "smog_index": round(textstat.smog_index(self.text), 1),
            "automated_readability_index": round(textstat.automated_readability_index(self.text), 1),
            "reading_time_minutes": round(textstat.reading_time(self.text, ms_per_char=14.69) / 60, 1),
        }
    
    def extract_keywords_simple(self, top_n: int = 20) -> list:
        """Simple keyword extraction using frequency."""
        # Common stop words to filter out
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
            'her', 'was', 'one', 'our', 'out', 'has', 'have', 'been', 'were', 'will',
            'with', 'this', 'that', 'from', 'they', 'what', 'which', 'their', 'there',
            'would', 'could', 'should', 'about', 'into', 'more', 'some', 'than', 'them',
            'then', 'these', 'when', 'where', 'your', 'just', 'also', 'only', 'other',
            'such', 'like', 'very', 'even', 'most', 'make', 'made', 'each', 'does',
            'how', 'its', 'may', 'use', 'any', 'being', 'both', 'find', 'here', 'many',
            'through', 'using', 'well', 'back', 'much', 'before', 'must', 'right', 'still',
            'own', 'same', 'see', 'now', 'way', 'come', 'since', 'another', 'over',
        }
        
        # Filter and count words
        filtered_words = [w for w in self.words if w not in stop_words and len(w) > 2]
        word_freq = Counter(filtered_words)
        
        total_words = len(filtered_words) or 1
        keywords = []
        
        for word, count in word_freq.most_common(top_n):
            density = round((count / total_words) * 100, 2)
            keywords.append({
                "keyword": word,
                "count": count,
                "density_percent": density
            })
            
        return keywords
    
    def extract_keywords_tfidf(self, top_n: int = 20) -> list:
        """Extract keywords using TF-IDF (requires sklearn)."""
        if not HAS_SKLEARN or not self.text.strip():
            return self.extract_keywords_simple(top_n)
        
        try:
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.95
            )
            
            # TF-IDF needs multiple documents, so we split into sentences
            sentences = re.split(r'[.!?]+', self.text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
            
            if len(sentences) < 2:
                return self.extract_keywords_simple(top_n)
            
            tfidf_matrix = vectorizer.fit_transform(sentences)
            feature_names = vectorizer.get_feature_names_out()
            
            # Sum TF-IDF scores across all sentences
            tfidf_scores = tfidf_matrix.sum(axis=0).A1
            
            # Create keyword list with scores
            keywords = []
            for idx in tfidf_scores.argsort()[::-1][:top_n]:
                keyword = feature_names[idx]
                score = round(tfidf_scores[idx], 3)
                count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', self.text.lower()))
                keywords.append({
                    "keyword": keyword,
                    "tfidf_score": score,
                    "count": count
                })
                
            return keywords
            
        except Exception:
            return self.extract_keywords_simple(top_n)
    
    def extract_phrases(self, n: int = 2, top_k: int = 10) -> list:
        """Extract common n-gram phrases."""
        if len(self.words) < n:
            return []
            
        ngrams = []
        for i in range(len(self.words) - n + 1):
            ngram = " ".join(self.words[i:i+n])
            ngrams.append(ngram)
            
        phrase_freq = Counter(ngrams)
        
        # Filter out phrases that appear only once
        phrases = [
            {"phrase": phrase, "count": count}
            for phrase, count in phrase_freq.most_common(top_k)
            if count > 1
        ]
        
        return phrases


# ============================================================================
# HTML Analyzer - Main SEO Analysis
# ============================================================================

class HTMLAnalyzer:
    """Analyze HTML content for SEO factors."""
    
    def __init__(self, html: str, base_url: str):
        self.soup = BeautifulSoup(html, 'lxml')
        self.base_url = base_url
        self.parsed_url = urlparse(base_url)
        self.issues: list[Issue] = []
        self.recommendations: list[Recommendation] = []
        
    def analyze_meta_tags(self) -> dict:
        """Analyze meta tags (title, description, etc.)."""
        result = {}
        
        # Title tag
        title_tag = self.soup.find('title')
        title = title_tag.get_text().strip() if title_tag else None
        title_analysis = MetaTagAnalysis(
            value=title,
            length=len(title) if title else 0
        )
        
        if not title:
            title_analysis.issues.append("missing")
            title_analysis.recommendations.append("Add a title tag")
            self.issues.append(Issue("high", "on_page", "TITLE_MISSING", "Page is missing a title tag"))
            self.recommendations.append(Recommendation(1, "on_page", "Add a descriptive title tag (50-60 characters)"))
        elif len(title) < 30:
            title_analysis.issues.append("too_short")
            title_analysis.recommendations.append("Expand title to 50-60 characters")
            self.issues.append(Issue("medium", "on_page", "TITLE_TOO_SHORT", f"Title is only {len(title)} characters (recommended: 50-60)", f"<title>{title}</title>"))
            self.recommendations.append(Recommendation(2, "on_page", "Expand title tag to 50-60 characters with primary keyword"))
        elif len(title) > 60:
            title_analysis.issues.append("too_long")
            title_analysis.recommendations.append("Shorten title to under 60 characters")
            self.issues.append(Issue("low", "on_page", "TITLE_TOO_LONG", f"Title is {len(title)} characters (may be truncated in search results)", f"<title>{title}</title>"))
            
        result["title"] = asdict(title_analysis)
        
        # Meta description
        meta_desc = self.soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '').strip() if meta_desc else None
        desc_analysis = MetaTagAnalysis(
            value=description,
            length=len(description) if description else 0
        )
        
        if not description:
            desc_analysis.issues.append("missing")
            desc_analysis.recommendations.append("Add a meta description")
            self.issues.append(Issue("high", "on_page", "META_DESC_MISSING", "Page is missing a meta description"))
            self.recommendations.append(Recommendation(1, "on_page", "Add a compelling meta description (150-160 characters)"))
        elif len(description) < 70:
            desc_analysis.issues.append("too_short")
            desc_analysis.recommendations.append("Expand description to 150-160 characters")
            self.issues.append(Issue("medium", "on_page", "META_DESC_TOO_SHORT", f"Meta description is only {len(description)} characters"))
        elif len(description) > 160:
            desc_analysis.issues.append("too_long")
            desc_analysis.recommendations.append("Shorten description to under 160 characters")
            self.issues.append(Issue("low", "on_page", "META_DESC_TOO_LONG", f"Meta description is {len(description)} characters (may be truncated)"))
            
        result["description"] = asdict(desc_analysis)
        
        # Canonical URL
        canonical = self.soup.find('link', attrs={'rel': 'canonical'})
        result["canonical"] = canonical.get('href') if canonical else None
        if not canonical:
            self.issues.append(Issue("medium", "technical", "CANONICAL_MISSING", "No canonical URL specified"))
            self.recommendations.append(Recommendation(3, "technical", "Add a canonical URL to prevent duplicate content issues"))
        
        # Robots meta
        robots_meta = self.soup.find('meta', attrs={'name': 'robots'})
        result["robots_meta"] = robots_meta.get('content') if robots_meta else None
        
        # Viewport
        viewport = self.soup.find('meta', attrs={'name': 'viewport'})
        result["viewport"] = viewport.get('content') if viewport else None
        if not viewport:
            self.issues.append(Issue("high", "technical", "VIEWPORT_MISSING", "No viewport meta tag (page may not be mobile-friendly)"))
            self.recommendations.append(Recommendation(1, "technical", "Add viewport meta tag for mobile responsiveness"))
        
        # Language
        html_tag = self.soup.find('html')
        result["language"] = html_tag.get('lang') if html_tag else None
        if not result["language"]:
            self.issues.append(Issue("low", "on_page", "LANG_MISSING", "HTML lang attribute not specified"))
        
        # Keywords (legacy, but still checked)
        keywords_meta = self.soup.find('meta', attrs={'name': 'keywords'})
        result["keywords_meta"] = keywords_meta.get('content') if keywords_meta else None
        
        return result
    
    def analyze_headings(self) -> dict:
        """Analyze heading structure (H1-H6)."""
        result = {}
        
        for i in range(1, 7):
            tag = f"h{i}"
            headings = self.soup.find_all(tag)
            result[tag] = HeadingAnalysis(
                count=len(headings),
                values=[h.get_text().strip()[:100] for h in headings[:10]]  # Limit to first 10
            )
        
        # Check H1
        h1_count = result["h1"].count
        if h1_count == 0:
            result["h1"].issues.append("missing")
            self.issues.append(Issue("high", "on_page", "H1_MISSING", "Page is missing an H1 tag"))
            self.recommendations.append(Recommendation(1, "on_page", "Add a single H1 tag with primary keyword"))
        elif h1_count > 1:
            result["h1"].issues.append("multiple")
            self.issues.append(Issue("medium", "on_page", "MULTIPLE_H1", f"Page has {h1_count} H1 tags (should have exactly 1)"))
            self.recommendations.append(Recommendation(2, "on_page", "Consolidate to a single H1 tag"))
        
        # Check heading hierarchy
        result["hierarchy_valid"] = self._check_heading_hierarchy()
        if not result["hierarchy_valid"]:
            self.issues.append(Issue("low", "on_page", "HEADING_HIERARCHY", "Heading hierarchy is not properly structured (skipped levels)"))
            
        return {k: asdict(v) if isinstance(v, HeadingAnalysis) else v for k, v in result.items()}
    
    def _check_heading_hierarchy(self) -> bool:
        """Check if heading hierarchy is valid (no skipped levels)."""
        headings = self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if not headings:
            return True
            
        levels = [int(h.name[1]) for h in headings]
        
        for i in range(1, len(levels)):
            # Allow going up any amount, but going down should only be 1 level at a time
            if levels[i] > levels[i-1] + 1:
                return False
                
        return True
    
    def analyze_images(self) -> dict:
        """Analyze images for alt text and optimization."""
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
            missing_alt_urls=missing_alt[:10],  # Limit to first 10
            lazy_loading_count=lazy_count
        )
        
        if missing_alt:
            result.issues.append(f"{len(missing_alt)} images missing alt text")
            self.issues.append(Issue("medium", "on_page", "MISSING_ALT", f"{len(missing_alt)} images are missing alt text", str(missing_alt[:3])))
            self.recommendations.append(Recommendation(2, "on_page", f"Add descriptive alt text to {len(missing_alt)} images"))
        
        return asdict(result)
    
    def analyze_links(self) -> dict:
        """Analyze internal and external links."""
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
            if href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
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
            self.issues.append(Issue("medium", "on_page", "NO_INTERNAL_LINKS", "Page has no internal links"))
            self.recommendations.append(Recommendation(3, "on_page", "Add internal links to related content"))
        
        return asdict(result)
    
    def analyze_structured_data(self) -> dict:
        """Analyze Schema.org and social meta tags."""
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
            self.issues.append(Issue("medium", "structured_data", "NO_SCHEMA", "No JSON-LD structured data found"))
            self.recommendations.append(Recommendation(3, "structured_data", "Add Schema.org JSON-LD markup (Organization, Article, FAQ, etc.)"))
        
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
            self.issues.append(Issue("medium", "structured_data", "NO_OG", "No Open Graph tags found"))
            self.recommendations.append(Recommendation(3, "structured_data", "Add Open Graph tags for better social sharing"))
        elif 'image' not in result["open_graph"]:
            self.issues.append(Issue("low", "structured_data", "OG_NO_IMAGE", "Open Graph image tag is missing"))
        
        # Twitter Card
        twitter_tags = self.soup.find_all('meta', attrs={'name': re.compile('^twitter:')})
        for tag in twitter_tags:
            prop = tag.get('name', '').replace('twitter:', '')
            result["twitter_card"][prop] = tag.get('content', '')[:200]
        
        if not result["twitter_card"]:
            self.issues.append(Issue("low", "structured_data", "NO_TWITTER_CARD", "No Twitter Card tags found"))
        
        return result
    
    def extract_text_content(self) -> str:
        """Extract main text content from page."""
        # Remove script and style elements
        for element in self.soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Try to find main content area
        main_content = (
            self.soup.find('main') or 
            self.soup.find('article') or 
            self.soup.find(id='content') or
            self.soup.find(class_='content') or
            self.soup.find('body')
        )
        
        if main_content:
            return main_content.get_text(separator=' ', strip=True)
        
        return self.soup.get_text(separator=' ', strip=True)


# ============================================================================
# Main SEO Analyzer
# ============================================================================

class SEOAnalyzer:
    """Main SEO and AI indexing analyzer."""
    
    def __init__(self, url: str, verbose: bool = False):
        self.url = url
        self.verbose = verbose
        self.parsed_url = urlparse(url)
        self.base_url = f"{self.parsed_url.scheme}://{self.parsed_url.netloc}"
        self.fetcher = AsyncFetcher()
        
    def log(self, message: str):
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(f"[INFO] {message}")
    
    async def analyze(self) -> dict:
        """Run full SEO analysis."""
        start_time = datetime.now()
        
        # URLs to fetch in parallel
        urls_to_fetch = [
            self.url,
            f"{self.base_url}/robots.txt",
            f"{self.base_url}/llms.txt",
            f"{self.base_url}/sitemap.xml",
        ]
        
        self.log(f"Fetching {len(urls_to_fetch)} URLs in parallel...")
        
        # Fetch all URLs in parallel
        responses = await self.fetcher.fetch_all(urls_to_fetch)
        
        # Get responses
        main_response = responses[self.url]
        robots_response = responses[f"{self.base_url}/robots.txt"]
        llms_response = responses[f"{self.base_url}/llms.txt"]
        sitemap_response = responses[f"{self.base_url}/sitemap.xml"]
        
        # Check main page
        if main_response["error"] or main_response["status"] != 200:
            return {
                "error": main_response["error"] or f"HTTP {main_response['status']}",
                "url": self.url,
                "timestamp": datetime.now().isoformat()
            }
        
        self.log("Analyzing HTML content...")
        
        # Analyze HTML
        html_analyzer = HTMLAnalyzer(main_response["content"], self.url)
        
        # Extract and analyze content
        text_content = html_analyzer.extract_text_content()
        content_analyzer = ContentAnalyzer(text_content)
        
        self.log("Extracting keywords...")
        
        # Parse robots.txt
        robots_parser = RobotsParser(robots_response["content"])
        
        # Build result
        result = {
            "url": self.url,
            "timestamp": datetime.now().isoformat(),
            "crawl_time_ms": round((datetime.now() - start_time).total_seconds() * 1000),
            
            "scores": self._calculate_scores(html_analyzer, content_analyzer, robots_parser, llms_response),
            
            "metadata": html_analyzer.analyze_meta_tags(),
            
            "headings": html_analyzer.analyze_headings(),
            
            "images": html_analyzer.analyze_images(),
            
            "links": html_analyzer.analyze_links(),
            
            "content": {
                "word_count": content_analyzer.get_word_count(),
                "readability": content_analyzer.get_readability(),
                "keywords_tfidf": content_analyzer.extract_keywords_tfidf(top_n=15),
                "keywords_frequency": content_analyzer.extract_keywords_simple(top_n=15),
                "top_bigrams": content_analyzer.extract_phrases(n=2, top_k=10),
                "top_trigrams": content_analyzer.extract_phrases(n=3, top_k=10),
            },
            
            "structured_data": html_analyzer.analyze_structured_data(),
            
            "technical": {
                "https": self.parsed_url.scheme == 'https',
                "response_time_ms": round(main_response["response_time_ms"]),
                "content_type": main_response["headers"].get("Content-Type", ""),
                "content_encoding": main_response["headers"].get("Content-Encoding", "none"),
                "server": main_response["headers"].get("Server", ""),
                "x_frame_options": main_response["headers"].get("X-Frame-Options", ""),
                "content_security_policy": "Content-Security-Policy" in main_response["headers"],
            },
            
            "ai_indexing": {
                "robots_txt": {
                    "present": robots_response["status"] == 200,
                    "ai_bots_status": robots_parser.get_ai_bot_status(),
                    "sitemaps_declared": robots_parser.get_sitemap_urls(),
                },
                "llms_txt": {
                    "present": llms_response["status"] == 200,
                    "content_preview": (llms_response["content"][:500] + "...") if llms_response["content"] else None,
                },
                "sitemap_xml": {
                    "present": sitemap_response["status"] == 200,
                },
            },
            
            "issues": [asdict(issue) for issue in html_analyzer.issues],
            
            "recommendations": [asdict(rec) for rec in sorted(html_analyzer.recommendations, key=lambda x: x.priority)],
        }
        
        # Add AI indexing specific issues
        self._add_ai_indexing_issues(result, robots_parser, llms_response, sitemap_response)
        
        # Add LLM context summary
        result["llm_context"] = self._generate_llm_context(result)
        
        return result
    
    def _calculate_scores(self, html_analyzer: HTMLAnalyzer, content_analyzer: ContentAnalyzer, 
                         robots_parser: RobotsParser, llms_response: dict) -> dict:
        """Calculate SEO scores."""
        scores = {
            "technical": 100,
            "on_page": 100,
            "content": 100,
            "structured_data": 100,
            "ai_readiness": 100,
        }
        
        # Deduct points based on issues
        for issue in html_analyzer.issues:
            category = issue.category
            if category in scores:
                if issue.severity == "high":
                    scores[category] -= 15
                elif issue.severity == "medium":
                    scores[category] -= 8
                else:
                    scores[category] -= 3
        
        # Content score based on word count
        word_count = content_analyzer.get_word_count()
        if word_count < 300:
            scores["content"] -= 20
        elif word_count < 500:
            scores["content"] -= 10
        
        # AI readiness score
        if llms_response["status"] != 200:
            scores["ai_readiness"] -= 20
        
        ai_bots = robots_parser.get_ai_bot_status()
        blocked_bots = sum(1 for status in ai_bots.values() if 'blocked' in status)
        if blocked_bots > 0:
            scores["ai_readiness"] -= blocked_bots * 5
        
        # Ensure scores don't go below 0
        scores = {k: max(0, v) for k, v in scores.items()}
        
        # Calculate overall
        scores["overall"] = round(sum(scores.values()) / len(scores))
        
        return scores
    
    def _add_ai_indexing_issues(self, result: dict, robots_parser: RobotsParser, 
                                llms_response: dict, sitemap_response: dict):
        """Add AI indexing specific issues."""
        
        if llms_response["status"] != 200:
            result["issues"].append({
                "severity": "medium",
                "category": "ai_indexing",
                "code": "NO_LLMS_TXT",
                "message": "No llms.txt file found for AI/LLM indexing optimization"
            })
            result["recommendations"].append({
                "priority": 2,
                "category": "ai_indexing",
                "action": "Create /llms.txt file to help AI models understand your site structure"
            })
        
        if sitemap_response["status"] != 200:
            result["issues"].append({
                "severity": "medium",
                "category": "technical",
                "code": "NO_SITEMAP",
                "message": "No sitemap.xml found"
            })
            result["recommendations"].append({
                "priority": 2,
                "category": "technical",
                "action": "Create sitemap.xml for better crawling and indexing"
            })
        
        # Check for blocked AI bots
        ai_status = robots_parser.get_ai_bot_status()
        blocked = [bot for bot, status in ai_status.items() if 'blocked' in status]
        
        if blocked:
            result["issues"].append({
                "severity": "low",
                "category": "ai_indexing",
                "code": "AI_BOTS_BLOCKED",
                "message": f"Some AI bots are blocked: {', '.join(blocked[:5])}"
            })
    
    def _generate_llm_context(self, result: dict) -> dict:
        """Generate a summary context for LLM analysis."""
        return {
            "summary": f"SEO analysis for {result['url']}",
            "overall_score": result["scores"]["overall"],
            "critical_issues_count": len([i for i in result["issues"] if i["severity"] == "high"]),
            "total_issues_count": len(result["issues"]),
            "key_metrics": {
                "has_title": result["metadata"]["title"]["value"] is not None,
                "has_meta_description": result["metadata"]["description"]["value"] is not None,
                "has_h1": result["headings"]["h1"]["count"] == 1,
                "word_count": result["content"]["word_count"],
                "has_schema": len(result["structured_data"]["json_ld"]) > 0,
                "has_og_tags": len(result["structured_data"]["open_graph"]) > 0,
                "is_https": result["technical"]["https"],
                "has_llms_txt": result["ai_indexing"]["llms_txt"]["present"],
                "has_sitemap": result["ai_indexing"]["sitemap_xml"]["present"],
            },
            "top_keywords": [k["keyword"] for k in result["content"]["keywords_frequency"][:5]],
            "prompt_for_improvement": self._generate_improvement_prompt(result),
        }
    
    def _generate_improvement_prompt(self, result: dict) -> str:
        """Generate a prompt for LLM to provide improvement suggestions."""
        issues_summary = "\n".join([
            f"- [{i['severity'].upper()}] {i['message']}"
            for i in result["issues"][:10]
        ])
        
        return f"""Analyze this SEO report and provide specific improvement recommendations:

URL: {result['url']}
Overall Score: {result['scores']['overall']}/100

Current Issues:
{issues_summary}

Key Metrics:
- Word Count: {result['content']['word_count']}
- Has Structured Data: {len(result['structured_data']['json_ld']) > 0}
- AI Indexing Ready: {result['ai_indexing']['llms_txt']['present']}
- Top Keywords: {', '.join([k['keyword'] for k in result['content']['keywords_frequency'][:5]])}

Please provide:
1. Priority fixes for critical SEO issues
2. Content optimization suggestions based on keywords
3. Structured data recommendations
4. AI indexing optimization tips
"""


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="SEO & AI Indexing Analyzer - Analyze web pages for SEO and AI model indexing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python seo_analyzer.py https://example.com
  python seo_analyzer.py https://example.com --output report.json
  python seo_analyzer.py https://example.com --verbose --pretty
        """
    )
    
    parser.add_argument("url", help="URL to analyze")
    parser.add_argument("-o", "--output", help="Output file path (default: stdout)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-p", "--pretty", action="store_true", help="Pretty print JSON output")
    
    args = parser.parse_args()
    
    # Validate URL
    if not args.url.startswith(('http://', 'https://')):
        args.url = 'https://' + args.url
    
    # Run analysis
    analyzer = SEOAnalyzer(args.url, verbose=args.verbose)
    
    if args.verbose:
        print(f"\n{'='*60}")
        print(f"SEO & AI Indexing Analyzer")
        print(f"{'='*60}")
        print(f"Target URL: {args.url}")
        print(f"{'='*60}\n")
    
    result = asyncio.run(analyzer.analyze())
    
    # Format output
    indent = 2 if args.pretty else None
    json_output = json.dumps(result, indent=indent, ensure_ascii=False)
    
    # Output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(json_output)
        if args.verbose:
            print(f"\nReport saved to: {args.output}")
    else:
        print(json_output)
    
    # Print summary if verbose
    if args.verbose and "error" not in result:
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"Overall Score: {result['scores']['overall']}/100")
        print(f"Issues Found: {len(result['issues'])}")
        print(f"  - High: {len([i for i in result['issues'] if i['severity'] == 'high'])}")
        print(f"  - Medium: {len([i for i in result['issues'] if i['severity'] == 'medium'])}")
        print(f"  - Low: {len([i for i in result['issues'] if i['severity'] == 'low'])}")
        print(f"\nTop Keywords: {', '.join([k['keyword'] for k in result['content']['keywords_frequency'][:5]])}")
        print(f"Word Count: {result['content']['word_count']}")
        print(f"AI Ready: {'Yes' if result['ai_indexing']['llms_txt']['present'] else 'No (missing llms.txt)'}")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
