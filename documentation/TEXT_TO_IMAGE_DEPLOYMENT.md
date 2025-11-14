# Text-to-Image Generation with Stable Diffusion 3.5 Large

This guide covers deploying NVIDIA's Stable Diffusion 3.5 Large NIM for text-to-image generation with Mercury AI Assistant.

## Model Overview

**Stable Diffusion 3.5 Large** is a state-of-the-art text-to-image generation model that creates high-quality images from text prompts.

### Key Features
- High-quality image generation (1024x1024 default)
- Fast inference (~5-10 seconds per image)
- Support for multiple image sizes
- Creative and artistic output
- Local deployment with NVIDIA NIMs

### Specifications
- **VRAM Usage**: ~25-30GB
- **Port**: 8000
- **Output Format**: Base64-encoded JPEG
- **Resolution**: 768-1344 pixels (width/height)
- **Model Type**: Diffusion-based generative model

## Prerequisites

- NVIDIA GPU with CUDA support (minimum 32GB VRAM recommended)
- Docker with NVIDIA Container Toolkit installed
- NGC API key
- HuggingFace API token (for model access)
- Sufficient VRAM alongside other models (e.g., ~66GB for Nemotron 49B + ~30GB for SD = ~96GB total)

## Deployment

### Step 1: Set Environment Variables

```bash
export NGC_API_KEY="your-ngc-api-key"
export HF_TOKEN="your-huggingface-token"
export LOCAL_NIM_CACHE=~/.cache/nim
```

### Step 2: Prepare Cache Directory

```bash
mkdir -p "$LOCAL_NIM_CACHE"
chmod 777 "$LOCAL_NIM_CACHE"
```

### Step 3: Deploy Stable Diffusion 3.5 Large NIM

```bash
docker run -d --name=stable-diffusion-3.5-large \
    --runtime=nvidia \
    --gpus='"device=0"' \
    -e NGC_API_KEY=$NGC_API_KEY \
    -e HF_TOKEN=$HF_TOKEN \
    -p 8000:8000 \
    -v "$LOCAL_NIM_CACHE:/opt/nim/.cache/" \
    nvcr.io/nim/stabilityai/stable-diffusion-3.5-large:latest
```

**Note**: This deployment uses port 8000. If running alongside Nemotron 49B (port 8999), there is no port conflict due to Docker's network isolation.

### Step 4: Monitor Initialization

The model takes several minutes to initialize. Monitor the logs:

```bash
docker logs -f stable-diffusion-3.5-large
```

Wait for initialization to complete. The model is ready when you see startup complete messages.

## Testing the Deployment

### Health Check

```bash
curl http://localhost:8000/v1/health/ready
```

Expected response: `{"status":"ready"}`

### Generate a Test Image

```bash
curl -X POST http://localhost:8000/v1/images/generations \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "a majestic dragon flying over a medieval castle at sunset, epic fantasy art, highly detailed, 8k",
    "height": 1024,
    "width": 1024
  }' \
  -o /tmp/test_image.json

# Extract and save the image
cat /tmp/test_image.json | jq -r '.artifacts[0].base64' | base64 --decode > /tmp/test_output.jpg

# View the image
xdg-open /tmp/test_output.jpg
```

## API Reference

### Endpoint

```
POST http://localhost:8000/v1/images/generations
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | Text description of the image to generate |
| `height` | integer | No | Image height (768, 832, 896, 960, 1024, 1088, 1152, 1216, 1280, or 1344) |
| `width` | integer | No | Image width (768, 832, 896, 960, 1024, 1088, 1152, 1216, 1280, or 1344) |
| `seed` | integer | No | Random seed for reproducible generation |

**Note**: Valid dimensions are: 768, 832, 896, 960, 1024, 1088, 1152, 1216, 1280, or 1344 pixels.

### Response Format

```json
{
  "artifacts": [
    {
      "base64": "base64-encoded-image-data",
      "finishReason": "SUCCESS",
      "seed": 12345
    }
  ]
}
```

### Example Request (Python)

```python
import requests
import base64
import json

url = "http://localhost:8000/v1/images/generations"
payload = {
    "prompt": "a serene mountain landscape at sunrise, photorealistic",
    "height": 1024,
    "width": 1024,
    "seed": 42
}

response = requests.post(url, json=payload)
data = response.json()

# Extract and save image
img_data = base64.b64decode(data['artifacts'][0]['base64'])
with open('output.jpg', 'wb') as f:
    f.write(img_data)

print(f"Image saved! Seed: {data['artifacts'][0]['seed']}")
```

### Example Request (cURL)

```bash
# Generate and save image in one command
curl -X POST http://localhost:8000/v1/images/generations \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "futuristic cityscape with flying cars, cyberpunk style, neon lights",
    "height": 1024,
    "width": 1024
  }' | jq -r '.artifacts[0].base64' | base64 --decode > output.jpg
