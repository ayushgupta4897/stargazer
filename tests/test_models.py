"""
Tests for data models.
"""

import pytest
from datetime import datetime
from stargazer.models import UserInfo, RepoInfo, ExtractionResult


class TestUserInfo:
    """Test UserInfo model."""
    
    def test_user_info_creation(self):
        """Test UserInfo creation with minimal data."""
        user = UserInfo(login="testuser")
        assert user.login == "testuser"
        assert user.name is None
        assert user.email is None
        assert user.public_repos == 0
        assert user.followers == 0
        assert user.following == 0
    
    def test_user_info_with_all_fields(self):
        """Test UserInfo creation with all fields."""
        user = UserInfo(
            login="testuser",
            name="Test User",
            email="test@example.com",
            location="Test City",
            company="Test Company",
            bio="Test bio",
            blog="https://testblog.com",
            twitter_username="testuser",
            public_repos=10,
            followers=100,
            following=50,
            created_at="2020-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            avatar_url="https://github.com/testuser.png",
            html_url="https://github.com/testuser"
        )
        
        assert user.login == "testuser"
        assert user.name == "Test User"
        assert user.email == "test@example.com"
        assert user.location == "Test City"
        assert user.company == "Test Company"
        assert user.bio == "Test bio"
        assert user.blog == "https://testblog.com"
        assert user.twitter_username == "testuser"
        assert user.public_repos == 10
        assert user.followers == 100
        assert user.following == 50
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
        assert user.avatar_url == "https://github.com/testuser.png"
        assert user.html_url == "https://github.com/testuser"
    
    def test_datetime_parsing(self):
        """Test datetime parsing from ISO string."""
        user = UserInfo(
            login="testuser",
            created_at="2020-01-01T00:00:00Z"
        )
        
        assert isinstance(user.created_at, datetime)
        assert user.created_at.year == 2020
        assert user.created_at.month == 1
        assert user.created_at.day == 1


class TestRepoInfo:
    """Test RepoInfo model."""
    
    def test_repo_info_creation(self):
        """Test RepoInfo creation with minimal data."""
        repo = RepoInfo(
            name="test-repo",
            full_name="testuser/test-repo",
            owner="testuser",
            html_url="https://github.com/testuser/test-repo"
        )
        
        assert repo.name == "test-repo"
        assert repo.full_name == "testuser/test-repo"
        assert repo.owner == "testuser"
        assert repo.html_url == "https://github.com/testuser/test-repo"
        assert repo.stargazers_count == 0
        assert repo.forks_count == 0
    
    def test_repo_info_with_all_fields(self):
        """Test RepoInfo creation with all fields."""
        repo = RepoInfo(
            name="test-repo",
            full_name="testuser/test-repo",
            owner="testuser",
            description="A test repository",
            html_url="https://github.com/testuser/test-repo",
            stargazers_count=100,
            forks_count=20,
            language="Python",
            created_at="2020-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z"
        )
        
        assert repo.name == "test-repo"
        assert repo.full_name == "testuser/test-repo"
        assert repo.owner == "testuser"
        assert repo.description == "A test repository"
        assert repo.html_url == "https://github.com/testuser/test-repo"
        assert repo.stargazers_count == 100
        assert repo.forks_count == 20
        assert repo.language == "Python"
        assert isinstance(repo.created_at, datetime)
        assert isinstance(repo.updated_at, datetime)


class TestExtractionResult:
    """Test ExtractionResult model."""
    
    def test_extraction_result_creation(self):
        """Test ExtractionResult creation."""
        repo = RepoInfo(
            name="test-repo",
            full_name="testuser/test-repo",
            owner="testuser",
            html_url="https://github.com/testuser/test-repo"
        )
        
        result = ExtractionResult(repository=repo)
        
        assert result.repository == repo
        assert result.stargazers == []
        assert result.forkers == []
        assert result.total_stargazers == 0
        assert result.total_forkers == 0
        assert isinstance(result.extracted_at, datetime)
    
    def test_extraction_result_with_users(self):
        """Test ExtractionResult with users."""
        repo = RepoInfo(
            name="test-repo",
            full_name="testuser/test-repo",
            owner="testuser",
            html_url="https://github.com/testuser/test-repo"
        )
        
        stargazer = UserInfo(login="stargazer1")
        forker = UserInfo(login="forker1")
        
        result = ExtractionResult(
            repository=repo,
            stargazers=[stargazer],
            forkers=[forker],
            total_stargazers=100,
            total_forkers=20
        )
        
        assert len(result.stargazers) == 1
        assert len(result.forkers) == 1
        assert result.total_stargazers == 100
        assert result.total_forkers == 20
        assert result.stargazers[0].login == "stargazer1"
        assert result.forkers[0].login == "forker1" 