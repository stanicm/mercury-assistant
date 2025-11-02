"""
Enhanced RAG Tool with NAT Profiling, Evaluation, and Observability.

This module extends the original nvbp_rag_tool with:
- Detailed profiling metrics for RAG operations
- Streaming response timing
- Token usage tracking
- Error rate monitoring
- Evaluation readiness (context tracking for faithfulness/relevancy metrics)
"""

# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
import time
import json
from typing import Optional
import httpx
from pydantic import ConfigDict

from nat.builder.builder import Builder
from nat.builder.framework_enum import LLMFrameworkEnum
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

logger = logging.getLogger(__name__)


class RAGServerEnhancedConfig(FunctionBaseConfig, name="nvbp_rag_enhanced"):
    """
    Enhanced configuration with profiling and evaluation support.
    
    Attributes:
        base_url: The base URL of the RAG server
        collection_name: Name of the knowledge base collection to query
        top_k: Number of top results to retrieve
        timeout: Request timeout in seconds
        use_knowledge_base: Whether to use the knowledge base
        profile: Enable profiling for this tool
        tags: Tags for categorizing metrics
        track_context: Track retrieved context for evaluation
    """
    model_config = ConfigDict(protected_namespaces=())

    base_url: str = "http://0.0.0.0:8081/v1"
    collection_name: str = "SPH"
    top_k: int = 3
    timeout: int = 120
    use_knowledge_base: bool = True
    profile: bool = True
    tags: Optional[list[str]] = ["rag", "retrieval"]
    track_context: bool = True  # For evaluation


