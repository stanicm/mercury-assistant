"""
This module implements a direct Wikipedia search that returns a single page link.
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
import asyncio
from functools import partial

from nat.builder.builder import Builder
from nat.builder.framework_enum import LLMFrameworkEnum
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.component_ref import LLMRef
from nat.data_models.function import FunctionBaseConfig
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)


class LangChainResearchConfig(FunctionBaseConfig, name="langchain_researcher_tool"):
    """Configuration class for the Wikipedia search tool."""
    llm_name: LLMRef


@register_function(config_type=LangChainResearchConfig, framework_wrappers=[LLMFrameworkEnum.LANGCHAIN])
async def langchain_research(tool_config: LangChainResearchConfig, builder: Builder):
    """Main function that implements the Wikipedia search tool."""
    import os

    # Set up NVIDIA API token for LLM access
    api_token = os.getenv("NVIDIA_API_KEY")
    os.environ["NVIDIA_API_KEY"] = api_token

    if not api_token:
        raise ValueError("API token must be provided in the configuration or in the environment variable `NVIDIA_API_KEY`")

    # Get the LLM for topic extraction
    llm = await builder.get_llm(llm_name=tool_config.llm_name, wrapper_type=LLMFrameworkEnum.LANGCHAIN)

    # Define the topic extraction prompt
    topic_prompt = PromptTemplate.from_template("""
    Extract the main subject or topic from the following query. Return ONLY the main subject, nothing else.
    Do not add any explanations or additional text.

    Query: {query}
    Main subject:""")

    class TopicExtract(BaseModel):
        topic: str = Field(description="The main subject or topic to search for")

    llm_with_output = llm.with_structured_output(TopicExtract)

    async def extract_topic(query: str) -> str:
        """Extract the main topic from the query."""
        try:
            logger.debug("[TOPIC_EXTRACT] Input query: %s", query)
            formatted_prompt = topic_prompt.format(query=query)
            logger.debug("[TOPIC_EXTRACT] Formatted prompt: %s", formatted_prompt)
            
            result = await llm_with_output.ainvoke(formatted_prompt)
            logger.debug("[TOPIC_EXTRACT] Raw result type: %s", type(result))
            logger.debug("[TOPIC_EXTRACT] Raw result: %s", result)
            
            topic = result.topic.strip()
            logger.info("[TOPIC_EXTRACT] Extracted topic: '%s'", topic)
            return topic
        except Exception as e:
            logger.error("[TOPIC_EXTRACT] Error extracting topic: %s", e)
            logger.info("[TOPIC_EXTRACT] Falling back to original query")
            return query

    async def wikipedia_search(query: str) -> tuple[str, str]:
        """Search Wikipedia and return the URL and content of the first matching page."""
        try:
            # Try to get the page directly
            page = await asyncio.get_event_loop().run_in_executor(
                None, partial(wikipedia.page, query, auto_suggest=False)
            )
            # Get the full content
            content = page.content
            
            # Format the content to ensure complete sentences
            formatted_content = content.replace('\n', ' ').strip()
            
            return page.url, formatted_content
            
        except (wikipedia.exceptions.PageError, wikipedia.exceptions.DisambiguationError):
            # If direct page fails, try search
            try:
                search_results = await asyncio.get_event_loop().run_in_executor(
                    None, partial(wikipedia.search, query, results=1)
                )
                if search_results:
                    page = await asyncio.get_event_loop().run_in_executor(
                        None, partial(wikipedia.page, search_results[0], auto_suggest=False)
                    )
                    # Get the full content
                    content = page.content
                    
                    # Format the content to ensure complete sentences
                    formatted_content = content.replace('\n', ' ').strip()
                    
                    return page.url, formatted_content
            except Exception:
                pass
                
        return f"Could not find a Wikipedia page for: {query}", ""

    async def _arun(inputs: str) -> str:
        """Process user input and return a Wikipedia page URL and content."""
        try:
            print(f"\n--- Wikipedia Tool ---")
            print(f"Input query: '{inputs}'")
            
            # Extract the main topic first
            topic = await extract_topic(inputs)
            print(f"Extracted topic: '{topic}'")
            logger.debug("Extracted topic: %s", topic)
            
            # Search Wikipedia with the extracted topic
            url, content = await wikipedia_search(topic)
            print(f"Wikipedia URL: {url}")
            print(f"Wikipedia content length: {len(content)} chars")
            
            if content:
                # Truncate content to fit within model's context window
                # 4096 token limit = ~16000 chars, leaving ~12000 for content
                MAX_CHARS = 12000
                if len(content) > MAX_CHARS:
                    content = content[:MAX_CHARS] + "... [Content truncated due to length]"
                    print(f"Content truncated to {MAX_CHARS} chars")
                
                result = f"{content}\n\nSource: {url}"
                print(f"Returning {len(result)} chars total")
                print(f"--- End Wikipedia Tool ---\n")
                return result
            print(f"--- End Wikipedia Tool ---\n")
            return url
            
        except Exception as e:
            return {
                'input': inputs,
                'chosen_worker_agent': None,
                'chat_history': [],
                'final_output': f"Error: {str(e)}"
            }

    yield FunctionInfo.from_fn(fn=_arun, description="find a Wikipedia page and generate a summary for a given query")
