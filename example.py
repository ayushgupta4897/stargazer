#!/usr/bin/env python3
"""
Example script demonstrating how to use the Stargazer library.
"""

import json
import logging
import sys
from stargazer import GitHubExtractor
from stargazer.github_client import GitHubAPIError, RateLimitError


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """Main example function."""
    setup_logging()
    
    # Initialize the extractor
    # You can pass a GitHub token for higher rate limits
    extractor = GitHubExtractor()
    
    # Example repository URL  
    repo_url = "https://github.com/octocat/Hello-World"
    
    # You can also use owner/repo format
    # repo_url = "octocat/Hello-World"
    
    print(f"🔍 Extracting information from: {repo_url}")
    print("-" * 50)
    
    try:
        # Extract repository information
        # Limit to first 5 stargazers and forkers for demo purposes
        result = extractor.extract_repository_info(
            repo_url,
            include_stargazers=True,
            include_forkers=True,
            max_stargazers=5,
            max_forkers=5,
            detailed_user_info=True,  # Get detailed user information
            aggressive_email_extraction=True  # Enable enhanced email extraction
        )
        
        # Display repository information
        print(f"📊 Repository: {result.repository.full_name}")
        print(f"   Description: {result.repository.description}")
        print(f"   Language: {result.repository.language}")
        print(f"   Stars: {result.repository.stargazers_count}")
        print(f"   Forks: {result.repository.forks_count}")
        print(f"   Created: {result.repository.created_at}")
        print(f"   URL: {result.repository.html_url}")
        print()
        
        # Display stargazers
        print(f"⭐ Stargazers (showing {len(result.stargazers)} of {result.total_stargazers}):")
        for i, user in enumerate(result.stargazers, 1):
            print(f"   {i}. {user.login}")
            if user.name:
                print(f"      Name: {user.name}")
            if user.location:
                print(f"      Location: {user.location}")
            if user.company:
                print(f"      Company: {user.company}")
            if user.email:
                print(f"      Email: {user.email}")
            print(f"      Profile: {user.html_url}")
            print()
        
        # Display forkers
        print(f"🍴 Forkers (showing {len(result.forkers)} of {result.total_forkers}):")
        for i, user in enumerate(result.forkers, 1):
            print(f"   {i}. {user.login}")
            if user.name:
                print(f"      Name: {user.name}")
            if user.location:
                print(f"      Location: {user.location}")
            if user.company:
                print(f"      Company: {user.company}")
            if user.email:
                print(f"      Email: {user.email}")
            print(f"      Profile: {user.html_url}")
            print()
        
        # Show rate limit status
        try:
            rate_limit = extractor.get_rate_limit_status()
            print(f"📊 Rate Limit Status:")
            print(f"   Limit: {rate_limit['rate']['limit']}")
            print(f"   Remaining: {rate_limit['rate']['remaining']}")
            print(f"   Reset: {rate_limit['rate']['reset']}")
            print()
        except Exception as e:
            print(f"   Could not get rate limit status: {e}")
        
        # Export to JSON
        export_data = {
            "repository": result.repository.dict(),
            "stargazers": [user.dict() for user in result.stargazers],
            "forkers": [user.dict() for user in result.forkers],
            "total_stargazers": result.total_stargazers,
            "total_forkers": result.total_forkers,
            "extracted_at": result.extracted_at.isoformat()
        }
        
        with open("stargazer_data.json", "w") as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print("💾 Data exported to stargazer_data.json")
        
    except RateLimitError as e:
        print(f"❌ Rate limit exceeded: {e}")
        print("💡 Consider using a GitHub personal access token for higher rate limits")
        print("   Set the GITHUB_TOKEN environment variable or pass it to GitHubExtractor()")
        sys.exit(1)
        
    except GitHubAPIError as e:
        print(f"❌ GitHub API Error: {e}")
        print("💡 Make sure the repository exists and is public")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


def demo_basic_usage():
    """Demonstrate basic usage without detailed information."""
    print("🚀 Basic Usage Demo")
    print("-" * 20)
    
    extractor = GitHubExtractor()
    
    try:
        # Quick extraction with minimal data
        result = extractor.extract_repository_info(
            "octocat/Hello-World",
            include_stargazers=True,
            include_forkers=False,
            max_stargazers=3,
            detailed_user_info=False  # Just basic info
        )
        
        print(f"Repository: {result.repository.full_name}")
        print(f"Stars: {result.repository.stargazers_count}")
        print(f"Recent stargazers: {', '.join(user.login for user in result.stargazers)}")
        
    except Exception as e:
        print(f"Error: {e}")


def demo_with_token():
    """Demonstrate usage with GitHub token."""
    print("🔑 Demo with GitHub Token")
    print("-" * 25)
    
    # You can pass the token directly
    # extractor = GitHubExtractor(github_token="your_token_here")
    
    # Or set it as an environment variable GITHUB_TOKEN
    extractor = GitHubExtractor()
    
    if extractor.client.config.has_token():
        print("✅ GitHub token is configured")
    else:
        print("⚠️  No GitHub token configured (using anonymous access)")
    
    try:
        rate_limit = extractor.get_rate_limit_status()
        print(f"Rate limit: {rate_limit['rate']['remaining']}/{rate_limit['rate']['limit']}")
    except Exception as e:
        print(f"Could not check rate limit: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "basic":
            demo_basic_usage()
        elif sys.argv[1] == "token":
            demo_with_token()
        else:
            print("Usage: python example.py [basic|token]")
    else:
        main() 