import importlib
import json
import unittest
from unittest.mock import patch


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(
            {"choices": [{"message": {"content": "short summary"}}]}
        ).encode("utf-8")


class SummarizerTests(unittest.TestCase):
    def test_summarize_text_calls_openai_chat_completion_endpoint(self):
        summarizer = importlib.import_module("backend.src.summarizer")

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch("backend.src.summarizer.urlopen", return_value=FakeResponse()) as urlopen:
                summary = summarizer.summarize_text(
                    "hello world",
                    model="test-model",
                    summary_format="Bullet points",
                    max_tokens=25,
                )

        request = urlopen.call_args.args[0]
        body = json.loads(request.data.decode("utf-8"))

        self.assertEqual(summary, "short summary")
        self.assertEqual(request.full_url, "https://api.openai.com/v1/chat/completions")
        self.assertEqual(body["model"], "test-model")
        self.assertEqual(body["max_tokens"], 25)
        self.assertIn("bullet points", body["messages"][0]["content"])


if __name__ == "__main__":
    unittest.main()
