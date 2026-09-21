import unittest

from backend.src.transcript import (
    TranscriptSegment,
    fetch_transcript,
    parse_video_id,
    transcript_text,
)


class FakeFetchedTranscript:
    def __init__(self, raw_data):
        self.raw_data = raw_data

    def to_raw_data(self):
        return self.raw_data


class FakeTranscript:
    def __init__(self, raw_data):
        self.raw_data = raw_data

    def fetch(self):
        return FakeFetchedTranscript(self.raw_data)


class FakeTranscriptList:
    def __init__(self, transcript):
        self.transcript = transcript

    def find_manually_created_transcript(self, languages):
        return self.transcript


class FakeApi:
    def __init__(self, raw_data, fail_direct_fetch=False):
        self.raw_data = raw_data
        self.fail_direct_fetch = fail_direct_fetch
        self.fetch_calls = []
        self.list_calls = []

    def fetch(self, video_id, languages):
        self.fetch_calls.append((video_id, languages))
        if self.fail_direct_fetch:
            raise RuntimeError("direct fetch failed")
        return FakeFetchedTranscript(self.raw_data)

    def list(self, video_id):
        self.list_calls.append(video_id)
        return FakeTranscriptList(FakeTranscript(self.raw_data))


class TranscriptTests(unittest.TestCase):
    def test_parse_video_id_accepts_common_youtube_inputs(self):
        self.assertEqual(
            parse_video_id("https://www.youtube.com/watch?v=abc123XYZ_9"),
            "abc123XYZ_9",
        )
        self.assertEqual(
            parse_video_id("https://youtu.be/abc123XYZ_9?si=share"),
            "abc123XYZ_9",
        )
        self.assertEqual(parse_video_id("abc123XYZ_9"), "abc123XYZ_9")

    def test_parse_video_id_rejects_markdown_links(self):
        with self.assertRaisesRegex(ValueError, "plain YouTube URL"):
            parse_video_id(
                "[https://www.youtube.com/watch?v=abc123XYZ_9]"
                "(https://www.youtube.com/watch?v=abc123XYZ_9)"
            )

    def test_transcript_text_preserves_segment_order(self):
        segments = [
            TranscriptSegment(text="first", start=0.0, duration=1.5),
            TranscriptSegment(text="second", start=1.5, duration=2.0),
        ]

        self.assertEqual(transcript_text(segments), "first second")

    def test_fetch_transcript_uses_instance_fetch_api(self):
        api = FakeApi(
            [
                {"text": "hello", "start": 0, "duration": 1.5},
                {"text": "world", "start": 1.5, "duration": 2},
            ]
        )

        segments = fetch_transcript("video123", ytt_api=api)

        self.assertEqual(api.fetch_calls, [("video123", ["en"])])
        self.assertEqual(
            segments,
            [
                TranscriptSegment(text="hello", start=0.0, duration=1.5),
                TranscriptSegment(text="world", start=1.5, duration=2.0),
            ],
        )

    def test_fetch_transcript_falls_back_to_available_transcript_list(self):
        api = FakeApi(
            [{"text": "fallback", "start": 3, "duration": 4}],
            fail_direct_fetch=True,
        )

        segments = fetch_transcript("video123", ytt_api=api)

        self.assertEqual(api.list_calls, ["video123"])
        self.assertEqual(
            segments,
            [TranscriptSegment(text="fallback", start=3.0, duration=4.0)],
        )


if __name__ == "__main__":
    unittest.main()
