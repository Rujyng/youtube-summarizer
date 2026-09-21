import json
import os
from pathlib import Path
from urllib.request import Request, urlopen


OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"


def summarize_text(transcript, model="gpt-3.5-turbo", summary_format="Any format", max_tokens=300):
    prompt = _summary_prompt(transcript, summary_format)
    return _call_chat_completion(prompt, model=model, max_tokens=max_tokens)


def summarize_chunk(chunk, model="gpt-3.5-turbo", max_tokens=300):
    prompt = (
        "This transcript is from Oliver's gaming channel. Extract only moments that "
        "help tell Oliver's experience: his reactions, comments, jokes, mistakes, "
        "theories, decisions, and discoveries. Keep specific moments that may be "
        "memorable to a viewer. Also capture meaningful gameplay progress, including "
        "objectives, locations, tools, threats, and story developments. Omit only "
        "routine or repeated actions that add nothing to the episode. Be concise and "
        "do not invent reactions that are not present in the transcript. Include the "
        "timestamp range.\n\n"
        f"Chunk {chunk.chunk_index} "
        f"({chunk.start_seconds:.2f}s-{chunk.end_seconds:.2f}s):\n\n"
        f"{chunk.text}"
    )
    return _call_chat_completion(prompt, model=model, max_tokens=max_tokens)


def summarize_chunk_results(chunk_results, model="gpt-3.5-turbo", summary_format="Any format", max_tokens=300):
    prompt = _final_summary_prompt(chunk_results)
    return _call_chat_completion(prompt, model=model, max_tokens=max_tokens)


def refine_summary(summary, refinement_request, model="gpt-3.5-turbo", max_tokens=300):
    prompt = f"{refinement_request}:\n\n{summary}"
    return _call_chat_completion(prompt, model=model, max_tokens=max_tokens)


def _summary_prompt(transcript, summary_format):
    if summary_format == "Bullet points":
        return f"Summarize the following text in bullet points:\n\n{transcript}"
    if summary_format == "Detailed explanations":
        return f"Provide a detailed explanation of the following text:\n\n{transcript}"
    if summary_format == "Short/concise summaries":
        return f"Provide a short and concise summary of the following text:\n\n{transcript}"
    return f"Summarize the following text:\n\n{transcript}"


def _final_summary_prompt(chunk_results):
    combined_results = "\n\n".join(
        f"Chunk result {index + 1}:\n{result}"
        for index, result in enumerate(chunk_results)
    )
    return (
        "Write a short recap for a viewer of Oliver's gaming channel. Tell the "
        "episode as one chronological story centered on Oliver, not as a log of "
        "what happened in the game. Include the best 2 or 3 moments based on his "
        "reactions, comments, jokes, mistakes, or discoveries. Give secondary focus "
        "to meaningful gameplay progress, including objectives, locations, tools, "
        "threats, and story developments. Merge repeated or overlapping moments and "
        "omit routine actions, minor details, and filler. Write one paragraph of 3 "
        "to 5 direct sentences. Do not use a heading or bullet points. Avoid "
        "unnecessary adjectives and do not invent details.\n\n"
        "Candidate moments from the episode:\n\n"
        f"{combined_results}\n\n"
        "Final selected summary and events:"
    )


def _call_chat_completion(prompt, model, max_tokens):
    _load_local_env()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("An error occurred: OPENAI_API_KEY is not set.")
        return None

    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.5,
    }
    request = Request(
        OPENAI_CHAT_COMPLETIONS_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        print(f"An error occurred: {exc}")
        return None

    return payload["choices"][0]["message"]["content"]


def _load_local_env():
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
