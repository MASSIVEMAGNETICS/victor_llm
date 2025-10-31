# Contributing to Victor AGI Framework

Thank you for your interest in contributing to the Victor Prime Synthesis Core AGI! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

We expect all contributors to treat each other with respect and create a welcoming environment for everyone. Please:

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

1. **Fork the Repository**: Create your own fork of the repository
2. **Clone Your Fork**: 
   ```bash
   git clone https://github.com/YOUR_USERNAME/victor_llm.git
   cd victor_llm
   ```
3. **Add Upstream Remote**:
   ```bash
   git remote add upstream https://github.com/MASSIVEMAGNETICS/victor_llm.git
   ```

## Development Setup

1. **Install Python 3.8+**: Ensure you have Python 3.8 or newer installed
2. **Create Virtual Environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Install Development Dependencies**:
   ```bash
   pip install pytest pytest-cov flake8 black isort
   ```

## Making Changes

1. **Create a Branch**: 
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make Your Changes**: 
   - Write clean, readable code
   - Follow the project's coding standards
   - Add comments for complex logic
   - Update documentation as needed

3. **Test Your Changes**:
   ```bash
   # Run existing tests
   python -m pytest test_bando_copilot.py -v
   
   # Test the main Victor Core
   python -m victor_core.main
   ```

4. **Commit Your Changes**:
   ```bash
   git add .
   git commit -m "feat: Add description of your feature"
   # or
   git commit -m "fix: Description of bug fix"
   ```

   Use conventional commit messages:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `test:` for adding or updating tests
   - `refactor:` for code refactoring
   - `perf:` for performance improvements
   - `chore:` for maintenance tasks

## Pull Request Process

1. **Update Your Fork**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push Your Changes**:
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create Pull Request**:
   - Go to the original repository on GitHub
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill out the PR template completely
   - Link any related issues

4. **PR Requirements**:
   - All tests must pass
   - Code must be properly formatted
   - Documentation must be updated
   - PR description must be clear and complete
   - At least one review approval required

5. **Address Review Comments**:
   - Make requested changes
   - Push updates to your branch
   - Respond to reviewer comments
   - Request re-review when ready

## Coding Standards

### Python Style

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Maximum line length: 127 characters
- Use 4 spaces for indentation (no tabs)

### Code Quality

- Write self-documenting code when possible
- Add docstrings for all public functions and classes
- Keep functions focused and single-purpose
- Avoid deep nesting (max 3-4 levels)

### Example Docstring Format

```python
def process_cognitive_input(input_data: dict, priority: int = 0) -> dict:
    """
    Process cognitive input through the Victor brain sectors.
    
    Args:
        input_data (dict): Raw input data containing text or commands
        priority (int, optional): Processing priority level. Defaults to 0.
    
    Returns:
        dict: Processed output with cognitive analysis results
    
    Raises:
        ValueError: If input_data is missing required fields
        ProcessingError: If cognitive processing fails
    """
    # Implementation here
    pass
```

### Formatting Tools

Run these before committing:

```bash
# Format code with black
black .

# Sort imports with isort
isort .

# Check linting with flake8
flake8 .
```

## Testing

### Writing Tests

- Add tests for all new features
- Update tests when modifying existing features
- Aim for high test coverage
- Use descriptive test names

### Test Structure

```python
import unittest

class TestYourFeature(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.test_data = {...}
    
    def test_specific_functionality(self):
        """Test description of what is being tested"""
        result = your_function(self.test_data)
        self.assertEqual(result, expected_value)
    
    def tearDown(self):
        """Clean up after tests"""
        pass
```

### Running Tests

```bash
# Run all tests
python -m pytest test_bando_copilot.py -v

# Run with coverage
python -m pytest test_bando_copilot.py -v --cov=. --cov-report=term

# Run specific test
python -m pytest test_bando_copilot.py::TestClassName::test_method_name -v
```

## Documentation

### Update Documentation When:

- Adding new features or modules
- Changing existing functionality
- Adding new dependencies
- Modifying installation or setup process

### Documentation Files to Update:

- `README.md` - Main project documentation
- Code docstrings - Inline documentation
- `docs/` - Additional documentation files
- `CONTRIBUTING.md` - This file, if changing contribution process

### Documentation Style

- Use clear, concise language
- Include code examples where helpful
- Keep formatting consistent
- Update table of contents if needed

## Questions?

If you have questions about contributing:

1. Check existing issues and discussions
2. Review the documentation
3. Open a new issue with your question
4. Tag it as "question"

## License

By contributing to Victor AGI Framework, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to Victor AGI Framework! Your contributions help make this project better for everyone.
