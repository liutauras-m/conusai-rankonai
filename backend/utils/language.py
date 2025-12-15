"""
Language Detection Utilities.

Detects page language using multiple signals for accurate results.
Supports SEO and AI optimization by providing language context.
"""

import re
from typing import Optional


# Common language codes and their full names
LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "pl": "Polish",
    "ru": "Russian",
    "ja": "Japanese",
    "zh": "Chinese",
    "ko": "Korean",
    "ar": "Arabic",
    "hi": "Hindi",
    "tr": "Turkish",
    "vi": "Vietnamese",
    "th": "Thai",
    "id": "Indonesian",
    "ms": "Malay",
    "sv": "Swedish",
    "da": "Danish",
    "fi": "Finnish",
    "no": "Norwegian",
    "cs": "Czech",
    "uk": "Ukrainian",
    "el": "Greek",
    "he": "Hebrew",
    "ro": "Romanian",
    "hu": "Hungarian",
    "sk": "Slovak",
    "bg": "Bulgarian",
    "hr": "Croatian",
    "sr": "Serbian",
    "sl": "Slovenian",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "et": "Estonian",
}


# Common words by language for content-based detection
LANGUAGE_INDICATORS: dict[str, set[str]] = {
    "en": {"the", "and", "is", "are", "was", "were", "have", "has", "been", "will", "would", "could", "should", "this", "that", "with", "from", "they", "their", "about"},
    "es": {"el", "la", "los", "las", "de", "del", "que", "en", "es", "por", "con", "para", "una", "uno", "como", "pero", "ser", "estar", "este", "esta"},
    "fr": {"le", "la", "les", "de", "des", "du", "que", "est", "sont", "pour", "dans", "avec", "sur", "par", "une", "cette", "nous", "vous", "leur", "mais"},
    "de": {"der", "die", "das", "und", "ist", "von", "mit", "auf", "den", "des", "eine", "einer", "haben", "wird", "sind", "werden", "nicht", "auch", "sich", "nach"},
    "it": {"il", "la", "di", "che", "per", "con", "una", "sono", "del", "della", "alla", "questo", "quella", "essere", "hanno", "anche", "come", "loro", "tutti", "nella"},
    "pt": {"o", "a", "os", "as", "de", "da", "do", "que", "em", "para", "com", "uma", "por", "como", "mas", "foi", "ser", "tem", "seu", "sua"},
    "nl": {"de", "het", "een", "van", "en", "in", "is", "dat", "op", "te", "zijn", "voor", "met", "als", "aan", "worden", "dit", "ook", "niet", "naar"},
    "pl": {"i", "w", "na", "do", "z", "jest", "nie", "to", "sie", "jak", "od", "po", "dla", "czy", "ale", "tak", "przez", "tego", "przy", "oraz"},
    "ru": {"и", "в", "на", "не", "что", "с", "по", "это", "как", "для", "из", "но", "все", "от", "его", "она", "они", "так", "или", "мы"},
}


