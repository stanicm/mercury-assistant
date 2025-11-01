# Mercury AI Assistant - Documentation

This directory contains comprehensive documentation for the Mercury AI Assistant project.

## Documentation Files

### Setup & Configuration
- **[VOICE_INPUT_SETUP.md](./VOICE_INPUT_SETUP.md)** - Complete guide for setting up voice input (Parakeet ASR) and voice output (Magpie TTS)
  - Prerequisites and system requirements
  - Docker and NGC setup
  - ASR and TTS deployment instructions
  - Troubleshooting guide

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
- [NVIDIA NeMo Agent Toolkit (NAT)](https://docs.nvidia.com/nat/)
- [Parakeet 0.6B ASR](https://build.nvidia.com/nvidia/parakeet-ctc-0_6b-asr)
- [Magpie TTS](https://build.nvidia.com/nvidia/magpie-tts-multilingual)
- [Nemotron Nano 9B](https://build.nvidia.com/nvidia/nvidia-nemotron-nano-9b-v2)

## Version History

| Version | Date | Key Features |
|---------|------|--------------|
| v1.2 | Nov 1, 2025 | Voice-to-voice (ASR + TTS), Parakeet 0.6B, Magpie TTS |
| v1.1 | Oct 31, 2025 | NAT v1.3.0 upgrade, Initial voice input, Parakeet 1.1B |
| v1.0 | Earlier | Initial release with AgentIQ v1.0.0 |

