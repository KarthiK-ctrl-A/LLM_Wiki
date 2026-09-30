import contextlib
import importlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests

from llm_wiki.cli import main
from llm_wiki.config import Settings
from llm_wiki.corpus import Source, audit_corpus, detect_extension, parse_manifest
from llm_wiki.downloader import CorpusDownloader, corpus_lock
from llm_wiki.embeddings import NomicEmbeddingService
from llm_wiki.llm import OllamaChatService

ROW = "| 1 | Flood policy | FEMA | HTML with PDF download | Coverage | https://example.org/doc |"
SOURCE = Source(
    1, "Flood policy", "FEMA", "HTML with PDF download", "Coverage", "https://example.org/doc"
)


class FakeResponse:
    def __init__(self, body=b"%PDF-1.7 example", content_type="application/pdf", error=None):
        self.body = body
        self.headers = {"Content-Type": content_type}
        self.url = "https://example.org/final"
        self.error = error

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def raise_for_status(self):
        if self.error:
            raise self.error

    def iter_content(self, chunk_size):
        yield self.body[:5]
        yield self.body[5:]


class FakeVectors(list):
    @property
    def shape(self):
        return (len(self), len(self[0]))


class ConfigurationTests(unittest.TestCase):
    def test_environment_overrides_file_and_paths_follow_env_location(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = Path(tmp) / ".env"
            env.write_text(
                "WIKI_CORPUS_DIR=archive\nWIKI_OLLAMA_MODEL=file-model\n", encoding="utf-8"
            )
            settings = Settings.load(env, {"WIKI_OLLAMA_MODEL": "environment-model"})
            self.assertEqual(settings.ollama_model, "environment-model")
            self.assertEqual(settings.corpus_dir, (Path(tmp) / "archive").resolve())

    def test_invalid_limits_rejected(self):
        for key, value in [
            ("WIKI_HTTP_TIMEOUT", "0"),
            ("WIKI_DOWNLOAD_DELAY", "-1"),
            ("WIKI_HTTP_TIMEOUT", "nan"),
            ("WIKI_EMBEDDING_DIMENSION", "0"),
        ]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                Settings.load(environ={key: value})


class CorpusTests(unittest.TestCase):
    def test_manifest_parses_data_and_ignores_header(self):
        text = "| # | Title | Source | Type | Why | URL |\n|---|---|---|---|---|---|\n" + ROW
        self.assertEqual(parse_manifest(text), [SOURCE])

    def test_duplicate_and_malformed_sources_fail(self):
        for text in [ROW + "\n" + ROW, "| 1 | Broken |", ROW.replace("https://", "file://"), ""]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_manifest(text)

    def test_html_landing_page_is_not_pdf(self):
        self.assertEqual(detect_extension(b"\n<!DOCTYPE html><html>PDF download</html>"), ".html")
        self.assertEqual(detect_extension(b"%PDF-1.7", "text/html"), ".pdf")
        with self.assertRaises(ValueError):
            detect_extension(b"", "application/pdf")

    def test_audit_identifies_missing_and_mislabeled_without_mutating(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / SOURCE.folder / (SOURCE.filename_stem + ".pdf")
            path.parent.mkdir()
            content = b"<!DOCTYPE html><html>landing page</html>"
            path.write_bytes(content)
            other = Source(2, "Other", "NAIC", "PDF", "Description", "https://example.org/other")
            report = audit_corpus([SOURCE, other], root)
            self.assertEqual(report["present"], 1)
            self.assertEqual(
                [i["issue"] for i in report["issues"]], ["extension_mismatch", "missing"]
            )
            self.assertEqual(path.read_bytes(), content)


class DownloaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.settings = Settings(self.root / "manifest.md", self.root, download_delay=0)
        self.session = Mock()
        self.session.get.return_value = FakeResponse()
        self.downloader = CorpusDownloader(self.settings, self.session)

    def events(self):
        path = self.root / "_metadata/download_events.jsonl"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def test_download_and_rerun_preserve_original_and_journal(self):
        metadata = self.root / "_metadata"
        metadata.mkdir()
        legacy = metadata / "metadata.jsonl"
        legacy.write_text("original\n", encoding="utf-8")
        self.assertEqual(self.downloader.run([SOURCE])["downloaded"], 1)
        event = self.events()[0]
        self.assertEqual(event["final_url"], "https://example.org/final")
        self.assertEqual(len(event["sha256"]), 64)
        self.assertFalse(Path(event["local_path"]).is_absolute())
        self.assertEqual(self.downloader.run([SOURCE])["skipped"], 1)
        self.session.get.assert_called_once()
        self.assertEqual(len(self.events()), 2)
        self.assertEqual(legacy.read_text(), "original\n")
        self.assertFalse(list(self.root.rglob("*.part")))

    def test_refresh_keeps_both_versions(self):
        self.downloader.run([SOURCE])
        first = self.root / self.events()[0]["local_path"]
        self.session.get.return_value = FakeResponse(b"%PDF-1.7 updated")
        self.downloader.run([SOURCE], refresh=True)
        second = self.root / self.events()[1]["local_path"]
        self.assertNotEqual(first, second)
        self.assertEqual(first.read_bytes(), b"%PDF-1.7 example")
        self.assertEqual(second.read_bytes(), b"%PDF-1.7 updated")

    def test_identical_refresh_reuses_content_address(self):
        self.downloader.run([SOURCE])
        self.downloader.run([SOURCE], refresh=True)
        self.assertEqual(self.events()[0]["local_path"], self.events()[1]["local_path"])
        self.assertEqual(len(list(self.root.rglob("*.pdf"))), 1)

    def test_mislabeled_legacy_file_is_preserved_and_new_html_is_correct(self):
        path = self.root / SOURCE.folder / (SOURCE.filename_stem + ".pdf")
        path.parent.mkdir()
        body = b"<html>Download PDF</html>"
        path.write_bytes(body)
        self.session.get.return_value = FakeResponse(body, "text/html")
        self.downloader.run([SOURCE])
        self.assertEqual(path.read_bytes(), body)
        self.assertTrue(self.events()[0]["local_path"].endswith(".html"))

    def test_http_failure_is_journaled_and_does_not_stop_other_sources(self):
        other = Source(2, "Other", "NAIC", "PDF", "Description", "https://example.org/other")
        self.session.get.side_effect = [
            FakeResponse(error=requests.HTTPError("403")),
            FakeResponse(),
        ]
        result = self.downloader.run([SOURCE, other])
        self.assertEqual(result, {"failed": 1, "downloaded": 1, "skipped": 0})
        self.assertEqual([e["status"] for e in self.events()], ["failed", "downloaded"])

    def test_oversized_download_is_not_published(self):
        settings = Settings(
            self.root / "manifest.md", self.root, max_download_bytes=6, download_delay=0
        )
        result = CorpusDownloader(settings, self.session).run([SOURCE])
        self.assertEqual(result["failed"], 1)
        self.assertFalse(list(self.root.rglob("*.part")))
        self.assertFalse(list(self.root.rglob("*.pdf")))

    def test_interrupted_stream_cleans_up_and_records_failure(self):
        response = FakeResponse()

        def chunks(chunk_size):
            yield b"%PDF-"
            raise requests.ConnectionError("interrupted")

        response.iter_content = chunks
        self.session.get.return_value = response
        self.assertEqual(self.downloader.run([SOURCE])["failed"], 1)
        self.assertFalse(list(self.root.rglob("*.part")))
        self.assertFalse(list(self.root.rglob("*.pdf")))

    def test_concurrent_writer_rejected_and_lock_released_on_failure(self):
        with self.assertRaisesRegex(ValueError, "example"):
            with corpus_lock(self.root):
                with self.assertRaises(RuntimeError):
                    self.downloader.run([SOURCE])
                raise ValueError("example")
        self.assertFalse((self.root / ".download.lock").exists())


class ProviderTests(unittest.TestCase):
    def test_embedding_prefixes_and_normalization_request(self):
        encoder = Mock()
        encoder.encode.return_value = FakeVectors([[1.0, 0.0]])
        service = NomicEmbeddingService(dimension=2, encoder=encoder)
        service.embed_documents(["Coverage"])
        self.assertEqual(encoder.encode.call_args.args[0], ["search_document: Coverage"])
        self.assertTrue(encoder.encode.call_args.kwargs["normalize_embeddings"])
        self.assertEqual(service.embed_query("Flood?"), [1.0, 0.0])
        self.assertEqual(encoder.encode.call_args.args[0], ["search_query: Flood?"])

    def test_bad_embeddings_rejected_before_storage(self):
        encoder = Mock()
        service = NomicEmbeddingService(dimension=2, encoder=encoder)
        for output in [[[1.0]], [[float("nan"), 0]], [[0.0, 0.0]], [[2.0, 0.0]]]:
            encoder.encode.return_value = FakeVectors(output)
            with self.subTest(output=output), self.assertRaises(ValueError):
                service.embed_query("Test")

    def test_blank_embedding_input_does_not_load_model(self):
        service = NomicEmbeddingService()
        for texts in [[], [" "], [None]]:
            with self.subTest(texts=texts), self.assertRaises(ValueError):
                service.embed_documents(texts)
        self.assertIsNone(service._model)

    def test_chat_uses_injected_client_and_rejects_empty_output(self):
        client = Mock()
        service = OllamaChatService("test-model", client=client)
        client.invoke.return_value = SimpleNamespace(content="Works")
        self.assertEqual(service.complete("Check"), "Works")
        client.invoke.return_value = SimpleNamespace(content="")
        with self.assertRaises(ValueError):
            service.complete("Check")
        with self.assertRaises(ValueError):
            service.complete(" ")

    def test_chat_errors_propagate(self):
        client = Mock()
        client.invoke.side_effect = TimeoutError("timed out")
        with self.assertRaises(TimeoutError):
            OllamaChatService("test", client=client).complete("Check")

    def test_legacy_imports_have_no_provider_side_effects(self):
        with patch("llm_wiki.cli.main") as cli:
            for name in ["embedding_service", "embedding_consumer", "test_nomic", "test_ollama"]:
                importlib.import_module(name)
            cli.assert_not_called()


class CliTests(unittest.TestCase):
    def test_audit_exit_code_and_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "manifest.md"
            manifest.write_text(ROW, encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = main(
                    [
                        "--env-file",
                        str(root / ".env"),
                        "audit-corpus",
                        "--manifest",
                        str(manifest),
                        "--output",
                        str(root / "absent"),
                    ]
                )
            self.assertEqual(result, 1)
            self.assertEqual(json.loads(output.getvalue())["present"], 0)
            self.assertFalse((root / "absent").exists())

    def test_configuration_failure_has_nonzero_exit(self):
        with patch.dict("os.environ", {"WIKI_HTTP_TIMEOUT": "-1"}):
            self.assertEqual(main(["audit-corpus"]), 2)


if __name__ == "__main__":
    unittest.main()
