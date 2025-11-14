# Nemotron 49B (Llama 3.3 Super) Deployment Guide

This guide covers deploying NVIDIA's Nemotron 49B FP4 model locally using Docker for use with Mercury AI Assistant.

## Model Overview

**Nemotron 49B (Llama 3.3 Super)** is NVIDIA's flagship 49-billion parameter language model with enhanced capabilities:
- Advanced reasoning with chain-of-thought
- Superior instruction following
- Extended context support (up to 128K)
- Available in FP4 quantization for reduced memory footprint
- Optimized for local deployment with memory-saving configurations

## Prerequisites

- NVIDIA GPU with CUDA support
- Docker with NVIDIA Container Toolkit installed
- NGC API key
- **VRAM Requirements**:
  - Minimum 66GB VRAM (memory-optimized deployment)
  - 91GB VRAM (standard deployment)
  - 95GB+ VRAM recommended for multi-model deployments

## Deployment Options

---

# Standard Deployment (~91GB VRAM)

Basic FP4 quantized deployment:

```bash
export NGC_API_KEY=<your-ngc-api-key>
export LOCAL_NIM_CACHE=~/.cache/nim
export NIM_MODEL_PROFILE='496a3bcf32f7c7e81e59b1c17395d49b6c412dcb9e94d1bd4675c7ab61ed4b8c'
export NIM_MANIFEST_ALLOW_UNSAFE=1

docker run -d --name nemotron-49b-fp4 \
    --gpus all \
    --shm-size=16GB \
    -e NGC_API_KEY \
    -e NIM_MANIFEST_ALLOW_UNSAFE \
    -e NIM_MODEL_PROFILE \
    -v "$LOCAL_NIM_CACHE:/opt/nim/.cache" \
    -u $(id -u) \
    -p 8999:8000 \
    nvcr.io/nim/nvidia/llama-3.3-nemotron-super-49b-v1.5:latest
```

**Characteristics:**
- Uses ~91GB VRAM
- Maximum performance with FP4 quantization
- Full 128K context window support
- Suitable for GPUs with >95GB VRAM

## Memory-Optimized Deployment (~66GB VRAM) ⭐ Recommended

Optimized for memory-constrained GPUs with 65K context:

```bash
export NGC_API_KEY=<your-ngc-api-key>
export LOCAL_NIM_CACHE=~/.cache/nim
export NIM_MODEL_PROFILE='496a3bcf32f7c7e81e59b1c17395d49b6c412dcb9e94d1bd4675c7ab61ed4b8c'
export NIM_MANIFEST_ALLOW_UNSAFE=1

docker run -d --name nemotron-49b-fp4-optimized \
    --gpus all \
    --shm-size=16GB \
    -e NGC_API_KEY \
    -e NIM_MANIFEST_ALLOW_UNSAFE \
    -e NIM_MODEL_PROFILE \
    -e NIM_MAX_BATCH_SIZE=1 \
    -e NIM_MAX_MODEL_LEN=65000 \
    -e NIM_KVCACHE_PERCENT=0.5 \
    -e NIM_LOW_MEMORY_MODE=1 \
    -e NIM_KV_CACHE_HOST_MEM_FRACTION=0.5 \
    -v "$LOCAL_NIM_CACHE:/opt/nim/.cache" \
    -u $(id -u) \
    -p 8999:8000 \
    nvcr.io/nim/nvidia/llama-3.3-nemotron-super-49b-v1.5:latest
```

**Characteristics:**
- Uses ~66GB VRAM (saves 25GB!)
- 65K context window (still very large)
- FP4 quantized for efficiency
- Minimal performance impact
- **Port**: 8999 (maps to container port 8000)

### 49B Memory Optimization Parameters

The 49B model benefits from the same optimization parameters as the 9B model, but with adjusted values:

- **NIM_MAX_MODEL_LEN=65000**: Provides 65K token context (vs 128K default)
  - Still sufficient for most use cases
  - Significant VRAM savings
  
- **NIM_KVCACHE_PERCENT=0.5**: Uses 50% of available memory for KV cache
  - More aggressive than 9B (0.6) due to larger model size
  - Balances performance with memory efficiency

- **NIM_KV_CACHE_HOST_MEM_FRACTION=0.5**: Offloads 50% of KV cache to system RAM
  - Critical for 49B model with large context
  - Requires adequate system RAM (32GB+ recommended)

## Verification

### 1. Check Container Status

```bash
docker ps --filter "name=nemotron-49b"
```

Expected output shows container running with port mapping `0.0.0.0:8999->8000/tcp`.

### 2. Monitor Logs

Monitor the initialization process (can take 10-20 minutes):

```bash
docker logs -f nemotron-49b-fp4-optimized
```

Wait for: `INFO: Uvicorn running on http://0.0.0.0:8000`

### 3. Test Health Endpoint

```bash
curl http://localhost:8999/v1/health/ready
```

Expected response: `{"status":"ready"}`

### 4. Test Chat Completion

```bash
curl -X POST http://localhost:8999/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nvidia/llama-3.3-nemotron-super-49b-v1.5",
    "messages": [{"role":"user", "content":"What is 2+2?"}],
    "max_tokens": 100
  }'
```

