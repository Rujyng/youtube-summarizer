from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

def summarize_text(transcript, model="gpt-3.5-turbo", summary_format="Any format", max_tokens=300):
    """
    Summarize text using OpenAI's ChatGPT API.
    :param transcript: Full transcript text to summarize.
    :param model: The OpenAI model to use (e.g., gpt-3.5-turbo or gpt-4).
    :param summary_format: The format of the summary (e.g., "Any format", "Bullet points", "Detailed explanations", "Short/concise summaries").
    :param max_tokens: Maximum tokens for the summary.
    :return: A summary of the transcript.
    """
    try:
        # Define the prompt based on the selected summary format
        if summary_format == "Bullet points":
            template = "Summarize the following text in bullet points:\n\n{transcript}"
        elif summary_format == "Detailed explanations":
            template = "Provide a detailed explanation of the following text:\n\n{transcript}"
        elif summary_format == "Short/concise summaries":
            template = "Provide a short and concise summary of the following text:\n\n{transcript}"
        else:
            template = "Summarize the following text:\n\n{transcript}"

        prompt_template = PromptTemplate(
            input_variables=["transcript"],
            template=template
        )

        llm = ChatOpenAI(model=model, max_tokens=max_tokens, temperature=0.5)

        chain = prompt_template | llm | StrOutputParser()

        summary = chain.invoke({"transcript": transcript})
        return summary
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
def refine_summary(summary, refinement_request, model="gpt-3.5-turbo", max_tokens=300):
    """
    Refine the summary based on user input.
    :param summary: The initial summary to refine.
    :param refinement_request: The user's request for refinement (e.g., "make it shorter", "focus on the key points", "explain the technical terms").
    :param model: The OpenAI model to use (e.g., gpt-3.5-turbo or gpt-4).
    :param max_tokens: Maximum tokens for the refined summary.
    :return: The refined summary.
    """
    try:
        template = "{refinement_request}:\n\n{summary}"

        prompt_template = PromptTemplate(
            input_variables=["refinement_request", "summary"],
            template=template
        )

        llm = ChatOpenAI(model=model, max_tokens=max_tokens, temperature=0.5)

        chain = prompt_template | llm | StrOutputParser()

        refined_summary = chain.invoke({
            "refinement_request": refinement_request,
            "summary": summary
        })

        return refined_summary
    except Exception as e:
        print(f"An error occurred: {e}")
        return None