class LanguageDetector:
    """
    Detect page language using multiple signals.
    
    Detection sources (in priority order):
    1. HTML lang attribute (most reliable)
    2. Content-Language HTTP header
    3. hreflang tags
    4. og:locale meta tag
    5. Content analysis (fallback)
    
    Example:
        detector = LanguageDetector()
        result = detector.detect(
            html_lang="en-US",
            content_language="en",
            text_content="Hello world...",
        )
        # result = {"code": "en", "name": "English", "confidence": "high", ...}
    """
    
    def detect(
        self,
        html_lang: Optional[str] = None,
        content_language: Optional[str] = None,
        og_locale: Optional[str] = None,
        hreflang_tags: Optional[list[dict]] = None,
        text_content: Optional[str] = None,
    ) -> dict:
        """
        Detect language from multiple sources.
        
        Args:
            html_lang: Value of HTML lang attribute
            content_language: Content-Language HTTP header
            og_locale: og:locale meta tag value
            hreflang_tags: List of hreflang link tags
            text_content: Page text content for fallback detection
            
        Returns:
            Dictionary with detection results:
            - code: ISO 639-1 language code (e.g., "en")
            - region: Region code if available (e.g., "US")
            - name: Full language name
            - confidence: Detection confidence ("high", "medium", "low")
            - source: Detection source used
            - alternatives: Other detected languages
            - issues: Any language-related SEO issues
        """
        result = {
            "code": None,
            "region": None,
            "name": None,
            "confidence": "low",
            "source": None,
            "alternatives": [],
            "issues": [],
        }
        
        # Try detection sources in priority order
        detected = None
        
        # 1. HTML lang attribute (highest priority)
        if html_lang:
            detected = self._parse_lang_code(html_lang)
            if detected:
                result.update(detected)
                result["confidence"] = "high"
                result["source"] = "html_lang"
        
        # 2. Content-Language header
        if not result["code"] and content_language:
            detected = self._parse_lang_code(content_language)
            if detected:
                result.update(detected)
                result["confidence"] = "high"
                result["source"] = "content_language_header"
        
        # 3. og:locale meta tag
        if not result["code"] and og_locale:
            detected = self._parse_og_locale(og_locale)
            if detected:
                result.update(detected)
                result["confidence"] = "medium"
                result["source"] = "og_locale"
        
        # 4. hreflang tags (can provide alternatives)
        if hreflang_tags:
            alternatives = self._extract_hreflang_languages(hreflang_tags)
            if alternatives:
                result["alternatives"] = alternatives
                # If no primary detected, use x-default or first hreflang
                if not result["code"]:
                    for alt in alternatives:
                        if alt.get("is_default"):
                            result.update(self._parse_lang_code(alt["code"]) or {})
                            result["confidence"] = "medium"
                            result["source"] = "hreflang_default"
                            break
        
        # 5. Content-based detection (fallback)
        if not result["code"] and text_content:
            detected = self._detect_from_content(text_content)
            if detected:
                result.update(detected)
                result["confidence"] = "low"
                result["source"] = "content_analysis"
        
        # Set language name
        if result["code"]:
            result["name"] = LANGUAGE_NAMES.get(
                result["code"].lower(), 
                result["code"].upper()
            )
        
        # Check for SEO issues
        result["issues"] = self._check_language_issues(
            html_lang=html_lang,
            content_language=content_language,
            hreflang_tags=hreflang_tags,
            detected_code=result["code"],
        )
        
        return result
    
    def _parse_lang_code(self, lang_value: str) -> Optional[dict]:
        """Parse a language code like 'en-US' or 'en'."""
        if not lang_value:
            return None
        
        # Clean and normalize
        lang_value = lang_value.strip().lower()
        
        # Handle formats: en, en-US, en_US
        match = re.match(r'^([a-z]{2,3})(?:[-_]([a-z]{2,4}))?', lang_value, re.IGNORECASE)
        if match:
            code = match.group(1).lower()
            region = match.group(2).upper() if match.group(2) else None
            return {"code": code, "region": region}
        
        return None
    
    def _parse_og_locale(self, locale: str) -> Optional[dict]:
        """Parse og:locale format like 'en_US'."""
        if not locale:
            return None
        
        # og:locale uses underscore: en_US
        return self._parse_lang_code(locale.replace("_", "-"))
    
    def _extract_hreflang_languages(self, hreflang_tags: list[dict]) -> list[dict]:
        """Extract language info from hreflang tags."""
        languages = []
        
        for tag in hreflang_tags:
            hreflang = tag.get("hreflang", "")
            href = tag.get("href", "")
            
            if hreflang == "x-default":
                languages.append({
                    "code": "x-default",
                    "href": href,
                    "is_default": True,
                })
            else:
                parsed = self._parse_lang_code(hreflang)
                if parsed:
                    languages.append({
                        "code": parsed["code"],
                        "region": parsed.get("region"),
                        "href": href,
                        "is_default": False,
                    })
        
        return languages
    
    def _detect_from_content(self, text: str, sample_size: int = 1000) -> Optional[dict]:
        """Detect language from text content using word frequency."""
        if not text or len(text.strip()) < 50:
            return None
        
        # Sample text for efficiency
        sample = text[:sample_size].lower()
        words = set(re.findall(r'\b[a-z\u0400-\u04ff]{2,}\b', sample))
        
        if not words:
            return None
        
        # Score each language by matching indicator words
        scores: dict[str, int] = {}
        for lang_code, indicators in LANGUAGE_INDICATORS.items():
            matches = words & indicators
            if matches:
                scores[lang_code] = len(matches)
        
        if not scores:
            return None
        
        # Get best match
        best_lang = max(scores, key=scores.get)
        best_score = scores[best_lang]
        
        # Require minimum confidence
        if best_score < 3:
            return None
        
        return {"code": best_lang, "region": None}
    
    def _check_language_issues(
        self,
        html_lang: Optional[str],
        content_language: Optional[str],
        hreflang_tags: Optional[list[dict]],
        detected_code: Optional[str],
    ) -> list[dict]:
        """Check for language-related SEO issues."""
        issues = []
        
        # Missing HTML lang attribute
        if not html_lang:
            issues.append({
                "code": "LANG_ATTR_MISSING",
                "severity": "medium",
                "message": "HTML lang attribute is missing - important for SEO and accessibility",
                "recommendation": "Add lang attribute to <html> tag, e.g., <html lang=\"en\">",
            })
        
        # Check for consistency between sources
        if html_lang and content_language:
            html_parsed = self._parse_lang_code(html_lang)
            header_parsed = self._parse_lang_code(content_language)
            
            if html_parsed and header_parsed:
                if html_parsed["code"] != header_parsed["code"]:
                    issues.append({
                        "code": "LANG_MISMATCH",
                        "severity": "medium",
                        "message": f"Language mismatch: HTML lang='{html_lang}' vs Content-Language='{content_language}'",
                        "recommendation": "Ensure HTML lang attribute matches Content-Language header",
                    })
        
        # Check hreflang implementation
        if hreflang_tags:
            has_self_reference = False
            has_x_default = False
            
            for tag in hreflang_tags:
                if tag.get("hreflang") == "x-default":
                    has_x_default = True
                # Would need current URL to check self-reference
            
            if not has_x_default and len(hreflang_tags) > 1:
                issues.append({
                    "code": "HREFLANG_NO_DEFAULT",
                    "severity": "low",
                    "message": "No x-default hreflang specified for multilingual site",
                    "recommendation": "Add hreflang='x-default' pointing to default language version",
                })
        
        return issues


def get_language_context_for_ai(language_info: dict) -> str:
    """
    Generate language context string for AI prompts.
    
    Args:
        language_info: Language detection result dictionary
        
    Returns:
        Formatted string for inclusion in AI prompts
    """
    if not language_info or not language_info.get("code"):
        return "Language: Not detected (assume English)"
    
    code = language_info["code"]
    name = language_info.get("name", code.upper())
    region = language_info.get("region")
    confidence = language_info.get("confidence", "unknown")
    
    lang_str = f"{name}"
    if region:
        lang_str += f" ({region})"
    
    context = f"Language: {lang_str} (confidence: {confidence})"
    
    # Add alternatives if multilingual
    alternatives = language_info.get("alternatives", [])
    if alternatives:
        alt_codes = [a["code"] for a in alternatives if a["code"] != "x-default"]
        if alt_codes:
            context += f"\nAlternative languages: {', '.join(alt_codes)}"
    
    return context
