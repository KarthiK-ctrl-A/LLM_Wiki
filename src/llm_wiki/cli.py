"""Composition root: parse options, construct adapters, and report exit status."""

import argparse
import json
import logging
from dataclasses import replace
from pathlib import Path

from llm_wiki.config import Settings
from llm_wiki.corpus import audit_corpus, parse_manifest


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(prog="llm-wiki", description="Insurance wiki foundations")
    cli.add_argument("--env-file", type=Path, default=Path(".env"))
    commands = cli.add_subparsers(dest="command", required=True)
    for name in ("audit-corpus", "download", "normalize"):
        command = commands.add_parser(name)
        command.add_argument("--manifest", type=Path)
        command.add_argument("--output", type=Path)
        if name == "normalize":
            command.add_argument("--review", type=Path, default=Path("config/corpus-review.json"))
        if name == "download":
            command.add_argument(
                "--source-id", type=int, action="append", help="Download only these IDs"
            )
            command.add_argument(
                "--refresh", action="store_true", help="Fetch immutable new versions"
            )
    smoke = commands.add_parser("smoke", help="Explicit live provider check")
    smoke.add_argument("provider", choices=["embeddings", "llm", "oracle", "graph"])
    smoke.add_argument("--report", type=Path, help="Save a credential-free verification report")
    return cli


def execute(args: argparse.Namespace) -> int:
    settings = Settings.load(args.env_file)
    if args.command == "normalize":
        from llm_wiki.normalization import normalize_corpus

        manifest = args.manifest or settings.corpus_manifest
        sources = parse_manifest(manifest.read_text(encoding="utf-8"))
        report = normalize_corpus(
            sources,
            settings.corpus_dir,
            args.output or Path("data/normalized/property_casualty_insurance"),
            args.review,
        )
        print(json.dumps({k: report[k] for k in ("counts", "accepted_count", "ready")}))
        return 0 if report["ready"] else 1
    if args.command in {"download", "audit-corpus"}:
        settings = replace(
            settings,
            corpus_manifest=args.manifest.resolve() if args.manifest else settings.corpus_manifest,
            corpus_dir=args.output.resolve() if args.output else settings.corpus_dir,
        )
        sources = parse_manifest(settings.corpus_manifest.read_text(encoding="utf-8"))
        if args.command == "audit-corpus":
            report = audit_corpus(sources, settings.corpus_dir)
            print(json.dumps(report, indent=2))
            return 1 if report["issues"] else 0
        from llm_wiki.downloader import CorpusDownloader, create_session

        if args.source_id:
            unknown = set(args.source_id) - {source.source_number for source in sources}
            if unknown:
                raise ValueError(f"Unknown source IDs: {sorted(unknown)}")
            sources = [source for source in sources if source.source_number in args.source_id]

        with create_session() as session:
            counts = CorpusDownloader(settings, session).run(sources, refresh=args.refresh)
        print(json.dumps(counts))
        return 1 if counts["failed"] else 0
    from llm_wiki.verification import verify

    report = verify(args.provider, settings)
    rendered = json.dumps(report, indent=2) + "\n"
    if args.report:
        from llm_wiki.normalization import atomic_text

        atomic_text(args.report, rendered)
    print(rendered)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        return execute(args)
    except ImportError as exc:
        logging.error("Missing dependency: %s. Install the relevant pyproject.toml extra.", exc)
        return 2
    except Exception as exc:
        # Process boundary only: library layers propagate errors for their callers.
        logging.error("%s: %s", type(exc).__name__, exc)
        return 2
