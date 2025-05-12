document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const chatMessages = document.getElementById('chat-messages');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-btn');
    const fileUploadBtn = document.getElementById('file-upload-btn');
    const fileUpload = document.getElementById('file-upload');
    const imageUploadBtn = document.getElementById('image-upload-btn');
    const imageUpload = document.getElementById('image-upload');
    const micButton = document.getElementById('mic-btn');
    const modelDropdown = document.getElementById('model-dropdown');
    
    console.log("Script loaded. Send button:", sendButton);
    
    // State variables
    let selectedModel = modelDropdown.value;
    let uploadedFiles = [];
    let uploadedImages = [];
    let isRecording = false;
    let mediaRecorder = null;
    let audioChunks = [];
    
    // Event Listeners
    modelDropdown.addEventListener('change', handleModelChange);
    
    // Direct onclick handler for send button
    document.getElementById('send-btn').onclick = function() {
        console.log("Send button clicked via onclick");
        sendMessage();
    };
    
    // Also add the event listener as a backup
    if (sendButton) {
        sendButton.addEventListener('click', function() {
            console.log("Send button clicked via event listener");
            sendMessage();
        });
    }
    
    // Enter key handler
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    fileUploadBtn.addEventListener('click', () => fileUpload.click());
    fileUpload.addEventListener('change', handleFileUpload);
    
    imageUploadBtn.addEventListener('click', () => imageUpload.click());
    imageUpload.addEventListener('change', handleImageUpload);
    
    micButton.addEventListener('click', toggleRecording);
    
    // Functions
    function handleModelChange() {
        selectedModel = modelDropdown.value;
        console.log("Model changed to:", selectedModel);
        if (selectedModel === 'custom') {
            document.getElementById('custom-endpoint').classList.remove('hidden');
        } else {
            document.getElementById('custom-endpoint').classList.add('hidden');
        }
    }
    
    function sendMessage() {
        console.log('sendMessage function called');
        const message = messageInput.value.trim();
        
        if (!message && uploadedFiles.length === 0 && uploadedImages.length === 0) {
            console.log("No message to send");
            return;
        }
        
        console.log("Sending message:", message);
        
        // Add user message to chat
        addMessageToChat('user', message);
        
        // Prepare data for API request
        const requestData = {
            model: selectedModel,
            message: message
        };
        
        // Clear input and uploaded files
        messageInput.value = '';
        uploadedFiles = [];
        uploadedImages = [];
        
        // Remove file previews
        const previews = document.querySelectorAll('.file-preview, .image-preview');
        previews.forEach(preview => preview.remove());
        
        // Show loading indicator
        const loadingId = showLoadingIndicator();
        
        // Make API request directly with fetch
        console.log("Sending API request to /api/chat");
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            console.log("Received response:", response.status);
            if (!response.ok) {
                return response.text().then(text => {
                    throw new Error(`HTTP error! status: ${response.status}, message: ${text}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log("Parsed response data:", data);
            // Remove loading indicator
            removeLoadingIndicator(loadingId);
            // Add AI response to chat
            addMessageToChat('ai', data.text);
        })
        .catch(error => {
            console.error('Error:', error);
            removeLoadingIndicator(loadingId);
            addMessageToChat('ai', 'Sorry, there was an error processing your request: ' + error.message);
        });
    }
    
    function addMessageToChat(sender, text, attachments = []) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender === 'user' ? 'user-message' : 'ai-message');
    
        // Add text content if provided
        if (text) {
            if (sender === 'ai') {
                // For AI messages, render markdown as HTML
                const textContainer = document.createElement('div');
                textContainer.classList.add('markdown-content');
                
                // Configure marked for proper handling of lists and formatting
                marked.setOptions({
                    breaks: true,          // Add line breaks on single line breaks
                    gfm: true,             // Enable GitHub Flavored Markdown
                    headerIds: true,       // Generate IDs for headers
                    mangle: false,         // Don't escape HTML
                    pedantic: false,       // Don't be overly precise with markdown spec
                    sanitize: false,       // Don't sanitize HTML (needed for proper rendering)
                    smartLists: true,      // Use smarter list behavior
                    smartypants: true,     // Use smart typography
                    xhtml: false           // Don't close void elements with />
                });
                
                // Add a safety check
                try {
                    textContainer.innerHTML = marked.parse(text);
                    
                    // Apply syntax highlighting to code blocks if needed
                    if (window.Prism) {
                        Prism.highlightAllUnder(textContainer);
                    }
                } catch (error) {
                    console.error('Error parsing markdown:', error);
                    // Fallback to basic formatting
                    textContainer.innerHTML = text.replace(/\n/g, '<br>');
                }
                
                messageDiv.appendChild(textContainer);
            } else {
                // For user messages, keep as plain text
                const textP = document.createElement('p');
                textP.textContent = text;
                textP.style.margin = '0';
                messageDiv.appendChild(textP);
            }
        }
    
        // Add attachments if any
        if (attachments && attachments.length > 0) {
            // Your existing attachment code here
        }
    
        chatMessages.appendChild(messageDiv);
        
        // Ensure scroll to bottom after content is rendered
        setTimeout(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 0);
    }
        
    function handleFileUpload(event) {
        const files = Array.from(event.target.files);
        if (files.length === 0) return;
        
        // Store files for sending
        uploadedFiles = files;
        
        // Create preview
        const previewDiv = document.createElement('div');
        previewDiv.classList.add('file-preview');
        
        const title = document.createElement('p');
        title.textContent = `Files for RAG processing (${files.length}):`;
        previewDiv.appendChild(title);
        
        files.forEach(file => {
            const fileInfo = document.createElement('p');
            fileInfo.textContent = `${file.name} (${formatFileSize(file.size)})`;
            previewDiv.appendChild(fileInfo);
        });
        
        // Add remove button
        const removeBtn = document.createElement('button');
        removeBtn.textContent = 'Remove';
        removeBtn.addEventListener('click', () => {
            previewDiv.remove();
            uploadedFiles = [];
            fileUpload.value = '';
        });
        previewDiv.appendChild(removeBtn);
        
        document.querySelector('.input-area').insertBefore(previewDiv, document.querySelector('.message-input-container'));
    }
    
    function handleImageUpload(event) {
        const images = Array.from(event.target.files);
        if (images.length === 0) return;
        
        // Store images for sending
        uploadedImages = images;
        
        // Create preview
        const previewDiv = document.createElement('div');
        previewDiv.classList.add('image-preview');
        
        const title = document.createElement('p');
        title.textContent = `Images for vision processing (${images.length}):`;
        previewDiv.appendChild(title);
        
        const thumbnailsDiv = document.createElement('div');
        thumbnailsDiv.style.display = 'flex';
        thumbnailsDiv.style.flexWrap = 'wrap';
        
        images.forEach(image => {
            const thumbnail = document.createElement('img');
            thumbnail.src = URL.createObjectURL(image);
            thumbnail.classList.add('thumbnail');
            thumbnailsDiv.appendChild(thumbnail);
        });
        
        previewDiv.appendChild(thumbnailsDiv);
        
        // Add remove button
        const removeBtn = document.createElement('button');
        removeBtn.textContent = 'Remove';
        removeBtn.addEventListener('click', () => {
            previewDiv.remove();
            uploadedImages = [];
            imageUpload.value = '';
        });
        previewDiv.appendChild(removeBtn);
        
        document.querySelector('.input-area').insertBefore(previewDiv, document.querySelector('.message-input-container'));
    }
    
    function toggleRecording() {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    }
    
    function startRecording() {
        isRecording = true;
        micButton.classList.add('recording');
        micButton.querySelector('.icon').textContent = '⏹️';
        
        // Show recording status to user
        addMessageToChat('system', 'Recording started...');
        
        // Make a request to start recording on the server
        fetch('/api/start-recording', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            console.log("Recording started:", data);
        })
        .catch(error => {
            console.error('Error starting recording:', error);
            addMessageToChat('system', 'Error starting recording. Please try again.');
            stopRecording();
        });
    }
    
    function stopRecording() {
        if (isRecording) {
            isRecording = false;
            micButton.classList.remove('recording');
            micButton.querySelector('.icon').textContent = '🎤';
            
            // Show loading indicator
            const loadingId = showLoadingIndicator();
            
            // Make a request to stop recording and get transcription
            fetch('/api/stop-recording', {
            method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
            removeLoadingIndicator(loadingId);
            if (data.transcription) {
                // Add user message to chat
                addMessageToChat('user', data.transcription);
                
                // Prepare data for API request
                const requestData = {
                model: selectedModel,
                message: data.transcription
                };
                
                // Show loading indicator for LLM response
                const llmLoadingId = showLoadingIndicator();
                
                // Make API request directly with fetch
                fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
                })
                .then(response => {
                if (!response.ok) {
                    return response.text().then(text => {
                    throw new Error(`HTTP error! status: ${response.status}, message: ${text}`);
                    });
                }
                return response.json();
                })
                .then(data => {
                // Remove loading indicator
                removeLoadingIndicator(llmLoadingId);
                // Add AI response to chat
                addMessageToChat('ai', data.text);
                })
                .catch(error => {
                console.error('Error:', error);
                removeLoadingIndicator(llmLoadingId);
                addMessageToChat('ai', 'Sorry, there was an error processing your request: ' + error.message);
                });
            } else {
                addMessageToChat('system', 'No transcription received. Please try again.');
            }
            })
            .catch(error => {
            console.error('Error stopping recording:', error);
            removeLoadingIndicator(loadingId);
            addMessageToChat('system', 'Error processing audio. Please try again.');
            });
        }
    }          
    
    function processAudio(audioBlob) {
        // Show loading indicator
        const loadingId = showLoadingIndicator();
        
        // Create form data for API request
        const formData = new FormData();
        formData.append('audio', audioBlob);
        formData.append('model', selectedModel);
        
        // Make API request to transcribe audio
        fetch('/api/transcribe', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            removeLoadingIndicator(loadingId);
            if (data.text) {
                messageInput.value = data.text;
                messageInput.focus();
            }
        })
        .catch(error => {
            console.error('Error transcribing audio:', error);
            removeLoadingIndicator(loadingId);
            alert('Error processing audio. Please try again.');
        });
    }
    
    function showLoadingIndicator() {
        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('message', 'ai-message', 'loading');
        loadingDiv.innerHTML = '<div class="loading-dots"><span></span><span></span><span></span></div>';
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return Date.now(); // Use timestamp as ID
    }
    
    function removeLoadingIndicator(id) {
        const loadingElement = document.querySelector('.loading');
        if (loadingElement) {
            loadingElement.remove();
        }
    }
    
    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' bytes';
        else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        else return (bytes / 1048576).toFixed(1) + ' MB';
    }

    function addMessageToChat(sender, text, attachments = []) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender === 'user' ? 'user-message' : 'ai-message');
        
        // Add text content
        if (text) {
          const textP = document.createElement('p');
          textP.textContent = text;
          messageDiv.appendChild(textP);
        }
        
        // Add attachments if any
        // [your existing attachment code]
        
        chatMessages.appendChild(messageDiv);
        
        // Ensure scroll to bottom
        setTimeout(() => {
          chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 10); // Small delay to ensure content is rendered
    }
/*
    function adjustMessageSize() {
        const messages = document.querySelectorAll('.message');
        messages.forEach(message => {
          // Reset any previously set max-height
          message.style.maxHeight = '';
          
          // Check if content is larger than visible area
          const isOverflowing = message.scrollHeight > message.clientHeight;
          
          if (isOverflowing) {
            // Set a reasonable max-height and enable scrolling for extremely long messages
            message.style.maxHeight = '80vh';
            message.style.overflowY = 'auto';
          }
        });
    }
      
    // Call this after adding a new message
    function addMessageToChat(sender, text, attachments = []) {
        // Existing code...
        chatMessages.appendChild(messageDiv);
        adjustMessageSize();
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
*/
    // Add CSS for loading animation
    const style = document.createElement('style');
    style.textContent = `
        .loading-dots {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 4px;
        }
        
        .loading-dots span {
            width: 8px;
            height: 8px;
            background-color: #888;
            border-radius: 50%;
            animation: pulse 1.5s infinite ease-in-out;
        }
        
        .loading-dots span:nth-child(2) {
            animation-delay: 0.5s;
        }
        
        .loading-dots span:nth-child(3) {
            animation-delay: 1s;
        }
        
        @keyframes pulse {
            0%, 100% {
                transform: scale(1);
                opacity: 0.5;
            }
            50% {
                transform: scale(1.5);
                opacity: 1;
            }
        }
        
        .recording {
            background-color: #ff4d4d !important;
            color: white !important;
        }
    `;
    document.head.appendChild(style);
    
    // Log that script has loaded
    console.log("Chat interface script loaded successfully");
});
