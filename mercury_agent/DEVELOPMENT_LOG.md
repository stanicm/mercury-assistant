# Mercury Agent Development Log
*Last Updated: May 7, 2025*

## Overview
This document summarizes the development journey of the Mercury Agent, a smart assistant that can answer questions using Wikipedia, handle general conversations, and search through documentation.

## Development Steps

### 1. Initial Project Setup (May 7, 2025)
- Copied the `multi_frameworks` example from `AgentIQ/examples` to `aiq/mercury`
- Renamed the project to `mercury_agent`
- Updated all references in the code to reflect the new name

**Key Files Modified:**
1. Updated import statements in all Python files to use `aiq_mercury_agent` instead of `multi_frameworks`
2. Updated configuration files to use the new module name

### 2. Wikipedia Search Integration
- Modified the research tool to use Wikipedia instead of web search
- Removed web search dependencies
- Added Wikipedia API integration

**Key Files Modified:**
1. `src/aiq_mercury_agent/langchain_research_tool.py`:
```python
async def wikipedia_search(query: str) -> str:
    """Search Wikipedia for information."""
    try:
        # Search Wikipedia
        search_results = wikipedia.search(query, results=1)
        if not search_results:
            return "No Wikipedia articles found."
        
        # Get the page content
        page = wikipedia.page(search_results[0])
        return f"Wikipedia Summary for '{page.title}':\n{page.summary}"
    except Exception as e:
        return f"Error searching Wikipedia: {str(e)}"
```

2. `pyproject.toml`:
```toml
[tool.poetry.dependencies]
wikipedia = "^1.4.0"  # Added Wikipedia package
```

### 3. Testing and Validation
- Tested the agent with various types of questions:
  - General knowledge questions (e.g., "What can you tell me about Spiderman?")
  - Technical questions (e.g., "What is quantum entanglement?")
  - Documentation queries

**Test Results:**
1. Spiderman Query Test:
```
Input: "What can you tell me about Spiderman?"
Result: Successfully provided detailed information about Spiderman's origin, powers, and history
```

2. Quantum Entanglement Test:
```
Input: "What is quantum entanglement in physics?"
Result: Successfully retrieved and presented information from Wikipedia
```

### 4. GitHub Repository Setup (May 7, 2025)
1. Created a new repository at https://github.com/stanicm/mercury_agent.git
2. Set up the project on GitHub:
   - Initialized git repository
   - Created `.gitignore` file
   - Added and committed all files
   - Pushed to GitHub

**Configuration Files:**
1. `configs/config.yml`:
```yaml
functions:
  llama_index_rag:
    _type: aiq_mercury_agent/llama_index_rag
    llm_name: nim_llm
    model_name: meta/llama-3.1-405b-instruct
    embedding_name: nim_embedder
    data_dir: /home/milos/aiq/aiq/mercury/README.md
  langchain_researcher_tool:
    _type: aiq_mercury_agent/langchain_researcher_tool
    llm_name: nim_llm
  haystack_chitchat_agent:
    _type: aiq_mercury_agent/haystack_chitchat_agent
    llm_name: meta/llama-3.1-405b-instruct
```

2. `.gitignore`:
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
.env
.venv
env/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

### 5. Successful Implementation Steps (May 8, 2025)
- **Adjusted Target Summary Length**: Modified the logic to dynamically set the target summary length based on whether a detail request was detected. This was implemented in `register.py`:
  ```python
  if is_detail_request:
      target_length = 1000
  else:
      target_length = 300
  ```

- **Implemented Retry Mechanism**: Added a retry mechanism for summaries shorter than 70% of the target length. This was done in `register.py`:
  ```python
  if len(summary.split()) < target_length * 0.7:
      retry_prompt = f"Generate a summary of exactly {target_length} words..."
      summary = await llm.ainvoke(retry_prompt)
  ```

- **Added Logging**: Introduced logging to track the generated summary length and any warnings. This was added in `register.py`:
  ```python
  logger.info(f"Generated summary length: {len(summary.split())} words")
  ```

- **Improved Error Handling**: Enhanced error handling for detail detection, defaulting to `is_detail_request = True` on error. This was implemented in `register.py`:
  ```python
  try:
      is_detail_request = await detail_detection.ainvoke(query)
  except Exception as e:
      logger.warning(f"Error in detail detection: {e}")
      is_detail_request = True
  ```

