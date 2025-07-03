"""
Stargazer: A minimal Python tool to extract GitHub repository star and fork information.
"""

__version__ = "0.1.0"
__author__ = "Stargazer Team"

from .extractor import GitHubExtractor
from .models import UserInfo, RepoInfo

__all__ = ["GitHubExtractor", "UserInfo", "RepoInfo"] 