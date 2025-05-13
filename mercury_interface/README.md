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

Mercury Interface is a web-based frontend that provides a user-friendly way to interact with various AI models, including the Mercury Agent. It can be used independently with different AI models or as part of the Mercury AI Assistant system.

## Features

- **Chat Interface**:
  - Support for multiple AI models
  - Real-time response streaming
  - Markdown formatting support
  - Chat history management

- **Voice Input**:
  - Microphone support
  - Speech-to-text using NVIDIA Riva
  - Real-time transcription

- **Model Integration**:
  - Mercury Agent integration
  - OpenAI models support
  - NVIDIA models support
  - Extensible model selection

## Prerequisites

Please refer to the main [README.md](../README.md) for complete installation instructions and prerequisites.


### Configure Environment Variables
```bash
export NVIDIA_API_KEY="your-nvidia-api-key"
export OPENAI_API_KEY="your-openai-api-key"  # Optional
```
## Usage

### Standalone Usage

1. Start the server:
   ```bash
   node server.js
   ```

2. Open your browser to http://localhost:5000

3. Select a model from the dropdown:
   - OpenAI models (if configured)
   - NVIDIA models
   - Other compatible LLM services

### Integration with Mercury Agent

1. Start the Mercury Interface server as above

2. Select "Mercury Agent" from the model dropdown

3. Use the interface to access Mercury Agent capabilities:
   - Research workflows (Wikipedia-based)
   - Retrieval workflows (local documents)
   - General chat capabilities

## Response Handling

The interface handles different response formats:

1. **Standard Format**:
   ```
   Workflow Result: ["content"]
   ```

2. **Research Format**:
   ```
   Workflow Result: ['<Document>content</Document>']
   ```

3. **Markdown Format**:
   - Supports code blocks
   - Lists and tables
   - Links and images

## Development

The interface is built with:
- Express.js for the backend
- Vanilla JavaScript for the frontend
- WebSocket for real-time communication
- NVIDIA Riva for speech recognition

## Project Structure

- `public/`: Frontend assets
  - `index.html`: Main interface
  - `script.js`: Frontend logic
  - `styles.css`: UI styling

- `server.js`: Backend server
  - WebSocket handling
  - Model integration
  - Response processing

- `riva_python_client/`: Speech recognition
  - NVIDIA Riva integration
  - Audio processing

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Disclaimer

Apologies in advance - this was written mostly in a hurry through generous use of AI tools. Thus limited-quality documentation or nasty code practices may be present. Creating production-level code is not the intent here.

## What is it?

It's a very simple UI, written in spare time, vibe-coding components and stitching them together. The idea is to create a personal demo platform that will serve multiple purposes:

  - Learning playground
  - Flexible demo playground (that the user control and understand)
  - Making it extendable such that various components can be added and switched between through UI (note the model selection in the upper left corner - imagine adding RAG, agents, multi-modal abilities etc.)
  - Serve as a basis for further enhancements that would lead to a small agentic avatar or other educational purposes (workshops etc).

## APIs

You need to make sure you are properly stating your API keys in the environment! Otherwise this won't work.

## What it can and cannot do so far

CAN DO:

It can call a Llama 3.1 405B for chit chat and Nemotron Super 49B model for reasoning. I also left a localhost:5000 option with the idea to launch an LLM NIM on Brev, expose the port on that remote machine, create an ssh tunnel to that port, thus the redirect to the localhost:5000. Note that the models can be easily switched/added through simple editing of the paths in server.js (with synchronous minor adjustments in public/script.js and public/index.html). Recently an agentic option was added - the Mercury Agent, which has three tools in its desposal for now: the chit-chat, the RAG and the Wikipedia research tool. For more info consult the readme file in the mercury_agent folder.

Note that the RAG setup in the Mercury agent is set up such that it expects a rag server up and running on port 8081. The RAG Blueprint from NVIDIA is not a part of this repository for now, so if you would like to set the RAG up, we would direct you to the following page: https://build.nvidia.com/nvidia/build-an-enterprise-rag-pipeline

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

Several options are at play, though the main candidate is upgrading Mercury agent capabilities and addition of TTS.

Other options include 3D robot/model development, then combining everything into a functioning avatar. Hopefully in the near future we will have capable small models able to run locally on in-house machines (e.g DGX Spark or its iteration).

## NVIDIA Riva Python Client

The `riva_python_client` folder contains the official NVIDIA Riva Python client repository, downloaded from [https://github.com/nvidia-riva/python-clients.git](https://github.com/nvidia-riva/python-clients.git). This client is used for speech recognition capabilities in the application.


