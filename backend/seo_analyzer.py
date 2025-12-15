#!/usr/bin/env python3
"""
SEO & AI Indexing Analyzer - CLI Entry Point.

A comprehensive tool to analyze web pages for SEO and AI model indexing improvements.
Outputs structured JSON with issues, recommendations, and extracted data for LLM guidance.

Usage:
    python seo_analyzer.py https://example.com
    python seo_analyzer.py https://example.com --output report.json
    python seo_analyzer.py https://example.com --verbose
"""

import argparse
import asyncio
import json

# Import from libs
from libs.seo import SEOAnalyzer


# ============================================================================
# CLI Interface
# ============================================================================

def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
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
    
    return parser


def print_header(url: str) -> None:
    """Print analysis header."""
    print(f"\n{'='*60}")
    print("SEO & AI Indexing Analyzer")
    print(f"{'='*60}")
    print(f"Target URL: {url}")
    print(f"{'='*60}\n")


def print_summary(result: dict) -> None:
    """Print analysis summary to console."""
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Overall Score: {result['scores']['overall']}/100")
    print(f"Issues Found: {len(result['issues'])}")
    print(f"  - High: {len([i for i in result['issues'] if i['severity'] == 'high'])}")
    print(f"  - Medium: {len([i for i in result['issues'] if i['severity'] == 'medium'])}")
    print(f"  - Low: {len([i for i in result['issues'] if i['severity'] == 'low'])}")
    
    top_keywords = ", ".join([
        k["keyword"] for k in result["content"]["keywords_frequency"][:5]
    ])
    print(f"\nTop Keywords: {top_keywords}")
    print(f"Word Count: {result['content']['word_count']}")
    
    ai_ready = "Yes" if result["ai_indexing"]["llms_txt"]["present"] else "No (missing llms.txt)"
    print(f"AI Ready: {ai_ready}")
    print(f"{'='*60}\n")


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Validate URL
    url = args.url
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Print header if verbose
    if args.verbose:
        print_header(url)
    
    # Run analysis
    analyzer = SEOAnalyzer(url, verbose=args.verbose)
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
        print_summary(result)


if __name__ == "__main__":
    main()
