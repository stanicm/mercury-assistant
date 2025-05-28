// Initialize video
document.addEventListener('DOMContentLoaded', function() {
    const video = document.getElementById('background-video');
    if (video) {
        // Function to switch videos randomly
        function switchVideo() {
            const videos = ['static_1F.mp4', 'static_2F.mp4'];
            const randomVideo = videos[Math.floor(Math.random() * videos.length)];
            video.src = `/videos/${randomVideo}`;
            video.play().catch(function(error) {
                console.log("Video autoplay failed:", error);
            });
        }

        // Switch video when the current one ends
        video.addEventListener('ended', switchVideo);

        // Initial video play
        video.play().catch(function(error) {
            console.log("Video autoplay failed:", error);
        });
    }
});

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
    const modelSelect = document.getElementById('modelSelect');
    const outputModeToggle = document.getElementById('outputModeToggle');
    const outputModeLabel = document.getElementById('outputModeLabel');
    
    console.log("Script loaded. Send button:", sendButton);
    
    // State variables
    let selectedModel = modelSelect.value;
    let uploadedFiles = [];
    let uploadedImages = [];
    let isRecording = false;
    let mediaRecorder = null;
    let audioChunks = [];
    let isSending = false;  // Add flag to prevent double sends
    
    // Event Listeners
    modelSelect.addEventListener('change', () => {
        selectedModel = modelSelect.value;
    });
    
    sendButton.addEventListener('click', sendMessage);
    
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
    
    outputModeToggle.addEventListener('change', function() {
        outputModeLabel.textContent = this.checked ? 'Audio Output' : 'Text Output';
    });
    
    // Functions
    function sendMessage() {
        if (isSending) return;
        
        const message = messageInput.value.trim();
        if (!message && uploadedFiles.length === 0 && uploadedImages.length === 0) return;
        
        isSending = true;
        
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
        
        // Make API request
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
            removeLoadingIndicator(loadingId);
            // Store the response text before adding it to chat
            const responseText = data.text;
            addMessageToChat('ai', responseText);
            
            // If audio output is enabled, generate TTS with only the latest response
            if (outputModeToggle.checked) {
                handleTTS(responseText);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            removeLoadingIndicator(loadingId);
            addMessageToChat('ai', 'Sorry, there was an error processing your request: ' + error.message);
        })
        .finally(() => {
            isSending = false;
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

    // Ensure marked library is included
    if (typeof marked === 'undefined') {
        console.error('Marked library is not loaded. Please include it in your HTML.');
    }

    // Function to display the response in a formatted way
    function displayResponse(response) {
        const responseElement = document.getElementById('response');
        const markdownContent = document.createElement('div');
        markdownContent.classList.add('markdown-content');
        markdownContent.innerHTML = marked.parse(response); // Use marked to render markdown
        responseElement.appendChild(markdownContent);
    }

    // Function to handle Text-to-Speech conversion and playback
    async function handleTTS(text) {
        try {
            // Ensure we're only processing the text we received
            const textToProcess = text.trim();
            console.log('Starting TTS request for text:', textToProcess);
            console.log('Text length in characters:', textToProcess.length);
            console.log('Text length in words:', textToProcess.split(/\s+/).length);
            
            // Make a POST request to the TTS endpoint
            const response = await fetch('/api/tts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: textToProcess,
                    voice: 'Magpie-Multilingual.ES-US.Diego.Happy'
                })
            });

            // Handle any errors from the TTS service
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.details || 'TTS request failed');
            }

            // Get the audio data as a blob
            // This blob contains the WAV audio data generated by the TTS service
            const audioBlob = await response.blob();
            console.log('Received audio blob:', audioBlob.size, 'bytes');
            
            // Validate the audio blob size
            // WAV files should be at least 1KB to contain valid audio data
            if (audioBlob.size < 1000) {
                throw new Error('Received audio data is too small to be valid');
            }

            // Create a URL for the audio blob
            // This URL can be used by the Audio API to play the sound
            const audioUrl = URL.createObjectURL(audioBlob);
            
            // Create a new Audio object for playback
            const audio = new Audio(audioUrl);
            
            // Add event listeners for debugging and cleanup
            audio.addEventListener('error', (e) => {
                console.error('Audio playback error:', e);
            });
            
            audio.addEventListener('playing', () => {
                console.log('Audio started playing');
            });
            
            audio.addEventListener('ended', () => {
                console.log('Audio playback completed');
                // Clean up the blob URL to prevent memory leaks
                URL.revokeObjectURL(audioUrl);
            });

            // Play the audio
            try {
                await audio.play();
                console.log('Audio play() called successfully');
            } catch (error) {
                console.error('Error playing audio:', error);
                throw error;
            }

        } catch (error) {
            console.error('Error in TTS:', error);
            // Show error message to user in the chat interface
            const errorMessage = document.createElement('div');
            errorMessage.className = 'message ai-message error';
            errorMessage.textContent = `Error generating speech: ${error.message}`;
            chatMessages.appendChild(errorMessage);
        }
    }
});
