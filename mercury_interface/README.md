<!--
  SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
-->

# Mercury Interface

A web-based interface for interacting with various AI models and the Mercury Agent. The interface supports text and voice input, and can connect to different AI models including the Mercury Agent for advanced workflows.

## Features

- Chat interface with support for multiple AI models
- Voice input using microphone
- Integration with Mercury Agent for:
  - Research workflows (Wikipedia-based information retrieval)
  - Retrieval workflows (local document search)
  - General chat capabilities
- Real-time response streaming
- Markdown formatting support

## Setup

1. Install Node.js dependencies:
   ```bash
   npm install
   ```

2. Set up environment variables:
   ```bash
   export NVIDIA_API_KEY="your-nvidia-api-key"
   export OPENAI_API_KEY="your-openai-api-key"  # Optional, for OpenAI models
   ```

3. Start the server:
   ```bash
   node server.js
   ```

4. Open your browser and navigate to the displayed URL (typically http://localhost:5000)

## Mercury Agent Integration

The interface can connect to the Mercury Agent for advanced workflows:

### Research Workflow
- Uses Wikipedia to search and summarize information
- Returns formatted responses with source attribution
- Handles XML-like document format in responses

### Retrieval Workflow
- Searches through local documentation
- Returns relevant information in a clean format
- Supports markdown formatting in responses

### Response Handling
The interface handles different response formats from the Mercury Agent:
- Standard format: `Workflow Result: ["content"]` or `Workflow Result: ['content']`
- Research format: `Workflow Result: ['<Document>content</Document>']`
- Handles escaped characters and formatting in responses

## Usage

1. Select a model from the dropdown:
   - Mercury Agent (for research and retrieval)
   - OpenAI models (if configured)
   - NVIDIA models (if configured)

2. Enter your message or use voice input

3. View the response in the chat interface

## Development

The interface is built with:
- Express.js for the backend
- Vanilla JavaScript for the frontend
- WebSocket for real-time communication
- NVIDIA Riva for speech recognition

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Disclaimer

This playground is getting shared before its intended time and was written mostly in a hurry through generous use of AI tools. Therefore apologies in advance for poor documentation or nasty code practices. Creating production-level code is not the intent here.

## What is it?

It's a very simple UI, written in spare time, vibe-coding components and stitching them together. The idea is to create a personal demo platform that will serve multiple purposes:

  - Learning playground
  - Flexible demo playground (that I control and understand)
  - Making it extendable such that various components can be added and switched between through UI (note the model selection in the upper left corner - imagine adding RAG, agents, multi-modal abilities etc.)
  - Serve as a basis for further enhancements that would lead to a small avatar for my kids to assist them in school (no cheating allowed though).

## (Known) Dependencies

The UI was developed on a Mac, implying it was not tested on any other OS. Off the top of my head - you would need at least *node* (to run server.js) and *sox* (for mic recording for Parakeet) tools. I used *brew* and *pip* as needed for various installations. Aside from that I have Python 3.11.7 installed, along with the Anaconda package. To what extent do the latter components play a role - I did not rigorously check. 

### Installing Node.js on Ubuntu

To install Node.js on Ubuntu, follow these steps:

1. Update your package list:
   ```bash
   sudo apt update
   ```

2. Install Node.js and npm using NodeSource:
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
   sudo apt-get install -y nodejs
   ```

3. Verify the installation:
   ```bash
   node --version
   npm --version
   ```

### Installing Sox on Ubuntu

For audio recording functionality, install Sox:
```bash
sudo apt-get install sox
```

Note: Sox is required for the microphone recording feature. The server uses Sox to record audio in the correct format (16-bit WAV, mono channel, 16kHz sample rate) for the Parakeet ASR service.

### Installing NVIDIA Riva Client and Prerequisites

For speech recognition functionality, you'll need to install the NVIDIA Riva client and its prerequisites:

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

Note: The NVIDIA Riva client is used for speech recognition capabilities. Make sure you have the necessary NVIDIA API keys configured in your environment.

## APIs

I experienced trouble with setting environment variables and did not bother resolving those issues, so I just hard-coded the API keys where needed. Thus, you will need to insert your NVIDIA API keys in three spots in server.js file. The places are clearly marked with YOUR_NVIDIA_API_KEY_HERE.

## What it can and cannot do so far

CAN DO:

It can call a Llama 3.1 405B for chit chat and Nemotron Super 49B model for reasoning. I also left a localhost:5000 option with the idea to launch an LLM NIM on Brev, expose the port on that remote machine, create an ssh tunnel to that port, thus the redirect to the localhost:5000. Note that the models can be easily switched/added through simple editing of the paths in server.js (with synchronous minor adjustments in public/script.js and public/index.html)

There is also the ASR ability using the API call to Parakeet. The input format seems to have specific requirements (16 bit wav, mono), so I ran across the *sox* tool that can effectively record directly to the needed format. 

CANNOT DO:

There are some "dead LLM options" such as using GPT-4o, Claude and Llama 3.2 - THESE DO NOT WORK. They're a remnant of the initial request to the AI to provide multiple options. I kept them because they can be used as placeholders for other tools. 

Similarly, there are two icons (one for intended RAG and one for image upload) next to the microphone option - THOSE DO NOT WORK EITHER (YET).

## Usage - Launching the interface page

Quite simple - after *node* tool is there, just navigate to the webui/ folder and execute:

        node server.js

you should get something that says:

        Server running at http://localhost:5000
        Open your browser and navigate to http://localhost:5000

## Planned next steps

Several options are at play, though the main candidate is the addition of an agent, which would then branch off into RAG, multi-modality tools and reasoning.

Other options include TTS addition w/ streaming and 3D avatar development, then combining everything into a functioning kid's avatar. Hopefully in the near future we will have capable small models able to run locally on in-house machines (e.g DGX Spark or its iteration).

## NVIDIA Riva Python Client

The `riva_python_client` folder contains the official NVIDIA Riva Python client repository, downloaded from [https://github.com/nvidia-riva/python-clients.git](https://github.com/nvidia-riva/python-clients.git). This client is used for speech recognition capabilities in the application.

## Deployment Notes

When deploying this application to different environments, consider the following potential path modifications:

- **Node.js and Sox Installation**: Ensure that the paths for Node.js and Sox are correctly set in your environment. Adjust the installation commands if necessary.
- **NVIDIA Riva Client**: The path to the NVIDIA Riva client may need to be updated based on your installation location. Check the `server.js` file for any hardcoded paths.
- **API Keys**: Replace any hardcoded API keys with environment variables or secure storage solutions to enhance security.
- **Output File Paths**: Verify that the output file paths in the code are suitable for your environment, especially if using a different operating system.
