# Copilot Instructions for ConuAI Tools

## Project Overview
SEO & AI Indexing analysis tool with **FastAPI backend** + **Next.js 15 frontend**. Analyzes websites for traditional SEO factors and AI crawler readiness (GPTBot, ClaudeBot, etc.).

## Architecture

### Workflow Pattern (Critical)
Backend uses a **step-based async workflow** via TaskIQ + Redis:
1. `POST /workflow/start` → returns `job_id`
2. `GET /workflow/{job_id}/status` → poll progress
3. `GET /workflow/{job_id}/result` → get results

Steps execute in order: **Overview** → then parallel: **Insights, Signals, Keywords, Marketing, Social**

### Adding New Workflow Tasks
1. Create class in `backend/tasks/` inheriting from `WorkflowTask` (see [base.py](backend/tasks/base.py))
2. Set `TASK_NAME` and `REQUIRES_OVERVIEW` (True if needs overview data)
3. Implement `async execute() -> dict`
4. Register in [tasks/__init__.py](backend/tasks/__init__.py)

### Service Layer
- `OpenAIService` / `GrokService` - LLM calls with `complete()` and `complete_json()` methods
- `CacheService` - Redis caching wrapper
- `WorkflowService` - Job state management via Redis
- `LanguageDetector` - Multi-source language detection (see [language.py](backend/utils/language.py))

### Language Detection
Language is detected using multiple sources (priority order):
1. HTML `lang` attribute
2. `Content-Language` HTTP header
3. `og:locale` meta tag
4. `hreflang` link tags
5. Content analysis (fallback)

Use `get_language_context_for_ai()` to format language info for LLM prompts. All AI tasks automatically include language context for localized responses.

### Social Metadata Analysis
Social sharing metadata is analyzed in `HTMLAnalyzer.analyze_social_metadata()`:
- Open Graph tags (Facebook, LinkedIn, WhatsApp, Slack)
- Twitter Card tags
- Social images with dimensions
- Platform compatibility scores (per platform)

The `SocialTask` generates AI-powered recommendations for improving social sharing.

## Key Conventions

### General
- Always use regular hyphens `-` instead of em dashes `—` in code and documentation

### Backend (Python)
- **Pydantic v2** models in `backend/models/` - use `model_config = ConfigDict(...)` pattern
- **Protocol classes** for interfaces (see `ILLMService` in [openai_service.py](backend/services/openai_service.py))
- Config via `backend/config.py` - use `get_api_key("provider")` for API keys
- All async code - use `httpx.AsyncClient` for HTTP calls

### Frontend (TypeScript/Next.js)
- **App Router** with route groups: `frontend/src/app/report/(sections)/`
- State via `ReportContext` in [report-context.tsx](frontend/src/app/report/report-context.tsx)
- API routes proxy to backend: `frontend/src/app/api/workflow/route.ts`
- UI: shadcn/ui components in `frontend/src/components/ui/`
- **Biome** for linting/formatting (not ESLint): `pnpm check:fix`

## Development Commands

```bash
# Frontend
cd frontend && pnpm dev          # Start Next.js (Turbopack)
pnpm check:fix                   # Biome lint + format

# Backend  
cd backend
uvicorn fast_api:app --reload    # Start API server
taskiq worker tasks.broker:broker # Start task worker (separate terminal)

# Docker (full stack)
docker compose up                # Runs nginx + frontend + backend + worker + redis
```

## Environment Variables
Root `.env` file (see `backend/config.py` for loading):
- `OPENAI_API_KEY`, `XAI_API_KEY`, `ANTHROPIC_API_KEY` - LLM providers
- `REDIS_URL` - defaults to `redis://localhost:6379`
- `NEXT_PUBLIC_TURNSTILE_SITE_KEY` / `TURNSTILE_SECRET_KEY` - Cloudflare CAPTCHA

## File Patterns
| Pattern | Location |
|---------|----------|
| API models | `backend/models/api.py` |
| SEO analysis logic | `backend/libs/seo/` |
| HTML/content parsing | `backend/analyzers/`, `backend/utils/` |
| Language detection | `backend/utils/language.py` |
| Report UI sections | `frontend/src/app/report/(sections)/{step}/` |
| UI components | `frontend/src/components/` (shadcn pattern) |
