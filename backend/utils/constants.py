"""
Constants and configuration for SEO Analyzer.

This module contains shared constants used across the application.
"""

# AI Crawler Bot Definitions
# Maps bot user-agent names to their descriptions
AI_BOTS: dict[str, str] = {
    # OpenAI
    "GPTBot": "OpenAI training crawler",
    "OAI-SearchBot": "ChatGPT search feature",
    "ChatGPT-User": "ChatGPT user browsing actions",
    
    # Anthropic
    "ClaudeBot": "Anthropic training crawler",
    "Claude-Web": "Claude web access",
    "anthropic-ai": "Anthropic AI crawler",
    
    # Google
    "Google-Extended": "Google Gemini/Bard training",
    "GoogleOther": "Google other services",
    
    # Others
    "PerplexityBot": "Perplexity AI search",
    "Bytespider": "ByteDance/TikTok crawler",
    "CCBot": "Common Crawl (used by many AI)",
    "Amazonbot": "Amazon Alexa/AI services",
    "Applebot-Extended": "Apple AI features",
    "cohere-ai": "Cohere AI training",
    "Diffbot": "Diffbot knowledge graph",
    "FacebookBot": "Meta AI training",
    "Meta-ExternalAgent": "Meta external AI agent",
    "omgili": "Webz.io data for AI",
    "Timpibot": "Timpi search engine",
}

# Stop words for keyword extraction
STOP_WORDS: set[str] = {
    'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
    'her', 'was', 'one', 'our', 'out', 'has', 'have', 'been', 'were', 'will',
    'with', 'this', 'that', 'from', 'they', 'what', 'which', 'their', 'there',
    'would', 'could', 'should', 'about', 'into', 'more', 'some', 'than', 'them',
    'then', 'these', 'when', 'where', 'your', 'just', 'also', 'only', 'other',
    'such', 'like', 'very', 'even', 'most', 'make', 'made', 'each', 'does',
    'how', 'its', 'may', 'use', 'any', 'being', 'both', 'find', 'here', 'many',
    'through', 'using', 'well', 'back', 'much', 'before', 'must', 'right', 'still',
    'own', 'same', 'see', 'now', 'way', 'come', 'since', 'another', 'over',
}

# SEO Thresholds
TITLE_MIN_LENGTH = 30
TITLE_MAX_LENGTH = 60
META_DESC_MIN_LENGTH = 70
META_DESC_MAX_LENGTH = 160
MIN_WORD_COUNT_GOOD = 500
MIN_WORD_COUNT_OK = 300

# Score deductions
SCORE_DEDUCTION_HIGH = 15
SCORE_DEDUCTION_MEDIUM = 8
SCORE_DEDUCTION_LOW = 3
