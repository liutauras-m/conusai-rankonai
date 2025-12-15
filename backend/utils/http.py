"""
Async HTTP Fetcher utility with multiple backends.

Provides parallel URL fetching with proper error handling, timeouts,
and support for different HTTP clients optimized for web scraping.

Backends:
- aiohttp: Fast async HTTP (default, lightweight)
- httpx: Modern HTTP/2 support, better compatibility
- curl_cffi: Browser TLS fingerprinting, bypasses bot detection
- playwright: Full browser rendering for JavaScript-heavy sites

Usage:
    # Default (aiohttp)
    fetcher = AsyncFetcher()
    
    # With curl impersonation (bypasses Cloudflare)
    fetcher = AsyncFetcher(backend=FetcherBackend.CURL_CFFI)
    
    # With browser rendering (for SPAs)
    fetcher = AsyncFetcher(backend=FetcherBackend.PLAYWRIGHT)
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any

import aiohttp

# Optional imports - graceful degradation
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    from curl_cffi.requests import AsyncSession
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False

try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


class FetcherBackend(Enum):
    """Available HTTP fetcher backends."""
    AIOHTTP = "aiohttp"          # Default, fast, lightweight
    HTTPX = "httpx"              # HTTP/2 support, modern
    CURL_CFFI = "curl_cffi"      # Browser TLS fingerprint, bypasses detection
    PLAYWRIGHT = "playwright"    # Full browser, JS rendering


# Common browser headers to avoid bot detection
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}


class BaseFetcher(ABC):
    """Abstract base class for HTTP fetchers."""
    
    @abstractmethod
    async def fetch(self, url: str) -> dict[str, Any]:
        """Fetch a single URL."""
        pass
    
    @abstractmethod
    async def fetch_all(self, urls: list[str]) -> dict[str, dict[str, Any]]:
        """Fetch multiple URLs in parallel."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Clean up resources."""
        pass


