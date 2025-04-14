import os
import logging
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import tempfile
from utils.pdf_processor import extract_text_from_pdf
from utils.gemini_helper import get_answer_from_gemini

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "manga-assistant-secret-key")

# Configure file upload settings
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx', 'csv', 'json', 'md', 'html', 'xml', 'jpg', 'jpeg', 'png'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    # If filename has an extension, check if it's in allowed extensions
    # If no extension, still allow it (could be a plain text file)
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    return True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # Check if the POST request has the file part
        if 'pdf_file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['pdf_file']
        
        # If user doesn't select a file, the browser submits an empty file without a filename
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # Create a temporary file to save the uploaded PDF
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = temp_file.name
                file.save(temp_path)
                
                # Process the PDF file
                try:
                    # Use a lower max_pages value for large PDFs to avoid timeout
                    file_size = os.path.getsize(temp_path)
                    max_pages = 10 if file_size > 5 * 1024 * 1024 else 20
                    
                    logger.debug(f"Processing PDF {filename} (Size: {file_size / 1024 / 1024:.2f} MB) with max_pages={max_pages}")
                    pdf_text = extract_text_from_pdf(temp_path, max_pages=max_pages)
                    
                    # Delete the temporary file
                    os.unlink(temp_path)
                    
                    if not pdf_text or pdf_text == "No readable text found in the PDF.":
                        return jsonify({
                            'success': False,
                            'warning': 'Could not extract text from this PDF. It may be scanned or contain only images.',
                            'filename': filename,
                            'text_preview': 'No readable text found.'
                        }), 200  # Still return 200 but with a warning
                    
                    # Truncate very large texts to avoid memory issues
                    if len(pdf_text) > 100000:
                        pdf_text = pdf_text[:100000] + "\n\n[Content truncated due to large size...]"
                        logger.warning(f"PDF text truncated as it exceeded 100,000 characters")
                    
                    return jsonify({
                        'success': True,
                        'message': 'PDF processed successfully',
                        'filename': filename,
                        'text_preview': pdf_text[:200] + '...' if len(pdf_text) > 200 else pdf_text,
                        'pdf_text': pdf_text
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing PDF: {str(e)}")
                    # Delete the temporary file if it exists
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                    return jsonify({
                        'error': f'Error processing PDF: {str(e)}',
                        'suggestion': 'Try uploading a smaller PDF or one with fewer pages.'
                    }), 500
        else:
            return jsonify({'error': 'File type not allowed. Please upload a PDF.'}), 400
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        question = data.get('question')
        pdf_text = data.get('pdf_text')
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        # If PDF text is provided, use it for context
        if pdf_text:
            answer = get_answer_from_gemini(question, pdf_text)
        else:
            # If no PDF context, just ask Gemini directly
            answer = get_answer_from_gemini(question)
        
        return jsonify({
            'success': True,
            'question': question,
            'answer': answer
        })
    
    except Exception as e:
        logger.error(f"Error getting answer: {str(e)}")
        return jsonify({'error': f'Error getting answer: {str(e)}'}), 500

if __name__ == '__main__':
    # For local development
    app.run(host='0.0.0.0', port=5000, debug=True)
