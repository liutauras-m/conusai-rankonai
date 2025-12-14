# SEO & AI Indexing Analyzer

A comprehensive Python tool to analyze web pages for SEO optimization and AI model indexing (ChatGPT, Grok, Claude, Perplexity, etc.).

---

## Features

- **Async Parallel Fetching** - Fetches main page, robots.txt, sitemap.xml, and llms.txt simultaneously
- **Meta Tags Analysis** - Title, description, canonical, viewport, robots directives
- **Heading Structure** - H1-H6 analysis with hierarchy validation
- **Image Analysis** - Alt text detection, lazy loading status
- **Link Analysis** - Internal/external links, nofollow attributes
- **Keyword Extraction** - TF-IDF and frequency-based extraction
- **Readability Scores** - Flesch-Kincaid, Gunning Fog, SMOG, and more
- **Structured Data** - JSON-LD, Open Graph, Twitter Cards validation
- **AI Bot Detection** - Checks permissions for 19+ AI crawlers
- **LLM Context Generation** - Ready-to-use prompts for AI improvement suggestions
- **Scoring System** - Technical, on-page, content, structured data, AI readiness scores

---

## Installation

### 1. Create Virtual Environment

```bash
cd /path/to/conuai-tools
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### Required Packages

| Package | Purpose |
|---------|---------|
| `aiohttp` | Async HTTP requests |
| `beautifulsoup4` | HTML parsing |
| `lxml` | Fast HTML/XML parser |
| `textstat` | Readability analysis |
| `scikit-learn` | TF-IDF keyword extraction (optional) |
| `validators` | URL validation (optional) |

---

## Usage

### Basic Usage

```bash
python seo_analyzer.py https://example.com
```

### With Options

```bash
# Verbose output with progress info
python seo_analyzer.py https://example.com --verbose

# Pretty-print JSON output
python seo_analyzer.py https://example.com --pretty

# Save to file
python seo_analyzer.py https://example.com --output report.json

