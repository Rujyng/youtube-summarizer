import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize_text(transcript, model="gpt-3.5-turbo", max_tokens=300):
    """
    Summarize text using OpenAI's ChatGPT API.
    :param transcript: Full transcript text to summarize.
    :param model: The OpenAI model to use (e.g., gpt-3.5-turbo or gpt-4).
    :param max_tokens: Maximum tokens for the summary.
    :return: A summary of the transcript.
    """
    try:
        # Call the OpenAI API
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Summarize the following text:\n\n{transcript}"}
            ],
            max_tokens=max_tokens,
            temperature=0.5,
        )
        # Extract and return the summary
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"An error occurred: {e}")
        return None