
# from src.summarizer import summarize_text, refine_summary
# from youtube_transcript_api import YouTubeTranscriptApi

# def get_transcript(video_id):
#     try:
#         transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
#         transcript = " ".join([entry['text'] for entry in transcript_list])
#         return transcript
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return None

# def run():
#     # video_id = input("Enter the video ID: ")
#     video_id = "4ks019Sq9_I"
#     transcript = get_transcript(video_id)
    
#     if transcript:
#         # Print the transcript and the summary to the console then compare their lengths and print the result
#         print("Transcript:")
#         print(transcript)
#         print("#################################################################")

#         # Allow user to select summary format
#         print("Select summary format:")
#         print("1. Any format")
#         print("2. Bullet points")
#         print("3. Detailed explanations")
#         print("4. Short/concise summaries")
#         format_choice = input("Enter the number of your choice: ")
        
#         summary_format = "Any format"
#         if format_choice == "2":
#             summary_format = "Bullet points"
#         elif format_choice == "3":
#             summary_format = "Detailed explanations"
#         elif format_choice == "4":
#             summary_format = "Short/concise summaries"

#         summary = summarize_text(transcript, summary_format=summary_format)
#         if summary:
#             print("Summary:")
#             print(summary)
#             print(f"Length of transcript: {len(transcript)} characters")
#             print(f"Length of summary: {len(summary)} characters")
#             print(f"Compression ratio: {round(len(summary) / len(transcript) * 100, 2)}%")

#             # Allow user to refine the summary interactively
#             while True:
#                 print("Do you want to refine the summary? (yes/no)")
#                 refine_choice = input().strip().lower()
#                 if refine_choice == "no":
#                     break
#                 refinement_request = input("Enter your refinement request (e.g., 'make it shorter', 'focus on the key points', 'explain the technical terms'): ")
#                 summary = refine_summary(summary, refinement_request)
#                 print("Refined Summary:")
#                 print(summary)
#         else:
#             print("Failed to generate summary.")
#     else:
#         print("Transcript not found for the given video ID.")

# if __name__ == "__main__":
#     run()

import json
from src.summarizer import summarize_text, refine_summary
from youtube_transcript_api import YouTubeTranscriptApi

def get_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([entry['text'] for entry in transcript_list])
        return transcript
    except Exception as e:
        return f"Error fetching transcript: {str(e)}"

def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])  # Input from API Gateway
        video_url = body.get("video_url")
        summary_format = body.get("summary_format", "Any format")
        refinement_request = body.get("refinement_request")

        video_id = video_url.split("v=")[-1]  # Extract video ID

        # Fetch transcript
        transcript = get_transcript(video_id)
        if not transcript:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Transcript not found."})
            }

        # Generate summary
        summary = summarize_text(transcript, summary_format=summary_format)
        if not summary:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Failed to generate summary."})
            }

        # Apply refinement if requested
        if refinement_request:
            summary = refine_summary(summary, refinement_request)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "summary": summary,
                "length_original": len(transcript),
                "length_summary": len(summary),
                "compression_ratio": round(len(summary) / len(transcript) * 100, 2)
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }