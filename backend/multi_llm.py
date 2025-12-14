#!/usr/bin/env python3
"""
Multi-LLM Parallel Query Tool
Query multiple AI models (GPT-4, Claude, Gemini, Grok, DeepSeek, Mistral) in parallel.
Returns structured JSON with responses from each model.

Usage:
    python multi_llm.py "Your prompt here"
    python multi_llm.py "Your prompt here" --models gpt-4,claude,grok
    python multi_llm.py "Your prompt here" --output responses.json
    cat seo_report.json | python multi_llm.py --stdin
"""

import asyncio
import json
import os
import sys
import argparse
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional
import time

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config import get_api_key
except ImportError:
    # Fallback if config not available
    def get_api_key(provider):
        key_mapping = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY", 
            "google": "GOOGLE_API_KEY",
            "xai": "XAI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "mistral": "MISTRAL_API_KEY",
            "groq": "GROQ_API_KEY",
        }
        env_key = key_mapping.get(provider.lower(), f"{provider.upper()}_API_KEY")
        value = os.environ.get(env_key, "")
        return value if value else None

# Check for required package
try:
    import aiohttp
except ImportError:
    print("Missing aiohttp. Install with: pip install aiohttp")
    sys.exit(1)


# ============================================================================
# Configuration - Model Definitions
# ============================================================================

@dataclass
class ModelConfig:
    """Configuration for an AI model."""
    name: str
    provider: str
    model_id: str
    api_base: str
    api_key_env: str
    max_tokens: int = 4096
    supports_system: bool = True


# Available models configuration
MODELS = {
    # OpenAI
    "gpt-4": ModelConfig(
        name="GPT-4 Turbo",
        provider="openai",
        model_id="gpt-4-turbo-preview",
        api_base="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
    ),
    "gpt-4o": ModelConfig(
        name="GPT-4o",
        provider="openai",
        model_id="gpt-4o",
        api_base="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
    ),
    "gpt-3.5": ModelConfig(
        name="GPT-3.5 Turbo",
        provider="openai",
        model_id="gpt-3.5-turbo",
        api_base="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
    ),
    
    # Anthropic
    "claude": ModelConfig(
        name="Claude 3.5 Sonnet",
        provider="anthropic",
        model_id="claude-3-5-sonnet-20241022",
        api_base="https://api.anthropic.com/v1",
        api_key_env="ANTHROPIC_API_KEY",
    ),
    "claude-opus": ModelConfig(
        name="Claude 3 Opus",
        provider="anthropic",
        model_id="claude-3-opus-20240229",
        api_base="https://api.anthropic.com/v1",
        api_key_env="ANTHROPIC_API_KEY",
    ),
    "claude-haiku": ModelConfig(
        name="Claude 3.5 Haiku",
        provider="anthropic",
        model_id="claude-3-5-haiku-20241022",
        api_base="https://api.anthropic.com/v1",
        api_key_env="ANTHROPIC_API_KEY",
    ),
    
    # Google
    "gemini": ModelConfig(
        name="Gemini 1.5 Pro",
        provider="google",
        model_id="gemini-1.5-pro",
        api_base="https://generativelanguage.googleapis.com/v1beta",
        api_key_env="GOOGLE_API_KEY",
    ),
    "gemini-flash": ModelConfig(
        name="Gemini 1.5 Flash",
        provider="google",
        model_id="gemini-1.5-flash",
        api_base="https://generativelanguage.googleapis.com/v1beta",
        api_key_env="GOOGLE_API_KEY",
    ),
    
    # xAI (Grok)
    "grok": ModelConfig(
        name="Grok 3",
        provider="xai",
        model_id="grok-3",
        api_base="https://api.x.ai/v1",
        api_key_env="XAI_API_KEY",
    ),
    "grok-2": ModelConfig(
        name="Grok 2",
        provider="xai",
        model_id="grok-2-latest",
        api_base="https://api.x.ai/v1",
        api_key_env="XAI_API_KEY",
    ),
    "grok-mini": ModelConfig(
        name="Grok 3 Mini",
        provider="xai",
        model_id="grok-3-mini",
        api_base="https://api.x.ai/v1",
        api_key_env="XAI_API_KEY",
    ),
    
    # DeepSeek
    "deepseek": ModelConfig(
        name="DeepSeek Chat",
        provider="deepseek",
        model_id="deepseek-chat",
        api_base="https://api.deepseek.com/v1",
        api_key_env="DEEPSEEK_API_KEY",
    ),
    "deepseek-coder": ModelConfig(
        name="DeepSeek Coder",
        provider="deepseek",
        model_id="deepseek-coder",
        api_base="https://api.deepseek.com/v1",
        api_key_env="DEEPSEEK_API_KEY",
    ),
    
    # Mistral
    "mistral": ModelConfig(
        name="Mistral Large",
        provider="mistral",
        model_id="mistral-large-latest",
        api_base="https://api.mistral.ai/v1",
        api_key_env="MISTRAL_API_KEY",
    ),
    "mistral-small": ModelConfig(
        name="Mistral Small",
        provider="mistral",
        model_id="mistral-small-latest",
        api_base="https://api.mistral.ai/v1",
        api_key_env="MISTRAL_API_KEY",
    ),
    
    # Groq (fast inference)
    "groq-llama": ModelConfig(
        name="Llama 3.1 70B (Groq)",
        provider="groq",
        model_id="llama-3.1-70b-versatile",
        api_base="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY",
    ),
    "groq-mixtral": ModelConfig(
        name="Mixtral 8x7B (Groq)",
        provider="groq",
        model_id="mixtral-8x7b-32768",
        api_base="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY",
    ),
}

