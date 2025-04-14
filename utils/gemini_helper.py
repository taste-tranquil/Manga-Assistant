import os
import logging
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Gemini client
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Model configuration
MODEL = "gemini-1.5-pro"  # Using the latest Gemini model

def get_answer_from_gemini(question, pdf_text=None):
    """
    Get an answer from Google Gemini AI based on the question and PDF text.
    
    Args:
        question (str): The question to ask
        pdf_text (str, optional): The text from the PDF. Defaults to None.
        
    Returns:
        str: The answer from Gemini
    """
    try:
        logger.debug(f"Getting answer for question: {question}")
        
        if not GOOGLE_API_KEY:
            logger.error("Google API key not found in environment variables")
            return "I'm sorry, but I can't answer your question right now because the API key is missing. Please check the configuration."
        
        # Create the generation config
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 800,
        }
        
        # Set up the model
        model = genai.GenerativeModel(
            model_name=MODEL,
            generation_config=generation_config
        )
        
        # Prepare the prompt
        if pdf_text:
            # For questions about the PDF, include the PDF text in the prompt
            prompt = (
                "You are 'Manga Assistant', an AI assistant specialized in answering questions about PDF documents. "
                "Your goal is to give accurate, helpful responses based on the provided PDF content. "
                "For questions not directly answerable from the PDF, provide general knowledge answers "
                "but prioritize the PDF content when relevant.\n\n"
                f"PDF CONTENT:\n{pdf_text[:30000]}\n\n"  # Limit context to avoid token limits
                f"USER QUESTION: {question}\n\n"
                "Please provide a helpful, accurate response based on the PDF content above."
            )
        else:
            # For general questions, don't include PDF context
            prompt = (
                "You are 'Manga Assistant', an AI assistant that can answer general knowledge questions. "
                "Provide helpful, accurate, and concise responses.\n\n"
                f"USER QUESTION: {question}"
            )
        
        # Get response from Gemini
        response = model.generate_content(prompt)
        
        # Extract and return the answer
        answer = response.text
        
        logger.debug(f"Received answer from Gemini: {answer[:100]}...")
        return answer
        
    except Exception as e:
        logger.error(f"Error getting answer from Gemini: {str(e)}")
        return f"I'm sorry, but I encountered an error while processing your question: {str(e)}"
