#!/usr/bin/env python3
"""
SEO AI Files Generator
Analyzes SEO report JSON and generates optimized robots.txt and llms.txt files
using OpenAI GPT-4 for intelligent recommendations.

Usage:
    python seo_ai_generator.py repot.json
    python seo_ai_generator.py repot.json --output-dir ./output
    python seo_ai_generator.py repot.json --dry-run
"""

import asyncio
import json
import os
import sys
import argparse
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config import get_api_key, GENERATED_DIR_STR
except ImportError:
    # Fallback if config not available
    GENERATED_DIR_STR = "./generated"
    def get_api_key(provider):
        return os.environ.get(f"{provider.upper()}_API_KEY")

try:
    import aiohttp
except ImportError:
    print("Missing aiohttp. Install with: pip install aiohttp")
    sys.exit(1)


# ============================================================================
# AI Bot Definitions with Categories
# ============================================================================

AI_BOTS = {
    # High-value AI search/chat bots - ALLOW
    "high_value": {
        "GPTBot": "OpenAI training & ChatGPT search",
        "OAI-SearchBot": "ChatGPT web search feature",
        "ChatGPT-User": "ChatGPT user browsing",
        "ClaudeBot": "Anthropic Claude training",
        "Claude-Web": "Claude web access",
        "anthropic-ai": "Anthropic AI systems",
        "Google-Extended": "Google Gemini/Bard",
        "GoogleOther": "Google AI services",
        "PerplexityBot": "Perplexity AI search",
        "Applebot-Extended": "Apple AI/Siri",
    },
    # Medium-value bots - ALLOW with caution
    "medium_value": {
        "CCBot": "Common Crawl (AI training data)",
        "Amazonbot": "Amazon Alexa/AI",
        "cohere-ai": "Cohere AI",
        "Diffbot": "Diffbot knowledge graph",
        "Meta-ExternalAgent": "Meta AI",
        "FacebookBot": "Meta/Facebook AI",
    },
    # Low-value/aggressive bots - BLOCK
    "block": {
        "Bytespider": "ByteDance/TikTok (aggressive crawler)",
        "omgili": "Webz.io (high volume scraper)",
        "Timpibot": "Timpi search (low value)",
        "PetalBot": "Huawei search (aggressive)",
        "SemrushBot": "SEMrush (competitor analysis)",
        "AhrefsBot": "Ahrefs (competitor analysis)",
        "MJ12bot": "Majestic (link analysis)",
        "DotBot": "Moz (SEO crawler)",
    }
}


# ============================================================================
# OpenAI Client
# ============================================================================

class OpenAIClient:
    """Simple async OpenAI client."""
    
    def __init__(self):
        self.api_key = get_api_key("openai")
        self.api_base = "https://api.openai.com/v1"
        
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    async def chat(self, messages: list, model: str = "gpt-4o") -> dict:
        """Send chat completion request."""
        if not self.is_configured():
            return {"error": "OPENAI_API_KEY not set"}
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4096,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                if resp.status != 200:
                    error = await resp.text()
                    return {"error": f"HTTP {resp.status}: {error[:200]}"}
                
                data = await resp.json()
                return {
                    "content": data["choices"][0]["message"]["content"],
                    "tokens": data.get("usage", {}).get("total_tokens", 0)
                }


# ============================================================================
# Robots.txt Generator
# ============================================================================

