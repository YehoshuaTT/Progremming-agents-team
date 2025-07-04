"""
Setup configuration for Autonomous Multi-Agent System
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="autonomous-multi-agent-system",
    version="1.0.0",
    author="Agent Development Team",
    author_email="dev@agents.example.com",
    description="An autonomous multi-agent system with advanced orchestration and learning capabilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/autonomous-agents",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-flask>=1.3.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "black>=22.0.0",
            "isort>=5.0.0",
            "flake8>=6.0.0",
            "mypy>=0.910",
            "bandit>=1.7.0",
            "safety>=2.0.0",
        ],
        "ml": [
            "torch>=1.12.0",
            "torchvision>=0.13.0",
            "transformers>=4.20.0",
        ],
        "gpu": [
            "torch>=1.12.0+cu113",
            "torchvision>=0.13.0+cu113",
        ]
    },
    entry_points={
        "console_scripts": [
            "agent-orchestrator=tools.enhanced_orchestrator:main",
            "agent-security=tools.security_framework:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.md"],
    },
)
