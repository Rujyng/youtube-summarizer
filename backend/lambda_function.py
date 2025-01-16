# # ====================================== Local terminal ======================================
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
#     video_id = "DEn8HvKhnZg&ab_channel=GoldenGully"
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

# # ====================================== For lambda ======================================
# import json
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

# def lambda_handler(event, context):
#     """
#     AWS Lambda handler for generating video summaries and optionally refining them.
#     Expects JSON input with the following fields:
#     - video_id: YouTube video ID (e.g., "I76wvt0aEE4").
#     - summary_format: (Optional) Format for the summary ("Any format", "Bullet points", etc.).
#     - refinement_request: (Optional) Refinement instructions for the summary.
#     """
#     try:
#         # Parse the JSON input
#         body = json.loads(event["body"])  # Input from API Gateway
#         video_id = body.get("video_id")  # Directly accept the video ID
#         summary_format = body.get("summary_format", "Any format")
#         refinement_request = body.get("refinement_request")

#         # Check if video_id is provided
#         if not video_id:
#             return {
#                 "statusCode": 400,
#                 "body": json.dumps({"error": "video_id is required in the request body."})
#             }

#         # Fetch transcript
#         transcript = get_transcript(video_id)
#         if not transcript:
#             return {
#                 "statusCode": 500,
#                 "body": json.dumps({"error": "Transcript not found for the given video ID."})
#             }

#         # Generate summary
#         summary = summarize_text(transcript, summary_format=summary_format)
#         if not summary:
#             return {
#                 "statusCode": 500,
#                 "body": json.dumps({"error": "Failed to generate summary."})
#             }

#         # Apply refinement if requested
#         if refinement_request:
#             summary = refine_summary(summary, refinement_request)

#         # Return the result
#         return {
#             "statusCode": 200,
#             "body": json.dumps({
#                 "summary": summary,
#                 "length_original": len(transcript),
#                 "length_summary": len(summary),
#                 "compression_ratio": round(len(summary) / len(transcript) * 100, 2)
#             })
#         }

#     except Exception as e:
#         # Handle any unexpected errors
#         print(f"Error: {e}")
#         return {
#             "statusCode": 500,
#             "body": json.dumps({"error": str(e)}),
#         }

# ====================================== For local api ======================================
from flask import Flask, request, jsonify
from flask_cors import CORS
from src.summarizer import summarize_text, refine_summary
from youtube_transcript_api import YouTubeTranscriptApi

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

def get_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([entry['text'] for entry in transcript_list])
        return transcript, None
    except Exception as e:
        return None, f"An error occurred: {str(e)}"

@app.route('/summarize', methods=['POST', 'OPTIONS'])
def summarize():
    if request.method == 'OPTIONS':
        # Preflight request
        response = jsonify({"message": "Preflight request success"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        response.headers.add("Access-Control-Allow-Methods", "POST,OPTIONS")
        return response, 200
    
    try:
        data = request.get_json()
        video_id = data.get("video_id")
        summary_format = data.get("summary_format", "Any format")
        refinement_request = data.get("refinement_request")

        # Fetch the transcript
        transcript, error = get_transcript(video_id)
        if error:
            return jsonify({"error": error}), 500

        # Generate the summary
        summary = summarize_text(transcript, summary_format=summary_format)
        if not summary:
            return jsonify({"error": "Failed to generate summary."}), 500

        # Apply refinement if requested
        if refinement_request:
            summary = refine_summary(summary, refinement_request)

        response = jsonify({
            "summary": summary,
            "length_original": len(transcript),
            "length_summary": len(summary),
            "compression_ratio": round(len(summary) / len(transcript) * 100, 2)
        })
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

    except Exception as e:
        response = jsonify({"error": str(e)})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)