# All options combined
python seo_analyzer.py https://example.com --verbose --pretty --output report.json
```

### Command Line Arguments

| Argument | Short | Description |
|----------|-------|-------------|
| `url` | - | URL to analyze (required) |
| `--output` | `-o` | Output file path (default: stdout) |
| `--verbose` | `-v` | Enable verbose output with progress info |
| `--pretty` | `-p` | Pretty-print JSON with indentation |

---

## Output Structure

The analyzer returns a comprehensive JSON report:

```json
{
  "url": "https://example.com",
  "timestamp": "2025-12-14T10:30:00Z",
  "crawl_time_ms": 1234,
  
  "scores": {
    "overall": 78,
    "technical": 85,
    "on_page": 72,
    "content": 80,
    "structured_data": 75,
    "ai_readiness": 65
  },
  
  "metadata": { ... },
  "headings": { ... },
  "images": { ... },
  "links": { ... },
  "content": { ... },
  "structured_data": { ... },
  "technical": { ... },
  "ai_indexing": { ... },
  "issues": [ ... ],
  "recommendations": [ ... ],
  "llm_context": { ... }
}
```

### Scores

| Score | Description |
|-------|-------------|
| `overall` | Average of all category scores |
| `technical` | HTTPS, response time, headers |
| `on_page` | Title, meta description, headings, images |
| `content` | Word count, readability, keywords |
| `structured_data` | JSON-LD, Open Graph, Twitter Cards |
| `ai_readiness` | llms.txt, AI bot permissions |

### Metadata Analysis

```json
{
  "metadata": {
    "title": {
      "value": "Page Title",
      "length": 45,
      "issues": [],
      "recommendations": []
    },
    "description": {
      "value": "Meta description...",
      "length": 155,
      "issues": [],
      "recommendations": []
    },
    "canonical": "https://example.com/page",
    "robots_meta": "index, follow",
    "viewport": "width=device-width, initial-scale=1",
    "language": "en"
  }
}
```

### Content Analysis

```json
{
  "content": {
    "word_count": 1250,
    "readability": {
      "flesch_reading_ease": 65.3,
      "flesch_kincaid_grade": 8.2,
      "gunning_fog": 10.1,
      "smog_index": 9.5,
      "automated_readability_index": 8.8,
      "reading_time_minutes": 5.2
    },
    "keywords_tfidf": [
      {"keyword": "python seo", "tfidf_score": 0.85, "count": 8}
    ],
    "keywords_frequency": [
      {"keyword": "seo", "count": 12, "density_percent": 0.96}
    ],
    "top_bigrams": [
      {"phrase": "seo analyzer", "count": 5}
    ],
    "top_trigrams": [
      {"phrase": "python seo tool", "count": 3}
    ]
  }
}
```

### AI Indexing Analysis

```json
{
  "ai_indexing": {
    "robots_txt": {
      "present": true,
      "ai_bots_status": {
        "GPTBot": "allowed",
        "ClaudeBot": "allowed",
        "PerplexityBot": "blocked",
        "Google-Extended": "allowed_by_default"
      },
      "sitemaps_declared": ["https://example.com/sitemap.xml"]
    },
    "llms_txt": {
      "present": true,
      "content_preview": "# Site Name\n> Description..."
    },
    "sitemap_xml": {
      "present": true
    }
  }
}
```

### AI Bots Monitored

| Bot | Service |
|-----|---------|
| `GPTBot` | OpenAI training |
| `OAI-SearchBot` | ChatGPT search |
| `ChatGPT-User` | ChatGPT browsing |
| `ClaudeBot` | Anthropic training |
| `Claude-Web` | Claude web access |
| `anthropic-ai` | Anthropic AI |
| `Google-Extended` | Gemini/Bard training |
| `GoogleOther` | Google services |
| `PerplexityBot` | Perplexity AI |
| `Bytespider` | ByteDance/TikTok |
| `CCBot` | Common Crawl |
| `Amazonbot` | Amazon Alexa/AI |
| `Applebot-Extended` | Apple AI |
| `cohere-ai` | Cohere AI |
| `Diffbot` | Diffbot |
| `FacebookBot` | Meta AI |
| `Meta-ExternalAgent` | Meta AI |
| `omgili` | Webz.io |
| `Timpibot` | Timpi search |

### Issues & Recommendations

```json
{
  "issues": [
    {
      "severity": "high",
      "category": "on_page",
      "code": "META_DESC_MISSING",
      "message": "Page is missing a meta description",
      "element": null
    }
  ],
  "recommendations": [
    {
      "priority": 1,
      "category": "on_page",
      "action": "Add a compelling meta description (150-160 characters)"
    }
  ]
}
```

#### Issue Severities

| Severity | Description |
|----------|-------------|
| `high` | Critical issues affecting SEO significantly |
| `medium` | Important issues to address |
| `low` | Minor improvements |

#### Issue Categories

| Category | Description |
|----------|-------------|
| `technical` | HTTPS, canonical, viewport, sitemap |
| `on_page` | Title, meta description, headings, images, links |
| `content` | Word count, readability |
| `structured_data` | JSON-LD, Open Graph, Twitter Cards |
| `ai_indexing` | llms.txt, AI bot permissions |

### LLM Context

The `llm_context` field provides a ready-to-use summary for AI analysis:

```json
{
  "llm_context": {
    "summary": "SEO analysis for https://example.com",
    "overall_score": 78,
    "critical_issues_count": 2,
    "total_issues_count": 8,
    "key_metrics": {
      "has_title": true,
      "has_meta_description": false,
      "has_h1": true,
      "word_count": 1250,
      "has_schema": true,
      "has_og_tags": true,
      "is_https": true,
      "has_llms_txt": false,
      "has_sitemap": true
    },
    "top_keywords": ["python", "seo", "analyzer"],
    "prompt_for_improvement": "Analyze this SEO report..."
  }
}
```

---

## Issue Codes Reference

### On-Page Issues

| Code | Description |
|------|-------------|
| `TITLE_MISSING` | No title tag found |
| `TITLE_TOO_SHORT` | Title under 30 characters |
| `TITLE_TOO_LONG` | Title over 60 characters |
| `META_DESC_MISSING` | No meta description |
| `META_DESC_TOO_SHORT` | Description under 70 characters |
| `META_DESC_TOO_LONG` | Description over 160 characters |
| `H1_MISSING` | No H1 tag found |
| `MULTIPLE_H1` | More than one H1 tag |
| `HEADING_HIERARCHY` | Skipped heading levels |
| `MISSING_ALT` | Images without alt text |
| `NO_INTERNAL_LINKS` | No internal links on page |
| `LANG_MISSING` | HTML lang attribute missing |

### Technical Issues

| Code | Description |
|------|-------------|
| `CANONICAL_MISSING` | No canonical URL specified |
| `VIEWPORT_MISSING` | No viewport meta tag |
| `NO_SITEMAP` | sitemap.xml not found |

### Structured Data Issues

| Code | Description |
|------|-------------|
| `NO_SCHEMA` | No JSON-LD structured data |
| `NO_OG` | No Open Graph tags |
| `OG_NO_IMAGE` | Open Graph image missing |
| `NO_TWITTER_CARD` | No Twitter Card tags |

### AI Indexing Issues

| Code | Description |
|------|-------------|
| `NO_LLMS_TXT` | llms.txt file not found |
| `AI_BOTS_BLOCKED` | Some AI bots blocked in robots.txt |

---

## Programmatic Usage

You can also use the analyzer as a Python module:

```python
import asyncio
from seo_analyzer import SEOAnalyzer

