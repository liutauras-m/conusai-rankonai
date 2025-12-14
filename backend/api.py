"""
FastAPI Backend for SEO Analyzer
Production-ready API with caching, rate limiting, and concurrency control.
"""

import asyncio
import hashlib
import json
import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import redis.asyncio as redis

from seo_analyzer import SEOAnalyzer
from multi_llm import query_multiple_models, MODELS
from seo_ai_generator import RobotsTxtGenerator, LlmsTxtGenerator, OpenAIClient

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT_ANALYSES", "5"))
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour default

# Concurrency semaphore
analysis_semaphore = asyncio.Semaphore(MAX_CONCURRENT)

# FastAPI app
app = FastAPI(
    title="SEO Analyzer API",
    description="Production API for SEO and AI indexing analysis",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection
redis_client: Optional[redis.Redis] = None


class AnalyzeRequest(BaseModel):
    url: HttpUrl


class InsightsRequest(BaseModel):
    prompt: str
    models: Optional[list[str]] = None


class GenerateFilesRequest(BaseModel):
    report: dict


class MarketingRequest(BaseModel):
    analysis: dict


class SuggestionsRequest(BaseModel):
    analysis: dict
    type: str  # "preferences" or "questions"


class AISummaryRequest(BaseModel):
    analysis: dict


class AnalyzeResponse(BaseModel):
    url: str
    timestamp: str
    cached: bool = False
    data: dict


@app.on_event("startup")
async def startup():
    global redis_client
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
        print(f"✓ Connected to Redis at {REDIS_URL}")
    except Exception as e:
        print(f"⚠ Redis connection failed: {e}. Running without cache.")
        redis_client = None


@app.on_event("shutdown")
async def shutdown():
    if redis_client:
        await redis_client.close()


def get_cache_key(url: str) -> str:
    """Generate a cache key for the URL."""
    return f"seo:analysis:{hashlib.sha256(url.encode()).hexdigest()[:16]}"


def get_insights_cache_key(prompt: str, models: list[str]) -> str:
    """Generate a cache key for insights."""
    key_data = f"{prompt}:{','.join(sorted(models))}"
    return f"seo:insights:{hashlib.sha256(key_data.encode()).hexdigest()[:16]}"


def get_files_cache_key(report: dict) -> str:
    """Generate a cache key for generated files."""
    # Use URL and key metrics for cache key
    url = report.get("url", "")
    return f"seo:files:{hashlib.sha256(url.encode()).hexdigest()[:16]}"


def get_marketing_cache_key(analysis: dict) -> str:
    """Generate a cache key for marketing content."""
    url = analysis.get("url", "")
    return f"seo:marketing:{hashlib.sha256(url.encode()).hexdigest()[:16]}"


def get_suggestions_cache_key(analysis: dict, suggestion_type: str) -> str:
    """Generate a cache key for AI suggestions."""
    url = analysis.get("url", "")
    key_data = f"{url}:{suggestion_type}"
    return f"seo:suggestions:{hashlib.sha256(key_data.encode()).hexdigest()[:16]}"


def get_ai_summary_cache_key(analysis: dict) -> str:
    """Generate a cache key for AI summary."""
    url = analysis.get("url", "")
    scores = json.dumps(analysis.get("scores", {}), sort_keys=True)
    key_data = f"{url}:{scores}"
    return f"seo:ai_summary:{hashlib.sha256(key_data.encode()).hexdigest()[:16]}"


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    redis_status = "connected" if redis_client else "disconnected"
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "redis": redis_status,
        "concurrent_limit": MAX_CONCURRENT,
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_url(request: AnalyzeRequest, req: Request):
    """
    Analyze a URL for SEO and AI indexing factors.
    
    - Results are cached for 1 hour
    - Maximum concurrent analyses limited to prevent overload
    - Rate limiting handled by nginx
    """
    url = str(request.url)
    cache_key = get_cache_key(url)
    
    # Check cache first
    if redis_client:
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                data = json.loads(cached)
                return AnalyzeResponse(
                    url=url,
                    timestamp=data.get("timestamp", datetime.now().isoformat()),
                    cached=True,
                    data=data,
                )
        except Exception as e:
            print(f"Cache read error: {e}")
    
    # Acquire semaphore for concurrency control
    try:
        async with asyncio.timeout(5):  # Wait max 5 seconds for a slot
            await analysis_semaphore.acquire()
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=503,
            detail="Server is busy. Please try again in a few moments.",
        )
    
    try:
        # Run the analysis
        analyzer = SEOAnalyzer(url, verbose=False)
        result = await analyzer.analyze()
        
        # Cache the result
        if redis_client:
            try:
                await redis_client.setex(
                    cache_key,
                    CACHE_TTL,
                    json.dumps(result, ensure_ascii=False),
                )
            except Exception as e:
                print(f"Cache write error: {e}")
        
        return AnalyzeResponse(
            url=url,
            timestamp=result.get("timestamp", datetime.now().isoformat()),
            cached=False,
            data=result,
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        analysis_semaphore.release()


@app.post("/insights")
async def generate_insights(request: InsightsRequest):
    """
    Query multiple LLMs in parallel for AI insights.
    
    - Uses GPT-4o and Grok by default
    - Returns responses from all available models
    - Results cached for 1 hour
    """
    prompt = request.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")
    
    # Default models
    models_to_query = request.models if request.models else ["gpt-4o", "grok"]
    
    # Filter to only available models
    available_models = [m for m in models_to_query if m in MODELS]
    if not available_models:
        raise HTTPException(
            status_code=400, 
            detail=f"No valid models specified. Available: {list(MODELS.keys())}"
        )
    
    cache_key = get_insights_cache_key(prompt, available_models)
    
    # Check cache first
    if redis_client:
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                data = json.loads(cached)
                data["cached"] = True
                return data
        except Exception as e:
            print(f"Cache read error: {e}")
    
    try:
        result = await query_multiple_models(prompt, available_models)
        response = {
            "success": True,
            "prompt": prompt,
            "models": available_models,
            "result": result,
            "cached": False,
        }
        
        # Cache the result
        if redis_client:
            try:
                await redis_client.setex(
                    cache_key,
                    CACHE_TTL,
                    json.dumps(response, ensure_ascii=False),
                )
            except Exception as e:
                print(f"Cache write error: {e}")
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-files")
async def generate_files(request: GenerateFilesRequest):
    """
    Generate robots.txt and llms.txt files using AI.
    
    - Uses OpenAI GPT-4o for intelligent content generation
    - Analyzes the SEO report to create optimized files
    - Results cached for 1 hour
    """
    report = request.report
    if not report:
        raise HTTPException(status_code=400, detail="Report is required")
    
    cache_key = get_files_cache_key(report)
    
    # Check cache first
    if redis_client:
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                data = json.loads(cached)
                data["cached"] = True
                return data
        except Exception as e:
            print(f"Cache read error: {e}")
    
    openai_client = OpenAIClient()
    
    try:
        # Generate robots.txt using AI
        robots_gen = RobotsTxtGenerator(report, openai_client)
        robots_content = await robots_gen.generate()
        
        # Generate llms.txt using AI
        llms_gen = LlmsTxtGenerator(report, openai_client)
        llms_content = await llms_gen.generate()
        
        response = {
            "success": True,
            "ai_powered": openai_client.is_configured(),
            "robots_txt": robots_content,
            "llms_txt": llms_content,
            "cached": False,
        }
        
        # Cache the result
        if redis_client:
            try:
                await redis_client.setex(
                    cache_key,
                    CACHE_TTL,
                    json.dumps(response, ensure_ascii=False),
                )
            except Exception as e:
                print(f"Cache write error: {e}")
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-marketing")
async def generate_marketing(request: MarketingRequest):
    """
    Generate content marketing recommendations using AI.
    
    - Generates target keywords with search intent
    - Creates ready-to-use social media posts
    - Suggests content ideas for the brand
    - Results cached for 1 hour
    """
    analysis = request.analysis
    if not analysis:
        raise HTTPException(status_code=400, detail="Analysis is required")
    
    cache_key = get_marketing_cache_key(analysis)
    
    # Check cache first
    if redis_client:
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                data = json.loads(cached)
                data["cached"] = True
                return data
        except Exception as e:
            print(f"Cache read error: {e}")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
    
    try:
        # Extract context from analysis
        metadata = analysis.get("metadata", {})
        content = analysis.get("content", {})
        llm_context = analysis.get("llm_context", {})
        
        brand = metadata.get("title", {}).get("value") or analysis.get("url", "the brand")
        description = metadata.get("description", {}).get("value") or ""
        url = analysis.get("url", "")
        
        # Get keywords from multiple sources
        freq_kw = [k.get("keyword", "") for k in content.get("keywords_frequency", [])[:15]]
        top_kw = llm_context.get("top_keywords", [])[:10]
        bigrams = [b.get("phrase", "") for b in content.get("top_bigrams", [])[:5]]
        trigrams = [t.get("phrase", "") for t in content.get("top_trigrams", [])[:3]]
        scores = analysis.get("scores", {})
        
        system_prompt = """You are an expert content marketing strategist specializing in SEO and social media marketing. 
Generate actionable marketing recommendations based on SEO analysis data.
Return valid JSON only, no markdown formatting or code blocks."""

        user_prompt = f"""Based on this comprehensive SEO analysis, generate content marketing recommendations:

WEBSITE ANALYSIS:
- URL: {url}
- Brand/Title: {brand}
- Description: {description}
- Word Count: {content.get("word_count", "N/A")}
- Current SEO Scores: {json.dumps(scores)}

EXTRACTED KEYWORDS (from page analysis):
- Frequency keywords: {", ".join(freq_kw)}
- Top semantic keywords: {", ".join(top_kw)}
- Key phrases (bigrams): {", ".join(bigrams)}
- Key phrases (trigrams): {", ".join(trigrams)}

TASK: Generate a JSON object with these three sections:

1. "targetKeywords": Array of 8 strategic keywords/phrases to target. For each:
   - "keyword": The keyword or phrase to target
   - "searchIntent": One of "informational", "transactional", "navigational", "commercial"
   - "difficulty": Estimated ranking difficulty "low", "medium", or "high"
   - "tip": A brief actionable tip on how to use this keyword

2. "socialPosts": Array of 3 ready-to-use social media posts (one for each platform):
   - "platform": "facebook", "linkedin", or "twitter"
   - "content": The full post text (appropriate length for each platform)
   - "hashtags": Array of 3-5 relevant hashtags
   - "callToAction": A clear CTA for the post
   - "bestTimeToPost": Suggested best time to post

3. "contentIdeas": Array of 5 blog post or content ideas

Return ONLY the JSON object with these three keys: targetKeywords, socialPosts, contentIdeas."""

        import httpx
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openai_key}",
                },
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2500,
                },
            )
            resp.raise_for_status()
            openai_data = resp.json()
        
        raw_content = openai_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Clean markdown code blocks
        cleaned = raw_content.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        marketing_data = json.loads(cleaned)
        
        response = {
            "success": True,
            "data": marketing_data,
            "cached": False,
        }
        
        # Cache the result
        if redis_client:
            try:
                await redis_client.setex(
                    cache_key,
                    CACHE_TTL,
                    json.dumps(response, ensure_ascii=False),
                )
            except Exception as e:
                print(f"Cache write error: {e}")
        
        return response
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-suggestions")
async def generate_suggestions(request: SuggestionsRequest):
    """
    Generate AI-powered preferences or questions based on analysis.
    
    - type="preferences": Generate user preference options
    - type="questions": Generate strategic questions for AI discoverability
    - Results cached for 1 hour
    """
    analysis = request.analysis
    suggestion_type = request.type
    
    if not analysis:
        raise HTTPException(status_code=400, detail="Analysis is required")
    if suggestion_type not in ("preferences", "questions"):
        raise HTTPException(status_code=400, detail="Type must be 'preferences' or 'questions'")
    
    cache_key = get_suggestions_cache_key(analysis, suggestion_type)
    
    # Check cache first
    if redis_client:
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                data = json.loads(cached)
                data["cached"] = True
                return data
        except Exception as e:
            print(f"Cache read error: {e}")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
    
    try:
        # Extract context
        metadata = analysis.get("metadata", {})
        content = analysis.get("content", {})
        llm_context = analysis.get("llm_context", {})
        
        brand = metadata.get("title", {}).get("value") or analysis.get("url", "the brand")
        description = metadata.get("description", {}).get("value") or ""
        keywords = llm_context.get("top_keywords", [])[:10] or \
            [k.get("keyword", "") for k in content.get("keywords_frequency", [])[:10]]
        scores = analysis.get("scores", {})
        
        if suggestion_type == "preferences":
            system_prompt = "You are an AI SEO expert. Generate user preference options based on SEO analysis. Return valid JSON only."
            user_prompt = f"""Based on this website analysis, generate 4 personalized preference options that users can select to focus their AI optimization efforts.

WEBSITE CONTEXT:
- Brand: {brand}
- Description: {description}
- Top Keywords: {", ".join(keywords)}
- Current Scores: {json.dumps(scores)}

Generate 4 preference options as a JSON array. Each option should be relevant to this specific website's content and goals.

Format:
[
  {{"id": "unique_snake_case_id", "label": "Short Label (2-3 words)", "detail": "One sentence explaining how this preference helps AI recommend this brand."}}
]

Return ONLY the JSON array, no markdown or explanation."""
        else:
            system_prompt = "You are an AI brand strategist. Generate questions users should answer to improve AI discoverability. Return valid JSON only."
            user_prompt = f"""Based on this website analysis, generate 5 strategic questions that will help improve how AI assistants recommend this brand.

WEBSITE CONTEXT:
- Brand: {brand}
- Description: {description}
- Top Keywords: {", ".join(keywords)}

Generate questions as a JSON array of strings. Questions should:
1. Be specific to this brand/website
2. Help craft FAQs and AI-friendly content
3. Focus on what makes this brand recommendable

Format:
["Question 1?", "Question 2?", "Question 3?", "Question 4?", "Question 5?"]

Return ONLY the JSON array, no markdown or explanation."""

        import httpx
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openai_key}",
                },
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1024,
                },
            )
            resp.raise_for_status()
            openai_data = resp.json()
        
        raw_content = openai_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Clean markdown code blocks
        cleaned = raw_content.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        result_data = json.loads(cleaned)
        
        response = {
            "success": True,
            "data": result_data,
            "type": suggestion_type,
            "cached": False,
        }
        
        # Cache the result
        if redis_client:
            try:
                await redis_client.setex(
                    cache_key,
                    CACHE_TTL,
                    json.dumps(response, ensure_ascii=False),
                )
            except Exception as e:
                print(f"Cache write error: {e}")
        
        return response
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai-summary")
async def generate_ai_summary(request: AISummaryRequest):
    """
    Generate AI-powered summary with improvement recommendations.
    
    - Explains each score category with actionable insights
    - Provides platform-specific tips for ChatGPT, Claude, Gemini, Perplexity, etc.
    - Prioritizes actions based on impact
    - Results cached for 1 hour
    """
    analysis = request.analysis
    if not analysis:
        raise HTTPException(status_code=400, detail="Analysis is required")
    
    cache_key = get_ai_summary_cache_key(analysis)
    
    # Check cache first
    if redis_client:
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                data = json.loads(cached)
                data["cached"] = True
                return data
        except Exception as e:
            print(f"Cache read error: {e}")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
    
    try:
        # Extract comprehensive context from analysis
        url = analysis.get("url", "")
        scores = analysis.get("scores", {})
        metadata = analysis.get("metadata", {})
        content = analysis.get("content", {})
        structured_data = analysis.get("structured_data", {})
        ai_indexing = analysis.get("ai_indexing", {})
        issues = analysis.get("issues", [])
        recommendations = analysis.get("recommendations", [])
        llm_context = analysis.get("llm_context", {})
        
        # Extract bot statuses
        bot_status = ai_indexing.get("robots_txt", {}).get("ai_bots_status", {})
        
        # Format issues for prompt
        issues_text = "\n".join([
            f"- [{i.get('severity', 'unknown').upper()}] {i.get('message', '')}"
            for i in issues[:10]
        ]) or "No significant issues found."
        
        # Format bot access
        allowed_bots = [bot for bot, status in bot_status.items() if "allowed" in status.lower()]
        blocked_bots = [bot for bot, status in bot_status.items() if "blocked" in status.lower()]
        
        system_prompt = """You are a senior AI SEO strategist specializing in optimizing websites for AI assistant discoverability. 
Your expertise spans all major AI platforms: ChatGPT/GPT-4, Claude, Gemini, Perplexity, Microsoft Copilot, Mistral, and others.
Analyze SEO reports and provide actionable, expert-level recommendations.
Return valid JSON only, no markdown formatting or code blocks."""

        user_prompt = f"""Analyze this comprehensive SEO report and generate an AI discoverability improvement summary.

WEBSITE: {url}

CURRENT SCORES (0-100):
- Overall: {scores.get('overall', 0)}
- AI Readiness: {scores.get('ai_readiness', 0)}
- Content: {scores.get('content', 0)}
- Structured Data: {scores.get('structured_data', 0)}
- On-Page SEO: {scores.get('on_page', 0)}
- Technical: {scores.get('technical', 0)}

METADATA:
- Title: {metadata.get('title', {}).get('value', 'N/A')}
- Description: {metadata.get('description', {}).get('value', 'N/A')}
- Has Canonical: {bool(metadata.get('canonical'))}
- Language: {metadata.get('language', 'N/A')}

CONTENT ANALYSIS:
- Word Count: {content.get('word_count', 0)}
- Top Keywords: {', '.join([k.get('keyword', '') for k in content.get('keywords_frequency', [])[:8]])}
- Readability (Flesch): {content.get('readability', {}).get('flesch_reading_ease', 'N/A')}

STRUCTURED DATA:
- JSON-LD Schemas: {len(structured_data.get('json_ld', []))} found
- Has Open Graph: {bool(structured_data.get('open_graph'))}
- Has Twitter Card: {bool(structured_data.get('twitter_card'))}

AI BOT ACCESS:
- Has llms.txt: {ai_indexing.get('llms_txt', {}).get('present', False)}
- Has sitemap.xml: {ai_indexing.get('sitemap_xml', {}).get('present', False)}
- Allowed AI Bots: {', '.join(allowed_bots[:10]) if allowed_bots else 'None explicitly allowed'}
- Blocked AI Bots: {', '.join(blocked_bots) if blocked_bots else 'None blocked'}

CURRENT ISSUES:
{issues_text}

Generate a JSON response with this exact structure:

{{
  "overallAssessment": {{
    "rating": "Excellent|Good|Needs Improvement|Poor",
    "summary": "2-3 sentence executive summary of AI discoverability status",
    "primaryStrength": "The main thing this site does well for AI",
    "primaryWeakness": "The most critical improvement needed"
  }},
  "scoreBreakdown": [
    {{
      "category": "AI Readiness",
      "score": {scores.get('ai_readiness', 0)},
      "rating": "Excellent|Good|Fair|Poor",
      "explanation": "What this score means for AI discoverability",
      "improvement": "Specific action to improve this score"
    }},
    {{
      "category": "Content",
      "score": {scores.get('content', 0)},
      "rating": "Excellent|Good|Fair|Poor", 
      "explanation": "How content quality affects AI understanding",
      "improvement": "Content optimization suggestion"
    }},
    {{
      "category": "Rich Data",
      "score": {scores.get('structured_data', 0)},
      "rating": "Excellent|Good|Fair|Poor",
      "explanation": "Schema markup quality for AI extraction",
      "improvement": "Structured data recommendation"
    }},
    {{
      "category": "Structure",
      "score": {scores.get('on_page', 0)},
      "rating": "Excellent|Good|Fair|Poor",
      "explanation": "How headings and meta info help AI",
      "improvement": "On-page optimization tip"
    }},
    {{
      "category": "Technical",
      "score": {scores.get('technical', 0)},
      "rating": "Excellent|Good|Fair|Poor",
      "explanation": "Speed and security impact on AI crawling",
      "improvement": "Technical enhancement suggestion"
    }}
  ],
  "platformInsights": [
    {{
      "platform": "ChatGPT",
      "status": "Optimized|Partially Optimized|Needs Work",
      "tip": "Specific tip to improve discoverability on ChatGPT/OpenAI",
      "botName": "GPTBot"
    }},
    {{
      "platform": "Claude",
      "status": "Optimized|Partially Optimized|Needs Work",
      "tip": "Specific tip for Claude/Anthropic",
      "botName": "ClaudeBot"
    }},
    {{
      "platform": "Gemini",
      "status": "Optimized|Partially Optimized|Needs Work",
      "tip": "Specific tip for Google Gemini",
      "botName": "Google-Extended"
    }},
    {{
      "platform": "Perplexity",
      "status": "Optimized|Partially Optimized|Needs Work",
      "tip": "Specific tip for Perplexity AI search",
      "botName": "PerplexityBot"
    }},
    {{
      "platform": "Copilot",
      "status": "Optimized|Partially Optimized|Needs Work",
      "tip": "Specific tip for Microsoft Copilot",
      "botName": "bingbot"
    }},
    {{
      "platform": "Mistral",
      "status": "Optimized|Partially Optimized|Needs Work",
      "tip": "Specific tip for Mistral AI",
      "botName": "MistralBot"
    }}
  ],
  "prioritizedActions": [
    {{
      "priority": 1,
      "action": "Most important action to take",
      "impact": "High|Medium|Low",
      "effort": "Quick Win|Moderate|Significant",
      "category": "ai_readiness|content|structured_data|technical"
    }},
    {{
      "priority": 2,
      "action": "Second most important action",
      "impact": "High|Medium|Low",
      "effort": "Quick Win|Moderate|Significant",
      "category": "ai_readiness|content|structured_data|technical"
    }},
    {{
      "priority": 3,
      "action": "Third action",
      "impact": "High|Medium|Low",
      "effort": "Quick Win|Moderate|Significant",
      "category": "ai_readiness|content|structured_data|technical"
    }}
  ],
  "quickWins": [
    "Easy improvement 1 that can be done today",
    "Easy improvement 2",
    "Easy improvement 3"
  ]
}}

Return ONLY the JSON object, no markdown or explanation."""

        import httpx
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openai_key}",
                },
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 3000,
                },
            )
            resp.raise_for_status()
            openai_data = resp.json()
        
        raw_content = openai_data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Clean markdown code blocks
        cleaned = raw_content.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        summary_data = json.loads(cleaned)
        
        response = {
            "success": True,
            "url": url,
            "scores": scores,
            "summary": summary_data,
            "cached": False,
        }
        
        # Cache the result
        if redis_client:
            try:
                await redis_client.setex(
                    cache_key,
                    CACHE_TTL,
                    json.dumps(response, ensure_ascii=False),
                )
            except Exception as e:
                print(f"Cache write error: {e}")
        
        return response
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cache/{url:path}")
async def clear_cache(url: str):
    """Clear cached results for a specific URL."""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Cache not available")
    
    cache_key = get_cache_key(url)
    deleted = await redis_client.delete(cache_key)
    
    return {"cleared": bool(deleted), "url": url}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
