# Nemotron Model Deployment Guide

This guide covers deploying NVIDIA's Nemotron models locally using Docker for use with Mercury AI Assistant.

## Available Models

### Nemotron Nano 9B
A powerful 9-billion parameter language model optimized for:
- Fast inference
- High-quality text generation
- Multi-agent workflows
- Reasoning capabilities

### Nemotron 49B (Llama 3.3 Super)
A flagship 49-billion parameter model with enhanced capabilities:
- Advanced reasoning with chain-of-thought
- Superior instruction following
- Extended context support (up to 128K)
- Available in FP4 quantization for reduced memory footprint

## Prerequisites

- NVIDIA GPU with CUDA support
- Docker with NVIDIA Container Toolkit installed
- NGC API key
- **For Nano 9B**: Minimum 65GB VRAM (memory-optimized) or 88GB (standard)
- **For 49B FP4**: Minimum 66GB VRAM (memory-optimized) or 91GB (standard)

## Deployment Options

---

# Nemotron Nano 9B Deployment

### Standard Deployment (~88GB VRAM)

Basic deployment with default settings:

```bash
docker run -d --rm --name=nemotron-nano-9b \
    --gpus all \
    --shm-size=16GB \
    -e NGC_API_KEY \
    -p 8000:8000 \
    nvcr.io/nim/nvidia/nvidia-nemotron-nano-9b-v2:latest
```

**Characteristics:**
- Uses ~88GB VRAM
- Maximum performance
- Suitable for GPUs with >90GB VRAM

### Memory-Optimized Deployment (~65GB VRAM) ⭐ Recommended

Optimized for memory-constrained GPUs:

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

**Characteristics:**
- Uses ~65GB VRAM (saves 23GB!)
- Minimal performance impact
- Allows running alongside Parakeet ASR + Magpie TTS on GPUs with ~75GB+ VRAM

## Memory Optimization Parameters Explained

### NIM_MAX_BATCH_SIZE=1
- **Purpose**: Limits concurrent request processing
- **Effect**: Reduces memory overhead from batching
- **Trade-off**: Lower throughput for multiple simultaneous requests
- **Best for**: Single-user or low-concurrency scenarios

### NIM_MAX_MODEL_LEN=4096
- **Purpose**: Sets maximum sequence length (tokens)
- **Effect**: Reduces KV cache allocation
- **Trade-off**: Shorter maximum context window
- **Default**: 8192 or higher
- **Best for**: Most conversational AI tasks

### NIM_KVCACHE_PERCENT=0.6
- **Purpose**: Allocates 60% of available memory for KV cache
- **Effect**: Leaves more memory for model weights and computation
- **Default**: 0.9 (90%)
- **Best for**: Multi-model deployments

### NIM_LOW_MEMORY_MODE=1
- **Purpose**: Enables various memory-saving optimizations
- **Effect**: Activates memory-efficient algorithms and data structures
- **Trade-off**: Slight latency increase
- **Best for**: Memory-constrained environments

### NIM_KV_CACHE_HOST_MEM_FRACTION=0.6
- **Purpose**: Uses CPU/host memory for overflow KV cache
- **Effect**: Offloads some cache to system RAM when GPU memory is full
- **Trade-off**: Slightly slower cache access
- **Best for**: Systems with abundant RAM but limited VRAM

## Verification

### 1. Check Container Status

```bash
docker ps --filter "name=nemotron"
```

Expected output shows container running.

### 2. Monitor Logs

```bash
docker logs -f nemotron-nano-9b
```

Wait for: `INFO: Uvicorn running on http://0.0.0.0:8000`

### 3. Test Health Endpoint

```bash
curl http://localhost:8000/v1/health/ready
```

Expected response: `{"status":"ready"}`

### 4. Test Chat Completion

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nvidia/nvidia-nemotron-nano-9b-v2",
    "messages": [{"role":"user", "content":"What is 2+2?"}],
    "max_tokens": 64
  }'
