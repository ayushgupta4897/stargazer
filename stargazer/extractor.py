"""
Main extraction service for GitHub repository information.
"""

import logging
from typing import Optional, Union, Tuple
from urllib.parse import urlparse

from .github_client import GitHubClient, GitHubAPIError, RateLimitError
from .models import ExtractionResult, RepoInfo, UserInfo


logger = logging.getLogger(__name__)


class GitHubExtractor:
    """Main service for extracting GitHub repository information."""
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize the extractor.
        
        Args:
            github_token: GitHub personal access token (optional)
        """
        self.client = GitHubClient(github_token)
    
    def extract_repository_info(
        self,
        repo_url: str,
        include_stargazers: bool = True,
        include_forkers: bool = True,
        max_stargazers: Optional[int] = None,
        max_forkers: Optional[int] = None,
        detailed_user_info: bool = False,
        aggressive_email_extraction: bool = True
    ) -> ExtractionResult:
        """Extract information from a GitHub repository.
        
        Args:
            repo_url: GitHub repository URL or owner/repo format
            include_stargazers: Whether to include stargazers
            include_forkers: Whether to include forkers
            max_stargazers: Maximum number of stargazers to fetch
            max_forkers: Maximum number of forkers to fetch
            detailed_user_info: Whether to fetch detailed user information
            aggressive_email_extraction: Whether to use multiple methods to extract emails
            
        Returns:
            Extraction result containing all gathered information
            
        Raises:
            GitHubAPIError: If the repository cannot be accessed
            RateLimitError: If rate limit is exceeded
        """
        # Parse repository owner and name
        owner, repo_name = self._parse_repo_identifier(repo_url)
        
        logger.info(f"Extracting information for {owner}/{repo_name}")
        
        # Get repository information
        try:
            repo_info = self.client.get_repository_info(owner, repo_name)
            logger.info(f"Repository has {repo_info.stargazers_count} stars and {repo_info.forks_count} forks")
        except GitHubAPIError as e:
            logger.error(f"Failed to get repository info: {e}")
            raise
        
        # Initialize result
        result = ExtractionResult(
            repository=repo_info,
            total_stargazers=repo_info.stargazers_count,
            total_forkers=repo_info.forks_count
        )
        
        # Extract stargazers
        if include_stargazers:
            try:
                stargazers = self._extract_stargazers(
                    owner, repo_name, max_stargazers, detailed_user_info, aggressive_email_extraction
                )
                result.stargazers = stargazers
                logger.info(f"Extracted {len(stargazers)} stargazers")
            except Exception as e:
                logger.warning(f"Failed to extract stargazers: {e}")
        
        # Extract forkers
        if include_forkers:
            try:
                forkers = self._extract_forkers(
                    owner, repo_name, max_forkers, detailed_user_info, aggressive_email_extraction
                )
                result.forkers = forkers
                logger.info(f"Extracted {len(forkers)} forkers")
            except Exception as e:
                logger.warning(f"Failed to extract forkers: {e}")
        
        return result
    
    def _parse_repo_identifier(self, repo_identifier: str) -> Tuple[str, str]:
        """Parse repository identifier to extract owner and repo name.
        
        Args:
            repo_identifier: GitHub URL or owner/repo format
            
        Returns:
            Tuple of (owner, repo_name)
            
        Raises:
            ValueError: If the identifier format is invalid
        """
        repo_identifier = repo_identifier.strip()
        
        # Handle GitHub URLs
        if repo_identifier.startswith(('http://', 'https://')):
            parsed = urlparse(repo_identifier)
            if parsed.netloc != 'github.com':
                raise ValueError("Only GitHub repositories are supported")
            
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) < 2:
                raise ValueError("Invalid GitHub repository URL")
            
            return path_parts[0], path_parts[1]
        
        # Handle owner/repo format
        if '/' in repo_identifier:
            parts = repo_identifier.split('/')
            if len(parts) != 2:
                raise ValueError("Invalid repository format. Use 'owner/repo'")
            
            return parts[0], parts[1]
        
        raise ValueError(
            "Invalid repository identifier. Use GitHub URL or 'owner/repo' format"
        )
    
    def _extract_stargazers(
        self,
        owner: str,
        repo_name: str,
        max_count: Optional[int],
        detailed_info: bool,
        aggressive_email_extraction: bool
    ) -> list[UserInfo]:
        """Extract stargazers information.
        
        Args:
            owner: Repository owner
            repo_name: Repository name
            max_count: Maximum number of stargazers to fetch
            detailed_info: Whether to fetch detailed user information
            aggressive_email_extraction: Whether to use multiple methods to extract emails
            
        Returns:
            List of user information
        """
        per_page = 30
        max_pages = None
        
        if max_count:
            max_pages = (max_count + per_page - 1) // per_page
        
        stargazers = self.client.get_stargazers(owner, repo_name, per_page, max_pages)
        
        if max_count:
            stargazers = stargazers[:max_count]
        
        # Fetch detailed information if requested
        if detailed_info:
            detailed_stargazers = []
            for user in stargazers:
                try:
                    detailed_user = self.client.get_user_info(user.login, aggressive_email_extraction)
                    detailed_stargazers.append(detailed_user)
                except Exception as e:
                    logger.warning(f"Failed to get detailed info for {user.login}: {e}")
                    detailed_stargazers.append(user)
            
            stargazers = detailed_stargazers
        
        return stargazers
    
    def _extract_forkers(
        self,
        owner: str,
        repo_name: str,
        max_count: Optional[int],
        detailed_info: bool,
        aggressive_email_extraction: bool
    ) -> list[UserInfo]:
        """Extract forkers information.
        
        Args:
            owner: Repository owner
            repo_name: Repository name
            max_count: Maximum number of forkers to fetch
            detailed_info: Whether to fetch detailed user information
            aggressive_email_extraction: Whether to use multiple methods to extract emails
            
        Returns:
            List of user information
        """
        per_page = 30
        max_pages = None
        
        if max_count:
            max_pages = (max_count + per_page - 1) // per_page
        
        forkers = self.client.get_forks(owner, repo_name, per_page, max_pages)
        
        if max_count:
            forkers = forkers[:max_count]
        
        # Fetch detailed information if requested
        if detailed_info:
            detailed_forkers = []
            for user in forkers:
                try:
                    detailed_user = self.client.get_user_info(user.login, aggressive_email_extraction)
                    detailed_forkers.append(detailed_user)
                except Exception as e:
                    logger.warning(f"Failed to get detailed info for {user.login}: {e}")
                    detailed_forkers.append(user)
            
            forkers = detailed_forkers
        
        return forkers
    
    def get_rate_limit_status(self) -> dict:
        """Get current rate limit status.
        
        Returns:
            Rate limit information
        """
        return self.client.get_rate_limit_status() 