class RobotsTxtGenerator:
    """Generate optimized robots.txt based on SEO report."""
    
    def __init__(self, report: dict):
        self.report = report
        self.url = report.get("url", "")
        self.parsed_url = urlparse(self.url)
        self.base_url = f"{self.parsed_url.scheme}://{self.parsed_url.netloc}"
        
    def generate(self) -> str:
        """Generate robots.txt content."""
        sitemap_url = f"{self.base_url}/sitemap.xml"
        
        # Check if sitemap was declared in existing robots.txt
        sitemaps = self.report.get("ai_indexing", {}).get("robots_txt", {}).get("sitemaps_declared", [])
        if sitemaps:
            sitemap_url = sitemaps[0]
        
        lines = [
            "# robots.txt for " + self.parsed_url.netloc,
            "# Generated by SEO AI Generator",
            f"# Last updated: {datetime.now().strftime('%Y-%m-%d')}",
            "",
            "# ===========================================",
            "# Default rules for all crawlers",
            "# ===========================================",
            "User-agent: *",
            "Allow: /",
            "Disallow: /api/",
            "Disallow: /admin/",
            "Disallow: /private/",
            "Disallow: /*.json$",
            "",
            "# Crawl rate limiting",
            "Crawl-delay: 1",
            "",
            "# ===========================================",
            "# HIGH-VALUE AI CRAWLERS - Explicitly Allow",
            "# ===========================================",
        ]
        
        # High-value AI bots - explicit allow
        for bot, desc in AI_BOTS["high_value"].items():
            lines.extend([
                f"# {desc}",
                f"User-agent: {bot}",
                "Allow: /",
                "Allow: /blog/",
                "Allow: /docs/",
                "Allow: /about/",
                "",
            ])
        
        lines.extend([
            "# ===========================================",
            "# MEDIUM-VALUE AI CRAWLERS - Allow with limits",
            "# ===========================================",
        ])
        
        # Medium-value bots - allow with crawl delay
        for bot, desc in AI_BOTS["medium_value"].items():
            lines.extend([
                f"# {desc}",
                f"User-agent: {bot}",
                "Allow: /",
                "Crawl-delay: 2",
                "",
            ])
        
        lines.extend([
            "# ===========================================",
            "# LOW-VALUE/AGGRESSIVE CRAWLERS - Block",
            "# ===========================================",
        ])
        
        # Block aggressive/low-value bots
        for bot, desc in AI_BOTS["block"].items():
            lines.extend([
                f"# {desc}",
                f"User-agent: {bot}",
                "Disallow: /",
                "",
            ])
        
        lines.extend([
            "# ===========================================",
            "# Sitemaps",
            "# ===========================================",
            f"Sitemap: {sitemap_url}",
            "",
            "# ===========================================",
            "# Additional AI/LLM resources",
            "# ===========================================",
            f"# llms.txt: {self.base_url}/llms.txt",
            f"# AI-friendly sitemap: {self.base_url}/sitemap.xml",
            "",
        ])
        
        return "\n".join(lines)


# ============================================================================
# LLMs.txt Generator  
# ============================================================================

