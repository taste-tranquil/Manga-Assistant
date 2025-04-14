import os
import logging
import json
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

# The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# Do not change this unless explicitly requested by the user
MODEL = "gpt-4o"

def get_answer_from_openai(question, pdf_text=None):
    """
    Get an answer from OpenAI based on the question and PDF text.
    
    Args:
        question (str): The question to ask
        pdf_text (str, optional): The text from the PDF. Defaults to None.
        
    Returns:
        str: The answer from OpenAI
    """
    try:
        logger.debug(f"Getting answer for question: {question}")
        
        if not OPENAI_API_KEY:
            logger.error("OpenAI API key not found in environment variables")
            return "I'm sorry, but I can't answer your question right now because the API key is missing. Please check the configuration."
        
        # Prepare messages for OpenAI
        messages = []
        
        # Add system message with context
        if pdf_text:
            context_message = (
                "You are 'Manga Assistant', an AI assistant specialized in answering questions about PDF documents. "
                "Your goal is to give accurate, helpful responses based on the provided PDF content. "
                "For questions not directly answerable from the PDF, provide general knowledge answers "
                "but prioritize the PDF content when relevant. "
                "Here is the text extracted from the PDF document:\n\n"
                f"{pdf_text[:8000]}..."  # Limit context to avoid token limits
            )
            messages.append({"role": "system", "content": context_message})
        else:
            # No PDF provided, act as a general assistant
            messages.append({
                "role": "system", 
                "content": "You are 'Manga Assistant', an AI assistant that can answer general knowledge questions. "
                "Provide helpful, accurate, and concise responses."
            })
        
        # Add the user's question
        messages.append({"role": "user", "content": question})
        
        # Get response from OpenAI
        response = openai.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=800,
            temperature=0.7,
        )
        
        answer = response.choices[0].message.content
        
        logger.debug(f"Received answer from OpenAI: {answer[:100]}...")
        return answer
        
    except Exception as e:
        logger.error(f"Error getting answer from OpenAI: {str(e)}")
        return f"I'm sorry, but I encountered an error while processing your question: {str(e)}"