# Default models to query
DEFAULT_MODELS = ["gpt-4o", "claude", "gemini", "grok", "deepseek", "mistral"]


# ============================================================================
# Response Data Class
# ============================================================================

@dataclass
class ModelResponse:
    """Response from a single model."""
    model_key: str
    model_name: str
    provider: str
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    latency_ms: float = 0
    tokens_used: Optional[int] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


# ============================================================================
# API Clients for Each Provider
# ============================================================================

class BaseClient:
    """Base class for API clients."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.api_key = get_api_key(config.provider) or os.environ.get(config.api_key_env)
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    async def query(self, session: aiohttp.ClientSession, prompt: str, 
                   system_prompt: Optional[str] = None) -> ModelResponse:
        raise NotImplementedError


class OpenAICompatibleClient(BaseClient):
    """Client for OpenAI-compatible APIs (OpenAI, xAI, DeepSeek, Mistral, Groq)."""
    
    async def query(self, session: aiohttp.ClientSession, prompt: str,
                   system_prompt: Optional[str] = None) -> ModelResponse:
        start_time = time.time()
        
        if not self.is_configured():
            return ModelResponse(
                model_key=self.config.name,
                model_name=self.config.model_id,
                provider=self.config.provider,
                success=False,
                error=f"API key not set: {self.config.api_key_env}"
            )
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        messages = []
        if system_prompt and self.config.supports_system:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.config.model_id,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": 0.7,
        }
        
        try:
            async with session.post(
                f"{self.config.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                latency = (time.time() - start_time) * 1000
                
                if resp.status != 200:
                    error_text = await resp.text()
                    return ModelResponse(
                        model_key=self.config.name,
                        model_name=self.config.model_id,
                        provider=self.config.provider,
                        success=False,
                        error=f"HTTP {resp.status}: {error_text[:200]}",
                        latency_ms=latency
                    )
                
                data = await resp.json()
                content = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens")
                
                return ModelResponse(
                    model_key=self.config.name,
                    model_name=self.config.model_id,
                    provider=self.config.provider,
                    success=True,
                    response=content,
                    latency_ms=latency,
                    tokens_used=tokens
                )
                
        except asyncio.TimeoutError:
            return ModelResponse(
                model_key=self.config.name,
                model_name=self.config.model_id,
                provider=self.config.provider,
                success=False,
                error="Request timeout (120s)",
                latency_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            return ModelResponse(
                model_key=self.config.name,
                model_name=self.config.model_id,
                provider=self.config.provider,
                success=False,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000
            )


class AnthropicClient(BaseClient):
    """Client for Anthropic Claude API."""
    
    async def query(self, session: aiohttp.ClientSession, prompt: str,
                   system_prompt: Optional[str] = None) -> ModelResponse:
        start_time = time.time()
        
        if not self.is_configured():
            return ModelResponse(
                model_key=self.config.name,
                model_name=self.config.model_id,
                provider=self.config.provider,
                success=False,
                error=f"API key not set: {self.config.api_key_env}"
            )
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        
        payload = {
            "model": self.config.model_id,
            "max_tokens": self.config.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            async with session.post(
                f"{self.config.api_base}/messages",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                latency = (time.time() - start_time) * 1000
                
                if resp.status != 200:
                    error_text = await resp.text()
                    return ModelResponse(
                        model_key=self.config.name,
                        model_name=self.config.model_id,
                        provider=self.config.provider,
                        success=False,
                        error=f"HTTP {resp.status}: {error_text[:200]}",
                        latency_ms=latency
                    )
                
                data = await resp.json()
                content = data["content"][0]["text"]
                tokens = data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0)
                
                return ModelResponse(
                    model_key=self.config.name,
                    model_name=self.config.model_id,
                    provider=self.config.provider,
                    success=True,
                    response=content,
                    latency_ms=latency,
                    tokens_used=tokens
                )
                
        except asyncio.TimeoutError:
            return ModelResponse(
                model_key=self.config.name,
                model_name=self.config.model_id,
                provider=self.config.provider,
                success=False,
                error="Request timeout (120s)",
                latency_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            return ModelResponse(
                model_key=self.config.name,
                model_name=self.config.model_id,
                provider=self.config.provider,
                success=False,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000
            )


class GoogleClient(BaseClient):
    """Client for Google Gemini API."""
    
    async def query(self, session: aiohttp.ClientSession, prompt: str,
                   system_prompt: Optional[str] = None) -> ModelResponse:
        start_time = time.time()
        
        if not self.is_configured():
            return ModelResponse(
                model_key=self.config.name,
                model_name=self.config.model_id,
                provider=self.config.provider,
                success=False,
                error=f"API key not set: {self.config.api_key_env}"
            )
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "maxOutputTokens": self.config.max_tokens,
                "temperature": 0.7,
            }
        }
        
        url = f"{self.config.api_base}/models/{self.config.model_id}:generateContent?key={self.api_key}"
        
        try:
            async with session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                latency = (time.time() - start_time) * 1000
                
                if resp.status != 200:
                    error_text = await resp.text()
                    return ModelResponse(
                        model_key=self.config.name,
                        model_name=self.config.model_id,
                        provider=self.config.provider,
                        success=False,
                        error=f"HTTP {resp.status}: {error_text[:200]}",
                        latency_ms=latency
                    )
                
                data = await resp.json()
                
                if "candidates" not in data or not data["candidates"]:
                    return ModelResponse(
                        model_key=self.config.name,
                        model_name=self.config.model_id,
                        provider=self.config.provider,
                        success=False,
                        error="No response candidates",
                        latency_ms=latency
                    )
                
                content = data["candidates"][0]["content"]["parts"][0]["text"]
                tokens = data.get("usageMetadata", {}).get("totalTokenCount")
                
                return ModelResponse(
                    model_key=self.config.name,
                    model_name=self.config.model_id,
                    provider=self.config.provider,
                    success=True,
                    response=content,
                    latency_ms=latency,
                    tokens_used=tokens
                )
                
        except asyncio.TimeoutError:
            return ModelResponse(
                model_key=self.config.name,
                model_name=self.config.model_id,
                provider=self.config.provider,
                success=False,
                error="Request timeout (120s)",
                latency_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            return ModelResponse(
                model_key=self.config.name,
                model_name=self.config.model_id,
                provider=self.config.provider,
                success=False,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000
            )


# ============================================================================
# Client Factory
# ============================================================================

def get_client(config: ModelConfig) -> BaseClient:
    """Get the appropriate client for a model configuration."""
    if config.provider == "anthropic":
        return AnthropicClient(config)
    elif config.provider == "google":
        return GoogleClient(config)
    else:
        # OpenAI, xAI, DeepSeek, Mistral, Groq all use OpenAI-compatible API
        return OpenAICompatibleClient(config)


# ============================================================================
# Multi-LLM Query Engine
# ============================================================================

class MultiLLM:
    """Query multiple LLMs in parallel."""
    
    def __init__(self, models: Optional[list[str]] = None):
        self.model_keys = models or DEFAULT_MODELS
        self.clients = {}
        
        for key in self.model_keys:
            if key in MODELS:
                self.clients[key] = get_client(MODELS[key])
            else:
                print(f"Warning: Unknown model '{key}', skipping", file=sys.stderr)
    
    def get_available_models(self) -> list[str]:
        """Get list of models with configured API keys."""
        return [key for key, client in self.clients.items() if client.is_configured()]
    
    def get_missing_keys(self) -> list[str]:
        """Get list of missing API key environment variables."""
        missing = []
        for key, client in self.clients.items():
            if not client.is_configured():
                missing.append(client.config.api_key_env)
        return list(set(missing))
    
    async def query_all(self, prompt: str, system_prompt: Optional[str] = None) -> dict:
        """Query all configured models in parallel."""
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            task_keys = []
            
            for key, client in self.clients.items():
                # Only query models with configured API keys
                if not client.is_configured():
                    continue
                tasks.append(client.query(session, prompt, system_prompt))
                task_keys.append(key)
            
            if not tasks:
                return {
                    "error": "No models configured. Set API keys in environment.",
                    "missing_keys": self.get_missing_keys(),
                    "timestamp": datetime.now().isoformat()
                }
            
            responses = await asyncio.gather(*tasks)
        
        total_time = (time.time() - start_time) * 1000
        
        # Build result
        result = {
            "prompt": prompt[:500] + "..." if len(prompt) > 500 else prompt,
            "system_prompt": system_prompt[:200] + "..." if system_prompt and len(system_prompt) > 200 else system_prompt,
            "timestamp": datetime.now().isoformat(),
            "total_time_ms": round(total_time),
            "models_queried": len(responses),
            "models_successful": sum(1 for r in responses if r.success),
            "responses": {}
        }
        
        for key, response in zip(task_keys, responses):
            result["responses"][key] = asdict(response)
        
        return result


# ============================================================================
# CLI Interface
# ============================================================================

def list_models():
    """Print available models."""
    print("\nAvailable Models:")
    print("-" * 70)
    
    for key, config in MODELS.items():
        api_key = os.environ.get(config.api_key_env)
        status = "✓ configured" if api_key else "✗ missing key"
        default = " (default)" if key in DEFAULT_MODELS else ""
        print(f"  {key:15} {config.name:25} [{status}]{default}")
    
    print("-" * 70)
    print("\nEnvironment variables needed:")
    seen = set()
    for config in MODELS.values():
        if config.api_key_env not in seen:
            value = "✓ set" if os.environ.get(config.api_key_env) else "✗ not set"
            print(f"  {config.api_key_env:20} [{value}]")
            seen.add(config.api_key_env)
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Query multiple AI models in parallel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python multi_llm.py "What is the capital of France?"
  python multi_llm.py "Explain quantum computing" --models gpt-4,claude,grok
  python multi_llm.py "Review this code" --system "You are a code reviewer"
  python multi_llm.py --stdin < prompt.txt
  python multi_llm.py --list

Environment variables:
  OPENAI_API_KEY      - For GPT-4, GPT-3.5
  ANTHROPIC_API_KEY   - For Claude models
  GOOGLE_API_KEY      - For Gemini models
  XAI_API_KEY         - For Grok models
  DEEPSEEK_API_KEY    - For DeepSeek models
  MISTRAL_API_KEY     - For Mistral models
  GROQ_API_KEY        - For Groq-hosted models
        """
    )
    
    parser.add_argument("prompt", nargs="?", help="The prompt to send to all models")
    parser.add_argument("-m", "--models", help="Comma-separated list of models to query")
    parser.add_argument("-s", "--system", help="System prompt to use")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser.add_argument("--stdin", action="store_true", help="Read prompt from stdin")
    parser.add_argument("-l", "--list", action="store_true", help="List available models")
    parser.add_argument("-p", "--pretty", action="store_true", help="Pretty print JSON")
    
    args = parser.parse_args()
    
    # List models
    if args.list:
        list_models()
        return
    
    # Get prompt
    if args.stdin:
        prompt = sys.stdin.read().strip()
    elif args.prompt:
        prompt = args.prompt
    else:
        parser.print_help()
        print("\nError: Please provide a prompt or use --stdin", file=sys.stderr)
        sys.exit(1)
    
    if not prompt:
        print("Error: Empty prompt", file=sys.stderr)
        sys.exit(1)
    
    # Parse models
    models = None
    if args.models:
        models = [m.strip() for m in args.models.split(",")]
    
    # Run queries
    llm = MultiLLM(models)
    
    # Show which models will be queried (only configured ones)
    available = llm.get_available_models()
    missing = llm.get_missing_keys()
    
    if not available:
        print("Error: No models configured. Please set API keys in environment.", file=sys.stderr)
        print(f"\nMissing environment variables:", file=sys.stderr)
        for key in missing:
            print(f"  - {key}", file=sys.stderr)
        print(f"\nSee .env.example for setup instructions.", file=sys.stderr)
        sys.exit(1)
    
    # Show what will be queried
    print(f"Querying {len(available)} configured model(s): {', '.join(available)}", file=sys.stderr)
    if missing:
        print(f"Skipping unconfigured: {', '.join(set(MODELS[k].api_key_env for k in llm.model_keys if k not in available))}", file=sys.stderr)
    
    result = asyncio.run(llm.query_all(
        prompt=prompt,
        system_prompt=args.system
    ))
    
    # Format output
    indent = 2 if args.pretty else None
    json_output = json.dumps(result, indent=indent, ensure_ascii=False)
    
    # Output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(json_output)
        print(f"Results saved to: {args.output}", file=sys.stderr)
    else:
        print(json_output)
    
    # Summary
    print(f"\nSummary: {result['models_successful']}/{result['models_queried']} successful, "
          f"total time: {result['total_time_ms']}ms", file=sys.stderr)


if __name__ == "__main__":
    main()
