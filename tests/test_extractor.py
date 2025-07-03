"""
Tests for the GitHubExtractor.
"""

import pytest
from unittest.mock import Mock, patch
from stargazer.extractor import GitHubExtractor
from stargazer.models import RepoInfo, UserInfo, ExtractionResult
from stargazer.github_client import GitHubAPIError


class TestGitHubExtractor:
    """Test GitHubExtractor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = GitHubExtractor()
    
    def test_parse_repo_identifier_url(self):
        """Test parsing GitHub URL."""
        owner, repo = self.extractor._parse_repo_identifier("https://github.com/owner/repo")
        assert owner == "owner"
        assert repo == "repo"
    
    def test_parse_repo_identifier_owner_repo(self):
        """Test parsing owner/repo format."""
        owner, repo = self.extractor._parse_repo_identifier("owner/repo")
        assert owner == "owner"
        assert repo == "repo"
    
    def test_parse_repo_identifier_invalid_url(self):
        """Test parsing invalid URL."""
        with pytest.raises(ValueError, match="Only GitHub repositories are supported"):
            self.extractor._parse_repo_identifier("https://gitlab.com/owner/repo")
    
    def test_parse_repo_identifier_invalid_format(self):
        """Test parsing invalid format."""
        with pytest.raises(ValueError, match="Invalid repository identifier"):
            self.extractor._parse_repo_identifier("invalid-format")
    
    def test_parse_repo_identifier_empty(self):
        """Test parsing empty string."""
        with pytest.raises(ValueError):
            self.extractor._parse_repo_identifier("")
    
    @patch('stargazer.extractor.GitHubClient')
    def test_extract_repository_info_success(self, mock_client_class):
        """Test successful repository information extraction."""
        # Mock the client
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock repository info
        mock_repo = RepoInfo(
            name="test-repo",
            full_name="owner/test-repo",
            owner="owner",
            html_url="https://github.com/owner/test-repo",
            stargazers_count=10,
            forks_count=5
        )
        mock_client.get_repository_info.return_value = mock_repo
        
        # Mock stargazers and forkers
        mock_stargazers = [UserInfo(login="star1"), UserInfo(login="star2")]
        mock_forkers = [UserInfo(login="fork1")]
        
        extractor = GitHubExtractor()
        extractor.client = mock_client
        
        # Mock the private methods
        extractor._extract_stargazers = Mock(return_value=mock_stargazers)
        extractor._extract_forkers = Mock(return_value=mock_forkers)
        
        # Test extraction
        result = extractor.extract_repository_info("owner/test-repo")
        
        assert isinstance(result, ExtractionResult)
        assert result.repository == mock_repo
        assert len(result.stargazers) == 2
        assert len(result.forkers) == 1
        assert result.total_stargazers == 10
        assert result.total_forkers == 5
    
    @patch('stargazer.extractor.GitHubClient')
    def test_extract_repository_info_api_error(self, mock_client_class):
        """Test repository extraction with API error."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock API error
        mock_client.get_repository_info.side_effect = GitHubAPIError("Repository not found")
        
        extractor = GitHubExtractor()
        extractor.client = mock_client
        
        with pytest.raises(GitHubAPIError, match="Repository not found"):
            extractor.extract_repository_info("owner/nonexistent-repo")
    
    @patch('stargazer.extractor.GitHubClient')
    def test_extract_repository_info_without_stargazers(self, mock_client_class):
        """Test extraction without stargazers."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_repo = RepoInfo(
            name="test-repo",
            full_name="owner/test-repo",
            owner="owner",
            html_url="https://github.com/owner/test-repo",
            stargazers_count=0,
            forks_count=0
        )
        mock_client.get_repository_info.return_value = mock_repo
        
        extractor = GitHubExtractor()
        extractor.client = mock_client
        
        result = extractor.extract_repository_info(
            "owner/test-repo",
            include_stargazers=False,
            include_forkers=False
        )
        
        assert len(result.stargazers) == 0
        assert len(result.forkers) == 0
    
    @patch('stargazer.extractor.GitHubClient')
    def test_extract_stargazers_with_limit(self, mock_client_class):
        """Test stargazers extraction with limit."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock many stargazers
        mock_stargazers = [UserInfo(login=f"star{i}") for i in range(50)]
        mock_client.get_stargazers.return_value = mock_stargazers
        
        extractor = GitHubExtractor()
        extractor.client = mock_client
        
        result = extractor._extract_stargazers("owner", "repo", max_count=10, detailed_info=False)
        
        assert len(result) == 10
        assert all(user.login.startswith("star") for user in result)
    
    @patch('stargazer.extractor.GitHubClient')
    def test_extract_forkers_detailed_info(self, mock_client_class):
        """Test forkers extraction with detailed info."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock basic forkers
        mock_forkers = [UserInfo(login="fork1"), UserInfo(login="fork2")]
        mock_client.get_forks.return_value = mock_forkers
        
        # Mock detailed user info
        detailed_user1 = UserInfo(login="fork1", name="Fork User 1", location="City 1")
        detailed_user2 = UserInfo(login="fork2", name="Fork User 2", location="City 2")
        mock_client.get_user_info.side_effect = [detailed_user1, detailed_user2]
        
        extractor = GitHubExtractor()
        extractor.client = mock_client
        
        result = extractor._extract_forkers("owner", "repo", max_count=None, detailed_info=True)
        
        assert len(result) == 2
        assert result[0].name == "Fork User 1"
        assert result[1].name == "Fork User 2"
        assert result[0].location == "City 1"
        assert result[1].location == "City 2"
    
    @patch('stargazer.extractor.GitHubClient')
    def test_get_rate_limit_status(self, mock_client_class):
        """Test rate limit status retrieval."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_rate_limit = {
            "rate": {
                "limit": 5000,
                "remaining": 4999,
                "reset": 1635206400
            }
        }
        mock_client.get_rate_limit_status.return_value = mock_rate_limit
        
        extractor = GitHubExtractor()
        extractor.client = mock_client
        
        result = extractor.get_rate_limit_status()
        
        assert result == mock_rate_limit
        mock_client.get_rate_limit_status.assert_called_once() 