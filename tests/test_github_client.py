"""
Tests for the GitHub client.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from stargazer.github_client import GitHubClient, GitHubAPIError, RateLimitError
from stargazer.models import UserInfo, RepoInfo


class TestGitHubClient:
    """Test GitHubClient class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = GitHubClient()
    
    def test_init_without_token(self):
        """Test client initialization without token."""
        client = GitHubClient()
        assert client.config.GITHUB_TOKEN is None
        assert client.session is not None
    
    def test_init_with_token(self):
        """Test client initialization with token."""
        client = GitHubClient(token="test-token")
        assert client.config.GITHUB_TOKEN == "test-token"
    
    @patch('stargazer.github_client.requests.Session')
    def test_create_session(self, mock_session_class):
        """Test session creation with retry strategy."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        client = GitHubClient()
        
        # Verify session was created and configured
        mock_session_class.assert_called_once()
        assert mock_session.mount.call_count == 2  # http and https
    
    @patch('stargazer.github_client.requests.Session')
    def test_make_request_success(self, mock_session_class):
        """Test successful API request."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"login": "testuser"}
        mock_session.get.return_value = mock_response
        
        client = GitHubClient()
        
        result = client._make_request("/test")
        
        assert result == {"login": "testuser"}
        mock_session.get.assert_called_once()
    
    @patch('stargazer.github_client.requests.Session')
    def test_make_request_rate_limit(self, mock_session_class):
        """Test rate limit handling."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock rate limit response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'X-RateLimit-Reset': '1635206400'}
        mock_session.get.return_value = mock_response
        
        client = GitHubClient()
        
        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            client._make_request("/test")
    
    @patch('stargazer.github_client.requests.Session')
    def test_make_request_404_error(self, mock_session_class):
        """Test 404 error handling."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock 404 response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_session.get.return_value = mock_response
        
        client = GitHubClient()
        
        with pytest.raises(GitHubAPIError, match="Repository not found"):
            client._make_request("/repos/nonexistent/repo")
    
    @patch('stargazer.github_client.requests.Session')
    def test_make_request_forbidden_error(self, mock_session_class):
        """Test 403 error handling."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock 403 response
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_session.get.return_value = mock_response
        
        client = GitHubClient()
        
        with pytest.raises(GitHubAPIError, match="Access forbidden"):
            client._make_request("/test")
    
    @patch('stargazer.github_client.requests.Session')
    def test_make_request_connection_error(self, mock_session_class):
        """Test connection error handling."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock connection error
        mock_session.get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        client = GitHubClient()
        
        with pytest.raises(GitHubAPIError, match="Request failed"):
            client._make_request("/test")
    
    @patch.object(GitHubClient, '_make_request')
    def test_get_repository_info(self, mock_make_request):
        """Test repository information retrieval."""
        mock_make_request.return_value = {
            "name": "test-repo",
            "full_name": "owner/test-repo",
            "owner": {"login": "owner"},
            "description": "Test repository",
            "html_url": "https://github.com/owner/test-repo",
            "stargazers_count": 100,
            "forks_count": 20,
            "language": "Python",
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z"
        }
        
        client = GitHubClient()
        repo = client.get_repository_info("owner", "test-repo")
        
        assert isinstance(repo, RepoInfo)
        assert repo.name == "test-repo"
        assert repo.full_name == "owner/test-repo"
        assert repo.owner == "owner"
        assert repo.description == "Test repository"
        assert repo.stargazers_count == 100
        assert repo.forks_count == 20
        assert repo.language == "Python"
        
        mock_make_request.assert_called_once_with("/repos/owner/test-repo")
    
    @patch.object(GitHubClient, '_make_request')
    def test_get_user_info(self, mock_make_request):
        """Test user information retrieval."""
        mock_make_request.return_value = {
            "login": "testuser",
            "name": "Test User",
            "email": "test@example.com",
            "location": "Test City",
            "company": "Test Company",
            "bio": "Test bio",
            "blog": "https://testblog.com",
            "twitter_username": "testuser",
            "public_repos": 10,
            "followers": 100,
            "following": 50,
            "created_at": "2020-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "avatar_url": "https://github.com/testuser.png",
            "html_url": "https://github.com/testuser"
        }
        
        client = GitHubClient()
        user = client.get_user_info("testuser")
        
        assert isinstance(user, UserInfo)
        assert user.login == "testuser"
        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.location == "Test City"
        assert user.company == "Test Company"
        assert user.public_repos == 10
        assert user.followers == 100
        assert user.following == 50
        
        mock_make_request.assert_called_once_with("/users/testuser")
    
    @patch.object(GitHubClient, '_paginate_users')
    def test_get_stargazers(self, mock_paginate_users):
        """Test stargazers retrieval."""
        mock_users = [UserInfo(login="star1"), UserInfo(login="star2")]
        mock_paginate_users.return_value = mock_users
        
        client = GitHubClient()
        stargazers = client.get_stargazers("owner", "repo")
        
        assert len(stargazers) == 2
        assert stargazers[0].login == "star1"
        assert stargazers[1].login == "star2"
        
        mock_paginate_users.assert_called_once_with("/repos/owner/repo/stargazers", 30, None)
    
    @patch.object(GitHubClient, '_make_request')
    def test_get_forks(self, mock_make_request):
        """Test forks retrieval."""
        mock_make_request.side_effect = [
            [
                {
                    "owner": {
                        "login": "forker1",
                        "avatar_url": "https://github.com/forker1.png",
                        "html_url": "https://github.com/forker1"
                    }
                },
                {
                    "owner": {
                        "login": "forker2",
                        "avatar_url": "https://github.com/forker2.png",
                        "html_url": "https://github.com/forker2"
                    }
                }
            ],
            []  # Empty response to end pagination
        ]
        
        client = GitHubClient()
        forkers = client.get_forks("owner", "repo")
        
        assert len(forkers) == 2
        assert forkers[0].login == "forker1"
        assert forkers[1].login == "forker2"
        
        assert mock_make_request.call_count == 2
    
    @patch.object(GitHubClient, '_make_request')
    def test_paginate_users(self, mock_make_request):
        """Test user pagination."""
        mock_make_request.side_effect = [
            [
                {
                    "login": "user1",
                    "avatar_url": "https://github.com/user1.png",
                    "html_url": "https://github.com/user1"
                }
            ],
            [
                {
                    "login": "user2",
                    "avatar_url": "https://github.com/user2.png",
                    "html_url": "https://github.com/user2"
                }
            ],
            []  # Empty response to end pagination
        ]
        
        client = GitHubClient()
        users = client._paginate_users("/test", 30, None)
        
        assert len(users) == 2
        assert users[0].login == "user1"
        assert users[1].login == "user2"
        
        assert mock_make_request.call_count == 3
    
    @patch.object(GitHubClient, '_make_request')
    def test_paginate_users_with_limit(self, mock_make_request):
        """Test user pagination with page limit."""
        mock_make_request.return_value = [
            {
                "login": "user1",
                "avatar_url": "https://github.com/user1.png",
                "html_url": "https://github.com/user1"
            }
        ]
        
        client = GitHubClient()
        users = client._paginate_users("/test", 30, 1)  # Max 1 page
        
        assert len(users) == 1
        assert users[0].login == "user1"
        
        mock_make_request.assert_called_once()
    
    @patch.object(GitHubClient, '_make_request')
    def test_get_rate_limit_status(self, mock_make_request):
        """Test rate limit status retrieval."""
        mock_rate_limit = {
            "rate": {
                "limit": 5000,
                "remaining": 4999,
                "reset": 1635206400
            }
        }
        mock_make_request.return_value = mock_rate_limit
        
        client = GitHubClient()
        result = client.get_rate_limit_status()
        
        assert result == mock_rate_limit
        mock_make_request.assert_called_once_with("/rate_limit") 