class AiohttpFetcher(BaseFetcher):
    """Fast async HTTP fetcher using aiohttp."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.headers = BROWSER_HEADERS.copy()
        self._session: aiohttp.ClientSession | None = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers=self.headers,
            )
        return self._session
    
    async def fetch(self, url: str) -> dict[str, Any]:
        start_time = datetime.now()
        result: dict[str, Any] = {
            "url": url,
            "status": None,
            "content": None,
            "headers": {},
            "error": None,
            "response_time_ms": 0,
            "backend": "aiohttp",
        }
        
        try:
            session = await self._get_session()
            async with session.get(url, ssl=False, allow_redirects=True) as response:
                result["status"] = response.status
                result["headers"] = dict(response.headers)
                
                if response.status == 200:
                    result["content"] = await response.text()
                    
                result["response_time_ms"] = (
                    datetime.now() - start_time
                ).total_seconds() * 1000
                
        except asyncio.TimeoutError:
            result["error"] = "Timeout"
        except aiohttp.ClientError as e:
            result["error"] = str(e)
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
            
        return result
    
    async def fetch_all(self, urls: list[str]) -> dict[str, dict[str, Any]]:
        tasks = [self.fetch(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return {r["url"]: r for r in results}
    
    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()


class HttpxFetcher(BaseFetcher):
    """Modern HTTP/2 fetcher using httpx."""
    
    def __init__(self, timeout: int = 30):
        if not HAS_HTTPX:
            raise ImportError("httpx not installed. Run: pip install httpx[http2]")
        self.timeout = timeout
        self.headers = BROWSER_HEADERS.copy()
        self._client: httpx.AsyncClient | None = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self.headers,
                http2=True,  # Enable HTTP/2
                follow_redirects=True,
                verify=False,
            )
        return self._client
    
    async def fetch(self, url: str) -> dict[str, Any]:
        start_time = datetime.now()
        result: dict[str, Any] = {
            "url": url,
            "status": None,
            "content": None,
            "headers": {},
            "error": None,
            "response_time_ms": 0,
            "backend": "httpx",
        }
        
        try:
            client = await self._get_client()
            response = await client.get(url)
            result["status"] = response.status_code
            result["headers"] = dict(response.headers)
            
            if response.status_code == 200:
                result["content"] = response.text
                
            result["response_time_ms"] = (
                datetime.now() - start_time
            ).total_seconds() * 1000
                
        except httpx.TimeoutException:
            result["error"] = "Timeout"
        except httpx.HTTPError as e:
            result["error"] = str(e)
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
            
        return result
    
    async def fetch_all(self, urls: list[str]) -> dict[str, dict[str, Any]]:
        tasks = [self.fetch(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return {r["url"]: r for r in results}
    
    async def close(self) -> None:
        if self._client:
            await self._client.aclose()


class CurlCffiFetcher(BaseFetcher):
    """
    Fetcher using curl_cffi with browser TLS fingerprinting.
    
    This bypasses most bot detection including Cloudflare by
    impersonating real browser TLS fingerprints.
    """
    
    # Browser impersonation options
    IMPERSONATE_OPTIONS = [
        "chrome120",
        "chrome119", 
        "chrome110",
        "safari17_0",
        "edge120",
    ]
    
    def __init__(self, timeout: int = 30, impersonate: str = "chrome120"):
        if not HAS_CURL_CFFI:
            raise ImportError("curl_cffi not installed. Run: pip install curl_cffi")
        self.timeout = timeout
        self.impersonate = impersonate
        self.headers = BROWSER_HEADERS.copy()
    
    async def fetch(self, url: str) -> dict[str, Any]:
        start_time = datetime.now()
        result: dict[str, Any] = {
            "url": url,
            "status": None,
            "content": None,
            "headers": {},
            "error": None,
            "response_time_ms": 0,
            "backend": "curl_cffi",
            "impersonate": self.impersonate,
        }
        
        try:
            async with AsyncSession() as session:
                response = await session.get(
                    url,
                    headers=self.headers,
                    impersonate=self.impersonate,
                    timeout=self.timeout,
                    verify=False,
                    allow_redirects=True,
                )
                result["status"] = response.status_code
                result["headers"] = dict(response.headers)
                
                if response.status_code == 200:
                    result["content"] = response.text
                    
                result["response_time_ms"] = (
                    datetime.now() - start_time
                ).total_seconds() * 1000
                
        except asyncio.TimeoutError:
            result["error"] = "Timeout"
        except Exception as e:
            result["error"] = f"Error: {str(e)}"
            
        return result
    
    async def fetch_all(self, urls: list[str]) -> dict[str, dict[str, Any]]:
        tasks = [self.fetch(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return {r["url"]: r for r in results}
    
    async def close(self) -> None:
        pass  # curl_cffi sessions are context-managed


class PlaywrightFetcher(BaseFetcher):
    """
    Full browser fetcher using Playwright.
    
    Best for JavaScript-heavy sites (SPAs) that require
    actual browser rendering to get content.
    """
    
    def __init__(self, timeout: int = 30, headless: bool = True):
        if not HAS_PLAYWRIGHT:
            raise ImportError(
                "playwright not installed. Run: pip install playwright && playwright install chromium"
            )
        self.timeout = timeout * 1000  # Playwright uses milliseconds
        self.headless = headless
        self._playwright = None
        self._browser = None
    
    async def _get_browser(self):
        if self._playwright is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless
            )
        return self._browser
    
    async def fetch(self, url: str) -> dict[str, Any]:
        start_time = datetime.now()
        result: dict[str, Any] = {
            "url": url,
            "status": None,
            "content": None,
            "headers": {},
            "error": None,
            "response_time_ms": 0,
            "backend": "playwright",
            "js_rendered": True,
        }
        
        try:
            browser = await self._get_browser()
            context = await browser.new_context(
                user_agent=BROWSER_HEADERS["User-Agent"],
                viewport={"width": 1920, "height": 1080},
            )
            page = await context.new_page()
            
            response = await page.goto(
                url, 
                wait_until="networkidle",
                timeout=self.timeout
            )
            
            if response:
                result["status"] = response.status
                result["headers"] = await response.all_headers()
            
            # Get fully rendered HTML
            result["content"] = await page.content()
            
            result["response_time_ms"] = (
                datetime.now() - start_time
            ).total_seconds() * 1000
            
            await context.close()
                
        except Exception as e:
            result["error"] = f"Browser error: {str(e)}"
            
        return result
    
    async def fetch_all(self, urls: list[str]) -> dict[str, dict[str, Any]]:
        # Playwright fetches sequentially to avoid resource issues
        results = {}
        for url in urls:
            results[url] = await self.fetch(url)
        return results
    
    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()


class AsyncFetcher:
    """
    Unified async HTTP fetcher with multiple backend support.
    
    Automatically selects the best available backend or uses
    the specified one for different scraping needs.
    
    Example:
        # Default (aiohttp - fast)
        fetcher = AsyncFetcher()
        results = await fetcher.fetch_all(urls)
        
        # Bypass Cloudflare
        fetcher = AsyncFetcher(backend=FetcherBackend.CURL_CFFI)
        
        # JavaScript rendering
        fetcher = AsyncFetcher(backend=FetcherBackend.PLAYWRIGHT)
    """
    
    def __init__(
        self, 
        timeout: int = 30,
        backend: FetcherBackend = FetcherBackend.AIOHTTP,
    ):
        self.timeout = timeout
        self.backend_type = backend
        self._fetcher = self._create_fetcher(backend)
    
    def _create_fetcher(self, backend: FetcherBackend) -> BaseFetcher:
        """Create the appropriate fetcher based on backend type."""
        if backend == FetcherBackend.HTTPX:
            if not HAS_HTTPX:
                raise ImportError("httpx not available")
            return HttpxFetcher(self.timeout)
        
        elif backend == FetcherBackend.CURL_CFFI:
            if not HAS_CURL_CFFI:
                raise ImportError("curl_cffi not available")
            return CurlCffiFetcher(self.timeout)
        
        elif backend == FetcherBackend.PLAYWRIGHT:
            if not HAS_PLAYWRIGHT:
                raise ImportError("playwright not available")
            return PlaywrightFetcher(self.timeout)
        
        else:
            return AiohttpFetcher(self.timeout)
    
    @staticmethod
    def get_available_backends() -> list[FetcherBackend]:
        """Get list of available backends based on installed packages."""
        available = [FetcherBackend.AIOHTTP]  # Always available
        
        if HAS_HTTPX:
            available.append(FetcherBackend.HTTPX)
        if HAS_CURL_CFFI:
            available.append(FetcherBackend.CURL_CFFI)
        if HAS_PLAYWRIGHT:
            available.append(FetcherBackend.PLAYWRIGHT)
            
        return available
    
    @staticmethod
    def get_best_backend() -> FetcherBackend:
        """
        Get the best available backend for web scraping.
        
        Priority: curl_cffi > httpx > aiohttp
        (playwright is not default as it's heavy)
        """
        if HAS_CURL_CFFI:
            return FetcherBackend.CURL_CFFI
        if HAS_HTTPX:
            return FetcherBackend.HTTPX
        return FetcherBackend.AIOHTTP
    
    async def fetch(self, url: str) -> dict[str, Any]:
        """Fetch a single URL."""
        return await self._fetcher.fetch(url)
    
    async def fetch_all(self, urls: list[str]) -> dict[str, dict[str, Any]]:
        """Fetch multiple URLs in parallel."""
        return await self._fetcher.fetch_all(urls)
    
    async def fetch_one(self, url: str) -> dict[str, Any]:
        """Convenience method to fetch a single URL."""
        return await self.fetch(url)
    
    async def close(self) -> None:
        """Clean up resources."""
        await self._fetcher.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
