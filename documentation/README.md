# Mercury AI Assistant - Documentation

This directory contains comprehensive documentation for the Mercury AI Assistant project.

## Documentation Files

### Setup & Configuration
- **[NEMOTRON_DEPLOYMENT.md](./NEMOTRON_DEPLOYMENT.md)** ⭐ Comprehensive Nemotron 49B FP4 deployment guide
  - Standard (~91GB) and memory-optimized (~66GB VRAM) deployment
  - Memory optimization parameters explained in detail
  - Multi-model deployment strategies
  - Production-ready configurations
  - Troubleshooting guide
  - Integration with Mercury Agent

- **[TEXT_TO_IMAGE_DEPLOYMENT.md](./TEXT_TO_IMAGE_DEPLOYMENT.md)** 🎨 NEW - Text-to-Image generation
  - Stable Diffusion 3.5 Large deployment (~30GB VRAM)
  - API reference and usage examples
  - Prompt engineering tips
  - Multi-model deployment with Nemotron 49B
  - Docker network isolation explained
  - Future Mercury Agent integration plans

- **[VOICE_INPUT_SETUP.md](./VOICE_INPUT_SETUP.md)** - Complete guide for voice I/O
  - Parakeet ASR (Speech-to-Text) deployment (~2-4GB VRAM)
  - Magpie TTS (Text-to-Speech) deployment (~4-6GB VRAM)
  - Prerequisites and system requirements
  - Docker and NGC setup
  - Troubleshooting guide

- **[RAG Configuration Guide](../CONFIGURATION_GAPS.md)** - RAG Blueprint integration
  - NVIDIA RAG Blueprint deployment
  - Configuration differences from official blueprint
  - Local vs hybrid deployment options
  - Integration with Mercury Agent
  - Document ingestion workflow

### Release Notes
- **[RELEASE_v1.2.md](./RELEASE_v1.2.md)** - Version 1.2 release notes (Current)
  - Full voice-to-voice conversation support
  - Parakeet 0.6B ASR + Magpie TTS integration
  - GPU memory optimization
  
- **[MODERNIZATION_SUMMARY.md](./MODERNIZATION_SUMMARY.md)** - Version 1.1 release notes
  - NVIDIA NAT v1.3.0 upgrade from AgentIQ v1.0.0
  - Initial voice input implementation
  - Complete migration guide

### Development
- **[DEVELOPMENT_LOG.md](./DEVELOPMENT_LOG.md)** - Development history and technical decisions
  - Component design rationale
  - Implementation notes
  - Evolution of the Mercury Agent

## Quick Links

### Main Documentation
- [Root README](../README.md) - Project overview and quick start
- [Mercury Agent README](../mercury_agent/README.md) - Agent-specific documentation
- [Mercury Interface README](../mercury_interface/README.md) - Web interface documentation

### External Resources

#### Core Frameworks
- [NVIDIA NeMo Agent Toolkit (NAT)](https://docs.nvidia.com/nat/)
- [NVIDIA RAG Blueprint](https://build.nvidia.com/nvidia/build-an-enterprise-rag-pipeline)
- [RAG Deployment Reference](https://github.com/stanicm/rag)

#### Models
- [Nemotron 49B FP4](https://build.nvidia.com/nvidia/llama-3_3-nemotron-super-49b-v1_5) - Flagship LLM (66-91GB VRAM)
- [Stable Diffusion 3.5 Large](https://build.nvidia.com/stabilityai/stable-diffusion-3-5-large) - Text-to-Image (~30GB VRAM)
- [Parakeet 0.6B ASR](https://build.nvidia.com/nvidia/parakeet-ctc-0_6b-asr) - Speech-to-Text (~2-4GB VRAM)
- [Magpie TTS](https://build.nvidia.com/nvidia/magpie-tts-multilingual) - Text-to-Speech (~4-6GB VRAM)

## Version History

| Version | Date | Key Features |
|---------|------|--------------|
| v1.4 | Nov 13, 2025 | Stable Diffusion 3.5 Large support, Text-to-image generation, Documentation updates |
| v1.3 | Nov 4, 2025 | Nemotron 49B FP4 support, RAG Blueprint integration, Memory optimizations |
| v1.2 | Nov 1, 2025 | Voice-to-voice (ASR + TTS), Parakeet 0.6B, Magpie TTS |
| v1.1 | Oct 31, 2025 | NAT v1.3.0 upgrade, Initial voice input, Parakeet 1.1B |
| v1.0 | Earlier | Initial release with AgentIQ v1.0.0 |

## Current Deployment Configuration

**Active LLM:** Nemotron 49B FP4 (Memory-optimized)
- VRAM Usage: ~66GB
- Port: 8999
- Context: 65K tokens
- Quantization: FP4

**Text-to-Image:** Stable Diffusion 3.5 Large
- VRAM Usage: ~30GB
- Port: 8000
- Output: 1024x1024 JPEG
- Status: Experimental (text2image branch)

**RAG Pipeline:** Fully deployed with:
- Vector Database: Milvus (459 entities)
- Document Extraction: Local NIMs (Page, Table, Chart extraction)
- Embedding: Local 1B NIM (~3GB VRAM)
- Reranking: Local 1B NIM (~3GB VRAM)
- OCR: NVIDIA API (cloud)
- Frontend: http://localhost:8090

**Total VRAM Usage (with SD 3.5 Large):** ~96GB (multi-modal deployment)

