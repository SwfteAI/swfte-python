# Contributing to Swfte Python SDK

Thank you for your interest in contributing to the Swfte Python SDK! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

## Contributor License Agreement

Before your first pull request can be merged, you must sign the [Swfte CLA](https://cla.swfte.com). This ensures that Swfte, Inc. retains the ability to license the project under the current or future terms.

By submitting a contribution, you certify that:

- You have the right to submit it under the MIT License
- You agree to the terms of the Swfte CLA
- Your contribution does not contain third-party code incompatible with the MIT License

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to keep our community approachable and respectable.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment
4. Create a branch for your changes

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip or poetry

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/swfte-python.git
cd swfte-python

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies including dev tools
pip install -e ".[dev]"
```

### Environment Variables

For running integration tests, you'll need:

```bash
export SWFTE_API_KEY="your-api-key"
export SWFTE_BASE_URL="https://api.swfte.com"
```

## Making Changes

1. Create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following our code style guidelines

3. Add or update tests as needed

4. Update documentation if you're changing public APIs

5. Commit your changes with clear, descriptive messages

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=swfte --cov-report=html

# Run specific test file
pytest tests/unit/test_agents.py

# Run with verbose output
pytest -v
```

### Test Structure

- `tests/unit/` - Unit tests with mocked HTTP responses
- `tests/integration/` - Integration tests against real API (requires API key)

### Writing Tests

- Each new feature should have corresponding tests
- Use `pytest-httpx` for mocking HTTP requests
- Aim for at least 80% code coverage

## Code Style

We use the following tools to maintain code quality:

### Formatting

```bash
# Format code with Black
black swfte/

# Sort imports with isort
isort swfte/
```

### Linting

```bash
# Run Ruff linter
ruff check swfte/

# Run type checker
mypy swfte/
```

### Pre-commit Hooks

We recommend setting up pre-commit:

```bash
pip install pre-commit
pre-commit install
```

### Style Guidelines

- Follow [PEP 8](https://pep8.org/) conventions
- Use type hints for all function signatures
- Write docstrings for public methods (Google style)
- Keep lines under 100 characters
- Use descriptive variable names

## Pull Request Process

1. **Update your branch**: Ensure your branch is up to date with `main`
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Run all checks locally**:
   ```bash
   black swfte/ tests/
   ruff check swfte/
   mypy swfte/
   pytest
   ```

3. **Push and create PR**: Push your branch and create a pull request

4. **PR Requirements**:
   - Clear description of changes
   - Link to related issues
   - All tests passing
   - Code review approval
   - No merge conflicts

5. **After merge**: Delete your branch

## Commit Message Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add support for streaming responses
fix: handle rate limit errors correctly
docs: update README with new examples
test: add unit tests for agents module
chore: update dependencies
refactor: simplify HTTP client logic
```

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

- Python version
- SDK version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages and stack traces

### Feature Requests

For feature requests, please describe:

- The problem you're trying to solve
- Your proposed solution
- Any alternatives you've considered

## Questions?

- Open a [GitHub Discussion](https://github.com/swfte/swfte-python/discussions)
- Join our [Discord community](https://discord.gg/swfte)
- Email us at sdk@swfte.com

Thank you for contributing!
