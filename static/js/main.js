// Main JavaScript for Manga Assistant

document.addEventListener('DOMContentLoaded', () => {
    // DOM elements
    const uploadForm = document.getElementById('upload-form');
    const pdfFileInput = document.getElementById('pdf-file');
    const uploadArea = document.getElementById('upload-area');
    const dragText = document.getElementById('drag-text');
    const uploadButton = document.getElementById('upload-button');
    const pdfPreviewContainer = document.getElementById('pdf-preview-container');
    const pdfPreview = document.getElementById('pdf-preview');
    const pdfFilename = document.getElementById('pdf-filename');
    const pdfTextContainer = document.getElementById('pdf-text-container');
    const askContainer = document.getElementById('ask-container');
    const questionInput = document.getElementById('question-input');
    const askButton = document.getElementById('ask-button');
    const chatContainer = document.getElementById('chat-container');
    const uploadSpinner = document.getElementById('upload-spinner');
    const askSpinner = document.getElementById('ask-spinner');
    const fileUploadBtn = document.getElementById('file-upload-btn');
    
    let pdfText = null; // Store the extracted PDF text
    
    // Event listeners for drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        uploadArea.classList.add('active');
    }
    
    function unhighlight() {
        uploadArea.classList.remove('active');
    }
    
    // Handle file drop
    uploadArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            pdfFileInput.files = files;
            handleFileSelect();
        }
    }
    
    // Handle file selection via button
    pdfFileInput.addEventListener('change', handleFileSelect);
    
    function handleFileSelect() {
        if (pdfFileInput.files.length > 0) {
            const file = pdfFileInput.files[0];
            
            // Any file type is now allowed
            // (We've removed the PDF-only restriction)
            
            uploadFile(file);
        }
    }
    
    // Handle form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (pdfFileInput.files.length > 0) {
            const file = pdfFileInput.files[0];
            uploadFile(file);
        } else {
            showAlert('Please select a file to upload.', 'danger');
        }
    });
    
    // Upload file (any type)
    function uploadFile(file) {
        // Show file size warning for large files
        if (file.size > 10 * 1024 * 1024) {
            showAlert('This file is quite large (' + (file.size / (1024 * 1024)).toFixed(1) + ' MB). Processing may take longer.', 'warning');
        }
        
        const formData = new FormData();
        formData.append('pdf_file', file);
        
        // Show loading spinner
        uploadButton.disabled = true;
        uploadSpinner.classList.remove('d-none');
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Success - full text was extracted
            if (data.success === true) {
                // Store the PDF text
                pdfText = data.pdf_text;
                
                // Show PDF preview
                pdfFilename.textContent = data.filename;
                pdfPreview.textContent = data.text_preview;
                pdfPreviewContainer.classList.remove('d-none');
                
                // Show ask container
                askContainer.classList.remove('d-none');
                
                // Hide the upload area
                uploadArea.classList.add('d-none');
                
                // Clear any previous chat messages
                chatContainer.innerHTML = '';
                
                // Add system message
                addAssistantMessage('I\'ve processed your file. You can now ask me questions about its content!');
                
                showAlert('File uploaded and processed successfully!', 'success');
            }
            // Success but with warning - couldn't extract text
            else if (data.success === false && data.warning) {
                // Show PDF filename
                pdfFilename.textContent = data.filename;
                pdfPreview.textContent = data.text_preview || 'No readable text found.';
                pdfPreviewContainer.classList.remove('d-none');
                
                // Show ask container
                askContainer.classList.remove('d-none');
                
                // Hide the upload area
                uploadArea.classList.add('d-none');
                
                // Clear any previous chat messages
                chatContainer.innerHTML = '';
                
                // Add system message about limited functionality
                addAssistantMessage('I couldn\'t extract text from this PDF. It may be scanned or contain only images. You can still ask me general questions, but I won\'t be able to answer questions about the PDF content.');
                
                showAlert(data.warning, 'warning');
            }
            // Error
            else {
                if (data.error && data.suggestion) {
                    showAlert(`${data.error} ${data.suggestion}`, 'danger');
                } else {
                    showAlert(data.error || 'Error processing file', 'danger');
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('An error occurred while uploading the file. The file may be too large or corrupt.', 'danger');
        })
        .finally(() => {
            // Hide loading spinner
            uploadButton.disabled = false;
            uploadSpinner.classList.add('d-none');
        });
    }
    
    // Ask button event listener
    askButton.addEventListener('click', askQuestion);
    
    // Question input enter key event
    questionInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            askQuestion();
        }
    });
    
    // Function to ask a question
    function askQuestion() {
        const question = questionInput.value.trim();
        
        if (question === '') {
            return;
        }
        
        // Add user message to chat
        addUserMessage(question);
        
        // Show typing indicator
        showTypingIndicator();
        
        // Disable ask button and clear input
        askButton.disabled = true;
        askSpinner.classList.remove('d-none');
        questionInput.value = '';
        
        // Send question to server
        fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                pdf_text: pdfText
            })
        })
        .then(response => response.json())
        .then(data => {
            // Remove typing indicator
            removeTypingIndicator();
            
            if (data.success) {
                // Add assistant message with the answer
                addAssistantMessage(data.answer);
            } else {
                showAlert(data.error || 'Error getting answer', 'danger');
                addAssistantMessage('I\'m sorry, I couldn\'t process your question. Please try again.');
            }
        })
        .catch(error => {
            // Remove typing indicator
            removeTypingIndicator();
            
            console.error('Error:', error);
            showAlert('An error occurred while processing your question.', 'danger');
            addAssistantMessage('I\'m sorry, an error occurred. Please try again.');
        })
        .finally(() => {
            // Enable ask button and hide spinner
            askButton.disabled = false;
            askSpinner.classList.add('d-none');
        });
    }
    
    // Function to add user message to chat
    function addUserMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message user-message';
        messageDiv.textContent = message;
        chatContainer.appendChild(messageDiv);
        scrollToBottom();
    }
    
    // Function to add assistant message to chat
    function addAssistantMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message assistant-message';
        
        // Process message for markdown-like formatting
        const formattedMessage = message
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
        
        messageDiv.innerHTML = formattedMessage;
        chatContainer.appendChild(messageDiv);
        scrollToBottom();
    }
    
    // Function to show typing indicator
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator assistant-message';
        typingDiv.id = 'typing-indicator';
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'typing-dot';
            typingDiv.appendChild(dot);
        }
        chatContainer.appendChild(typingDiv);
        scrollToBottom();
    }
    
    // Function to remove typing indicator
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    // Scroll chat container to bottom
    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // Function to show alerts
    function showAlert(message, type) {
        const alertContainer = document.getElementById('alert-container');
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        alertContainer.appendChild(alertDiv);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alertDiv);
            bsAlert.close();
        }, 5000);
    }
    
    // Add click handler for "Upload another file" button
    document.getElementById('upload-another-btn').addEventListener('click', () => {
        // Show upload area and hide other containers
        uploadArea.classList.remove('d-none');
        pdfPreviewContainer.classList.add('d-none');
        askContainer.classList.add('d-none');
        
        // Clear file input
        pdfFileInput.value = '';
        
        // Clear PDF text
        pdfText = null;
    });
    
    // Add click handler for chat paperclip button
    if (fileUploadBtn) {
        fileUploadBtn.addEventListener('click', () => {
            // Trigger the file input click
            pdfFileInput.click();
        });
    }
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
