#!/usr/bin/env python3
"""Victor LLM – top-level CLI entry point."""

import sys
from pathlib import Path

# Ensure repo root is importable when run directly.
_REPO_ROOT = Path(__file__).parent.resolve()
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from victor_cli.main import main

if __name__ == "__main__":
    sys.exit(main())
