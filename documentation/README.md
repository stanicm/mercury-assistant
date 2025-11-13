# Mercury AI Assistant - Documentation

This directory contains comprehensive documentation for the Mercury AI Assistant project.

## Documentation Files

### Setup & Configuration
- **[NEMOTRON_DEPLOYMENT.md](./NEMOTRON_DEPLOYMENT.md)** ⭐ Comprehensive Nemotron deployment guide
  - **Nemotron Nano 9B**: Standard (~88GB) and optimized (~65GB VRAM)
  - **Nemotron 49B FP4**: Standard (~91GB) and optimized (~66GB VRAM) deployment
  - Memory optimization parameters explained in detail
  - Model comparison table and performance metrics
  - Multi-model deployment strategies
  - Production-ready configurations
  - Troubleshooting guide

- **[VOICE_INPUT_SETUP.md](./VOICE_INPUT_SETUP.md)** - Complete guide for voice I/O
  - Parakeet ASR (Speech-to-Text) deployment
  - Magpie TTS (Text-to-Speech) deployment
  - Prerequisites and system requirements
  - Docker and NGC setup
  - Troubleshooting guide

- **[RAG Configuration Guide](../CONFIGURATION_GAPS.md)** ⭐ NEW - RAG Blueprint integration
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
- [Nemotron Nano 9B](https://build.nvidia.com/nvidia/nvidia-nemotron-nano-9b-v2) - Lightweight LLM
- [Nemotron 49B FP4](https://build.nvidia.com/nvidia/llama-3_3-nemotron-super-49b-v1_5) - Flagship LLM
- [Parakeet 0.6B ASR](https://build.nvidia.com/nvidia/parakeet-ctc-0_6b-asr) - Speech-to-Text
- [Magpie TTS](https://build.nvidia.com/nvidia/magpie-tts-multilingual) - Text-to-Speech

## Version History

| Version | Date | Key Features |
|---------|------|--------------|
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

**RAG Pipeline:** Fully deployed with:
- Vector Database: Milvus (459 entities)
- Document Extraction: Local NIMs (Page, Table, Chart extraction)
- Embedding: Local 1B NIM (~3GB VRAM)
- Reranking: Local 1B NIM (~3GB VRAM)
- OCR: NVIDIA API (cloud)
- Frontend: http://localhost:8090

**Total VRAM Usage:** ~72GB (95% local deployment)

