"""
Setup configuration for Stargazer package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="stargazer",
    version="0.1.0",
    author="Stargazer Team",
    author_email="your-email@example.com",
    description="A minimal Python library for extracting GitHub repository stargazers and forkers information",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/stargazer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Version Control :: Git",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "stargazer=stargazer.cli:main",
        ],
    },
    keywords="github, api, stargazers, forks, repository, analysis",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/stargazer/issues",
        "Source": "https://github.com/yourusername/stargazer",
        "Documentation": "https://github.com/yourusername/stargazer#readme",
    },
) 