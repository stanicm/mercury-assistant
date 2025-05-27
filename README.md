# Mercury AI Assistant

![Mercury Banner](mercury_interface/public/Mercury_banner.jpg)

Mercury is an AI assistant built using the NVIDIA AIQ Toolkit, NVIDIA RAG Blueprint*, NVIDIA RIVA and running NVIDIA NIM-deployed models that combines multiple frameworks (LangChain, LlamaIndex, and Haystack) to provide a versatile prototyping/learning platform. It consists of two main components that can be used independently or together:

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

*Note that the RAG setup in the Mercury agent is set up such that it expects a rag server up and running on port 8081. The RAG Blueprint from NVIDIA is not a part of this repository for now, so if you would like to set the RAG up, we would direct you to the following page: https://build.nvidia.com/nvidia/build-an-enterprise-rag-pipeline

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

### System Requirements
- Python 3.12 or higher (required for Mercury Agent; developed using 3.12.7)
- Node.js 20.x or higher (for Mercury Interface)

  #### Ubuntu/Debian
   ```bash
   # 1. Update your package list:
   sudo apt update

   # 2. Install Node.js and npm using NodeSource:
   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
   sudo apt-get install -y nodejs

   # 3. Verify the installation:
   node --version
   npm --version
   ```
   
  #### macOS (using Homebrew)
  ```bash
  brew install node@20
  ```
  
  #### Windows - NOT TESTED
  ```bash
  #### Download and install from https://nodejs.org/
  ```
  
- NVIDIA API Key for LLM access

### Required Python Packages
1. AIQ Toolkit and LangChain integration:
   ```bash
   pip install agentiq
   pip install 'agentiq[langchain]'  # Installs AIQ with LangChain integration
   ```

2. Additional Python dependencies:
   ```bash
   pip install langchain llama-index haystack
   ```

3. Mercury Agent specific dependencies:
   ```bash
   pip install arxiv~=2.1.3 colorama~=0.4.6 markdown-it-py~=3.0 nvidia-haystack==0.1.2 wikipedia~=1.4.0
   ```

### Installing NVIDIA Riva Client, Sox and Prerequisites

For speech recognition functionality, you'll need to install the NVIDIA Riva client and its prerequisites and make sure you have the necessary NVIDIA API keys configured in your environment.:

1. Install PortAudio development files:
   ```bash
   sudo apt-get install portaudio19-dev
   ```

2. Install PyAudio:
   ```bash
   pip install pyaudio
   ```

3. Install NVIDIA Riva client:
   ```bash
   pip install nvidia-riva-client
   ```
   
- Sox for audio recording (required for voice input in Mercury Interface) - required for the microphone recording feature. The server uses Sox to record audio in the correct format (16-bit WAV, mono channel, 16kHz sample rate) for the Parakeet ASR service.

  
  #### Ubuntu/Debian
  ```bash
  sudo apt-get install sox
  ```

  #### macOS (using Homebrew)
  ```bash
  brew install sox
  ```

  #### Windows - NOT TESTED
  ```bash
  # Download and install from https://sourceforge.net/projects/sox/
  ```
  
## Deployment Notes

When deploying this application to different environments, consider the following potential path modifications:

- **Node.js and Sox Installation**: Ensure that the paths for Node.js and Sox are correctly set in your environment. Adjust the installation commands if necessary.
- **NVIDIA Riva Client**: The path to the NVIDIA Riva client may need to be updated based on your installation location. Check the `server.js` file for any hardcoded paths.
- **API Keys**: Make sure your API keys are properly exported as environment variables.
- **Output File Paths**: Verify that the output file paths (e.g. where sox stores its .wav file before sending it to the ASR model) in the code are suitable for your environment, especially if using a different operating system.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/stanicm/mercury-assistant.git
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

### Optional: Text-to-Speech Setup

Mercury Interface supports text-to-speech capabilities using NVIDIA's Magpie TTS Multilingual model. This is an optional feature that requires additional setup:

1. Set up NVIDIA NGC API key for container registry access:
   ```bash
   export NGC_API_KEY="your-ngc-api-key-here"
   ```

2. Authenticate with NVIDIA Container Registry:
   ```bash
   echo "$NGC_API_KEY" | docker login nvcr.io --username '$oauthtoken' --password-stdin
   ```

3. Deploy magpie-tts-multilingual model using Docker:
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

For more details about the Magpie TTS model, visit: https://build.nvidia.com/nvidia/magpie-tts-multilingual/deploy

**Features:**
- Toggle between text and audio output
- Automatic audio playback for AI responses
- Support for multiple voices
- High-quality multilingual speech synthesis 
