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