"""
This module implements a Retrieval Augmented Generation (RAG) tool that interfaces with a RAG server.
It provides functionality to query a knowledge base and generate responses based on retrieved information.

Key Components:
1. RAGServerConfig: Configuration class for the RAG server connection and parameters
2. nvbp_rag_tool: Main function that implements the RAG tool functionality

The tool is designed to:
- Connect to a RAG server running on a specified URL
- Query a specific collection in the knowledge base
- Retrieve and process responses from the server
- Handle streaming responses and error cases

This tool is used by the mercury_agent workflow when queries are classified as 'Retrieve' type,
particularly for questions related to SPH (Smoothed Particle Hydrodynamics) or when RAG is explicitly requested.
"""

# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
from typing import Optional
import json

import httpx
from pydantic import ConfigDict

from aiq.builder.builder import Builder
from aiq.builder.framework_enum import LLMFrameworkEnum
from aiq.builder.function_info import FunctionInfo
from aiq.cli.register_workflow import register_function
from aiq.data_models.function import FunctionBaseConfig

logger = logging.getLogger(__name__)


class RAGServerConfig(FunctionBaseConfig, name="nvbp_rag"):
    """
    Configuration class for the RAG server connection and parameters.
    
    Attributes:
        base_url: The base URL of the RAG server (default: "http://0.0.0.0:8081/v1")
        collection_name: Name of the knowledge base collection to query (default: "SPH")
        top_k: Number of top results to retrieve (default: 3)
        timeout: Request timeout in seconds (default: 120)
        use_knowledge_base: Whether to use the knowledge base for retrieval (default: True)
    """
    model_config = ConfigDict(protected_namespaces=())

    base_url: str = "http://0.0.0.0:8081/v1"
    collection_name: str = "SPH"
    top_k: int = 3
    timeout: int = 120
    use_knowledge_base: bool = True


@register_function(config_type=RAGServerConfig, framework_wrappers=[LLMFrameworkEnum.LANGCHAIN])
async def nvbp_rag_tool(tool_config: RAGServerConfig, builder: Builder):
    """
    Main function that implements the RAG tool functionality.
    
    This function:
    1. Creates an async client for HTTP requests
    2. Sends queries to the RAG server
    3. Processes streaming responses
    4. Handles errors and timeouts
    
    Args:
        tool_config: Configuration object containing RAG server parameters
        builder: Builder object for creating framework-specific components
        
    Returns:
        A function that can be used to query the RAG server
    """
    from colorama import Fore

    async def _arun(query: str) -> str:
        """
        Query the RAG server for relevant information.
        
        This function:
        1. Establishes a connection to the RAG server
        2. Sends the user query with configured parameters
        3. Processes the streaming response
        4. Handles any errors that occur during the process
        
        Args:
            query: The user's input query to be processed by the RAG server
            
        Returns:
            str: The response from the RAG server, or an error message if the request fails
        """
        try:
            async with httpx.AsyncClient(timeout=tool_config.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{tool_config.base_url}/generate",
                    json={
                        "messages": [
                            {
                                "role": "user",
                                "content": query
                            }
                        ],
                        "use_knowledge_base": tool_config.use_knowledge_base,
                        "collection_name": tool_config.collection_name,
                        "reranker_top_k": tool_config.top_k,
                        "vdb_top_k": tool_config.top_k
                    }
                ) as response:
                    response.raise_for_status()
                    full_response = ""
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                if data.get("choices") and len(data["choices"]) > 0:
                                    content = data["choices"][0]["delta"].get("content", "")
                                    if content:
                                        full_response += content
                            except json.JSONDecodeError:
                                continue
                    logger.info("%s RAG Server Response: %s %s", Fore.MAGENTA, full_response, Fore.RESET)
                    return full_response if full_response else "No response from RAG server"
        except Exception as e:
            logger.error("Error querying RAG server: %s", str(e))
            return f"Error querying RAG server: {str(e)}"

    yield FunctionInfo.from_fn(_arun, description="Query the RAG server for relevant information")
