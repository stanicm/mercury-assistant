# Mercury AI Assistant - Version 1.2 Release Notes

**Release Date**: November 1, 2025

## 🎉 What's New in v1.2

### Full Voice-to-Voice Conversation Support

Mercury now supports complete speech-to-speech interaction with locally deployed NVIDIA NIMs:

**Voice Input (ASR)**
- ✅ **Parakeet 0.6B ASR** deployed on ports 9000 (HTTP) / 50051 (gRPC)
- VRAM usage: ~2-4GB
- Offline transcription mode for accurate speech-to-text
- Browser-based audio capture with FFmpeg conversion

**Voice Output (TTS)**
- ✅ **Magpie TTS Multilingual** deployed on ports 9001 (HTTP) / 50052 (gRPC)
- VRAM usage: ~4-6GB
- 40+ voices across EN-US, ES-US, FR-FR
- Emotional voice variants (Happy, Calm, Angry, Fearful, etc.)
- Default voice: Diego (Happy)

### Infrastructure Improvements

**GPU Memory Optimization**
- Successfully running 3 models simultaneously on single GPU:
  - Nemotron Nano 9B: ~88GB (LLM)
  - Parakeet 0.6B ASR: ~2-4GB (Speech-to-Text)
  - Magpie TTS: ~4-6GB (Text-to-Speech)
- Total VRAM usage: ~96GB on Blackwell Max-Q GPU

**Server Updates**
- Updated `server.js` to use offline transcription script for Parakeet 0.6B
- Transcription output parsing for offline script format
- TTS endpoint configured for Magpie on port 50052
- Improved error handling for audio processing

## 📋 Complete Feature Set

### Core Capabilities
- 🎤 **Voice Input**: Browser-based microphone capture → Parakeet ASR
- 🧠 **AI Processing**: Intelligent routing to specialized agents
  - Research Agent: Wikipedia search + summarization
  - RAG Agent: SPH documentation retrieval
  - Chitchat Agent: General conversation
- 🔊 **Voice Output**: Magpie TTS with multilingual voices
- 💬 **Text Chat**: Full keyboard-based interaction
- 🎯 **Reasoning Filtering**: Clean answers with reasoning stored in buffer

### Agent Intelligence
- Smart query classification (Research/Retrieve/General)
- Reasoning trace extraction and storage
- Context-aware response generation
- Multi-agent collaboration

### Browser Interface
- Modern, responsive UI
- Microphone and speaker controls
- Real-time transcription
- TTS audio playback
- Model selection (Mercury Agent, Nemotron, NIM LLM, etc.)

## 🔄 Changes from v1.1

### Added
- Magpie TTS Multilingual integration
- Voice output support in browser interface
- Offline transcription mode for ASR

### Changed
- Upgraded from Parakeet 1.1B to Parakeet 0.6B ASR (lower VRAM)
- Updated transcription pipeline to use offline script
- Modified TTS configuration to use port 50052
- Changed default TTS voice to Diego (Happy)

### Documentation
- Updated README.md with Parakeet 0.6B and Magpie TTS setup
- Enhanced VOICE_INPUT_SETUP.md with both ASR and TTS instructions
- Added VRAM usage estimates for all models

## 🚀 Getting Started

### Quick Setup

1. **Deploy Parakeet 0.6B ASR**:
```bash
docker run -d --rm --name=parakeet-asr-0.6b \
    --gpus all --shm-size=8GB \
    -e NGC_API_KEY \
    -e NIM_HTTP_API_PORT=9000 \
    -e NIM_GRPC_API_PORT=50051 \
    -p 9000:9000 -p 50051:50051 \
    nvcr.io/nim/nvidia/parakeet-ctc-0.6b-asr:latest
```

2. **Deploy Magpie TTS**:
```bash
docker run -d --rm --name=magpie-tts-multilingual \
    --gpus all --shm-size=8GB \
    -e NGC_API_KEY \
    -e NIM_HTTP_API_PORT=9001 \
    -e NIM_GRPC_API_PORT=50052 \
    -p 9001:9001 -p 50052:50052 \
    nvcr.io/nim/nvidia/magpie-tts-multilingual:latest
```

3. **Start Mercury**:
```bash
cd mercury_interface
node server.js
```

4. **Access via browser**:
   - Local: `http://localhost:5000`
   - Remote: Use SSH tunnel (see docs)

## 📊 System Requirements

### Hardware
- NVIDIA GPU with CUDA support
- Minimum 96GB VRAM for full voice-to-voice setup
- Tested on: NVIDIA RTX PRO 6000 Blackwell Max-Q

### Software
- Docker with NVIDIA Container Toolkit
- NGC API key
- NVIDIA NeMo Agent Toolkit (NAT) v1.3.0
- Node.js (for web interface)
- Python 3.12+ (for agents)

## 🔗 Resources

- **Parakeet 0.6B ASR**: https://build.nvidia.com/nvidia/parakeet-ctc-0_6b-asr
- **Magpie TTS**: https://build.nvidia.com/nvidia/magpie-tts-multilingual
- **Nemotron Nano 9B**: https://build.nvidia.com/nvidia/nvidia-nemotron-nano-9b-v2
- **NVIDIA NAT**: https://docs.nvidia.com/nat/

## 🙏 Acknowledgments

Built with:
- NVIDIA NeMo Agent Toolkit (NAT)
- NVIDIA NIMs (Parakeet, Magpie, Nemotron)
- LangChain & Haystack frameworks
- NVIDIA RAG Blueprint

---

**Previous Releases**: [v1.1](./MODERNIZATION_SUMMARY.md) - NAT v1.3.0 upgrade with voice input

