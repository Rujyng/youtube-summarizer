# filepath: /Users/tan/Documents/FF_Projects/youtube-summarizer/run.py
import openai
from src.summarizer import summarize_text
from youtube_transcript_api import YouTubeTranscriptApi

def get_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([entry['text'] for entry in transcript_list])
        return transcript
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def run():
    video_id = input("Enter the video ID: ")
    transcript = get_transcript(video_id)
    
    if transcript:
        # Print the transcript and the summary to the console then compare their lengths and print the result
        print("Transcript:")
        print(transcript)
        print("Summary:")
        summary = summarize_text(transcript)
        print(summary)
        print(f"Length of transcript: {len(transcript)} characters")
        print(f"Length of summary: {len(summary)} characters")
        print(f"Compression ratio: {round(len(summary) / len(transcript) * 100, 2)}%")
    else:
        print("Transcript not found for the given video ID.")

if __name__ == "__main__":
    run()