- **Enhanced Retry Prompt**: Updated the retry prompt to ensure complete sentences and paragraphs. This was done in `register.py`:
  ```python
  retry_prompt = f"Generate a summary of exactly {target_length} words, ensuring all sentences and paragraphs are complete."
  ```

- **Simplified Workflow**: Removed the retry logic and updated the summary prompt for clarity. This was implemented in `register.py`:
  ```python
  summary_prompt = f"Generate a summary of exactly {target_length} words..."
  ```

- **Updated README Files**: Added required dependencies and usage instructions to the README files. This was done in `README.md` and `mercury_interface/README.md`.

- **Committed and Pushed Changes**: Successfully committed and pushed all changes to the remote repository.

### 6. Text-to-Speech Setup (May 8, 2025)
- Set up NVIDIA NGC API key for container registry access:
  ```bash
  export NGC_API_KEY="your-ngc-api-key-here"
  ```

- Authenticated with NVIDIA Container Registry:
  ```bash
  echo "$NGC_API_KEY" | docker login nvcr.io --username '$oauthtoken' --password-stdin
  ```

- Deployed magpie-tts-multilingual model using Docker:
  ```bash
  docker run -it --rm --name=magpie-tts-multilingual \
      --runtime=nvidia \
      --gpus '"device=0"' \
      --shm-size=8GB \
      -e NGC_API_KEY=$NGC_API_KEY \
      -e NIM_HTTP_API_PORT=9000 \
      -e NIM_GRPC_API_PORT=50051 \
      -p 9000:9000 \
      -p 50051:50051 \
      nvcr.io/nim/nvidia/magpie-tts-multilingual:latest
  ```

**Configuration Details:**
- HTTP API accessible at: `http://localhost:9000`
- gRPC API accessible at: `localhost:50051`
- Container uses NVIDIA GPU runtime
- Allocated 8GB shared memory
- Exposed ports for both HTTP and gRPC communication

**Next Steps:**
1. Test TTS service functionality
2. Integrate TTS capabilities into Mercury Interface
3. Add voice output options to chat interface

### 7. Text-to-Speech Integration (May 9, 2025)
- Integrated NVIDIA RIVA Magpie TTS model with Mercury Interface
- Added TTS endpoint to server.js
- Implemented client-side audio playback
- Added error handling and logging

**Key Changes:**
1. Added TTS endpoint in `server.js`:
```javascript
app.post('/api/tts', async (req, res) => {
    const { text, voice } = req.body;
    // ... TTS implementation ...
});
```

2. Added client-side TTS handling in `script.js`:
```javascript
async function handleTTS(text) {
    // ... TTS client implementation ...
}
```

3. Added audio output toggle in the interface:
```html
<input type="checkbox" id="outputModeToggle">
<label for="outputModeToggle" id="outputModeLabel">Text Output</label>
```

**Configuration Details:**
- TTS service running on: `0.0.0.0:50051`
- Default voice: `Magpie-Multilingual.ES-US.Diego.Happy`
- Audio format: WAV (LINEAR_PCM)
- Sample rate: 16kHz

**Features:**
- Toggle between text and audio output
- Automatic audio playback for AI responses
- Error handling and user feedback
- Temporary file cleanup

**Next Steps:**
1. Add voice selection options
2. Implement audio caching
3. Add volume control
4. Support for more languages

## How to Use the Mercury Agent

### Basic Usage
1. Start the agent using the command: `aiq run --config_file configs/config.yml`
2. Type your question or request
3. The agent will automatically:
   - Determine the best way to answer your question
   - Search Wikipedia if it's a factual question
   - Have a casual conversation if it's a general question
   - Search documentation if it's about the project

### Example Questions
- "What can you tell me about Spiderman?" (General conversation)
- "What is quantum entanglement in physics?" (Wikipedia search)
- "How does this project work?" (Documentation search)

## Future Improvements
- Add more sources of information
- Improve response accuracy
- Add support for more languages
- Enhance the user interface

## Notes
- The agent is designed to be user-friendly and doesn't require technical knowledge to use
- All responses are based on reliable sources (Wikipedia, project documentation)
- The agent can handle a wide range of questions and topics

---
*This log will be updated as the project evolves.* 