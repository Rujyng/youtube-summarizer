import io
import builtins
import sys
import types
import unittest
from argparse import Namespace

from backend.cli import run_summarize
from backend.src.transcript import TranscriptSegment


class CliTests(unittest.TestCase):
    def test_run_summarize_prints_summary_and_stats(self):
        output = io.StringIO()
        args = Namespace(
            video="https://youtu.be/video123",
            summary_format="Bullet points",
            refinement_request=None,
            model="test-model",
            max_tokens=300,
        )

        exit_code = run_summarize(
            args,
            fetch_transcript=lambda video: [
                TranscriptSegment(text="hello", start=0.0, duration=1.0),
                TranscriptSegment(text="world", start=1.0, duration=1.0),
            ],
            summarize=lambda transcript, **kwargs: "short summary",
            refine=lambda summary, request, **kwargs: summary,
            output=output,
            progress_output=io.StringIO(),
        )

        printed = output.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("Summary:", printed)
        self.assertIn("short summary", printed)
        self.assertIn("Transcript segments: 2", printed)
        self.assertIn("Length original: 11 characters", printed)

    def test_run_summarize_reports_invalid_video_input(self):
        output = io.StringIO()
        args = Namespace(
            video="[https://www.youtube.com/watch?v=video123]"
            "(https://www.youtube.com/watch?v=video123)",
            summary_format="Bullet points",
            refinement_request=None,
            model="test-model",
            max_tokens=300,
        )

        exit_code = run_summarize(
            args,
            fetch_transcript=lambda video: self.fail("should not fetch transcript"),
            summarize=lambda transcript, **kwargs: "short summary",
            refine=lambda summary, request, **kwargs: summary,
            output=output,
            progress_output=io.StringIO(),
        )

        self.assertEqual(exit_code, 2)
        self.assertIn("Invalid video input:", output.getvalue())

    def test_run_summarize_reports_transcript_fetch_failure(self):
        output = io.StringIO()
        args = Namespace(
            video="https://youtu.be/video123",
            summary_format="Bullet points",
            refinement_request=None,
            model="test-model",
            max_tokens=300,
        )

        exit_code = run_summarize(
            args,
            fetch_transcript=lambda video: (_ for _ in ()).throw(
                RuntimeError("empty transcript response")
            ),
            summarize=lambda transcript, **kwargs: self.fail("should not summarize"),
            refine=lambda summary, request, **kwargs: summary,
            output=output,
            progress_output=io.StringIO(),
        )

        printed = output.getvalue()
        self.assertEqual(exit_code, 1)
        self.assertIn("Failed to fetch transcript for video123.", printed)
        self.assertIn("empty transcript response", printed)

    def test_run_summarize_fetches_transcript_before_importing_summarizer(self):
        args = Namespace(
            video="https://youtu.be/video123",
            summary_format="Bullet points",
            refinement_request=None,
            model="test-model",
            max_tokens=300,
        )
        fetched = False
        original_import = builtins.__import__
        original_summarizer = sys.modules.get("backend.src.summarizer")
        fake_summarizer = types.ModuleType("backend.src.summarizer")
        fake_summarizer.summarize_text = lambda transcript, **kwargs: "short summary"
        fake_summarizer.refine_summary = lambda summary, request, **kwargs: summary

        def fail_if_summarizer_imported_before_fetch(name, *args, **kwargs):
            if name == "backend.src.summarizer" and not fetched:
                raise AssertionError("summarizer imported before transcript fetch")
            if name == "backend.src.summarizer":
                return fake_summarizer
            return original_import(name, *args, **kwargs)

        def fetch(video):
            nonlocal fetched
            fetched = True
            return [TranscriptSegment(text="hello", start=0.0, duration=1.0)]

        try:
            sys.modules.pop("backend.src.summarizer", None)
            builtins.__import__ = fail_if_summarizer_imported_before_fetch
            exit_code = run_summarize(
                args,
                fetch_transcript=fetch,
                output=io.StringIO(),
                progress_output=io.StringIO(),
            )
        finally:
            builtins.__import__ = original_import
            if original_summarizer is not None:
                sys.modules["backend.src.summarizer"] = original_summarizer
            else:
                sys.modules.pop("backend.src.summarizer", None)

        self.assertEqual(exit_code, 0)
        self.assertTrue(fetched)


if __name__ == "__main__":
    unittest.main()
