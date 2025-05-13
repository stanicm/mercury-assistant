<!--
SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

# Mercury Agent

Mercury Agent is a backend system that demonstrates how to integrate multiple AI frameworks seamlessly using a set of LangChain / LangGraph agents in NVIDIA AgentIQ. It can be used independently or as part of the Mercury AI Assistant system.

## Overview

Mercury Agent combines the strengths of multiple AI frameworks:
- **Haystack Agent** – For general conversation with a configurable LLM
- **LangChain Research Tool** – For web search and research
- **LlamaIndex RAG Tool** – For document Q&A and retrieval

The system uses AgentIQ's plugin system and `Builder` object to wrap these tools as LangChain Tools, demonstrating how different AI frameworks can work together seamlessly.

## Key Features

- **Multi-Agent Architecture**:
  - Supervisor agent for task routing
  - RAG agent using LlamaIndex
  - Research agent using LangChain
  - Chitchat agent using Haystack

  Note that the RAG setup in the Mercury agent is set up such that it expects a rag server up and running on port 8081. The RAG Blueprint from NVIDIA is not a part of this repository for now, so if you would like to set the RAG up, we would direct you to the following page: https://build.nvidia.com/nvidia/build-an-enterprise-rag-pipeline

- **Framework Integration**:
  - Custom plugin system for new tools
  - High-level API for async LangChain tools
  - YAML-based configuration
  - Simplified developer experience

## Prerequisites

- Python 3.10 or higher
- NVIDIA API Key
- AIQ Toolkit (installed from NVIDIA's package repository)

## Installation

1. Set your NVIDIA API Key:
   ```bash
   export NVIDIA_API_KEY=<YOUR_API_KEY>
   ```

2. Install the Mercury Agent:
   ```bash
   pip install -e .
   ```

## Usage

### Standalone Usage

Run the agent directly:
```bash
aiq run --config_file=configs/config.yml --input "your question here"
```

Example queries:
1. For RAG (document retrieval):
   ```bash
   aiq run --config_file=configs/config.yml --input "tell me about this workflow"
   ```

2. For Research:
   ```bash
   aiq run --config_file=configs/config.yml --input "what is Compound AI?"
   ```

### Integration with Mercury Interface

When used with Mercury Interface:
1. Start the Mercury Interface server
2. Select "Mercury Agent" from the model dropdown
3. Use the web interface to interact with all agent capabilities

## Architecture

The multi-agent architecture consists of:
1. **Supervisor Agent**: Routes incoming queries to appropriate worker agents
2. **Worker Agents**:
   - RAG Agent: Uses LlamaIndex for document retrieval
   - Research Agent: Uses LangChain for web research
   - Chitchat Agent: Uses Haystack for general conversation

![LangGraph multi-agents workflow](../../docs/source/_static/aiq_mercury_agent_agentic_schema.png)

## Configuration

The agent's behavior can be configured through `configs/config.yml`:
- LLM model selection
- Tool configurations
- Data directory settings
- Workflow parameters

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.
