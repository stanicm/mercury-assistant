"""
This module implements a research tool using LangChain and Wikipedia integration.
It provides functionality for extracting topics from user queries and retrieving relevant information from Wikipedia.

Key Components:
1. LangChainResearchConfig: Configuration class for the research tool
2. langchain_research: Main function that implements the research functionality
3. Wikipedia integration: Functions for searching and retrieving Wikipedia content
4. Topic extraction: LLM-based extraction of search topics from user queries

The tool is designed to:
- Extract relevant search topics from user queries using LLM
- Search Wikipedia for information on the extracted topics
- Handle various Wikipedia search scenarios (disambiguation, no results, etc.)
- Provide structured and informative responses

This tool is used by the mercury_agent workflow when queries are classified as 'Research' type,
particularly for factual questions that can be answered using Wikipedia content.
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
import wikipedia

from aiq.builder.builder import Builder
from aiq.builder.framework_enum import LLMFrameworkEnum
from aiq.builder.function_info import FunctionInfo
from aiq.cli.register_workflow import register_function
from aiq.data_models.component_ref import FunctionRef
from aiq.data_models.component_ref import LLMRef
from aiq.data_models.function import FunctionBaseConfig

logger = logging.getLogger(__name__)


class LangChainResearchConfig(FunctionBaseConfig, name="langchain_researcher_tool"):
    """
    Configuration class for the LangChain research tool.
    
    Attributes:
        llm_name: Reference to the language model to be used for topic extraction
    """
    llm_name: LLMRef


@register_function(config_type=LangChainResearchConfig, framework_wrappers=[LLMFrameworkEnum.LANGCHAIN])
async def langchain_research(tool_config: LangChainResearchConfig, builder: Builder):
    """
    Main function that implements the LangChain research tool functionality.
    
    This function:
    1. Sets up the LLM for topic extraction
    2. Configures Wikipedia search functionality
    3. Creates a pipeline for processing user queries
    4. Returns a tool that can be used for research queries
    
    Args:
        tool_config: Configuration object containing the LLM reference
        builder: Builder object for creating framework-specific components
        
    Returns:
        A function that can be used for research queries
    """
    import os
    from langchain_core.prompts import PromptTemplate
    from pydantic import BaseModel
    from pydantic import Field

    # Set up NVIDIA API token for LLM access
    api_token = os.getenv("NVIDIA_API_KEY")
    os.environ["NVIDIA_API_KEY"] = api_token

    if not api_token:
        raise ValueError(
            "API token must be provided in the configuration or in the environment variable `NVIDIA_API_KEY`")

    # Initialize the LLM for topic extraction
    llm = await builder.get_llm(llm_name=tool_config.llm_name, wrapper_type=LLMFrameworkEnum.LANGCHAIN)

    async def wikipedia_search(topic: str) -> str:
        """
        Search Wikipedia for information on a given topic.
        
        This function:
        1. Searches Wikipedia for the given topic
        2. Retrieves a summary of the most relevant article
        3. Handles various search scenarios (disambiguation, no results, etc.)
        
        Args:
            topic: The topic to search for on Wikipedia
            
        Returns:
            str: A summary of the Wikipedia article or an appropriate message
        """
        try:
            # Search Wikipedia
            search_results = wikipedia.search(topic, results=3)
            if not search_results:
                return f"No Wikipedia articles found for topic: {topic}"
            
            # Get the summary of the first result
            summary = wikipedia.summary(search_results[0], sentences=3)
            return f"Wikipedia Summary for '{search_results[0]}':\n{summary}"
        except wikipedia.exceptions.DisambiguationError as e:
            # Handle disambiguation pages
            return f"Multiple matches found for '{topic}'. Please be more specific. Options: {', '.join(e.options[:5])}"
        except wikipedia.exceptions.PageError:
            return f"No Wikipedia page found for topic: {topic}"
        except Exception as e:
            return f"Error searching Wikipedia: {str(e)}"

    # Define the prompt template for topic extraction
    prompt_template = """
    You are an expert at extracting the most relevant search topic from user queries to search on Wikipedia.
    Your task is to identify the most specific and relevant topic that will yield the best Wikipedia results.
    
    Guidelines:
    1. For compound topics (e.g., "Japanese architecture"), keep the full phrase as it represents a specific subject
    2. For general topics, focus on the main subject of interest
    3. Avoid breaking up compound topics into individual words
    4. Maintain cultural and historical context in the topic
    
    ------
    {inputs}
    ------
    The output MUST use the following format:
    '''
    topic: a clear and specific topic or keyword to search on Wikipedia, focusing on the main subject of interest
    '''
    Begin!
    [/INST]
    """
    prompt = PromptTemplate(
        input_variables=['inputs'],
        template=prompt_template,
    )

    # Define the output structure for topic extraction
    class TopicExtract(BaseModel):
        """
        Pydantic model for structured topic extraction output.
        
        Attributes:
            topic: The extracted topic or keyword for Wikipedia search
        """
        topic: str = Field(description="most important keyword or topic to search on Wikipedia")

    # Configure the LLM to output structured data
    llm_with_output_structure = llm.with_structured_output(TopicExtract)

    async def execute_tool(out):
        """
        Execute the Wikipedia search with the extracted topic.
        
        This function:
        1. Extracts the topic from the LLM output
        2. Performs the Wikipedia search
        3. Handles any errors that occur during the process
        
        Args:
            out: The structured output from the LLM containing the extracted topic
            
        Returns:
            str: The Wikipedia search results or an error message
        """
        try:
            topic = out.topic
            if topic is not None and topic not in ['', '\n']:
                output_summary = await wikipedia_search(topic)
            else:
                output_summary = f"Could not extract a valid topic for Wikipedia search"

        except Exception as e:
            output_summary = f"Error in Wikipedia search: {str(e)}"
            logger.exception("error in executing tool: %s", e, exc_info=True)

        return output_summary

    # Create the research pipeline
    research = (prompt | llm_with_output_structure | execute_tool)

    async def _arun(inputs: str) -> str:
        """
        Process user input and perform Wikipedia research.
        
        This function:
        1. Takes user input
        2. Extracts a search topic
        3. Performs the Wikipedia search
        4. Returns the results
        
        Args:
            inputs: The user's input query
            
        Returns:
            str: The Wikipedia search results or an error message
        """
        output = await research.ainvoke(inputs)
        logger.info("output from langchain_research_tool: %s", output)
        return output

    yield FunctionInfo.from_fn(_arun, description="extract relevant information from Wikipedia search")
