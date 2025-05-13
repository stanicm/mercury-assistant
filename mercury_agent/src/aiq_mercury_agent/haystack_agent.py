"""
This module implements a chitchat agent using the Haystack framework.
It provides functionality for handling general conversation and non-specific queries.

Key Components:
1. HaystackChitchatConfig: Configuration class for the Haystack agent
2. haystack_chitchat_agent_as_tool: Main function that implements the chitchat functionality

The agent is designed to:
- Handle general conversation and casual queries
- Generate responses using NVIDIA's language models
- Process user inputs and generate appropriate responses
- Integrate with the mercury_agent workflow for general queries

This agent is used by the mercury_agent workflow when queries are classified as 'General' type,
particularly for casual conversation, greetings, or queries that don't fit other categories.
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

from aiq.builder.builder import Builder
from aiq.builder.function_info import FunctionInfo
from aiq.cli.register_workflow import register_function
from aiq.data_models.component_ref import LLMRef
from aiq.data_models.function import FunctionBaseConfig

logger = logging.getLogger(__name__)


class HaystackChitchatConfig(FunctionBaseConfig, name="haystack_chitchat_agent"):
    """
    Configuration class for the Haystack chitchat agent.
    
    Attributes:
        llm_name: Reference to the language model to be used for generating responses
    """
    llm_name: LLMRef


@register_function(config_type=HaystackChitchatConfig)
async def haystack_chitchat_agent_as_tool(tool_config: HaystackChitchatConfig, builder: Builder):
    """
    Main function that implements the Haystack chitchat agent functionality.
    
    This function:
    1. Initializes the NVIDIA generator with specified parameters
    2. Sets up the model configuration
    3. Creates a function for processing user inputs
    4. Returns a tool that can be used for general conversation
    
    Args:
        tool_config: Configuration object containing the LLM reference
        builder: Builder object for creating framework-specific components
        
    Returns:
        A function that can be used for general conversation
    """
    from haystack_integrations.components.generators.nvidia import NvidiaGenerator

    # Initialize the NVIDIA generator with specified parameters
    generator = NvidiaGenerator(
        model=tool_config.llm_name,
        api_url="https://integrate.api.nvidia.com/v1",
        model_arguments={
            "temperature": 0.2,  # Lower temperature for more focused responses
            "top_p": 0.7,       # Nucleus sampling parameter
            "max_tokens": 1024,  # Maximum length of generated response
        },
    )

    # Warm up the generator for faster initial response
    generator.warm_up()

    async def _arun(inputs: str) -> str:
        """
        Process user input and generate a response using the Haystack agent.
        
        This function:
        1. Takes user input
        2. Generates a response using the configured language model
        3. Returns the generated response
        
        Args:
            inputs: The user's input text to be processed
            
        Returns:
            str: The generated response from the language model
        """
        out = generator.run(prompt=inputs)
        output = out["replies"][0]  # noqa: W293 E501

        logger.info("output from langchain_research_tool: %s", output)  # noqa: W293 E501
        return output

    yield FunctionInfo.from_fn(_arun, description="extract relevent information from search the web")  # noqa: W293 E501
