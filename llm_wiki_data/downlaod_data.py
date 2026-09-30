"""Legacy misspelled entry point. Prefer: llm-wiki download."""

import sys
from pathlib import Path

from llm_wiki.cli import main

if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    raise SystemExit(main(["--env-file", str(project_root / ".env"), "download", *sys.argv[1:]]))