class LlmsTxtGenerator:
    """Generate llms.txt based on SEO report and AI analysis."""
    
    def __init__(self, report: dict, ai_analysis: Optional[str] = None):
        self.report = report
        self.ai_analysis = ai_analysis
        self.url = report.get("url", "")
        self.parsed_url = urlparse(self.url)
        self.base_url = f"{self.parsed_url.scheme}://{self.parsed_url.netloc}"
        
    def generate(self) -> str:
        """Generate llms.txt content."""
        metadata = self.report.get("metadata", {})
        content = self.report.get("content", {})
        structured = self.report.get("structured_data", {})
        
        # Extract data
        title = metadata.get("title", {}).get("value", "Unknown")
        description = metadata.get("description", {}).get("value", "")
        keywords = metadata.get("keywords_meta", "")
        
        # Get top keywords from analysis
        top_keywords = [k["keyword"] for k in content.get("keywords_frequency", [])[:10]]
        top_phrases = [p["phrase"] for p in content.get("top_bigrams", [])[:5]]
        
        # Extract headings for structure
        headings = self.report.get("headings", {})
        h2_values = headings.get("h2", {}).get("values", [])
        
        # Get OG data
        og = structured.get("open_graph", {})
        site_name = og.get("site_name", self.parsed_url.netloc)
        
        lines = [
            f"# {site_name}",
            f"# llms.txt - AI/LLM Crawler & Agent Information",
            f"# Spec: https://llmstxt.org/",
            f"# Last updated: {datetime.now().strftime('%Y-%m-%d')}",
            "",
            "## Site Overview",
            "",
            f"> {description}" if description else "> AI-powered platform",
            "",
            "## Quick Facts",
            "",
            f"- **Name:** {site_name}",
            f"- **URL:** {self.base_url}",
            f"- **Type:** {og.get('type', 'website')}",
            f"- **Language:** {metadata.get('language', 'en')}",
            "",
            "## Core Topics & Expertise",
            "",
        ]
        
        # Add keywords as topics
        if top_keywords:
            for kw in top_keywords[:8]:
                lines.append(f"- {kw.title()}")
        
        lines.extend([
            "",
            "## Key Phrases",
            "",
        ])
        
        if top_phrases:
            for phrase in top_phrases:
                lines.append(f"- {phrase.title()}")
        
        lines.extend([
            "",
            "## Site Sections",
            "",
        ])
        
        # Add sections from H2 headings
        for h2 in h2_values[:6]:
            if h2.strip():
                lines.append(f"- **{h2.strip().replace(':', '')}**")
        
        lines.extend([
            "",
            "## Structured Data Available",
            "",
            f"- Open Graph: {'✓ Yes' if og else '✗ No'}",
            f"- Twitter Cards: {'✓ Yes' if structured.get('twitter_card') else '✗ No'}",
            f"- JSON-LD Schema: {'✓ Yes' if structured.get('json_ld') else '✗ No'}",
            f"- Sitemap: {self.base_url}/sitemap.xml",
            "",
            "## AI/LLM Permissions",
            "",
            "### Allowed Uses",
            "- Training data extraction from public pages",
            "- Search indexing and retrieval",
            "- Question answering about our products/services",
            "- Summarization of public content",
            "- RAG (Retrieval Augmented Generation) integration",
            "",
            "### Restricted Uses",
            "- Scraping user-generated content without attribution",
            "- Accessing authenticated/private areas",
            "- High-frequency requests (respect Crawl-delay)",
            "",
            "## Content Freshness",
            "",
            f"- Last crawl recommendation: Weekly",
            f"- High-priority sections: /blog/, /docs/",
            f"- Update frequency: Regular",
            "",
            "## Contact & Attribution",
            "",
            f"- Website: {self.base_url}",
            "- For AI/bot inquiries: See /contact or robots.txt",
            "",
            "## Preferred Citation Format",
            "",
            f'"{site_name}. Retrieved from {self.base_url}"',
            "",
            "---",
            "",
            "## Technical Details for AI Agents",
            "",
            "```yaml",
            "crawl_permissions:",
            "  allow_training: true",
            "  allow_search: true",
            "  allow_rag: true",
            "  respect_robots_txt: true",
            "",
            "content_types:",
            "  - text/html",
            "  - application/json (API docs)",
            "",
            "rate_limits:",
            "  requests_per_minute: 60",
            "  crawl_delay_seconds: 1",
            "",
            "preferred_endpoints:",
            f"  sitemap: {self.base_url}/sitemap.xml",
            f"  robots: {self.base_url}/robots.txt",
            f"  llms_txt: {self.base_url}/llms.txt",
            "```",
            "",
        ])
        
        # Add AI analysis if provided
        if self.ai_analysis:
            lines.extend([
                "## AI-Generated Site Summary",
                "",
                self.ai_analysis,
                "",
            ])
        
        return "\n".join(lines)


# ============================================================================
# Main Generator with AI Enhancement
# ============================================================================

