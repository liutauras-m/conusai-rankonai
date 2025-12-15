"""
SEO Analyzer - Main Orchestrator.

Coordinates the SEO analysis process using specialized components.
"""


from datetime import datetime
from urllib.parse import urlparse

from analyzers import HTMLAnalyzer, RobotsParser
from utils import AsyncFetcher, ContentAnalyzer

from .scoring import ScoreCalculator
from .issues import AIIndexingIssueDetector
from .llm_context import LLMContextGenerator
from .result_builder import ResultBuilder


class SEOAnalyzer:
    """
    Main SEO and AI indexing analyzer.
    
    Orchestrates the analysis process by coordinating specialized components:
    - AsyncFetcher: Parallel URL fetching
    - HTMLAnalyzer: HTML/SEO analysis
    - ContentAnalyzer: Text/keyword analysis
    - RobotsParser: robots.txt analysis
    - ScoreCalculator: Score calculation
    - AIIndexingIssueDetector: AI-specific issues
    - LLMContextGenerator: LLM context generation
    - ResultBuilder: Result assembly
    
    Example:
        analyzer = SEOAnalyzer("https://example.com")
        result = await analyzer.analyze()
        
        # With verbose logging
        analyzer = SEOAnalyzer("https://example.com", verbose=True)
        result = await analyzer.analyze()
    """
    
    def __init__(self, url: str, verbose: bool = False):
        """
        Initialize the analyzer.
        
        Args:
            url: Target URL to analyze
            verbose: Enable verbose logging
        """
        self.url = url
        self.verbose = verbose
        self.parsed_url = urlparse(url)
        self.base_url = f"{self.parsed_url.scheme}://{self.parsed_url.netloc}"
        
        # Initialize components
        self.fetcher = AsyncFetcher()
        self.score_calculator = ScoreCalculator()
        self.issue_detector = AIIndexingIssueDetector()
        self.context_generator = LLMContextGenerator()
        
    def log(self, message: str) -> None:
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(f"[INFO] {message}")
    
    async def analyze(self) -> dict:
        """
        Run full SEO analysis.
        
        Returns:
            Complete analysis result dictionary containing:
            - url: Analyzed URL
            - timestamp: Analysis timestamp
            - scores: SEO scores by category
            - metadata: Meta tag analysis
            - headings: Heading structure analysis
            - images: Image analysis
            - links: Link analysis
            - content: Content/keyword analysis
            - structured_data: Schema/social meta analysis
            - technical: Technical SEO factors
            - ai_indexing: AI bot indexing status
            - issues: List of issues found
            - recommendations: List of recommendations
            - llm_context: Summary for LLM analysis
        """
        start_time = datetime.now()
        
        # Fetch all required URLs
        responses = await self._fetch_urls()
        
        # Extract responses
        main_response = responses[self.url]
        robots_response = responses[f"{self.base_url}/robots.txt"]
        llms_response = responses[f"{self.base_url}/llms.txt"]
        sitemap_response = responses[f"{self.base_url}/sitemap.xml"]
        
        # Check for fetch errors
        if main_response["error"] or main_response["status"] != 200:
            return self._build_error_response(main_response)
        
        # Run analysis
        self.log("Analyzing HTML content...")
        html_analyzer = HTMLAnalyzer(main_response["content"], self.url)
        
        text_content = html_analyzer.extract_text_content()
        content_analyzer = ContentAnalyzer(text_content)
        
        self.log("Extracting keywords...")
        robots_parser = RobotsParser(robots_response["content"])
        
        # Calculate scores
        scores = self.score_calculator.calculate(
            html_analyzer=html_analyzer,
            content_analyzer=content_analyzer,
            robots_parser=robots_parser,
            llms_response=llms_response,
        )
        
        # Build result
        result_builder = ResultBuilder(self.url, self.parsed_url)
        result = result_builder.build(
            html_analyzer=html_analyzer,
            content_analyzer=content_analyzer,
            robots_parser=robots_parser,
            main_response=main_response,
            robots_response=robots_response,
            llms_response=llms_response,
            sitemap_response=sitemap_response,
            scores=scores,
            start_time=start_time,
        )
        
        # Add AI indexing issues
        ai_issues, ai_recommendations = self.issue_detector.detect_issues(
            robots_parser=robots_parser,
            llms_response=llms_response,
            sitemap_response=sitemap_response,
        )
        result["issues"].extend(ai_issues)
        result["recommendations"].extend(ai_recommendations)
        
        # Add LLM context
        result["llm_context"] = self.context_generator.generate_context(result)
        
        return result
    
    async def _fetch_urls(self) -> dict:
        """Fetch all required URLs in parallel."""
        urls_to_fetch = [
            self.url,
            f"{self.base_url}/robots.txt",
            f"{self.base_url}/llms.txt",
            f"{self.base_url}/sitemap.xml",
        ]
        
        self.log(f"Fetching {len(urls_to_fetch)} URLs in parallel...")
        return await self.fetcher.fetch_all(urls_to_fetch)
    
    def _build_error_response(self, main_response: dict) -> dict:
        """Build error response when main page fetch fails."""
        return {
            "error": main_response["error"] or f"HTTP {main_response['status']}",
            "url": self.url,
            "timestamp": datetime.now().isoformat()
        }
