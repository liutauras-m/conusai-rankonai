"""
Shared configuration for ConusAI Tools backend.
Loads environment variables from root .env file.
"""

import os
from pathlib import Path
from typing import Optional

# Find root .env file (parent of backend directory)
# In Docker, BACKEND_DIR is /app, so we use /app for data too
BACKEND_DIR = Path(__file__).parent
IS_DOCKER = os.environ.get("REDIS_URL", "").startswith("redis://redis:")

if IS_DOCKER:
    # In Docker, use /app directory for everything
    ROOT_DIR = BACKEND_DIR
    DATA_DIR = BACKEND_DIR / "data"
else:
    # In development, use parent directory
    ROOT_DIR = BACKEND_DIR.parent
    DATA_DIR = ROOT_DIR / "data"

REPORTS_DIR = DATA_DIR / "reports"
GENERATED_DIR = DATA_DIR / "generated"

# Load environment variables from root .env
try:
    from dotenv import load_dotenv
    # Load from root .env first, then backend .env for overrides
    load_dotenv(ROOT_DIR / ".env")
    load_dotenv(BACKEND_DIR / ".env", override=True)
except ImportError:
    # Fallback: manually parse .env file
    def _load_env_file(path: Path):
        if not path.exists():
            return
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and value:
                        os.environ.setdefault(key, value)
    
    _load_env_file(ROOT_DIR / ".env")
    _load_env_file(BACKEND_DIR / ".env")


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable value."""
    return os.environ.get(key, default)


def get_api_key(provider: str) -> Optional[str]:
    """Get API key for a provider."""
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


# Ensure directories exist (only in development, Docker container has limited perms)
if not IS_DOCKER:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)


# Export commonly used paths as strings for compatibility
ROOT_DIR_STR = str(ROOT_DIR)
DATA_DIR_STR = str(DATA_DIR)
REPORTS_DIR_STR = str(REPORTS_DIR)
GENERATED_DIR_STR = str(GENERATED_DIR)
