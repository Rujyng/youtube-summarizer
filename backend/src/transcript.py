from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse


@dataclass(frozen=True)
class TranscriptSegment:
    text: str
    start: float
    duration: float


@dataclass(frozen=True)
class TranscriptChunk:
    chunk_index: int
    start_seconds: float
    end_seconds: float
    text: str
    segment_count: int
    character_count: int
    estimated_token_count: int


def parse_video_id(video):
    value = video.strip()
    if value.startswith("[") and "](" in value:
        raise ValueError("Use a plain YouTube URL, not a Markdown link.")

    parsed = urlparse(value)

    if not parsed.scheme and not parsed.netloc:
        return value

    hostname = parsed.hostname or ""
    if hostname in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            video_ids = parse_qs(parsed.query).get("v")
            if video_ids:
                return video_ids[0]
        if parsed.path.startswith("/shorts/") or parsed.path.startswith("/embed/"):
            return parsed.path.split("/")[2]

    if hostname == "youtu.be":
        return parsed.path.lstrip("/").split("/")[0]

    raise ValueError(f"Unsupported YouTube URL: {video}")


def fetch_transcript(video_id, ytt_api=None, languages=None):
    if languages is None:
        languages = ["en"]
    if ytt_api is None:
        from youtube_transcript_api import YouTubeTranscriptApi

        if not hasattr(YouTubeTranscriptApi, "fetch"):
            transcript = _fetch_with_legacy_api(YouTubeTranscriptApi, video_id, languages)
            return _segments_from_raw_data(transcript)

        ytt_api = YouTubeTranscriptApi()

    try:
        fetched_transcript = ytt_api.fetch(video_id, languages=languages)
    except Exception:
        transcript_list = ytt_api.list(video_id)
        transcript = _find_available_transcript(transcript_list, languages)
        fetched_transcript = transcript.fetch()

    transcript = _to_raw_data(fetched_transcript)
    return _segments_from_raw_data(transcript)


def _fetch_with_legacy_api(youtube_transcript_api, video_id, languages):
    try:
        return youtube_transcript_api.get_transcript(video_id, languages=languages)
    except Exception:
        transcript_list = youtube_transcript_api.list_transcripts(video_id)
        transcript = _find_available_transcript(transcript_list, languages)
        return transcript.fetch()


def _to_raw_data(fetched_transcript):
    if hasattr(fetched_transcript, "to_raw_data"):
        return fetched_transcript.to_raw_data()
    return fetched_transcript


def _segments_from_raw_data(transcript):
    return [
        TranscriptSegment(
            text=entry["text"],
            start=float(entry["start"]),
            duration=float(entry["duration"]),
        )
        for entry in transcript
    ]


def _find_available_transcript(transcript_list, languages):
    for name in (
        "find_manually_created_transcript",
        "find_generated_transcript",
        "find_transcript",
    ):
        finder = getattr(transcript_list, name, None)
        if finder is None:
            continue
        try:
            return finder(languages)
        except Exception:
            continue
    raise ValueError("No usable transcript found for the requested languages.")


def transcript_text(segments):
    return " ".join(segment.text for segment in segments)


def chunk_transcript(segments, max_estimated_tokens=1000):
    chunks = []
    current_segments = []

    for segment in segments:
        candidate_segments = current_segments + [segment]
        candidate_text = transcript_text(candidate_segments)

        if current_segments and estimate_token_count(candidate_text) > max_estimated_tokens:
            chunks.append(_build_chunk(len(chunks), current_segments))
            current_segments = [segment]
        else:
            current_segments = candidate_segments

    if current_segments:
        chunks.append(_build_chunk(len(chunks), current_segments))

    return chunks


def estimate_token_count(text):
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


def _build_chunk(chunk_index, segments):
    text = transcript_text(segments)
    start_seconds = segments[0].start
    end_seconds = segments[-1].start + segments[-1].duration

    return TranscriptChunk(
        chunk_index=chunk_index,
        start_seconds=start_seconds,
        end_seconds=end_seconds,
        text=text,
        segment_count=len(segments),
        character_count=len(text),
        estimated_token_count=estimate_token_count(text),
    )