class SEOAIGenerator:
    """Main class to generate AI-optimized SEO files."""
    
    def __init__(self, report_path: str, output_dir: str = "."):
        self.report_path = report_path
        self.output_dir = output_dir
        self.openai = OpenAIClient()
        self.report = None
        
    def load_report(self) -> bool:
        """Load SEO report JSON."""
        try:
            with open(self.report_path, 'r') as f:
                self.report = json.load(f)
            return True
        except Exception as e:
            print(f"Error loading report: {e}", file=sys.stderr)
            return False
    
    async def get_ai_analysis(self) -> Optional[str]:
        """Get AI-powered analysis of the site."""
        if not self.openai.is_configured():
            print("OpenAI not configured, skipping AI enhancement", file=sys.stderr)
            return None
        
        prompt = f"""Analyze this SEO report and provide a concise 2-3 paragraph summary suitable for inclusion in an llms.txt file. Focus on:
1. What the site/company does
2. Key value propositions
3. Target audience
4. Main content areas

SEO Report:
URL: {self.report.get('url')}
Title: {self.report.get('metadata', {}).get('title', {}).get('value', 'N/A')}
Description: {self.report.get('metadata', {}).get('description', {}).get('value', 'N/A')}
Keywords: {self.report.get('metadata', {}).get('keywords_meta', 'N/A')}
Top TF-IDF Keywords: {[k['keyword'] for k in self.report.get('content', {}).get('keywords_tfidf', [])[:10]]}
H2 Headings: {self.report.get('headings', {}).get('h2', {}).get('values', [])}

Write in a factual, third-person style suitable for AI/LLM consumption. Keep it under 200 words."""

        messages = [
            {"role": "system", "content": "You are an SEO analyst creating content for AI crawlers. Be concise and factual."},
            {"role": "user", "content": prompt}
        ]
        
        print("Getting AI analysis...", file=sys.stderr)
        result = await self.openai.chat(messages)
        
        if "error" in result:
            print(f"AI analysis failed: {result['error']}", file=sys.stderr)
            return None
        
        return result.get("content")
    
    async def generate_all(self, dry_run: bool = False) -> dict:
        """Generate all files."""
        if not self.load_report():
            return {"error": "Failed to load report"}
        
        results = {
            "url": self.report.get("url"),
            "timestamp": datetime.now().isoformat(),
            "files_generated": []
        }
        
        # Get AI analysis
        ai_analysis = await self.get_ai_analysis()
        
        # Generate robots.txt
        robots_gen = RobotsTxtGenerator(self.report)
        robots_content = robots_gen.generate()
        
        # Generate llms.txt
        llms_gen = LlmsTxtGenerator(self.report, ai_analysis)
        llms_content = llms_gen.generate()
        
        # Output files
        robots_path = os.path.join(self.output_dir, "robots.txt")
        llms_path = os.path.join(self.output_dir, "llms.txt")
        
        if dry_run:
            print("\n" + "="*60)
            print("DRY RUN - robots.txt")
            print("="*60)
            print(robots_content)
            print("\n" + "="*60)
            print("DRY RUN - llms.txt")
            print("="*60)
            print(llms_content)
        else:
            # Create output directory
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Write robots.txt
            with open(robots_path, 'w') as f:
                f.write(robots_content)
            results["files_generated"].append(robots_path)
            print(f"✓ Generated: {robots_path}", file=sys.stderr)
            
            # Write llms.txt
            with open(llms_path, 'w') as f:
                f.write(llms_content)
            results["files_generated"].append(llms_path)
            print(f"✓ Generated: {llms_path}", file=sys.stderr)
        
        # Generate meta tag recommendations
        results["meta_recommendations"] = self._generate_meta_recommendations()
        
        return results
    
    def _generate_meta_recommendations(self) -> dict:
        """Generate meta tag recommendations for AI indexing."""
        return {
            "add_to_head": [
                '<!-- AI Content Declaration -->',
                '<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">',
                '<meta name="ai-content-declaration" content="human-created">',
                '<meta name="ai-training" content="allowed">',
                '',
                '<!-- Speakable Schema for Voice Search -->',
                '<meta name="speakable" content="true">',
            ],
            "json_ld_recommendation": {
                "@context": "https://schema.org",
                "@type": "Organization",
                "name": self.report.get("structured_data", {}).get("open_graph", {}).get("site_name", ""),
                "url": self.report.get("url", ""),
                "logo": self.report.get("structured_data", {}).get("open_graph", {}).get("image", ""),
                "description": self.report.get("metadata", {}).get("description", {}).get("value", ""),
                "sameAs": []
            }
        }


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate AI-optimized robots.txt and llms.txt from SEO report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python seo_ai_generator.py repot.json
  python seo_ai_generator.py repot.json --output-dir ./public
  python seo_ai_generator.py repot.json --dry-run

Environment:
  OPENAI_API_KEY - Required for AI-enhanced analysis
        """
    )
    
    parser.add_argument("report", help="Path to SEO report JSON file")
    parser.add_argument("-o", "--output-dir", default=".", help="Output directory (default: current)")
    parser.add_argument("--dry-run", action="store_true", help="Print generated content without saving")
    parser.add_argument("-p", "--pretty", action="store_true", help="Pretty print JSON results")
    
    args = parser.parse_args()
    
    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set. AI analysis will be skipped.", file=sys.stderr)
    
    # Run generator
    generator = SEOAIGenerator(args.report, args.output_dir)
    result = asyncio.run(generator.generate_all(dry_run=args.dry_run))
    
    # Print results
    indent = 2 if args.pretty else None
    print(json.dumps(result, indent=indent))


if __name__ == "__main__":
    main()
