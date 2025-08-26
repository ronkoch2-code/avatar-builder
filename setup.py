#!/usr/bin/env python3
"""
Setup script for Avatar Intelligence System
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    try:
        with open("README.md", "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return "Avatar Intelligence System - AI-powered conversation analysis and avatar generation"

# Read requirements
def read_requirements():
    try:
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    except FileNotFoundError:
        return [
            "neo4j>=5.0.0",
            "pandas>=1.5.0", 
            "numpy>=1.21.0",
            "python-dateutil>=2.8.0",
            "regex>=2022.0.0"
        ]

setup(
    name="avatar-intelligence-system",
    version="1.0.0",
    author="Ron Koch",
    author_email="your.email@example.com",  # Update with your email
    description="AI-powered conversation analysis and personalized avatar generation system",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/avatar-intelligence-system",  # Update with your repo
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications :: Chat",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=0.5",
        ],
    },
    entry_points={
        "console_scripts": [
            "avatar-deploy=src.avatar_system_deployment:main",
            "avatar-pipeline=src.avatar_intelligence_pipeline:main",
        ],
    },
    package_data={
        "": ["*.md", "*.txt", "*.cypher"],
        "sql": ["*.cypher"],
        "docs": ["*.md"],
        "examples": ["*.py"],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="ai, avatar, conversation-analysis, neo4j, nlp, chatbot, personalization",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/avatar-intelligence-system/issues",
        "Source": "https://github.com/yourusername/avatar-intelligence-system",
        "Documentation": "https://github.com/yourusername/avatar-intelligence-system/blob/main/README.md",
    },
)
