"""
Enhanced Wikipedia Research Tool with NAT Profiling and Observability.

This module extends the original langchain_research_tool with:
- Detailed profiling metrics
- LLM token tracking
- Multi-stage performance monitoring (topic extraction + search + summarization)
- Error tracking
"""

# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
import time
import wikipedia
import asyncio
from functools import partial
from typing import Optional

from nat.builder.builder import Builder
from nat.builder.framework_enum import LLMFrameworkEnum
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.component_ref import LLMRef
from nat.data_models.function import FunctionBaseConfig
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class LangChainResearchEnhancedConfig(FunctionBaseConfig, name="langchain_researcher_tool_enhanced"):
    """Enhanced configuration with profiling support."""
    llm_name: LLMRef
    profile: bool = True
    tags: Optional[list[str]] = ["research", "wikipedia", "langchain"]


@register_function(config_type=LangChainResearchEnhancedConfig, framework_wrappers=[LLMFrameworkEnum.LANGCHAIN])
async def langchain_research_enhanced(tool_config: LangChainResearchEnhancedConfig, builder: Builder):
    """
    Enhanced Wikipedia research tool with detailed profiling.
    
    This implementation tracks:
    - Topic extraction performance
    - Wikipedia search latency
    - Content retrieval size
    - Overall end-to-end latency
    - Token usage (estimated)
    """
    import os

    # Set up NVIDIA API token
    api_token = os.getenv("NVIDIA_API_KEY")
    os.environ["NVIDIA_API_KEY"] = api_token

    if not api_token:
        raise ValueError("API token must be provided via NVIDIA_API_KEY environment variable")

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

    # Profiling metrics
    metrics = {
        "total_calls": 0,
        "topic_extraction_time": 0.0,
        "wikipedia_search_time": 0.0,
        "total_latency": 0.0,
        "total_chars_retrieved": 0,
        "errors": 0
    }

    async def extract_topic(query: str) -> str:
        """Extract the main topic from the query with timing."""
        extraction_start = time.time()
        try:
            logger.debug("[TOPIC_EXTRACT] Input query: %s", query)
            formatted_prompt = topic_prompt.format(query=query)
            
            result = await llm_with_output.ainvoke(formatted_prompt)
            topic = result.topic.strip()
            
            extraction_time = time.time() - extraction_start
            metrics["topic_extraction_time"] += extraction_time
            
            logger.info(
                f"[PROFILE] Topic Extraction | "
                f"Time: {extraction_time:.3f}s | "
                f"Topic: '{topic}'"
            )
            return topic
        except Exception as e:
            logger.error("[TOPIC_EXTRACT] Error: %s", e)
            return query

    async def wikipedia_search(query: str) -> tuple[str, str]:
        """Search Wikipedia and return the URL and content with timing."""
        search_start = time.time()
        try:
            # Try to get the page directly
            page = await asyncio.get_event_loop().run_in_executor(
                None, partial(wikipedia.page, query, auto_suggest=False)
            )
            content = page.content.replace('\n', ' ').strip()
            
            search_time = time.time() - search_start
            metrics["wikipedia_search_time"] += search_time
            metrics["total_chars_retrieved"] += len(content)
            
            logger.info(
                f"[PROFILE] Wikipedia Search | "
                f"Time: {search_time:.3f}s | "
                f"Content Length: {len(content)} chars | "
                f"URL: {page.url}"
            )
            
            return page.url, content
            
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
                    content = page.content.replace('\n', ' ').strip()
                    
                    search_time = time.time() - search_start
                    metrics["wikipedia_search_time"] += search_time
                    metrics["total_chars_retrieved"] += len(content)
                    
                    logger.info(
                        f"[PROFILE] Wikipedia Search (fallback) | "
                        f"Time: {search_time:.3f}s | "
                        f"Content Length: {len(content)} chars"
                    )
                    
                    return page.url, content
            except Exception:
                pass
                
        return f"Could not find a Wikipedia page for: {query}", ""

    async def _arun(inputs: str) -> str:
        """Process user input with comprehensive profiling."""
        call_start = time.time()
        
        try:
            metrics["total_calls"] += 1
            
            logger.info(f"\n{'='*50}")
            logger.info(f"[RESEARCH] Starting Wikipedia research")
            logger.info(f"[RESEARCH] Input: '{inputs}'")
            
            # Extract the main topic
            topic = await extract_topic(inputs)
            logger.info(f"[RESEARCH] Extracted topic: '{topic}'")
            
            # Search Wikipedia
            url, content = await wikipedia_search(topic)
            
            if content:
                # Truncate content to fit within model's context window
                MAX_CHARS = 12000
                if len(content) > MAX_CHARS:
                    content = content[:MAX_CHARS] + "... [Content truncated due to length]"
                    logger.info(f"[RESEARCH] Content truncated to {MAX_CHARS} chars")
                
                result = f"{content}\n\nSource: {url}"
                
                # Calculate total latency
                total_latency = time.time() - call_start
                metrics["total_latency"] += total_latency
                
                # Estimate tokens
                estimated_tokens = len(result) // 4
                
                # Log comprehensive profiling summary
                if tool_config.profile:
                    avg_latency = metrics["total_latency"] / metrics["total_calls"]
                    avg_extraction = metrics["topic_extraction_time"] / metrics["total_calls"]
                    avg_search = metrics["wikipedia_search_time"] / metrics["total_calls"]
                    
                    logger.info(
                        f"\n[PROFILE SUMMARY] Wikipedia Research\n"
                        f"  Current Call:\n"
                        f"    Total Time: {total_latency:.3f}s\n"
                        f"    Topic Extraction: {metrics['topic_extraction_time']:.3f}s\n"
                        f"    Wikipedia Search: {metrics['wikipedia_search_time']:.3f}s\n"
                        f"    Est. Tokens: {estimated_tokens}\n"
                        f"  Cumulative Stats:\n"
                        f"    Total Calls: {metrics['total_calls']}\n"
                        f"    Avg Latency: {avg_latency:.3f}s\n"
                        f"    Avg Extraction: {avg_extraction:.3f}s\n"
                        f"    Avg Search: {avg_search:.3f}s\n"
                        f"    Total Chars Retrieved: {metrics['total_chars_retrieved']:,}\n"
                        f"    Errors: {metrics['errors']}"
                    )
                
                logger.info(f"{'='*50}\n")
                return result
            
            return url
            
        except Exception as e:
            metrics["errors"] += 1
            total_latency = time.time() - call_start
            logger.error(
                f"[ERROR] Research failed after {total_latency:.3f}s: {str(e)}"
            )
            return f"Error: {str(e)}"

    # Add metadata for profiling
    _arun.__profiling_enabled__ = tool_config.profile
    _arun.__profiling_tags__ = tool_config.tags
    _arun.__profiling_metrics__ = metrics

    yield FunctionInfo.from_fn(
        fn=_arun, 
        description="find a Wikipedia page and generate a summary for a given query with detailed profiling"
    )

