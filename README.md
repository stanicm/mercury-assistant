# Mercury AI Assistant

![Mercury Banner](mercury_interface/public/Mercury_banner.jpg)

Mercury is an AI assistant built using the NVIDIA NeMo Agent Toolkit (NAT), NVIDIA RAG Blueprint*, NVIDIA RIVA and running NVIDIA NIM-deployed models that combines multiple frameworks (LangChain, LlamaIndex, and Haystack) to provide a versatile prototyping/learning platform. It consists of two main components that can be used independently or together:

1. **Mercury Agent**: An agentic backend system (based on NVIDIA's NeMo Agent Toolkit) that provides:
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
1. NVIDIA NeMo Agent Toolkit (NAT) and framework integrations:
   ```bash
   pip install nvidia-nat nvidia-nat-langchain nvidia-nat-llama-index
   ```

2. Mercury Agent specific dependencies:
   ```bash
   pip install arxiv~=2.1.3 colorama~=0.4.6 markdown-it-py~=3.0 nvidia-haystack==0.1.2 wikipedia~=1.4.0
   ```

### Installing NVIDIA Riva Client and Audio Tools

For speech recognition functionality, you'll need to install the NVIDIA Riva client and audio processing tools:

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

4. Install FFmpeg (required for browser audio conversion):
   
   #### Ubuntu/Debian
   ```bash
   sudo apt-get install ffmpeg
   ```

   #### macOS (using Homebrew)
   ```bash
   brew install ffmpeg
   ```

   #### Windows - NOT TESTED
   ```bash
   # Download and install from https://ffmpeg.org/download.html
   ```

**Note:** Mercury Interface uses **browser-based audio capture** (via JavaScript MediaRecorder API), so no client-side audio tools are needed. The browser captures audio from your microphone and sends it to the server, where FFmpeg converts it to WAV format for transcription.
  
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
nat run --config_file=configs/config.yml --input "your question here"
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

### Optional: Voice Input Setup (Speech-to-Text)

Mercury Interface supports voice input using NVIDIA's Parakeet ASR model. This is an optional feature that requires:

1. **NVIDIA Container Toolkit** installed (for Docker GPU access)
2. **NGC API Key** for accessing the Parakeet ASR NIM
3. **Browser requirements**: HTTPS or localhost access for microphone permissions

#### Step 1: Set up NGC API Key and Docker authentication

```bash
export NGC_API_KEY="your-ngc-api-key-here"
echo "$NGC_API_KEY" | docker login nvcr.io --username '$oauthtoken' --password-stdin
```

#### Step 2: Deploy Parakeet 0.6B ASR NIM

**Recommended:** Parakeet 0.6B for lower VRAM usage (~2-4GB):

```bash
docker run -d --rm --name=parakeet-asr-0.6b \
    --gpus all \
    --shm-size=8GB \
    -e NGC_API_KEY \
    -e NIM_HTTP_API_PORT=9000 \
    -e NIM_GRPC_API_PORT=50051 \
    -p 9000:9000 \
    -p 50051:50051 \
    nvcr.io/nim/nvidia/parakeet-ctc-0.6b-asr:latest
```

Wait for the message: `{"status":"ready"}` when checking `http://localhost:9000/v1/health/ready`

For more details: https://build.nvidia.com/nvidia/parakeet-ctc-0_6b-asr

#### Step 3: Deploy Nemotron Nano 9B LLM (Required for Mercury Agent)

**Standard deployment (~88GB VRAM)**:

```bash
docker run -d --rm --name=nemotron-nano-9b \
    --gpus all \
    --shm-size=16GB \
    -e NGC_API_KEY \
    -p 8000:8000 \
    nvcr.io/nim/nvidia/nvidia-nemotron-nano-9b-v2:latest
```

**Memory-optimized deployment (~65GB VRAM)** - Recommended for GPUs with limited VRAM:

```bash
docker run -d --rm --name=nemotron-nano-9b \
    --gpus all \
    --shm-size=16GB \
    -e NGC_API_KEY \
    -e NIM_MAX_BATCH_SIZE=1 \
    -e NIM_MAX_MODEL_LEN=4096 \
    -e NIM_KVCACHE_PERCENT=0.6 \
    -e NIM_LOW_MEMORY_MODE=1 \
    -e NIM_KV_CACHE_HOST_MEM_FRACTION=0.6 \
    -p 8000:8000 \
    nvcr.io/nim/nvidia/nvidia-nemotron-nano-9b-v2:latest
```

**Memory optimization saves 23GB VRAM** (88GB → 65GB) using:
- `NIM_MAX_BATCH_SIZE=1`: Single request processing
- `NIM_MAX_MODEL_LEN=4096`: Reduced sequence length
- `NIM_KVCACHE_PERCENT=0.6`: 60% memory for KV cache
- `NIM_LOW_MEMORY_MODE=1`: Low memory optimizations
- `NIM_KV_CACHE_HOST_MEM_FRACTION=0.6`: Host memory for KV cache

Wait for initialization. Check status at `http://localhost:8000/v1/health/ready`

For more details: 
- Model page: https://build.nvidia.com/nvidia/nvidia-nemotron-nano-9b-v2
- Detailed deployment guide: [documentation/NEMOTRON_DEPLOYMENT.md](./documentation/NEMOTRON_DEPLOYMENT.md)

#### Step 4: Deploy Magpie TTS NIM (Optional)

For text-to-speech output with 40+ multilingual voices:

```bash
docker run -d --rm --name=magpie-tts-multilingual \
    --gpus all \
    --shm-size=8GB \
    -e NGC_API_KEY \
    -e NIM_HTTP_API_PORT=9001 \
    -e NIM_GRPC_API_PORT=50052 \
    -p 9001:9001 \
    -p 50052:50052 \
    nvcr.io/nim/nvidia/magpie-tts-multilingual:latest
```

Wait for initialization (may take several minutes). Check status at `http://localhost:9001/v1/health/ready`

For more details: https://build.nvidia.com/nvidia/magpie-tts-multilingual

#### Step 5: Browser Access for Microphone

Modern browsers (Chrome, Firefox, Edge) require **HTTPS** or **localhost** for microphone access due to security policies.

**Option A: Local Access (Simplest)**
If accessing from the server machine:
```
http://localhost:5000
```

**Option B: Remote Access via SSH Tunnel (Recommended)**
If accessing from a remote machine:

```bash
# On your client machine (Mac/Windows/Linux)
ssh -L 5000:localhost:5000 your-username@your-server-ip

# Then open in browser:
http://localhost:5000
```

Keep the SSH terminal open while using Mercury. The tunnel forwards the server's port 5000 to your local machine.

**Option C: HTTPS Setup**
Set up SSL certificates for proper HTTPS access (more complex, production-ready).

#### Features:
- 🎤 Browser-based audio capture (works from any device)
- 🔄 Automatic audio format conversion (WebM → WAV)
- 🌍 Multilingual support (23+ languages)
- ⚡ Real-time transcription via local Parakeet ASR

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

## 📚 Documentation

For detailed documentation, see the [documentation directory](./documentation/):

- **[Voice Setup Guide](./documentation/VOICE_INPUT_SETUP.md)** - Complete setup for voice input (ASR) and output (TTS)
- **[Release Notes v1.2](./documentation/RELEASE_v1.2.md)** - Latest release with full voice-to-voice support
- **[Modernization Summary](./documentation/MODERNIZATION_SUMMARY.md)** - NAT v1.3.0 upgrade details
- **[Development Log](./documentation/DEVELOPMENT_LOG.md)** - Development history and technical decisions

## 🔗 External Resources

- [NVIDIA NeMo Agent Toolkit](https://docs.nvidia.com/nat/)
- [Parakeet 0.6B ASR](https://build.nvidia.com/nvidia/parakeet-ctc-0_6b-asr)
- [Magpie TTS Multilingual](https://build.nvidia.com/nvidia/magpie-tts-multilingual)
- [Nemotron Nano 9B](https://build.nvidia.com/nvidia/nvidia-nemotron-nano-9b-v2)
- [NVIDIA RAG Blueprint](https://build.nvidia.com/nvidia/build-an-enterprise-rag-pipeline)
