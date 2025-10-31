# Quick Start Guide for Contributors

Welcome to the Victor AGI Framework! This guide will help you get started with contributing to the project in just a few minutes.

## 🚀 Quick Setup (5 minutes)

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/victor_llm.git
cd victor_llm
```

### 2. Set Up Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install dev tools
pip install pytest pytest-cov flake8 black isort
```

### 3. Verify Setup

```bash
# Try running the main Victor AGI
python -m victor_core.main

# Run tests (some may fail without FastAPI, that's OK for now)
python -m pytest test_bando_copilot.py -v
```

## 🔧 Making Changes (10 minutes)

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Your Changes

Edit files, add features, fix bugs...

### 3. Format and Test

```bash
# Format your code
black .
isort .

# Check for issues
flake8 . --select=E9,F63,F7,F82

# Run tests
python -m pytest test_bando_copilot.py -v
```

### 4. Commit

```bash
git add .
git commit -m "feat: Your descriptive message"
```

## 📝 Creating a PR (5 minutes)

### 1. Push Your Branch

```bash
git push origin feature/your-feature-name
```

### 2. Open PR on GitHub

1. Go to https://github.com/MASSIVEMAGNETICS/victor_llm
2. Click "New Pull Request"
3. Select your branch
4. Fill out the template (it auto-loads)
5. Click "Create Pull Request"

### 3. PR Checklist

Make sure your PR has:
- [ ] Clear description of changes
- [ ] Related issue links (if applicable)
- [ ] Tests for new features
- [ ] Updated documentation
- [ ] All checkboxes reviewed

## 🎯 Common Tasks

### Adding a New Feature

```bash
# 1. Create feature branch
git checkout -b feature/quantum-optimizer

# 2. Add your code in the appropriate module
# Example: victor_core/ops/quantum.py

# 3. Add tests
# Example: test_quantum.py

# 4. Update docs
# Edit README.md or add docs/quantum.md

# 5. Format and test
black .
pytest -v

# 6. Commit and push
git commit -m "feat: Add quantum optimization module"
git push origin feature/quantum-optimizer
```

### Fixing a Bug

```bash
# 1. Create fix branch
git checkout -b fix/memory-leak

# 2. Fix the bug
# Edit the relevant file(s)

# 3. Add regression test
# Ensure bug doesn't come back

# 4. Test
pytest -v

# 5. Commit and push
git commit -m "fix: Resolve memory leak in fractal processing"
git push origin fix/memory-leak
```

### Updating Documentation

```bash
# 1. Create docs branch
git checkout -b docs/improve-readme

# 2. Edit documentation
# README.md, CONTRIBUTING.md, or docs/

# 3. Verify links and formatting
# Preview markdown locally

# 4. Commit and push
git commit -m "docs: Improve installation instructions"
git push origin docs/improve-readme
```

## 🤝 Getting Help

- **Questions?** Open an issue with the `question` label
- **Bug report?** Use the bug report template
- **Feature idea?** Use the feature request template
- **Review needed?** Tag a maintainer in your PR

## 📚 More Information

- [CONTRIBUTING.md](CONTRIBUTING.md) - Detailed contribution guidelines
- [PR_PROCESS.md](PR_PROCESS.md) - Complete PR workflow
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) - Community guidelines
- [README.md](README.md) - Project overview and setup

## 💡 Tips

- **Keep PRs small** - Easier to review and merge
- **One feature per PR** - Don't mix unrelated changes
- **Write good commit messages** - Use conventional commits
- **Test locally** - Don't rely on CI to catch issues
- **Be patient** - Reviews may take 2-3 business days
- **Be respectful** - Follow the code of conduct

## 🎉 Thank You!

Every contribution, no matter how small, helps make Victor AGI better. We appreciate your time and effort!

---

**Ready to contribute?** Start with a small fix or improvement, get familiar with the process, then tackle bigger features!
