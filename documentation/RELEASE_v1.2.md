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
  - Nemotron Nano 9B: ~65GB with optimization (standard: ~88GB)
  - Parakeet 0.6B ASR: ~2-4GB (Speech-to-Text)
  - Magpie TTS: ~4-6GB (Text-to-Speech)
- Total VRAM usage: ~73GB optimized (standard: ~96GB) on Blackwell Max-Q GPU
- **New**: Memory optimization parameters save 23GB for Nemotron Nano 9B

**Server Updates**
- Updated `server.js` to use offline transcription script for Parakeet 0.6B
- Transcription output parsing for offline script format
- TTS endpoint configured for Magpie on port 50052
- Improved error handling for audio processing
- **Fixed**: TTS audio truncation for long responses by reducing chunk size to avoid gRPC 4MB message limit
- Added comprehensive debugging logs for TTS chunking and sox audio combination

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

### Fixed
- TTS audio truncation for long responses (reduced chunk size from 1500 to 1000 chars)
- gRPC 4MB message limit causing silent failures in TTS generation
- First paragraph of long responses being cut off in audio output

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

3. **Deploy Nemotron Nano 9B (LLM)**:

**Standard deployment (~88GB VRAM)**:
```bash
docker run -d --rm --name=nemotron-nano-9b \
    --gpus all --shm-size=16GB \
    -e NGC_API_KEY \
    -p 8000:8000 \
    nvcr.io/nim/nvidia/nvidia-nemotron-nano-9b-v2:latest
```

**Memory-optimized deployment (~65GB VRAM)** - Recommended for memory-constrained GPUs:
```bash
docker run -d --rm --name=nemotron-nano-9b \
    --gpus all --shm-size=16GB \
    -e NGC_API_KEY \
    -e NIM_MAX_BATCH_SIZE=1 \
    -e NIM_MAX_MODEL_LEN=4096 \
    -e NIM_KVCACHE_PERCENT=0.6 \
    -e NIM_LOW_MEMORY_MODE=1 \
    -e NIM_KV_CACHE_HOST_MEM_FRACTION=0.6 \
    -p 8000:8000 \
    nvcr.io/nim/nvidia/nvidia-nemotron-nano-9b-v2:latest
```

**Memory Optimization Parameters:**
- `NIM_MAX_BATCH_SIZE=1`: Limits batch processing to single request
- `NIM_MAX_MODEL_LEN=4096`: Reduces maximum sequence length
- `NIM_KVCACHE_PERCENT=0.6`: Allocates 60% of available memory for KV cache
- `NIM_LOW_MEMORY_MODE=1`: Enables low memory optimizations
- `NIM_KV_CACHE_HOST_MEM_FRACTION=0.6`: Uses host memory for additional KV cache

These parameters reduce VRAM usage from ~88GB to ~65GB, saving 23GB.

4. **Start Mercury**:
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
- **Standard setup**: Minimum 96GB VRAM (Nemotron 88GB + Parakeet 2-4GB + Magpie 4-6GB)
- **Memory-optimized**: Minimum 73GB VRAM (Nemotron 65GB + Parakeet 2-4GB + Magpie 4-6GB)
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

