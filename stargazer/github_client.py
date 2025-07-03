"""
GitHub API client for making requests to the GitHub API.
"""

import time
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin, urlparse, parse_qs
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import Config
from .models import UserInfo, RepoInfo


logger = logging.getLogger(__name__)


class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors."""
    pass


class RateLimitError(GitHubAPIError):
    """Exception for rate limit errors."""
    pass


class GitHubClient:
    """GitHub API client with rate limiting and error handling."""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize the GitHub client.
        
        Args:
            token: GitHub personal access token (optional)
        """
        self.config = Config()
        if token:
            self.config.GITHUB_TOKEN = token
        
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.config.MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the GitHub API.
        
        Args:
            endpoint: API endpoint (e.g., '/repos/owner/repo')
            params: Query parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            GitHubAPIError: If the request fails
            RateLimitError: If rate limit is exceeded
        """
        url = urljoin(self.config.GITHUB_API_BASE_URL, endpoint)
        headers = self.config.get_headers()
        
        try:
            response = self.session.get(
                url,
                headers=headers,
                params=params,
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            # Check rate limit
            if response.status_code == 429:
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                current_time = int(time.time())
                wait_time = max(reset_time - current_time, 60)  # Wait at least 1 minute
                
                raise RateLimitError(
                    f"Rate limit exceeded. Try again in {wait_time} seconds."
                )
            
            response.raise_for_status()
            
            # Add small delay to be respectful to the API
            time.sleep(0.1)
            
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 404:
                raise GitHubAPIError(f"Repository not found: {endpoint}")
            elif response.status_code == 403:
                raise GitHubAPIError(f"Access forbidden: {endpoint}")
            else:
                raise GitHubAPIError(f"HTTP error {response.status_code}: {str(e)}")
        
        except requests.exceptions.RequestException as e:
            raise GitHubAPIError(f"Request failed: {str(e)}")
    
    def get_repository_info(self, owner: str, repo: str) -> RepoInfo:
        """Get repository information.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository information
        """
        endpoint = f"/repos/{owner}/{repo}"
        data = self._make_request(endpoint)
        
        return RepoInfo(
            name=data["name"],
            full_name=data["full_name"],
            owner=data["owner"]["login"],
            description=data.get("description"),
            html_url=data["html_url"],
            stargazers_count=data["stargazers_count"],
            forks_count=data["forks_count"],
            language=data.get("language"),
            created_at=data["created_at"],
            updated_at=data["updated_at"]
        )
    
    def get_user_info(self, username: str, aggressive_email_extraction: bool = True) -> UserInfo:
        """Get user information.
        
        Args:
            username: GitHub username
            aggressive_email_extraction: Whether to use multiple methods to extract emails
            
        Returns:
            User information
        """
        endpoint = f"/users/{username}"
        data = self._make_request(endpoint)
        
        # Try to get email from profile first
        email = data.get("email")
        
        # If email is not public and aggressive extraction is enabled, try other methods
        if not email and aggressive_email_extraction:
            logger.debug(f"Email not public for {username}, trying aggressive extraction methods...")
            
            # Try to extract from commits
            try:
                email = self._extract_email_from_commits(username)
                if email:
                    logger.info(f"Found email for {username} from commits: {email}")
            except Exception as e:
                logger.debug(f"Could not extract email from commits for {username}: {e}")
            
            # If still no email, try to extract from events
            if not email:
                try:
                    email = self._extract_email_from_events(username)
                    if email:
                        logger.info(f"Found email for {username} from events: {email}")
                except Exception as e:
                    logger.debug(f"Could not extract email from events for {username}: {e}")
            
            # If still no email, try to extract from user's repositories
            if not email:
                try:
                    email = self._extract_email_from_user_repos(username)
                    if email:
                        logger.info(f"Found email for {username} from repositories: {email}")
                except Exception as e:
                    logger.debug(f"Could not extract email from user repos for {username}: {e}")
            
            if not email:
                logger.debug(f"No email found for {username} after trying all methods")
        elif not email:
            logger.debug(f"No public email for {username} and aggressive extraction disabled")
        
        return UserInfo(
            login=data["login"],
            name=data.get("name"),
            email=email,
            location=data.get("location"),
            company=data.get("company"),
            bio=data.get("bio"),
            blog=data.get("blog"),
            twitter_username=data.get("twitter_username"),
            public_repos=data["public_repos"],
            followers=data["followers"],
            following=data["following"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            avatar_url=data["avatar_url"],
            html_url=data["html_url"]
        )
    
    def get_stargazers(self, owner: str, repo: str, per_page: int = 30, max_pages: Optional[int] = None) -> List[UserInfo]:
        """Get repository stargazers.
        
        Args:
            owner: Repository owner
            repo: Repository name
            per_page: Number of results per page
            max_pages: Maximum number of pages to fetch (None for all)
            
        Returns:
            List of user information
        """
        endpoint = f"/repos/{owner}/{repo}/stargazers"
        return self._paginate_users(endpoint, per_page, max_pages)
    
    def get_forks(self, owner: str, repo: str, per_page: int = 30, max_pages: Optional[int] = None) -> List[UserInfo]:
        """Get repository forks.
        
        Args:
            owner: Repository owner
            repo: Repository name
            per_page: Number of results per page
            max_pages: Maximum number of pages to fetch (None for all)
            
        Returns:
            List of user information for fork owners
        """
        endpoint = f"/repos/{owner}/{repo}/forks"
        users = []
        page = 1
        
        while True:
            if max_pages and page > max_pages:
                break
                
            params = {"page": page, "per_page": per_page}
            data = self._make_request(endpoint, params)
            
            if not data:
                break
            
            # Extract owner information from forks
            for fork in data:
                owner_info = fork["owner"]
                user = UserInfo(
                    login=owner_info["login"],
                    avatar_url=owner_info["avatar_url"],
                    html_url=owner_info["html_url"]
                )
                users.append(user)
            
            page += 1
        
        return users
    
    def _paginate_users(self, endpoint: str, per_page: int, max_pages: Optional[int]) -> List[UserInfo]:
        """Paginate through user results.
        
        Args:
            endpoint: API endpoint
            per_page: Number of results per page
            max_pages: Maximum number of pages to fetch
            
        Returns:
            List of user information
        """
        users = []
        page = 1
        
        while True:
            if max_pages and page > max_pages:
                break
                
            params = {"page": page, "per_page": per_page}
            data = self._make_request(endpoint, params)
            
            if not data:
                break
            
            for user_data in data:
                user = UserInfo(
                    login=user_data["login"],
                    avatar_url=user_data["avatar_url"],
                    html_url=user_data["html_url"]
                )
                users.append(user)
            
            page += 1
        
        return users
    
    def _extract_email_from_commits(self, username: str) -> Optional[str]:
        """Try to extract email from user's recent commits.
        
        Args:
            username: GitHub username
            
        Returns:
            Email address if found, None otherwise
        """
        try:
            # Get user's recent events to find commits
            endpoint = f"/users/{username}/events"
            events = self._make_request(endpoint, params={"per_page": 30})
            
            for event in events:
                if event.get("type") == "PushEvent":
                    commits = event.get("payload", {}).get("commits", [])
                    for commit in commits:
                        if commit.get("author", {}).get("email"):
                            email = commit["author"]["email"]
                            # Filter out noreply emails and obvious fake emails
                            if (email and 
                                not email.endswith("@users.noreply.github.com") and
                                "@" in email and
                                not email.startswith("noreply")):
                                logger.debug(f"Found email from commit for {username}: {email}")
                                return email
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting email from commits for {username}: {e}")
            return None
    
    def _extract_email_from_events(self, username: str) -> Optional[str]:
        """Try to extract email from user's public events.
        
        Args:
            username: GitHub username
            
        Returns:
            Email address if found, None otherwise
        """
        try:
            # Get user's public events
            endpoint = f"/users/{username}/events/public"
            events = self._make_request(endpoint, params={"per_page": 30})
            
            for event in events:
                # Check various event types that might contain email
                if event.get("type") == "CreateEvent":
                    # Sometimes create events have author info
                    if event.get("payload", {}).get("commits"):
                        for commit in event["payload"]["commits"]:
                            if commit.get("author", {}).get("email"):
                                email = commit["author"]["email"]
                                if (email and 
                                    not email.endswith("@users.noreply.github.com") and
                                    "@" in email and
                                    not email.startswith("noreply")):
                                    logger.debug(f"Found email from event for {username}: {email}")
                                    return email
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting email from events for {username}: {e}")
            return None
    
    def _extract_email_from_user_repos(self, username: str) -> Optional[str]:
        """Try to extract email from user's repository commits.
        
        Args:
            username: GitHub username
            
        Returns:
            Email address if found, None otherwise
        """
        try:
            # Get user's repositories
            endpoint = f"/users/{username}/repos"
            repos = self._make_request(endpoint, params={"per_page": 10, "sort": "updated"})
            
            for repo in repos[:3]:  # Check only first 3 repos to avoid rate limiting
                if repo.get("owner", {}).get("login") == username:  # Only check user's own repos
                    try:
                        # Get recent commits from this repo
                        commits_endpoint = f"/repos/{username}/{repo['name']}/commits"
                        commits = self._make_request(commits_endpoint, params={"per_page": 10, "author": username})
                        
                        for commit in commits:
                            if commit.get("commit", {}).get("author", {}).get("email"):
                                email = commit["commit"]["author"]["email"]
                                if (email and 
                                    not email.endswith("@users.noreply.github.com") and
                                    "@" in email and
                                    not email.startswith("noreply")):
                                    logger.debug(f"Found email from repo commits for {username}: {email}")
                                    return email
                    except Exception as e:
                        logger.debug(f"Error checking repo {repo['name']} for {username}: {e}")
                        continue
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting email from user repos for {username}: {e}")
            return None
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status.
        
        Returns:
            Rate limit information
        """
        endpoint = "/rate_limit"
        return self._make_request(endpoint) 