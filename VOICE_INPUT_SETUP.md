# Mercury Voice Input Setup Guide

This document describes the setup requirements and troubleshooting steps for enabling voice input in the Mercury Interface.

## Overview

Mercury's browser interface includes an **optional voice input feature** that allows users to interact with the assistant using speech instead of text. This feature requires a local NVIDIA Parakeet ASR (Automatic Speech Recognition) NIM container running on your system.

## Current Status

✅ **Text-based chat**: Fully functional in both CLI and browser interface  
✅ **Mercury Agent**: Successfully modernized to NVIDIA NeMo Agent Toolkit (NAT) v1.3.0  
⚠️ **Voice input**: Requires additional NGC permissions (see below)

## Prerequisites

### 1. System Requirements
- NVIDIA GPU with CUDA support
- Docker with NVIDIA Container Toolkit installed
- NGC API key with appropriate permissions

### 2. NVIDIA Container Toolkit Installation

The NVIDIA Container Toolkit is required to run GPU-accelerated Docker containers:

```bash
# Add NVIDIA Container Toolkit repository
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install the toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker to use the NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker

# Restart Docker
sudo systemctl restart docker
```

### 3. NGC API Key Setup

The NGC API key must be exported in your environment and saved in `.bashrc`:

```bash
# Add to ~/.bashrc
export NGC_API_KEY='your-ngc-api-key-here'
export NVIDIA_API_KEY='your-ngc-api-key-here'

# Source the file
source ~/.bashrc
```

### 4. Docker Login to NGC Registry

Authenticate Docker with the NGC registry:

```bash
docker login nvcr.io --username='$oauthtoken' --password="$NGC_API_KEY"
```

## Parakeet ASR NIM Setup

### Model Information

- **Model**: NVIDIA Parakeet 1.1B RNNT Multilingual ASR
- **Container**: `nvcr.io/nim/nvidia/parakeet-1-1b-rnnt-multilingual:latest`
- **Purpose**: Converts speech audio to text for the Mercury interface
- **Ports**: 
  - HTTP: 9000
  - gRPC: 50051 (used by Mercury)

### Running the Container

```bash
docker run -d --name=parakeet-1-1b-rnnt-multilingual \
   --runtime=nvidia \
   --shm-size=8GB \
   -e NGC_API_KEY="$NGC_API_KEY" \
   -e NIM_HTTP_API_PORT=9000 \
   -e NIM_GRPC_API_PORT=50051 \
   -p 9000:9000 \
   -p 50051:50051 \
   -e NIM_TAGS_SELECTOR=mode=str \
   -v "$HOME/nim_cache:/home/nvs/.cache/nim" \
   nvcr.io/nim/nvidia/parakeet-1-1b-rnnt-multilingual:latest
```

### Checking Container Status

```bash
# Check if container is running
docker ps --filter "name=parakeet"

# View logs
docker logs parakeet-1-1b-rnnt-multilingual

# Follow logs in real-time
docker logs -f parakeet-1-1b-rnnt-multilingual
```

## Known Issues and Troubleshooting

### Issue 1: NGC Permission Denied

**Symptom**: Container fails to download model files with error:
```
Permission error: The requested operation requires permissions that the user does not have. 
This may be due to the user not being a member of the organization that owns the repo.
```