@register_function(config_type=RAGServerEnhancedConfig, framework_wrappers=[LLMFrameworkEnum.LANGCHAIN])
async def nvbp_rag_tool_enhanced(tool_config: RAGServerEnhancedConfig, builder: Builder):
    """
    Enhanced RAG tool with comprehensive profiling and evaluation tracking.
    
    This implementation tracks:
    - RAG server latency (total and streaming)
    - Token streaming rate
    - Retrieved context (for evaluation)
    - Response quality metrics preparation
    - Error rates and timeout handling
    """
    from colorama import Fore

    # Profiling metrics
    metrics = {
        "total_calls": 0,
        "total_latency": 0.0,
        "streaming_latency": 0.0,
        "total_tokens_generated": 0,
        "total_contexts_retrieved": 0,
        "errors": 0,
        "timeouts": 0,
        "avg_tokens_per_second": 0.0
    }

    # Context tracking for evaluation
    context_history = []

    async def _arun(query: str) -> str:
        """
        Query the RAG server with comprehensive profiling.
        
        Args:
            query: The user's input query to be processed by the RAG server
            
        Returns:
            str: The response from the RAG server with profiling metadata
        """
        call_start = time.time()
        streaming_start = None
        first_token_latency = None
        token_count = 0
        
        try:
            metrics["total_calls"] += 1
            
            logger.info(f"\n{'='*50}")
            logger.info(f"[RAG] Starting RAG query")
            logger.info(f"[RAG] Query: '{query}'")
            logger.info(f"[RAG] Collection: {tool_config.collection_name}")
            logger.info(f"[RAG] Top-K: {tool_config.top_k}")
            
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
                    
                    # Mark when streaming starts
                    streaming_start = time.time()
                    connection_latency = streaming_start - call_start
                    
                    logger.info(f"[RAG] Connection established in {connection_latency:.3f}s")
                    
                    full_response = ""
                    retrieved_contexts = []
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                
                                # Track first token latency (Time To First Token - TTFT)
                                if first_token_latency is None and data.get("choices"):
                                    first_token_latency = time.time() - call_start
                                
                                if data.get("choices") and len(data["choices"]) > 0:
                                    content = data["choices"][0]["delta"].get("content", "")
                                    if content:
                                        full_response += content
                                        token_count += 1
                                
                                # Track retrieved contexts (if available in response)
                                if "contexts" in data and tool_config.track_context:
                                    retrieved_contexts.extend(data["contexts"])
                                    
                            except json.JSONDecodeError:
                                continue
                    
                    # Calculate streaming metrics
                    streaming_time = time.time() - streaming_start
                    total_latency = time.time() - call_start
                    tokens_per_second = token_count / streaming_time if streaming_time > 0 else 0
                    
                    # Update cumulative metrics
                    metrics["total_latency"] += total_latency
                    metrics["streaming_latency"] += streaming_time
                    metrics["total_tokens_generated"] += token_count
                    metrics["total_contexts_retrieved"] += len(retrieved_contexts)
                    
                    # Calculate running average for tokens per second
                    metrics["avg_tokens_per_second"] = (
                        (metrics["avg_tokens_per_second"] * (metrics["total_calls"] - 1) + tokens_per_second) 
                        / metrics["total_calls"]
                    )
                    
                    # Store context for evaluation if enabled
                    if tool_config.track_context and retrieved_contexts:
                        context_history.append({
                            "query": query,
                            "contexts": retrieved_contexts,
                            "response": full_response,
                            "timestamp": time.time()
                        })
                        # Keep only last 100 for memory efficiency
                        if len(context_history) > 100:
                            context_history.pop(0)
                    
                    # Log comprehensive profiling info
                    if tool_config.profile:
                        avg_latency = metrics["total_latency"] / metrics["total_calls"]
                        avg_streaming = metrics["streaming_latency"] / metrics["total_calls"]
                        
                        logger.info(
                            f"\n[PROFILE SUMMARY] RAG Server\n"
                            f"  Current Call:\n"
                            f"    Total Time: {total_latency:.3f}s\n"
                            f"    Connection: {connection_latency:.3f}s\n"
                            f"    TTFT (First Token): {first_token_latency:.3f}s\n"
                            f"    Streaming Time: {streaming_time:.3f}s\n"
                            f"    Tokens Generated: {token_count}\n"
                            f"    Tokens/Second: {tokens_per_second:.1f}\n"
                            f"    Contexts Retrieved: {len(retrieved_contexts)}\n"
                            f"  Cumulative Stats:\n"
                            f"    Total Calls: {metrics['total_calls']}\n"
                            f"    Avg Total Latency: {avg_latency:.3f}s\n"
                            f"    Avg Streaming: {avg_streaming:.3f}s\n"
                            f"    Avg Tokens/Second: {metrics['avg_tokens_per_second']:.1f}\n"
                            f"    Total Tokens: {metrics['total_tokens_generated']}\n"
                            f"    Total Contexts: {metrics['total_contexts_retrieved']}\n"
                            f"    Errors: {metrics['errors']}\n"
                            f"    Timeouts: {metrics['timeouts']}"
                        )
                    
                    logger.info(f"{Fore.MAGENTA}RAG Response: {full_response}{Fore.RESET}")
                    logger.info(f"{'='*50}\n")
                    
                    return full_response if full_response else "No response from RAG server"
                    
        except httpx.TimeoutException:
            metrics["timeouts"] += 1
            metrics["errors"] += 1
            total_latency = time.time() - call_start
            logger.error(
                f"[ERROR] RAG server timeout after {total_latency:.3f}s (limit: {tool_config.timeout}s)"
            )
            return f"Error: RAG server timeout after {total_latency:.1f}s"
            
        except Exception as e:
            metrics["errors"] += 1
            total_latency = time.time() - call_start
            logger.error(
                f"[ERROR] RAG query failed after {total_latency:.3f}s: {str(e)}"
            )
            return f"Error querying RAG server: {str(e)}"

    # Add metadata for profiling and evaluation
    _arun.__profiling_enabled__ = tool_config.profile
    _arun.__profiling_tags__ = tool_config.tags
    _arun.__profiling_metrics__ = metrics
    _arun.__context_history__ = context_history  # For evaluation access

    yield FunctionInfo.from_fn(
        fn=_arun, 
        description="Query the RAG server with comprehensive profiling and evaluation tracking"
    )

