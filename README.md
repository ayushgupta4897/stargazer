# Stargazer 🌟

A minimal, modular Python library for extracting information about GitHub repository stargazers and forkers.

## Features

- **Modular Design**: Clean separation of concerns with dedicated modules for different functionalities
- **Comprehensive Data Extraction**: Get detailed information about repository stars, forks, and user metadata
- **Enhanced Email Extraction**: Advanced email discovery from commits, events, and repositories
- **Rate Limit Handling**: Built-in rate limiting and retry mechanisms
- **Flexible Configuration**: Support for GitHub personal access tokens
- **Error Handling**: Robust error handling with custom exceptions
- **Export Support**: Export data to JSON format
- **Comprehensive Testing**: Full test coverage with pytest

## Installation

### From Source

```bash
git clone https://github.com/yourusername/stargazer.git
cd stargazer
pip install -r requirements.txt
```

### For Development

```bash
git clone https://github.com/yourusername/stargazer.git
cd stargazer
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Quick Start

```python
from stargazer import GitHubExtractor

# Initialize the extractor
extractor = GitHubExtractor()

# Extract repository information
result = extractor.extract_repository_info(
    "octocat/Hello-World",
    max_stargazers=10,
    max_forkers=5,
    detailed_user_info=True
)

# Access the data
print(f"Repository: {result.repository.full_name}")
print(f"Stars: {result.repository.stargazers_count}")
print(f"Forks: {result.repository.forks_count}")

# Iterate through stargazers
for user in result.stargazers:
    print(f"Stargazer: {user.login}")
    if user.name:
        print(f"  Name: {user.name}")
    if user.location:
        print(f"  Location: {user.location}")
    if user.company:
        print(f"  Company: {user.company}")
```

## Usage Examples

### Basic Usage

```python
from stargazer import GitHubExtractor

extractor = GitHubExtractor()
result = extractor.extract_repository_info("owner/repo")
```

### With GitHub Token (Recommended)

```python
from stargazer import GitHubExtractor

# Option 1: Pass token directly
extractor = GitHubExtractor(github_token="your_token_here")

# Option 2: Set environment variable GITHUB_TOKEN
extractor = GitHubExtractor()
```

### Advanced Configuration

```python
from stargazer import GitHubExtractor

extractor = GitHubExtractor()

result = extractor.extract_repository_info(
    repo_url="https://github.com/owner/repo",
    include_stargazers=True,
    include_forkers=True,
    max_stargazers=100,
    max_forkers=50,
    detailed_user_info=True,  # Get full user profiles
    aggressive_email_extraction=True  # Extract emails from commits/events
)
```

### Enhanced Email Extraction

Stargazer uses multiple strategies to extract email addresses:

```python
# Enable aggressive email extraction (default: True)
result = extractor.extract_repository_info(
    "owner/repo",
    detailed_user_info=True,
    aggressive_email_extraction=True
)

# Check extraction success
emails_found = sum(1 for user in result.stargazers if user.email)
print(f"Found emails for {emails_found}/{len(result.stargazers)} users")

# Access email data
for user in result.stargazers:
    if user.email:
        print(f"{user.login}: {user.email}")
```

**Email Extraction Methods:**
1. **Public Profile**: Checks if email is public in user's GitHub profile
2. **Commit History**: Analyzes recent commits for email addresses
3. **Public Events**: Scans public activity events for email information
4. **Repository Commits**: Examines commits in user's own repositories

### Export Data

```python
import json

# Export to JSON
data = {
    "repository": result.repository.dict(),
    "stargazers": [user.dict() for user in result.stargazers],
    "forkers": [user.dict() for user in result.forkers],
    "extracted_at": result.extracted_at.isoformat()
}

with open("github_data.json", "w") as f:
    json.dump(data, f, indent=2, default=str)
```

## API Reference

### GitHubExtractor

Main class for extracting GitHub repository information.

#### Methods

- `extract_repository_info(repo_url, **options)`: Extract comprehensive repository information
- `get_rate_limit_status()`: Get current GitHub API rate limit status

#### Options

- `include_stargazers` (bool): Include stargazers data (default: True)
- `include_forkers` (bool): Include forkers data (default: True)
- `max_stargazers` (int): Maximum number of stargazers to fetch (default: None)
- `max_forkers` (int): Maximum number of forkers to fetch (default: None)
- `detailed_user_info` (bool): Fetch detailed user profiles (default: False)
- `aggressive_email_extraction` (bool): Use multiple methods to extract emails (default: True)

### Data Models

#### UserInfo

User information model with the following fields:
- `login`: GitHub username
- `name`: Full name (optional)
- `email`: Email address (optional)
- `location`: Location (optional)
- `company`: Company (optional)
- `bio`: Bio (optional)
- `blog`: Blog URL (optional)
- `twitter_username`: Twitter handle (optional)
- `public_repos`: Number of public repositories
- `followers`: Number of followers
- `following`: Number of following
- `created_at`: Account creation date
- `updated_at`: Last update date
- `avatar_url`: Avatar URL
- `html_url`: Profile URL

#### RepoInfo

Repository information model with the following fields:
- `name`: Repository name
- `full_name`: Full repository name (owner/repo)
- `owner`: Repository owner
- `description`: Repository description
- `html_url`: Repository URL
- `stargazers_count`: Number of stars
- `forks_count`: Number of forks
- `language`: Primary language
- `created_at`: Repository creation date
- `updated_at`: Last update date

#### ExtractionResult

Result model containing:
- `repository`: Repository information
- `stargazers`: List of stargazer information
- `forkers`: List of forker information
- `total_stargazers`: Total number of stargazers
- `total_forkers`: Total number of forkers
- `extracted_at`: Extraction timestamp

## Configuration

### GitHub Token

For higher rate limits, use a GitHub personal access token:

1. Create a token at https://github.com/settings/tokens
2. Set the `GITHUB_TOKEN` environment variable, or
3. Pass the token directly to `GitHubExtractor(github_token="your_token")`

### Rate Limits

- **Without token**: 60 requests per hour
- **With token**: 5,000 requests per hour

## Error Handling

The library provides custom exceptions:

- `GitHubAPIError`: General GitHub API errors
- `RateLimitError`: Rate limit exceeded errors

```python
from stargazer import GitHubExtractor
from stargazer.github_client import GitHubAPIError, RateLimitError

try:
    extractor = GitHubExtractor()
    result = extractor.extract_repository_info("owner/repo")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
except GitHubAPIError as e:
    print(f"GitHub API error: {e}")
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=stargazer

# Run specific test file
pytest tests/test_models.py
```

## Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/stargazer.git
cd stargazer

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest

# Format code
black stargazer/ tests/
```

### Project Structure

```
stargazer/
├── stargazer/
│   ├── __init__.py
│   ├── models.py          # Data models
│   ├── github_client.py   # GitHub API client
│   ├── extractor.py       # Main extraction service
│   └── config.py          # Configuration
├── tests/
│   ├── test_models.py
│   ├── test_github_client.py
│   ├── test_extractor.py
│   └── __init__.py
├── example.py             # Usage examples
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

## Examples

See `example.py` for comprehensive usage examples:

```bash
# Run main example
python example.py

# Run basic usage demo
python example.py basic

# Check GitHub token configuration
python example.py token
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Create a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Built using the GitHub REST API
- Powered by Python, Pydantic, and Requests 