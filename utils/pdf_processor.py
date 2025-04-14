import os
import logging
import PyPDF2

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path, max_pages=20):
    """
    Extract text from a PDF file with optimizations for performance.
    
    Args:
        pdf_path (str): Path to the PDF file
        max_pages (int): Maximum number of pages to process
        
    Returns:
        str: Extracted text from the PDF
    """
    try:
        logger.debug(f"Extracting text from PDF: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file does not exist: {pdf_path}")
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        extracted_text = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            # Limit pages to prevent timeouts with large PDFs
            pages_to_process = min(num_pages, max_pages)
            logger.debug(f"PDF has {num_pages} pages, processing {pages_to_process}")
            
            # Extract text from each page with a limit
            for page_num in range(pages_to_process):
                try:
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    
                    if page_text:
                        extracted_text.append(page_text)
                    else:
                        logger.warning(f"No text extracted from page {page_num + 1}")
                        
                except Exception as page_error:
                    logger.warning(f"Error extracting text from page {page_num + 1}: {str(page_error)}")
                    continue
            
            # Add a note if we limited the pages
            if num_pages > max_pages:
                extracted_text.append(f"\n\n[Note: Only showing text from the first {max_pages} pages of {num_pages} total pages]")
        
        # Join all text with newlines and clean up
        final_text = "\n\n".join(extracted_text).strip()
        
        if not final_text:
            logger.warning("No text extracted from the PDF")
            return "No readable text found in the PDF."
        
        logger.debug(f"Successfully extracted {len(final_text)} characters from PDF")
        return final_text
        
    except PyPDF2.errors.PdfReadError as e:
        logger.error(f"Error reading PDF: {str(e)}")
        raise ValueError(f"The PDF file is invalid or corrupted: {str(e)}")
        
    except Exception as e:
        logger.error(f"Unexpected error extracting text from PDF: {str(e)}")
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

def get_pdf_metadata(pdf_path):
    """
    Extract metadata from a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        dict: PDF metadata
    """
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            metadata = pdf_reader.metadata
            
            # Convert to a regular dictionary
            if metadata:
                return {
                    'title': metadata.get('/Title', ''),
                    'author': metadata.get('/Author', ''),
                    'subject': metadata.get('/Subject', ''),
                    'creator': metadata.get('/Creator', ''),
                    'producer': metadata.get('/Producer', ''),
                    'num_pages': len(pdf_reader.pages)
                }
            else:
                return {
                    'title': '',
                    'author': '',
                    'subject': '',
                    'creator': '',
                    'producer': '',
                    'num_pages': len(pdf_reader.pages)
                }
                
    except Exception as e:
        logger.error(f"Error extracting PDF metadata: {str(e)}")
        return {
            'title': '',
            'author': '',
            'subject': '',
            'creator': '',
            'producer': '',
            'num_pages': 0,
            'error': str(e)
        }