**Solution**: 
1. Visit the [NGC Catalog](https://catalog.ngc.nvidia.com/)
2. Search for "Parakeet ASR" or navigate to NVIDIA RIVA models
3. Click on the Parakeet RNNT model
4. Accept the license agreement/terms of use
5. Generate a new NGC API key if needed
6. Update your `.bashrc` and re-export the key
7. Re-authenticate Docker: `docker login nvcr.io --username='$oauthtoken' --password="$NGC_API_KEY"`

### Issue 2: NVIDIA Runtime Not Found

**Symptom**: 
```
exec: "nvidia-container-runtime": executable file not found in $PATH
```

**Solution**: Install NVIDIA Container Toolkit (see Prerequisites section above)

### Issue 3: GPU Device Selection Failed

**Symptom**:
```
could not select device driver "" with capabilities: [[gpu]]
```

**Solution**: 
- Use `--runtime=nvidia` instead of `--gpus` flag
- Ensure NVIDIA Container Toolkit is properly configured
- Verify GPU is accessible: `nvidia-smi`

### Issue 4: Container Stuck During Model Download

**Symptom**: Container starts but logs show it's stuck at "fetching filemap"

**Possible Causes**:
- Slow network connection (model files are large, ~1-2 GB)
- NGC API key lacks proper permissions
- Network/firewall blocking NGC API access

**Solution**:
- Be patient - initial download can take 10-30 minutes depending on connection
- Check NGC API key permissions
- Verify network connectivity to `api.ngc.nvidia.com`
- Check container logs for error messages

## Mercury Interface Configuration

The Mercury browser interface is already configured to use the local Parakeet ASR server at `localhost:50051`. 

Configuration in `mercury_interface/server.js`:

```javascript
const transcribeProcess = spawn('python', [
  '/home/milos/mercury-assistant/mercury_interface/riva_python_client/scripts/asr/transcribe_file.py',
  '--server', 'localhost:50051',  // Local Parakeet ASR server
  '--language-code', 'en-US',
  '--input-file', outputFilePath
]);
```

Once the Parakeet container is running successfully, voice input should work automatically.

## Testing Voice Input

1. Ensure Parakeet ASR container is running:
   ```bash
   docker ps --filter "name=parakeet"
   ```

2. Start the Mercury interface:
   ```bash
   cd mercury_interface
   node server.js
   ```

3. Open your browser to `http://localhost:5000`

4. Click the microphone icon to record a voice message

5. Speak your query and click stop

6. The audio should be transcribed and sent to Mercury Agent

## Alternative: Using Cloud ASR (Original Configuration)

If you cannot get the local Parakeet ASR working, you can revert to using NVIDIA's cloud ASR service by modifying `server.js`:

```javascript
const transcribeProcess = spawn('python', [
  '/home/milos/mercury-assistant/mercury_interface/riva_python_client/scripts/asr/transcribe_file.py',
  '--server', 'grpc.nvcf.nvidia.com:443',
  '--use-ssl',
  '--metadata', 'function-id', 'e6fa172c-79bf-4b9c-bb37-14fe17b4226c',
  '--metadata', 'authorization', `Bearer ${process.env.NVIDIA_API_KEY}`,
  '--language-code', 'en-US',
  '--input-file', outputFilePath
]);
```

**Note**: This requires your NGC API key to have access to NVIDIA Cloud Functions (NVCF) ASR services.

## Resources

- [NVIDIA NGC Catalog](https://catalog.ngc.nvidia.com/)
- [NVIDIA Container Toolkit Documentation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)
- [NVIDIA NIM Documentation](https://docs.nvidia.com/nim/)
- [NVIDIA RIVA Documentation](https://docs.nvidia.com/riva/)

### Issue 5: GPU Architecture Compatibility (Compute Capability 12.0)

**Symptom**: 
```
RuntimeError: CUDA error: no kernel image is available for execution on the device
```

**Cause**: The Parakeet ASR NIM container ships with pre-compiled CUDA/PyTorch binaries that don't include support for newer GPU architectures like Ada Lovelace (compute capability 12.0). This affects GPUs such as:
- NVIDIA RTX 6000 Ada
- NVIDIA RTX PRO 6000 Black Knight Edition
- GeForce RTX 4090
- Other Ada Lovelace generation GPUs

**Diagnosis**:
```bash
# Check your GPU's compute capability
nvidia-smi --query-gpu=name,compute_cap --format=csv
```

If your GPU has compute capability 12.0 or newer, the current Parakeet NIM may not work.

**Solution Options**:
1. **Wait for updated NIM**: NVIDIA periodically updates NIM containers. Check for updates:
   ```bash
   docker pull nvcr.io/nim/nvidia/parakeet-1-1b-rnnt-multilingual:latest
   ```

2. **Contact NVIDIA Support**: Report the compatibility issue and request support for compute capability 12.0 GPUs

3. **Use Cloud ASR**: Revert to cloud-based ASR (if your NGC API key has NVCF permissions)

4. **Use text-only mode**: Mercury works perfectly without voice input

**Workaround**: None currently available. This is a limitation of the pre-compiled binaries in the NIM container.

## Summary

Voice input is an **optional feature** that successfully enhances the Mercury interface with speech-to-text capabilities! 

### ✅ Successfully Configured Components:

1. ✅ NVIDIA Container Toolkit (installed)
2. ✅ Docker NGC authentication (configured)
3. ✅ NGC API key with Parakeet ASR model permissions (configured)
4. ✅ GPU compatibility resolved (Parakeet NIM v1.1.0 works with Blackwell GPUs)
5. ✅ Browser-based audio capture (works from any device)
6. ✅ Remote access via SSH tunnel (enables microphone permissions)

### 🎉 Current Status: WORKING!

**Solution Summary:**
- **Parakeet ASR NIM v1.1.0** successfully runs on Blackwell architecture GPUs (compute capability 12.0+)
- **Browser-based audio capture** eliminates need for client-side tools (Sox, arecord, etc.)
- **SSH tunnel** enables remote access with microphone permissions: `ssh -L 5000:localhost:5000 user@server`
- **FFmpeg** on server converts browser audio (WebM) to WAV for ASR transcription

### Architecture:
```
Browser (any device) 
  → MediaRecorder API captures microphone
  → Sends WebM audio to server
  → FFmpeg converts to WAV (16kHz, mono, 16-bit)
  → Parakeet ASR NIM transcribes
  → Mercury Agent responds
```

**Recommendation**: Voice input is fully functional! Use SSH tunnel for remote access or localhost for local access.

