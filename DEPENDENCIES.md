# Dependency Management for Autonomous Multi-Agent System

This document describes the various dependency management files available in this project.

## File Overview

### 1. `requirements.txt` 
- **Format**: pip requirements format
- **Purpose**: Standard Python package dependencies
- **Usage**: `pip install -r requirements.txt`
- **Best for**: Basic Python installations, CI/CD pipelines

### 2. `requirements.yml`
- **Format**: YAML with extended metadata
- **Purpose**: Structured dependency specification with categories
- **Usage**: Custom dependency management scripts
- **Best for**: Documentation and structured dependency organization

### 3. `environment.yml`
- **Format**: Conda environment specification
- **Purpose**: Complete conda environment recreation
- **Usage**: `conda env create -f environment.yml`
- **Best for**: Data science workflows, reproducible environments

### 4. `setup.py`
- **Format**: Python setuptools configuration
- **Purpose**: Package installation and distribution
- **Usage**: `pip install -e .` (development) or `pip install .`
- **Best for**: Installing the project as a package

## Installation Options

### Option 1: Basic pip installation
```bash
pip install -r requirements.txt
```

### Option 2: Conda environment (Recommended for data science)
```bash
conda env create -f environment.yml
conda activate autonomous-agents
```

### Option 3: Development installation
```bash
pip install -e .[dev]
```

### Option 4: Full installation with ML dependencies
```bash
pip install -e .[dev,ml]
```

## Dependency Categories

### Core Dependencies
- `pytest` - Testing framework
- `pytest-asyncio` - Async testing support
- `bandit` - Security scanner
- `requests` - HTTP client
- `pyyaml` - YAML parsing

### Security Dependencies
- `bandit>=1.7.0` - Security vulnerability scanner
- `safety>=2.0.0` - Dependency vulnerability checker

### Machine Learning Dependencies
- `numpy>=1.21.0` - Numerical computing
- `scikit-learn>=1.0.0` - Machine learning library
- `pandas>=1.3.0` - Data manipulation

### Development Dependencies
- `black>=22.0.0` - Code formatter
- `isort>=5.0.0` - Import sorter
- `flake8>=6.0.0` - Code linter
- `mypy>=0.910` - Type checker

### Async Dependencies
- `aiofiles>=23.0.0` - Async file operations
- `aiosqlite>=0.21.0` - Async SQLite

### Knowledge Graph Dependencies
- `networkx>=3.0` - Graph algorithms
- `py2neo>=2021.2.4` - Neo4j Python driver
- `neo4j>=5.0.0` - Neo4j database driver

## Security Compliance

All dependencies are:
- ✅ Scanned with `bandit` for security vulnerabilities
- ✅ Checked with `safety` for known CVEs
- ✅ Pinned to minimum versions for stability
- ✅ Regularly updated for security patches

## Environment Variables

Set these environment variables for optimal performance:

```bash
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"
export FLASK_ENV=development  # for development
export FLASK_APP=app.py       # if using Flask components
```

## Updates and Maintenance

To update dependencies:

1. **Check for vulnerabilities**:
   ```bash
   safety check
   bandit -r .
   ```

2. **Update requirements**:
   ```bash
   pip-compile requirements.in  # if using pip-tools
   ```

3. **Test updated dependencies**:
   ```bash
   pytest tests/
   ```

## Troubleshooting

### Common Issues

1. **ImportError**: Ensure all dependencies are installed
2. **Version conflicts**: Use virtual environments
3. **Security warnings**: Update vulnerable packages immediately

### Environment Recreation

If environment is corrupted:
```bash
# Conda
conda env remove -n autonomous-agents
conda env create -f environment.yml

# Pip + venv
rm -rf venv/
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```
