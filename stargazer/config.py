"""
Configuration management for Stargazer.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for GitHub API settings."""
    
    # GitHub API settings
    GITHUB_API_BASE_URL = "https://api.github.com"
    GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")
    
    # Rate limiting
    DEFAULT_RATE_LIMIT_DELAY = 1  # seconds
    MAX_RETRIES = 3
    
    # Pagination
    DEFAULT_PER_PAGE = 30
    MAX_PER_PAGE = 100
    
    # Timeout settings
    REQUEST_TIMEOUT = 30  # seconds
    
    @classmethod
    def get_headers(cls) -> dict:
        """Get headers for GitHub API requests."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Stargazer/0.1.0"
        }
        
        if cls.GITHUB_TOKEN:
            headers["Authorization"] = f"token {cls.GITHUB_TOKEN}"
        
        return headers
    
    @classmethod
    def has_token(cls) -> bool:
        """Check if GitHub token is available."""
        return cls.GITHUB_TOKEN is not None and cls.GITHUB_TOKEN.strip() != "" 