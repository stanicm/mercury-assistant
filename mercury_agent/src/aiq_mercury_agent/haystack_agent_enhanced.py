"""
Enhanced Haystack Chitchat Agent with NAT Profiling and Observability.

This module extends the original haystack_agent with:
- Profiling decorators for performance tracking
- Token usage monitoring
- Latency measurements
- Error tracking and logging
"""

# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
import time
from typing import Optional

from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.component_ref import LLMRef
from nat.data_models.function import FunctionBaseConfig

logger = logging.getLogger(__name__)


class HaystackChitchatEnhancedConfig(FunctionBaseConfig, name="haystack_chitchat_agent_enhanced"):
    """
    Enhanced configuration class for the Haystack chitchat agent with profiling support.
    
    Attributes:
        llm_name: Reference to the language model to be used
        base_url: The base URL for the NIM server
        profile: Enable profiling for this tool
        tags: Tags for categorizing metrics
    """
    llm_name: LLMRef
    base_url: str = "https://integrate.api.nvidia.com/v1"
    profile: bool = True
    tags: Optional[list[str]] = ["chitchat", "haystack"]


@register_function(config_type=HaystackChitchatEnhancedConfig)
async def haystack_chitchat_agent_enhanced(tool_config: HaystackChitchatEnhancedConfig, builder: Builder):
    """
    Enhanced Haystack chitchat agent with profiling capabilities.
    
    This function adds:
    - Performance metrics collection
    - Token usage tracking
    - Error rate monitoring
    - Latency measurements
    
    Args:
        tool_config: Configuration object containing the LLM reference and profiling settings
        builder: Builder object for creating framework-specific components
        
    Returns:
        A function that can be used for general conversation with profiling
    """
    from haystack_integrations.components.generators.nvidia import NvidiaGenerator

    # Initialize the NVIDIA generator
    generator = NvidiaGenerator(
        model=tool_config.llm_name,
        api_url=tool_config.base_url,
        model_arguments={
            "temperature": 0.5,
            "top_p": 0.9,
            "max_tokens": 1024,
        }
    )

    # Warm up is required by Haystack
    generator.warm_up()

    # Profiling metrics storage
    metrics = {
        "total_calls": 0,
        "total_tokens": 0,
        "total_latency": 0.0,
        "errors": 0,
        "last_call_time": None
    }

    async def _arun(inputs: str) -> str:
        """
        Process user input with profiling metrics.
        
        Args:
            inputs: The user's input text to be processed
            
        Returns:
            str: The generated response from the language model
        """
        start_time = time.time()
        
        try:
            # Track call
            metrics["total_calls"] += 1
            
            logger.info(f"[HAYSTACK_CHITCHAT] Processing input: {inputs[:50]}...")
            
            # Run the synchronous Haystack generator in an executor
            import asyncio
            loop = asyncio.get_event_loop()
            out = await loop.run_in_executor(None, lambda: generator.run(prompt=inputs))
            output = out["replies"][0]
            
            # Calculate latency
            latency = time.time() - start_time
            metrics["total_latency"] += latency
            metrics["last_call_time"] = latency
            
            # Estimate tokens (rough approximation: ~4 chars per token)
            estimated_tokens = (len(inputs) + len(output)) // 4
            metrics["total_tokens"] += estimated_tokens
            
            # Log profiling info
            if tool_config.profile:
                logger.info(
                    f"[PROFILE] Haystack Chitchat | "
                    f"Latency: {latency:.2f}s | "
                    f"Est. Tokens: {estimated_tokens} | "
                    f"Total Calls: {metrics['total_calls']} | "
                    f"Avg Latency: {metrics['total_latency']/metrics['total_calls']:.2f}s"
                )
            
            logger.info("output from haystack_chitchat_agent_enhanced: %s", output)
            return output
            
        except Exception as e:
            metrics["errors"] += 1
            latency = time.time() - start_time
            logger.error(
                f"[ERROR] Haystack Chitchat failed after {latency:.2f}s: {str(e)}"
            )
            raise

    # Add metadata for profiling
    _arun.__profiling_enabled__ = tool_config.profile
    _arun.__profiling_tags__ = tool_config.tags
    _arun.__profiling_metrics__ = metrics

    yield FunctionInfo.from_fn(
        fn=_arun, 
        description="handle general conversation and chitchat queries with profiling"
    )

