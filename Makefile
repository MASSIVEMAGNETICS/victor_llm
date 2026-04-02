.PHONY: install install-dev test smoke lint format benchmark demo clean help

PYTHON ?= python3
PIP    ?= pip

help:
	@echo "Victor LLM – Makefile targets"
	@echo ""
	@echo "  install      Install runtime dependencies"
	@echo "  install-dev  Install dev/test dependencies"
	@echo "  test         Run all tests (smoke + toolkit)"
	@echo "  smoke        Run only smoke tests (fast)"
	@echo "  lint         Lint with ruff"
	@echo "  format       Auto-format with ruff"
	@echo "  benchmark    Run inference benchmark (5 prompts)"
	@echo "  demo         Run the end-to-end demo"
	@echo "  clean        Remove generated artifacts"

install:
	$(PIP) install -r requirements.txt

install-dev: install
	$(PIP) install pytest pytest-cov pytest-timeout ruff pyyaml

test: smoke
	$(PYTHON) -m unittest test_godmode_toolkit -v 2>&1 | tail -5

smoke:
	$(PYTHON) -m pytest tests/test_smoke.py -v --tb=short

lint:
	$(PYTHON) -m ruff check victor_cli/ tests/ demos/ benchmarks/

format:
	$(PYTHON) -m ruff check --fix victor_cli/ tests/ demos/ benchmarks/

benchmark:
	$(PYTHON) benchmarks/harness.py --prompts 5 --max-tokens 16

demo:
	$(PYTHON) demos/demo_e2e.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache/ dist/ build/ *.egg-info/ runs/ victor_tokenizers/
