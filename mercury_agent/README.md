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

Please refer to the main [README.md](../README.md) for complete installation instructions and prerequisites.

### Required Dependencies

- arxiv ~= 2.1.3
- colorama ~= 0.4.6
- markdown-it-py ~= 3.0
- nvidia-haystack == 0.1.2
- wikipedia ~= 1.4.0

## Usage

### Standalone Usage

Run the agent directly:
```
aiq run --config_file mercury_agent/configs/config.yml --input "Your query here"
```