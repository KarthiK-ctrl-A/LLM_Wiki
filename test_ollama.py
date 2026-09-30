"""Manual live check, retained for compatibility; offline tests live in tests/."""

from llm_wiki.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["smoke", "llm"]))