async def analyze_page():
    analyzer = SEOAnalyzer("https://example.com", verbose=True)
    result = await analyzer.analyze()
    
    print(f"Overall Score: {result['scores']['overall']}")
    print(f"Issues Found: {len(result['issues'])}")
    
    for issue in result['issues']:
        print(f"  [{issue['severity'].upper()}] {issue['message']}")
    
    return result

# Run the analysis
result = asyncio.run(analyze_page())
```

### Using Individual Components

```python
from seo_analyzer import (
    AsyncFetcher,
    HTMLAnalyzer,
    ContentAnalyzer,
    RobotsParser
)

# Fetch pages
fetcher = AsyncFetcher(timeout=30)
responses = await fetcher.fetch_all([
    "https://example.com",
    "https://example.com/robots.txt"
])

# Analyze HTML
html_analyzer = HTMLAnalyzer(html_content, base_url)
meta_tags = html_analyzer.analyze_meta_tags()
headings = html_analyzer.analyze_headings()

# Analyze content
content_analyzer = ContentAnalyzer(text_content)
keywords = content_analyzer.extract_keywords_tfidf(top_n=20)
readability = content_analyzer.get_readability()

# Parse robots.txt
robots = RobotsParser(robots_content)
ai_status = robots.get_ai_bot_status()
```

---

## Examples

### Analyzing Multiple Sites

```bash
#!/bin/bash
sites=("https://site1.com" "https://site2.com" "https://site3.com")

for site in "${sites[@]}"; do
    filename=$(echo $site | sed 's/https:\/\///' | sed 's/\//_/g')
    python seo_analyzer.py "$site" --output "reports/${filename}.json"
done
```

### Extracting Specific Data with jq

```bash
# Get overall score
python seo_analyzer.py https://example.com | jq '.scores.overall'

# List all high severity issues
python seo_analyzer.py https://example.com | jq '.issues[] | select(.severity == "high")'

# Get top 5 keywords
python seo_analyzer.py https://example.com | jq '.content.keywords_frequency[:5]'

# Check AI bot status
python seo_analyzer.py https://example.com | jq '.ai_indexing.robots_txt.ai_bots_status'
```

### Integration with CI/CD

```yaml
# .github/workflows/seo-check.yml
name: SEO Check

on:
  push:
    branches: [main]

jobs:
  seo-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run SEO Analysis
        run: |
          python seo_analyzer.py https://yoursite.com --output seo-report.json
          
      - name: Check Score
        run: |
          score=$(cat seo-report.json | jq '.scores.overall')
          if [ "$score" -lt 70 ]; then
            echo "SEO score too low: $score"
            exit 1
          fi
```

---

## Troubleshooting

### SSL Certificate Errors

The analyzer disables SSL verification by default. If you need strict SSL:

```python
# In seo_analyzer.py, change:
async with session.get(url, headers=self.headers, ssl=False) as response:
# To:
async with session.get(url, headers=self.headers, ssl=True) as response:
```

### Timeout Issues

Increase the timeout for slow sites:

```python
analyzer = SEOAnalyzer(url, verbose=True)
analyzer.fetcher = AsyncFetcher(timeout=60)  # 60 seconds
```

### JavaScript-Rendered Content

This analyzer fetches raw HTML and doesn't execute JavaScript. For SPAs:

1. Use server-side rendering (SSR)
2. Pre-render pages for crawlers
3. Consider adding Playwright integration for JS rendering

---

## Contributing

Feel free to submit issues and enhancement requests!

---

## License

MIT License - feel free to use in your projects.

---

## Related Resources

- [SEO & AI Indexing Best Practices](README.MD) - Comprehensive guide in this repo
- [llms.txt Specification](https://llmstxt.org/)
- [Schema.org Documentation](https://schema.org/)
- [Google SEO Starter Guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)
- [OpenAI GPTBot Documentation](https://platform.openai.com/docs/gptbot)