Expected response includes `"content": "2+2 equals 4."`

## GPU Memory Monitoring

### Check VRAM Usage

```bash
nvidia-smi --query-gpu=name,memory.used,memory.free,memory.total --format=csv
```

### Expected Memory Usage

**Standard deployment**:
```
Memory Used: ~91GB
```

**Memory-optimized deployment** ⭐ Recommended:
```
Memory Used: ~66GB
```

## Multi-Model Deployment

When running multiple NIMs on the same GPU:

### Configuration Example (98GB GPU)

1. **Nemotron 49B FP4** (memory-optimized): ~66GB
2. **Stable Diffusion 3.5 Large**: ~30GB

**Total**: ~96GB (fits in 98GB GPU)

### Configuration Example (98GB GPU - ASR/TTS Focus)

1. **Nemotron 49B FP4** (memory-optimized): ~66GB
2. **Parakeet 0.6B ASR**: ~2-4GB
3. **Magpie TTS**: ~4-6GB

**Total**: ~74GB (leaves room for RAG NIMs)

### Deployment Order

1. Start Nemotron 49B first (largest VRAM footprint)
2. Start other NIMs in order of size
3. Monitor VRAM usage with `nvidia-smi`

This ensures proper memory allocation.

## Troubleshooting

### Issue: Out of Memory Error

**Symptom**: Container crashes with CUDA OOM error

**Solutions**:
1. Ensure using memory-optimized parameters
2. Reduce `NIM_MAX_MODEL_LEN` further (e.g., to 32000)
3. Stop other GPU-intensive containers
4. Verify no other processes are using GPU: `nvidia-smi`

### Issue: Slow Initialization

**Symptom**: Container takes >20 minutes to start

**Solutions**:
1. Verify NGC_API_KEY: `echo $NGC_API_KEY`
2. Check internet connection (model download ~25GB)
3. Monitor disk space: `df -h $LOCAL_NIM_CACHE`
4. Check Docker logs for specific errors

### Issue: Container Exits Immediately

**Symptom**: Container starts then stops

**Solutions**:
1. Check NGC authentication: `echo $NGC_API_KEY`
2. Verify model profile: `echo $NIM_MODEL_PROFILE`
3. Review logs: `docker logs nemotron-49b-fp4-optimized`
4. Ensure sufficient disk space (>50GB free)

### Issue: Port Mapping Error (8999:8999)

**Symptom**: Model accessible on 8999 but container mapping shows `8999:8999`

**Cause**: Container was launched with incorrect port mapping

**Solution**: 
```bash
# Stop and remove existing container
docker stop nemotron-49b-fp4-optimized
docker rm nemotron-49b-fp4-optimized

# Relaunch with correct mapping
docker run -d --name nemotron-49b-fp4-optimized \
    ... \
    -p 8999:8000 \  # Correct: host 8999 -> container 8000
    ...
```

## Performance Tuning

### Latency Optimization

For lowest latency (already optimal in memory-optimized config):

```bash
-e NIM_MAX_BATCH_SIZE=1  # Already set
-e NIM_MAX_MODEL_LEN=32000  # Even shorter context
```

### Context Window Optimization

For maximum context (up to 128K):

```bash
-e NIM_MAX_MODEL_LEN=131072  # Full 128K context
-e NIM_KVCACHE_PERCENT=0.7  # More cache
-e NIM_KV_CACHE_HOST_MEM_FRACTION=0.3  # Less host offload
```

**Note**: This will increase VRAM usage to ~85-90GB.

## Integration with Mercury

Mercury Agent uses Nemotron 49B when configured in `mercury_agent/configs/config.yml`:

```yaml
llms:
  nim_llm:
    _type: nim
    model_name: nvidia/llama-3.3-nemotron-super-49b-v1.5
    base_url: "http://localhost:8999/v1"
    temperature: 0.0
    max_tokens: 1024
    timeout: 180
  chitchat_llm:
    _type: nim
    model_name: nvidia/llama-3.3-nemotron-super-49b-v1.5
    base_url: "http://localhost:8999/v1"
    temperature: 0.7
    max_tokens: 1024
    timeout: 180
```

### Port Configuration

- **Host Port**: 8999 (accessible from Mercury)
- **Container Port**: 8000 (internal)
- **Endpoint**: `http://localhost:8999/v1/chat/completions`

## Resources

- **Nemotron 49B**: https://build.nvidia.com/nvidia/llama-3_3-nemotron-super-49b-v1_5
- **NIM Documentation**: https://docs.nvidia.com/nim/
- **Mercury Documentation**: [../README.md](../README.md)
- **Text-to-Image Guide**: [TEXT_TO_IMAGE_DEPLOYMENT.md](./TEXT_TO_IMAGE_DEPLOYMENT.md)

## Version History

| Version | Date | Notes |
|---------|------|-------|
| v1.0 | Nov 4, 2025 | Initial deployment with Nemotron 49B FP4 and memory optimization |
| v1.1 | Nov 13, 2025 | Simplified guide, removed Nemotron 9B references, focused on 49B only |

