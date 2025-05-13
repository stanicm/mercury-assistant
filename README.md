# Mercury AI Assistant

Mercury is an AI assistant built using the NVIDIA AIQ Toolkit, NVIDIA RAG Blueprint, NVIDIA RIVA and running NVIDIA NIM-deployed models that combines multiple frameworks (LangChain, LlamaIndex, and Haystack) to provide a versatile prototyping/learning platform. It consists of two main components that can be used independently or together:

1. **Mercury Agent**: An agentic backend system (based on NVIDIA's Agent Intelligence Toolkit) that provides:
   - Wikipedia-based research capabilities
   - Document retrieval and RAG (Retrieval-Augmented Generation)
   - Chit-chat functionality
   - Multi-agent architecture for intelligent task routing

2. **Mercury Interface**: A web-based frontend that provides:
   - User-friendly chat interface
   - Voice input capabilities
   - Support for multiple AI models (single LLMs)
   - Real-time response streaming

## Component Usage

### Using Mercury Agent Alone
The Mercury Agent can be used independently as a command-line tool for:
- Research queries using Wikipedia
- Document retrieval from local files
- General conversation
- Integration into other applications

### Using Mercury Interface Alone
The Mercury Interface can be used independently with:
- NVIDIA models
- Any other compatible LLM service

### Using Both Together
When used together, Mercury Interface provides a user-friendly way to access all Mercury Agent capabilities:
- Seamless integration of research and retrieval workflows
- Voice input support
- Real-time response streaming
- Markdown formatting support

## Prerequisites

### Common Requirements
- Python 3.10 or higher
- NVIDIA API Key for LLM access

### Mercury Agent Requirements
- AIQ Toolkit (installed from NVIDIA's package repository)
- LangChain, LlamaIndex, and Haystack packages

### Mercury Interface Requirements
- Node.js 20.x or higher
- Sox for audio recording
- NVIDIA Riva client for speech recognition

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/mercury-assistant.git
   cd mercury-assistant
   ```

2. Install Mercury Agent:
   ```bash
   cd mercury_agent
   pip install -e .
   ```

3. Install Mercury Interface:
   ```bash
   cd ../mercury_interface
   npm install
   ```

4. Configure environment variables:
   ```bash
   export NVIDIA_API_KEY="your-api-key"
   export OPENAI_API_KEY="your-openai-api-key"  # Optional, for OpenAI models
   ```

## Usage

### Using Mercury Agent
```bash
cd mercury_agent
aiq run --config_file=configs/config.yml --input "your question here"
```

### Using Mercury Interface
```bash
cd mercury_interface
node server.js
```
Then open your browser to http://localhost:5000

### Using Both Together
1. Start the Mercury Interface as above
2. Select "Mercury Agent" from the model dropdown
3. Use the interface to interact with all Mercury Agent capabilities

## Project Structure

- `mercury_agent/`: Backend agent system
  - `configs/`: Configuration files
  - `src/`: Source code for agent workflows
  - `data/`: Local documentation for RAG

- `mercury_interface/`: Web-based frontend
  - `public/`: Frontend assets
  - `server.js`: Backend server
  - `riva_python_client/`: Speech recognition client

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details. 
