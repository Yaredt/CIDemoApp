# Contributing to Multi-Agent Lead Generation System

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in Issues
2. Create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (Python version, OS, etc.)
   - Relevant logs or screenshots

### Suggesting Enhancements

1. Check existing issues for similar suggestions
2. Create an issue describing:
   - Use case and problem being solved
   - Proposed solution
   - Alternative approaches considered
   - Impact on existing functionality

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Run code formatters (`black`, `isort`)
7. Update documentation
8. Commit with clear messages
9. Push to your fork
10. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/CIDemoApp.git
cd CIDemoApp

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements.txt
pip install -e .[dev,test]

# Install pre-commit hooks
pre-commit install
```

## Code Style

### Python Style Guide

- Follow PEP 8
- Use Black for formatting (line length: 100)
- Use isort for import sorting
- Use type hints
- Write docstrings for all public functions/classes

### Example

```python
from typing import List, Optional

def process_leads(
    leads: List[Lead],
    min_score: float = 50.0,
    validate: bool = True
) -> List[Lead]:
    """
    Process and filter leads based on score.

    Args:
        leads: List of leads to process
        min_score: Minimum score threshold
        validate: Whether to validate leads

    Returns:
        Filtered list of leads

    Raises:
        ValueError: If min_score is invalid
    """
    if not 0 <= min_score <= 100:
        raise ValueError("Score must be between 0 and 100")

    return [lead for lead in leads if lead.score.overall_score >= min_score]
```

## Testing

### Writing Tests

- Use pytest
- Aim for >80% code coverage
- Include unit tests for new functions
- Add integration tests for new agents
- Mock external API calls

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=agents --cov=tools --cov=orchestration

# Specific test file
pytest tests/test_agents.py

# Specific test
pytest tests/test_agents.py::TestBankingAgent::test_execute
```

## Documentation

- Update README.md for user-facing changes
- Update docstrings for code changes
- Add examples for new features
- Update ARCHITECTURE.md for design changes

## Commit Messages

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style/formatting
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

Examples:
```
feat(banking-agent): add support for credit unions

fix(enrichment): handle missing company website

docs(readme): update installation instructions
```

## Areas for Contribution

### High Priority
- Additional industry agents
- More data source integrations
- Enhanced scoring algorithms
- Performance optimizations

### Medium Priority
- UI/Dashboard
- CRM integrations
- Email automation
- Advanced reporting

### Good First Issues
- Documentation improvements
- Test coverage expansion
- Code cleanup
- Example scripts

## Questions?

- Open a GitHub Issue
- Tag with `question` label
- We'll respond within 48 hours

Thank you for contributing! 🙏
