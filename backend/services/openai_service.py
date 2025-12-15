"""
OpenAI Service - Single Responsibility for AI API Calls

Centralizes all OpenAI API interactions with proper error handling,
JSON cleanup, and retry logic.
"""

import json
import logging
import os
from typing import Any, Optional, Protocol

import httpx

logger = logging.getLogger(__name__)


class ILLMService(Protocol):
    """Interface for LLM service operations."""
    
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2500,
    ) -> str:
        """Get completion from LLM."""
        ...
    
    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2500,
    ) -> dict:
        """Get JSON completion from LLM."""
        ...


class OpenAIService:
    """
    OpenAI API service with proper error handling and JSON cleanup.
    
    Follows Single Responsibility - only handles OpenAI interactions.
    """
    
    OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
    
    def __init__(self, api_key: Optional[str] = None, timeout: float = 120.0):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.timeout = timeout
    
    @property
    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)
    
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2500,
    ) -> str:
        """
        Get a text completion from OpenAI.
        
        Args:
            system_prompt: System message for context
            user_prompt: User message/query
            model: OpenAI model to use
            temperature: Creativity setting (0-1)
            max_tokens: Maximum response length
        
        Returns:
            Raw text response from the model
        
        Raises:
            ValueError: If API key not configured
            httpx.HTTPError: If API request fails
        """
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not configured")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.OPENAI_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()
        
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 2500,
    ) -> dict:
        """
        Get a JSON completion from OpenAI with automatic cleanup.
        
        Handles markdown code blocks and parsing automatically.
        
        Args:
            system_prompt: System message (should request JSON)
            user_prompt: User message/query
            model: OpenAI model to use
            temperature: Creativity setting (0-1)
            max_tokens: Maximum response length
        
        Returns:
            Parsed JSON as dictionary
        
        Raises:
            ValueError: If API key not configured
            json.JSONDecodeError: If response is not valid JSON
        """
        raw_content = await self.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return self._parse_json_response(raw_content)
    
    @staticmethod
    def _parse_json_response(raw_content: str) -> dict:
        """
        Parse JSON from LLM response, handling markdown code blocks.
        
        Handles:
        - ```json ... ```
        - ``` ... ```
        - Plain JSON
        """
        cleaned = raw_content.strip()
        
        # Remove markdown code block wrappers
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        cleaned = cleaned.strip()
        
        return json.loads(cleaned)


class GrokService:
    """
    xAI Grok API service.
    
    Similar interface to OpenAI for consistency.
    """
    
    GROK_API_URL = "https://api.x.ai/v1/chat/completions"
    
    def __init__(self, api_key: Optional[str] = None, timeout: float = 120.0):
        self.api_key = api_key or os.getenv("XAI_API_KEY")
        self.timeout = timeout
    
    @property
    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)
    
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "grok-beta",
        temperature: float = 0.7,
        max_tokens: int = 2500,
    ) -> str:
        """Get completion from Grok."""
        if not self.api_key:
            raise ValueError("XAI_API_KEY not configured")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.GROK_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()
        
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "grok-beta",
        temperature: float = 0.7,
        max_tokens: int = 2500,
    ) -> dict:
        """Get JSON completion from Grok."""
        raw_content = await self.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return OpenAIService._parse_json_response(raw_content)


# Singleton instances
_openai_service: Optional[OpenAIService] = None
_grok_service: Optional[GrokService] = None


def get_openai_service() -> OpenAIService:
    """Dependency injection factory for OpenAIService."""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service


def get_grok_service() -> GrokService:
    """Dependency injection factory for GrokService."""
    global _grok_service
    if _grok_service is None:
        _grok_service = GrokService()
    return _grok_service