```

## GPU Memory Monitoring

### Check VRAM Usage

```bash
nvidia-smi --query-gpu=name,memory.used,memory.free,memory.total --format=csv
```

### Expected Memory Usage

**Standard deployment**:
```
Memory Used: ~88GB
```

**Memory-optimized deployment**:
```
Memory Used: ~65GB
```

## Multi-Model Deployment

When running multiple NIMs on the same GPU:

### Configuration Example (97GB GPU)

1. **Nemotron Nano 9B** (memory-optimized): ~65GB
2. **Parakeet 0.6B ASR**: ~2-4GB
3. **Magpie TTS**: ~4-6GB

**Total**: ~73GB (fits comfortably in 97GB)

### Deployment Order

1. Start Nemotron first (largest VRAM footprint)
2. Start Parakeet ASR
3. Start Magpie TTS last

This ensures proper memory allocation.

## Troubleshooting

### Issue: Out of Memory Error

**Symptom**: Container crashes with CUDA OOM error

**Solutions**:
1. Use memory-optimized parameters
2. Reduce `NIM_MAX_MODEL_LEN` further (e.g., 2048)
3. Ensure no other processes are using GPU
4. Stop other NIMs and restart in order

### Issue: Slow Initialization

**Symptom**: Container takes >10 minutes to start

**Solutions**:
1. Check NGC_API_KEY is set correctly
2. Verify internet connection (model download)
3. Monitor disk space (models are large)
4. Check Docker logs for specific errors

### Issue: Container Exits Immediately

**Symptom**: Container starts then stops

**Solutions**:
1. Check NGC authentication: `echo $NGC_API_KEY`
2. Verify NVIDIA Container Toolkit: `nvidia-smi`
3. Review logs: `docker logs nemotron-nano-9b`
4. Ensure sufficient disk space

## Performance Tuning

### Latency Optimization

For lowest latency (trading memory for speed):

```bash
-e NIM_MAX_BATCH_SIZE=1  # Already set in memory-optimized
-e NIM_MAX_MODEL_LEN=2048  # Shorter context
```

### Throughput Optimization

For maximum throughput (requires more VRAM):

```bash
-e NIM_MAX_BATCH_SIZE=4
-e NIM_MAX_MODEL_LEN=4096
-e NIM_KVCACHE_PERCENT=0.8
```

---

# Nemotron 49B (Llama 3.3 Super) Deployment

## Standard Deployment (~91GB VRAM)

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

### Testing the 49B Model

```bash
# Test health
curl http://localhost:8999/v1/health/ready

# Test chat completion
curl -X POST http://localhost:8999/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nvidia/llama-3.3-nemotron-super-49b-v1.5",
    "messages": [{"role":"user", "content":"What is 2+2?"}],
    "max_tokens": 100
  }'
```

---

## Integration with Mercury

Mercury Agent can use either Nemotron model when configured in `mercury_agent/configs/config.yml`:

### For Nemotron Nano 9B:

```yaml
llms:
  nim_llm:
    _type: nim
    model_name: nvidia/nvidia-nemotron-nano-9b-v2
    base_url: "http://localhost:8000/v1"
    temperature: 0.0
    max_tokens: 1024
```

### For Nemotron 49B:

```yaml
llms:
  nim_llm:
    _type: nim
    model_name: nvidia/llama-3.3-nemotron-super-49b-v1.5
    base_url: "http://localhost:8999/v1"
    temperature: 0.0
    max_tokens: 1024
  chitchat_llm:
    _type: nim
    model_name: nvidia/llama-3.3-nemotron-super-49b-v1.5
    base_url: "http://localhost:8999/v1"
    temperature: 0.7
    max_tokens: 1024
```

## Model Comparison

| Feature | Nemotron Nano 9B | Nemotron 49B FP4 |
|---------|------------------|------------------|
| **Parameters** | 9B | 49B |
| **VRAM (Standard)** | ~88GB | ~91GB |
| **VRAM (Optimized)** | ~65GB | ~66GB |
| **Context Window** | 4K-8K | 65K-128K |
| **Port** | 8000 | 8999 |
| **Best For** | Fast inference, multi-agent | Advanced reasoning, long context |
| **Quantization** | FP16 | FP4 |

## Resources

- **Nemotron Nano 9B**: https://build.nvidia.com/nvidia/nvidia-nemotron-nano-9b-v2
- **Nemotron 49B**: https://build.nvidia.com/nvidia/llama-3.3-nemotron-super-49b-v1.5
- **NIM Documentation**: https://docs.nvidia.com/nim/
- **Mercury Documentation**: [../README.md](../README.md)

## Version History

| Version | Date | Notes |
|---------|------|-------|
| v1.0 | Nov 1, 2025 | Initial deployment with memory optimization parameters |
| v2.0 | Nov 4, 2025 | Added Nemotron 49B FP4 deployment with memory optimization |

