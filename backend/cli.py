import argparse
import sys

from backend.src.transcript import (
    chunk_transcript,
    fetch_transcript,
    parse_video_id,
    transcript_text,
)


def run_summarize(
    args,
    fetch_transcript=fetch_transcript,
    chunk_summarize=None,
    summarize=None,
    refine=None,
    output=sys.stdout,
    progress_output=sys.stderr,
):
    print("Parsing video ID...", file=progress_output)
    try:
        video_id = parse_video_id(args.video)
    except ValueError as exc:
        print(f"Invalid video input: {exc}", file=output)
        return 2

    print(f"Fetching transcript for {video_id}...", file=progress_output)
    try:
        segments = fetch_transcript(video_id)
    except Exception as exc:
        print(f"Failed to fetch transcript for {video_id}.", file=output)
        print(
            "The video may not have captions, or YouTube may have returned an "
            "empty/unsupported transcript response.",
            file=output,
        )
        print(f"Details: {exc}", file=output)
        return 1

    transcript = transcript_text(segments)
    print(f"Fetched {len(segments)} transcript segments.", file=progress_output)
    chunks = chunk_transcript(
        segments,
        max_estimated_tokens=getattr(args, "chunk_max_tokens", 1000),
    )
    print(f"Created {len(chunks)} transcript chunks.", file=progress_output)

    if chunk_summarize is None or summarize is None or refine is None:
        print("Loading summarizer...", file=progress_output)
        from backend.src.summarizer import (
            refine_summary,
            summarize_chunk,
            summarize_chunk_results,
        )

        chunk_summarize = chunk_summarize or summarize_chunk
        summarize = summarize or summarize_chunk_results
        refine = refine or refine_summary

    chunk_results = []
    for chunk in chunks:
        print(f"Summarizing chunk {chunk.chunk_index + 1}/{len(chunks)}...", file=progress_output)
        chunk_result = chunk_summarize(
            chunk,
            model=args.model,
            max_tokens=args.chunk_summary_tokens,
        )
        if not chunk_result:
            print(f"Failed to summarize chunk {chunk.chunk_index}.", file=output)
            return 1
        chunk_results.append(chunk_result)

    print("Calling model for final summary...", file=progress_output)
    summary = summarize(
        chunk_results,
        model=args.model,
        summary_format=args.summary_format,
        max_tokens=args.max_tokens,
    )
    if not summary:
        print("Failed to generate summary.", file=output)
        return 1

    if args.refinement_request:
        summary = refine(
            summary,
            args.refinement_request,
            model=args.model,
            max_tokens=args.max_tokens,
        )
        if not summary:
            print("Failed to refine summary.", file=output)
            return 1

    print("Summary:", file=output)
    print(summary, file=output)
    print("", file=output)
    print(f"Transcript segments: {len(segments)}", file=output)
    print(f"Transcript chunks: {len(chunks)}", file=output)
    if chunks:
        print(f"First chunk: {_chunk_metadata(chunks[0])}", file=output)
        print(f"Last chunk: {_chunk_metadata(chunks[-1])}", file=output)
    print(f"Length original: {len(transcript)} characters", file=output)
    print(f"Chunk summaries: {len(chunk_results)}", file=output)
    print(f"Length summary: {len(summary)} characters", file=output)
    if transcript:
        ratio = round(len(summary) / len(transcript) * 100, 2)
        print(f"Compression ratio: {ratio}%", file=output)

    return 0


def _chunk_metadata(chunk):
    return (
        f"{chunk.start_seconds:.2f}-{chunk.end_seconds:.2f}s, "
        f"{chunk.segment_count} segments, "
        f"{chunk.character_count} chars, "
        f"~{chunk.estimated_token_count} tokens"
    )


def build_parser():
    parser = argparse.ArgumentParser(
        prog="youtube-summarizer",
        description="Backend-only CLI for summarizing YouTube transcripts.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    summarize_parser = subparsers.add_parser(
        "summarize",
        help="Fetch a YouTube transcript and summarize it.",
    )
    summarize_parser.add_argument("video", help="YouTube URL or video ID.")
    summarize_parser.add_argument(
        "--summary-format",
        default="Any format",
        choices=[
            "Any format",
            "Bullet points",
            "Detailed explanations",
            "Short/concise summaries",
        ],
    )
    summarize_parser.add_argument(
        "--refinement-request",
        help="Optional instruction for refining the generated summary.",
    )
    summarize_parser.add_argument("--model", default="gpt-3.5-turbo")
    summarize_parser.add_argument("--max-tokens", type=int, default=300)
    summarize_parser.add_argument("--chunk-max-tokens", type=int, default=1000)
    summarize_parser.add_argument("--chunk-summary-tokens", type=int, default=300)
    summarize_parser.set_defaults(func=run_summarize)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
