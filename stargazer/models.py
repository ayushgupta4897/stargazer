"""
Data models for GitHub user and repository information.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class UserInfo(BaseModel):
    """Model for GitHub user information."""
    
    login: str = Field(..., description="GitHub username")
    name: Optional[str] = Field(None, description="Full name")
    email: Optional[str] = Field(None, description="Email address")
    location: Optional[str] = Field(None, description="Location")
    company: Optional[str] = Field(None, description="Company")
    bio: Optional[str] = Field(None, description="Bio")
    blog: Optional[str] = Field(None, description="Blog URL")
    twitter_username: Optional[str] = Field(None, description="Twitter username")
    public_repos: int = Field(0, description="Number of public repositories")
    followers: int = Field(0, description="Number of followers")
    following: int = Field(0, description="Number of following")
    created_at: Optional[datetime] = Field(None, description="Account creation date")
    updated_at: Optional[datetime] = Field(None, description="Last update date")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    html_url: Optional[str] = Field(None, description="Profile URL")
    
    @validator('created_at', 'updated_at', pre=True)
    def parse_datetime(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v


class RepoInfo(BaseModel):
    """Model for GitHub repository information."""
    
    name: str = Field(..., description="Repository name")
    full_name: str = Field(..., description="Full repository name (owner/repo)")
    owner: str = Field(..., description="Repository owner")
    description: Optional[str] = Field(None, description="Repository description")
    html_url: str = Field(..., description="Repository URL")
    stargazers_count: int = Field(0, description="Number of stars")
    forks_count: int = Field(0, description="Number of forks")
    language: Optional[str] = Field(None, description="Primary language")
    created_at: Optional[datetime] = Field(None, description="Repository creation date")
    updated_at: Optional[datetime] = Field(None, description="Last update date")
    
    @validator('created_at', 'updated_at', pre=True)
    def parse_datetime(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v


class ExtractionResult(BaseModel):
    """Model for extraction results."""
    
    repository: RepoInfo
    stargazers: list[UserInfo] = Field(default_factory=list)
    forkers: list[UserInfo] = Field(default_factory=list)
    total_stargazers: int = Field(0, description="Total number of stargazers")
    total_forkers: int = Field(0, description="Total number of forkers")
    extracted_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 