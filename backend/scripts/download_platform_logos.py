#!/usr/bin/env python3
"""Download platform icons/logos for popular AI products.

What it does
- Fetches each platform homepage.
- Extracts best candidate from <link rel="icon"> / apple-touch-icon / shortcut icon.
- Downloads that file to an output directory.
- Falls back to /favicon.ico if needed.
- Optional final fallback via Google's S2 favicon endpoint.

Important
- Brand logos and trademarks are typically protected. This script only downloads
  files that sites publicly expose (often favicons). Before using these assets
  in a product/marketing context, confirm you have the right to do so.

Usage
  python3 scripts/download_platform_logos.py --out frontend/public/logos/platforms

Examples
  # Include extra platforms
  python3 scripts/download_platform_logos.py --add "MyTool=https://example.com" \
    --out frontend/public/logos/platforms

  # Disable Google favicon fallback
  python3 scripts/download_platform_logos.py --no-google-fallback

"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Iterable, Optional


@dataclass(frozen=True)
class Platform:
    name: str
    # Try these in order; first successful fetch wins.
    base_urls: tuple[str, ...]
    # Optional: directly download an icon from this URL (skips HTML parsing).
    # You can also use a directive: "google-s2:<domain>".
    forced_icon_url: str | None = None


# These are the *official* product or company domains where a platform's icon is
# typically served correctly. We download only publicly exposed site icons.
DEFAULT_PLATFORMS: list[Platform] = [
    Platform("ChatGPT", ("https://chatgpt.com", "https://chat.openai.com", "https://openai.com")),
    Platform("Claude", ("https://claude.ai", "https://www.anthropic.com")),
    Platform("Gemini", ("https://gemini.google.com", "https://ai.google")),
    Platform("Microsoft Copilot", ("https://copilot.microsoft.com", "https://www.microsoft.com")),
    Platform("Perplexity", ("https://www.perplexity.ai",)),
    # x.ai often exposes only a tiny 32x32 .ico; use Google S2 to fetch a larger PNG.
    Platform("Grok", ("https://x.ai", "https://x.ai/grok"), forced_icon_url="google-s2:x.ai"),
    Platform("Meta AI", ("https://ai.meta.com", "https://www.meta.ai")),
    Platform("Mistral", ("https://chat.mistral.ai", "https://mistral.ai")),
    Platform("Cohere", ("https://cohere.com", "https://coral.cohere.com")),
    Platform("DeepSeek", ("https://chat.deepseek.com", "https://www.deepseek.com")),
]


@dataclass(frozen=True)
class IconCandidate:
    rel: str
    href: str
    sizes: str | None
    type: str | None


class IconLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.candidates: list[IconCandidate] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "link":
            return
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        rel = attr_map.get("rel", "").strip().lower()
        href = attr_map.get("href", "").strip()
        if not href:
            return

        # Typical icon rels:
        # - icon
        # - shortcut icon
        # - apple-touch-icon / apple-touch-icon-precomposed
        # - mask-icon
        is_icon = (
            "icon" in rel
            or rel in {"apple-touch-icon", "apple-touch-icon-precomposed", "mask-icon"}
        )
        if not is_icon:
            return

        self.candidates.append(
            IconCandidate(
                rel=rel,
                href=href,
                sizes=(attr_map.get("sizes") or None),
                type=(attr_map.get("type") or None),
            )
        )


def _slugify(name: str) -> str:
    name = name.strip().lower()
    name = re.sub(r"\([^)]*\)", "", name)  # remove parentheticals
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name or "platform"


def _best_size_score(sizes: str | None) -> int:
    if not sizes:
        return 0
    s = sizes.strip().lower()
    if s == "any":
        return 10_000
    best = 0
    for part in s.split():
        m = re.match(r"^(\d+)x(\d+)$", part)
        if not m:
            continue
        w, h = int(m.group(1)), int(m.group(2))
        best = max(best, min(w, h))
    return best


def _rel_bonus(rel: str) -> int:
    # Prefer apple-touch-icon for larger raster icons.
    rel = rel.lower()
    if "apple-touch-icon" in rel:
        return 500
    if "icon" == rel or rel.endswith(" icon"):
        return 100
    if "mask-icon" in rel:
        return 50
    return 0


def choose_best_candidate(candidates: Iterable[IconCandidate]) -> Optional[IconCandidate]:
    best: Optional[IconCandidate] = None
    best_score = -1

    for c in candidates:
        score = _best_size_score(c.sizes) + _rel_bonus(c.rel)
        # Prefer explicit SVG types slightly, but don't override huge sizes.
        if c.type and "svg" in c.type.lower():
            score += 40
        if score > best_score:
            best_score = score
            best = c

    return best


def http_get(url: str, timeout_s: float, user_agent: str) -> tuple[bytes, dict[str, str]]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        headers = {k.lower(): v for k, v in resp.headers.items()}
        return resp.read(), headers


def download_binary(url: str, timeout_s: float, user_agent: str) -> tuple[bytes, dict[str, str]]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        headers = {k.lower(): v for k, v in resp.headers.items()}
        return resp.read(), headers


def ext_from_url_or_content_type(url: str, content_type: str | None) -> str:
    path = urllib.parse.urlparse(url).path
    _, ext = os.path.splitext(path)
    ext = ext.lower().strip()
    if ext in {".png", ".jpg", ".jpeg", ".svg", ".ico", ".webp", ".avif"}:
        return ext

    if content_type:
        ct = content_type.split(";")[0].strip().lower()
        mapping = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/svg+xml": ".svg",
            "image/x-icon": ".ico",
            "image/vnd.microsoft.icon": ".ico",
            "image/webp": ".webp",
            "image/avif": ".avif",
        }
        if ct in mapping:
            return mapping[ct]

    return ".img"


def google_s2_favicon(domain: str, size: int = 256) -> str:
    return f"https://www.google.com/s2/favicons?domain={urllib.parse.quote(domain)}&sz={size}"


def resolve_forced_icon_url(forced: str) -> str:
    forced = forced.strip()
    if forced.lower().startswith("google-s2:"):
        domain = forced.split(":", 1)[1].strip()
        if not domain:
            raise ValueError("Invalid forced icon directive: google-s2:<domain>")
        return google_s2_favicon(domain, size=256)
    return forced


def domain_from_url(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc
    return host.split(":")[0]


def resolve_icon_url(base_url: str, href: str) -> str:
    # Handles relative, absolute, and protocol-relative URLs.
    return urllib.parse.urljoin(base_url, href)


def _try_download_from_base_url(
    name: str,
    base_url: str,
    out_dir: str,
    timeout_s: float,
    user_agent: str,
    use_google_fallback: bool,
    sleep_s: float,
) -> dict:
    slug = _slugify(name)
    os.makedirs(out_dir, exist_ok=True)

    result: dict = {
        "name": name,
        "base_url": base_url,
        "status": "error",
        "chosen": None,
        "saved_path": None,
        "error": None,
        "timestamp": int(time.time()),
    }

    html_bytes, _headers = http_get(base_url, timeout_s=timeout_s, user_agent=user_agent)
    html = html_bytes.decode("utf-8", errors="ignore")

    parser = IconLinkParser()
    parser.feed(html)
    best = choose_best_candidate(parser.candidates)

    icon_url: Optional[str] = None
    chosen_reason: str = ""

    if best:
        icon_url = resolve_icon_url(base_url, best.href)
        chosen_reason = f"html:{best.rel} sizes={best.sizes or ''}".strip()
    else:
        icon_url = urllib.parse.urljoin(base_url, "/favicon.ico")
        chosen_reason = "fallback:/favicon.ico"

    icon_bytes: Optional[bytes] = None
    icon_headers: dict[str, str] = {}

    try:
        icon_bytes, icon_headers = download_binary(icon_url, timeout_s=timeout_s, user_agent=user_agent)
    except Exception:
        icon_bytes = None

    if not icon_bytes and use_google_fallback:
        domain = domain_from_url(base_url)
        icon_url = google_s2_favicon(domain)
        chosen_reason = "fallback:google-s2"
        icon_bytes, icon_headers = download_binary(icon_url, timeout_s=timeout_s, user_agent=user_agent)

    if not icon_bytes:
        raise RuntimeError("Could not download icon (blocked or not found)")

    content_type = icon_headers.get("content-type")
    ext = ext_from_url_or_content_type(icon_url, content_type)
    file_name = f"{slug}{ext}"
    save_path = os.path.join(out_dir, file_name)

    with open(save_path, "wb") as f:
        f.write(icon_bytes)

    result.update(
        {
            "status": "ok",
            "chosen": {"url": icon_url, "reason": chosen_reason, "content_type": content_type},
            "saved_path": save_path,
        }
    )

    time.sleep(sleep_s)
    return result


def download_for_platform(
    platform: Platform,
    out_dir: str,
    timeout_s: float,
    user_agent: str,
    use_google_fallback: bool,
    sleep_s: float,
) -> dict:
    last_error: Optional[str] = None
    if platform.forced_icon_url:
        try:
            icon_url = resolve_forced_icon_url(platform.forced_icon_url)
            icon_bytes, icon_headers = download_binary(icon_url, timeout_s=timeout_s, user_agent=user_agent)
            content_type = icon_headers.get("content-type")
            ext = ext_from_url_or_content_type(icon_url, content_type)
            save_path = os.path.join(out_dir, f"{_slugify(platform.name)}{ext}")
            os.makedirs(out_dir, exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(icon_bytes)
            time.sleep(sleep_s)
            return {
                "name": platform.name,
                "base_url": platform.base_urls[0] if platform.base_urls else "",
                "status": "ok",
                "chosen": {"url": icon_url, "reason": "forced", "content_type": content_type},
                "saved_path": save_path,
                "error": None,
                "timestamp": int(time.time()),
            }
        except Exception as e:
            # Fall back to base_urls below.
            last_error = str(e)

    for base_url in platform.base_urls:
        try:
            return _try_download_from_base_url(
                name=platform.name,
                base_url=base_url,
                out_dir=out_dir,
                timeout_s=timeout_s,
                user_agent=user_agent,
                use_google_fallback=use_google_fallback,
                sleep_s=sleep_s,
            )
        except urllib.error.HTTPError as e:
            last_error = f"HTTPError {e.code}: {e.reason}"
        except urllib.error.URLError as e:
            last_error = f"URLError: {e.reason}"
        except Exception as e:
            last_error = str(e)

    return {
        "name": platform.name,
        "base_url": platform.base_urls[0] if platform.base_urls else "",
        "status": "error",
        "chosen": None,
        "saved_path": None,
        "error": last_error or "Unknown error",
        "timestamp": int(time.time()),
    }


def parse_add_items(items: list[str]) -> list[Platform]:
    parsed: list[Platform] = []
    for item in items:
        if "=" not in item:
            raise ValueError(f"Invalid --add value '{item}'. Expected NAME=https://example.com")
        name, url = item.split("=", 1)
        name = name.strip()
        url = url.strip()
        if not name or not url:
            raise ValueError(f"Invalid --add value '{item}'.")
        parsed.append(Platform(name=name, base_urls=(url,)))
    return parsed


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Download platform icons/logos (favicons) from popular AI tools")
    ap.add_argument(
        "--out",
        default="frontend/public/logos/platforms",
        help="Output directory for downloaded files (default: frontend/public/logos/platforms)",
    )
    ap.add_argument("--timeout", type=float, default=12.0, help="HTTP timeout seconds (default: 12)")
    ap.add_argument(
        "--user-agent",
        default="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        help="User-Agent header",
    )
    ap.add_argument(
        "--no-google-fallback",
        action="store_true",
        help="Disable Google S2 favicon fallback",
    )
    ap.add_argument(
        "--sleep",
        type=float,
        default=0.4,
        help="Delay between platforms in seconds (default: 0.4)",
    )
    ap.add_argument(
        "--add",
        action="append",
        default=[],
        help="Add a platform in the form NAME=https://example.com (repeatable)",
    )
    ap.add_argument(
        "--only",
        action="append",
        default=[],
        help="Only download platforms whose name contains this substring (repeatable)",
    )
    ap.add_argument(
        "--report-json",
        default="",
        help="Optional path to write a JSON report (default: disabled)",
    )

    args = ap.parse_args(argv)

    platforms: list[Platform] = list(DEFAULT_PLATFORMS)
    if args.add:
        platforms.extend(parse_add_items(args.add))

    if args.only:
        needles = [s.lower().strip() for s in args.only if s.strip()]
        platforms = [p for p in platforms if any(n in p.name.lower() for n in needles)]

    out_dir = args.out
    use_google = not args.no_google_fallback

    results: list[dict] = []
    print(f"Downloading icons to: {out_dir}")
    print(f"Platforms: {len(platforms)} | Google fallback: {'on' if use_google else 'off'}")

    ok = 0
    for platform in platforms:
        print(f"- {platform.name}: {platform.base_urls[0] if platform.base_urls else ''}")
        res = download_for_platform(
            platform=platform,
            out_dir=out_dir,
            timeout_s=args.timeout,
            user_agent=args.user_agent,
            use_google_fallback=use_google,
            sleep_s=args.sleep,
        )
        results.append(res)
        if res["status"] == "ok":
            ok += 1
            print(f"  saved: {res['saved_path']}")
        else:
            print(f"  failed: {res['error']}")

    if args.report_json:
        os.makedirs(os.path.dirname(args.report_json) or ".", exist_ok=True)
        with open(args.report_json, "w", encoding="utf-8") as f:
            json.dump({"results": results}, f, indent=2)
        print(f"Wrote report: {args.report_json}")

    print(f"Done. Success: {ok}/{len(platforms)}")
    return 0 if ok > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
