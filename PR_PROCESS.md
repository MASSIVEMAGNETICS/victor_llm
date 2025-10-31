# Pull Request Publishing Process

This document outlines the complete process for creating, reviewing, and publishing pull requests in the Victor AGI Framework repository.

## Table of Contents

1. [Overview](#overview)
2. [Before Creating a PR](#before-creating-a-pr)
3. [Creating a Pull Request](#creating-a-pull-request)
4. [PR Review Process](#pr-review-process)
5. [Automated Checks](#automated-checks)
6. [Merging and Publishing](#merging-and-publishing)
7. [Release Process](#release-process)

## Overview

Our PR process is designed to maintain high code quality and ensure smooth collaboration. All contributions go through:

- Automated testing and linting
- Security and dependency checks
- Code review by maintainers
- Documentation validation
- Integration testing

## Before Creating a PR

### 1. Set Up Your Environment

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/victor_llm.git
cd victor_llm

# Add upstream remote
git remote add upstream https://github.com/MASSIVEMAGNETICS/victor_llm.git

# Create a feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Follow the coding standards in [CONTRIBUTING.md](CONTRIBUTING.md)
- Write tests for new functionality
- Update documentation as needed
- Keep commits focused and atomic

### 3. Test Locally

```bash
# Install test dependencies
pip install pytest pytest-cov flake8 black isort

# Run tests
python -m pytest test_bando_copilot.py -v

# Run linting
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Format code
black .
isort .
```

### 4. Commit Your Changes

Use conventional commit messages:

```bash
git add .
git commit -m "feat: Add new cognitive processing feature"
# or
git commit -m "fix: Resolve memory leak in fractal processing"
```

**Commit Message Prefixes:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions or updates
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `chore:` - Maintenance tasks
- `ci:` - CI/CD changes

## Creating a Pull Request

### 1. Push Your Branch

```bash
# Update your fork
git fetch upstream
git rebase upstream/main

# Push to your fork
git push origin feature/your-feature-name
```

### 2. Open the PR

1. Go to https://github.com/MASSIVEMAGNETICS/victor_llm
2. Click "New Pull Request"
3. Select your fork and branch
4. Click "Create Pull Request"

### 3. Fill Out the PR Template

The PR template will be automatically loaded. Fill out all sections:

#### Required Sections:

1. **Description**: Explain what changes you made and why
2. **Type of Change**: Check the applicable box(es)
3. **Related Issues**: Link any related issues (e.g., `Fixes #123`)
4. **Changes Made**: List key changes
5. **Testing**: Describe how you tested your changes
6. **Documentation**: Check if docs were updated
7. **Checklist**: Complete all checklist items

#### Example PR Description:

```markdown
## Description

This PR adds a new quantum annealing optimization method to the cognitive 
processing sector, improving decision-making speed by approximately 30%.

## Type of Change

- [x] New feature
- [ ] Bug fix
- [ ] Breaking change

## Related Issues

Relates to #45
Fixes #67

## Changes Made

- Added `QuantumOptimizer` class in `victor_core/ops/quantum.py`
- Integrated quantum optimizer with `CognitiveExecutiveSector`
- Added comprehensive tests for quantum optimization
- Updated documentation with usage examples

## Testing

- [x] Tested locally with Python 3.8, 3.10, and 3.12
- [x] All existing tests pass
- [x] Added 15 new tests for quantum optimization
- [x] Manual testing with various input scenarios

### Test Commands

\```bash
python -m pytest test_bando_copilot.py -v
python -m pytest victor_core/ops/test_quantum.py -v
\```

## Documentation

- [x] Updated README.md with quantum optimization section
- [x] Added docstrings to all new functions
- [x] Added usage examples in docs/quantum_optimization.md

## Checklist

- [x] My code follows the style guidelines
- [x] I have performed a self-review
- [x] I have commented complex logic
- [x] I have updated documentation
- [x] My changes generate no new warnings
- [x] I have added tests
- [x] All tests pass locally
```

## PR Review Process

### Automated Review

Once you create the PR, several automated checks will run:

1. **CI Workflow**: Tests on multiple Python versions
2. **Linting**: Code style and quality checks
3. **Security Checks**: Vulnerability scanning
4. **PR Checklist**: Validates your PR description
5. **Size Labeling**: Adds size label based on changes
6. **Auto-labeling**: Adds relevant labels

### Manual Review

1. **Initial Review**: A maintainer will review within 2-3 business days
2. **Feedback**: Address any comments or requested changes
3. **Re-review**: Request re-review after making changes
4. **Approval**: At least one approval required before merging

### Common Review Feedback

- Code style issues
- Missing tests
- Incomplete documentation
- Security concerns
- Performance issues
- Breaking changes without justification

### Addressing Feedback

```bash
# Make requested changes
git add .
git commit -m "fix: Address review feedback"
git push origin feature/your-feature-name
```

The PR will automatically update and re-run checks.

## Automated Checks

### CI Workflow

Tests your code on Python 3.8, 3.9, 3.10, 3.11, and 3.12:

- Installs dependencies
- Runs all tests with coverage
- Uploads coverage reports

**Status**: Must pass before merging

### Linting

Checks code quality:

- **flake8**: Python syntax and style errors
- **black**: Code formatting (informational)
- **isort**: Import sorting (informational)

**Status**: Syntax errors must be fixed; formatting is recommended

### Security Checks

Scans for vulnerabilities:

- **safety**: Checks dependencies for known vulnerabilities
- **bandit**: Scans code for security issues

**Status**: Critical issues must be addressed

### PR Checklist

Validates your PR:

- Checks description length
- Verifies required sections
- Counts completed checklist items

**Status**: Informational warnings

### Dependency Review

Checks for:

- New vulnerable dependencies
- License conflicts
- Breaking version changes

**Status**: Must address moderate+ severity issues

## Merging and Publishing

### Merge Criteria

Your PR can be merged when:

- [x] All CI checks pass
- [x] At least one approval from a maintainer
- [x] No unresolved conversations
- [x] Up to date with main branch
- [x] No merge conflicts

### Merge Methods

We use **Squash and Merge** by default:

1. All commits are squashed into one
2. Commit message becomes the PR title
3. PR description is included in commit body
4. Cleaner git history

For special cases, maintainers may use:
- **Merge commit**: For feature branches with complex history
- **Rebase and merge**: For clean, linear history

### After Merging

1. Your branch will be automatically deleted (if from the main repo)
2. Related issues will be automatically closed (if using `Fixes #123`)
3. CI will run on the main branch
4. Changes will be included in the next release

## Release Process

### Creating a Release

Releases are automated using tags:

```bash
# Create a version tag
git tag -a v1.2.3 -m "Release version 1.2.3"
git push upstream v1.2.3
```

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **Major** (v2.0.0): Breaking changes
- **Minor** (v1.1.0): New features, backward compatible
- **Patch** (v1.0.1): Bug fixes, backward compatible

### Release Workflow

When you push a version tag:

1. GitHub Actions runs all tests
2. Generates changelog from commits
3. Creates a GitHub Release
4. Includes installation instructions
5. Notifies relevant channels

### Release Notes

The release notes are automatically generated from:

- Commit messages since last release
- PR descriptions for major changes
- Closed issues since last release

## Troubleshooting

### CI Failing

```bash
# Check test failures
# Review the CI log in the GitHub Actions tab

# Run tests locally
python -m pytest test_bando_copilot.py -v
```

### Merge Conflicts

```bash
# Update your branch
git fetch upstream
git rebase upstream/main

# Resolve conflicts
# Edit conflicting files
git add .
git rebase --continue

# Force push (only for your feature branch!)
git push origin feature/your-feature-name --force
```

### Failed Security Checks

Review the security report in the PR checks and:

1. Update vulnerable dependencies
2. Fix code security issues
3. Add comments explaining false positives

## Getting Help

If you need assistance:

1. **Read the Documentation**: Check [CONTRIBUTING.md](CONTRIBUTING.md)
2. **Ask in PR Comments**: Tag maintainers with questions
3. **Open an Issue**: For broader discussions about the process
4. **Check Examples**: Look at recent merged PRs

## Best Practices

### DO:

- ✅ Keep PRs focused on a single feature/fix
- ✅ Write descriptive commit messages
- ✅ Add tests for new functionality
- ✅ Update documentation
- ✅ Respond to review feedback promptly
- ✅ Keep your branch up to date

### DON'T:

- ❌ Mix multiple unrelated changes in one PR
- ❌ Submit PRs with failing tests
- ❌ Skip the PR template
- ❌ Force push to main or other shared branches
- ❌ Ignore review feedback
- ❌ Add unnecessary dependencies

## Summary Checklist

Before submitting a PR, verify:

- [ ] Code follows project style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] PR template completely filled out
- [ ] Commit messages follow conventions
- [ ] No merge conflicts with main
- [ ] Security checks pass
- [ ] Related issues are linked

---

Thank you for contributing to the Victor AGI Framework! Your contributions help advance the state of AGI development.
