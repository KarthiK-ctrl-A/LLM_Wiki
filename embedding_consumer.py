"""Compatibility entry point for the embedding demonstration."""

from llm_wiki.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["smoke", "embeddings"]))