```

## Prompt Engineering Tips

### Effective Prompts
- Be specific and descriptive
- Include style references (e.g., "photorealistic", "oil painting", "digital art")
- Mention quality descriptors (e.g., "highly detailed", "8k", "sharp focus")
- Specify lighting and mood (e.g., "dramatic lighting", "golden hour")

### Example Prompts

**Landscape:**
```
a serene mountain lake at sunset, snow-capped peaks, reflection in water, 
dramatic clouds, golden hour lighting, photorealistic, highly detailed
```

**Portrait:**
```
portrait of a wise elderly wizard, long white beard, detailed wrinkles, 
magical staff, fantasy art, dramatic lighting, 8k resolution
```

**Architecture:**
```
modern minimalist house, large windows, concrete and glass, surrounded by 
forest, architectural photography, natural lighting
```

**Abstract:**
```
abstract geometric patterns, vibrant colors, flowing shapes, digital art, 
high contrast, modern design
```

## Multi-Model Deployment

### Running with Nemotron 49B

When running both Stable Diffusion 3.5 Large and Nemotron 49B simultaneously:

**Total VRAM Requirements:**
- Nemotron 49B FP4 (optimized): ~66GB
- Stable Diffusion 3.5 Large: ~30GB
- **Total**: ~96GB

**Port Configuration:**
- Nemotron 49B: Port 8999 (external) → 8000 (internal)
- Stable Diffusion: Port 8000 (external) → 8000 (internal)

**No port conflict** because each container has its own isolated network namespace. External ports 8000 and 8999 map to different containers.

### Deployment Order

1. Start Nemotron 49B first (largest VRAM consumer)
2. Start Stable Diffusion 3.5 Large second
3. Verify both are operational with health checks

## Docker Network Isolation Explained

**Why no port conflict?**

Each Docker container runs in its own isolated network namespace:
- **Internal ports** (inside container): Can be the same (e.g., both use 8000)
- **External ports** (on host): Must be different (8999 vs 8000)
- **Mapping**: `-p <host-port>:<container-port>`

Example:
```bash
# Nemotron: Host port 8999 → Container port 8000
-p 8999:8000  

# Stable Diffusion: Host port 8000 → Container port 8000
-p 8000:8000
```

Access:
- Nemotron: `http://localhost:8999/v1/...`
- Stable Diffusion: `http://localhost:8000/v1/...`

## GPU Memory Monitoring

### Check VRAM Usage

```bash
nvidia-smi --query-gpu=name,memory.used,memory.free,memory.total --format=csv
```

### Expected Memory Usage

**Stable Diffusion 3.5 Large alone:**
```
Memory Used: ~25-30GB
```

**With Nemotron 49B (optimized):**
```
Nemotron 49B: ~66GB
Stable Diffusion: ~30GB
Total: ~96GB
```

## Troubleshooting

### Issue: Connection Refused (Port 8001)

**Symptom**: `failed to connect to all addresses; last error: UNKNOWN: ipv4:127.0.0.1:8001: Failed to connect to remote host`

**Cause**: Internal Triton backend (GRPC port 8001) not ready

**Solution**: Restart the container
```bash
docker restart stable-diffusion-3.5-large
docker logs -f stable-diffusion-3.5-large
```

### Issue: Invalid Height/Width Error

**Symptom**: `"msg":"Input should be 768, 832, 896, 960, 1024, 1088, 1152, 1216, 1280 or 1344"`

**Cause**: Using unsupported image dimensions

**Solution**: Use one of the supported sizes:
- 768, 832, 896, 960, 1024, 1088, 1152, 1216, 1280, or 1344

### Issue: Out of Memory Error

**Symptom**: CUDA OOM error during generation

**Solutions**:
1. Stop other GPU-intensive containers
2. Use smaller image dimensions (e.g., 768x768)
3. Ensure sufficient GPU memory (32GB+ recommended)

### Issue: Container Exits Immediately

**Symptom**: Container starts then stops

**Solutions**:
1. Verify NGC authentication: `echo $NGC_API_KEY`
2. Verify HuggingFace token: `echo $HF_TOKEN`
3. Check logs: `docker logs stable-diffusion-3.5-large`
4. Ensure sufficient disk space for model cache

## Integration with Mercury Agent

### Future Integration (In Development)

Mercury Agent will support text-to-image generation through a dedicated worker:

```yaml
# Future config.yml integration
functions:
  text_to_image:
    _type: text_to_image_tool
    endpoint: "http://localhost:8000/v1/images/generations"
    default_size: 1024
```

### NAT Multimodal Agent Design

Based on NVIDIA NeMo Agent Toolkit best practices:
1. **Image generation**: Create image file on disk
2. **Metadata passing**: Pass file path/reference to LLM (not image bytes)
3. **Context efficiency**: Avoid flooding LLM context window with image data
4. **Artifact management**: Store images separately in designated directory

This approach ensures:
- Efficient context window usage
- Fast agent response times
- Proper separation of modalities
- Scalable multi-agent workflows

## Resources

- **Stable Diffusion 3.5 Large**: https://build.nvidia.com/stabilityai/stable-diffusion-3-5-large
- **HuggingFace Model Card**: https://huggingface.co/stabilityai/stable-diffusion-3.5-large
- **NIM Documentation**: https://docs.nvidia.com/nim/
- **Mercury Documentation**: [../README.md](../README.md)

## Version History

| Version | Date | Notes |
|---------|------|-------|
| v1.0 | Nov 13, 2025 | Initial deployment guide for Stable Diffusion 3.5 Large |

---

**Branch**: `text2image`  
**Status**: Experimental - Text-to-image feature in development

