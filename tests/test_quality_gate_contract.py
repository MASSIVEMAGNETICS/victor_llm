"""Regression tests for CI and Makefile failure propagation."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_smoke_workflow_fails_closed_on_dependency_install_errors() -> None:
    workflow = (ROOT / ".github" / "workflows" / "smoke-tests.yml").read_text(encoding="utf-8")
    assert "pip install numpy tqdm" in workflow
    assert "|| true" not in workflow


def test_smoke_workflow_runs_all_tests_without_masking_exit_status() -> None:
    workflow = (ROOT / ".github" / "workflows" / "smoke-tests.yml").read_text(encoding="utf-8")
    assert "shell: bash" in workflow
    assert "python -m pytest tests -v --tb=short --timeout=120" in workflow
    assert "python -m unittest test_godmode_toolkit -v" in workflow
    assert "| tail" not in workflow


def test_make_test_target_preserves_unittest_exit_status() -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    unittest_commands = [
        line.strip() for line in makefile.splitlines()
        if "python -m unittest test_godmode_toolkit" in line or "$(PYTHON) -m unittest test_godmode_toolkit" in line
    ]
    assert unittest_commands == ["$(PYTHON) -m unittest test_godmode_toolkit -v"]
    assert "| tail" not in makefile
