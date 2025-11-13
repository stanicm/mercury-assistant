"""
This module implements a text-to-image generation tool using Stable Diffusion 3.5 Large.

Key Features:
- Generates images from text prompts
- Stores images as artifacts on disk (following NAT multimodal best practices)
- Returns metadata only (not image data) to avoid context saturation
- Supports profiling and telemetry
- Configurable image dimensions and output location

NAT Multimodal Pattern:
According to NAT documentation, multimodal agents should store artifacts (images, audio, etc.) 
separately on disk and pass only metadata/references to the LLM to avoid flooding the context window.
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
import base64
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
from nat.builder.builder import Builder
from nat.builder.framework_enum import LLMFrameworkEnum
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

# Configure logging
logger = logging.getLogger(__name__)


class Text2ImageConfig(FunctionBaseConfig, name="text2image_tool"):
    """
    Configuration class for the text-to-image generation tool.
    
    Attributes:
        endpoint: Stable Diffusion API endpoint URL
        output_dir: Directory to save generated images (artifacts)
        default_height: Default image height in pixels (must be 768-1344)
        default_width: Default image width in pixels (must be 768-1344)
        timeout: Request timeout in seconds
        profile: Enable profiling/telemetry
        tags: Tags for categorization and filtering
    """
    endpoint: str = "http://localhost:8000/v1/images/generations"
    output_dir: str = "/tmp/mercury_images"
    default_height: int = 1024
    default_width: int = 1024
    timeout: int = 60
    profile: bool = False
    tags: Optional[list[str]] = ["image", "generation", "multimodal"]


@register_function(config_type=Text2ImageConfig, framework_wrappers=[LLMFrameworkEnum.LANGCHAIN])
async def text2image_tool(tool_config: Text2ImageConfig, builder: Builder):
    """
    Main function that implements the text-to-image generation tool.
    
    This tool:
    1. Accepts a text prompt from the user
    2. Calls Stable Diffusion 3.5 Large API
    3. Saves the generated image to disk (artifact storage)
    4. Returns metadata only (file path, prompt, seed, size)
    
    Following NAT multimodal best practices, images are stored as separate artifacts
    and only metadata is passed to the LLM to avoid context window saturation.
    
    Args:
        tool_config: Configuration for the image generation tool
        builder: NAT builder for creating framework-specific components
        
    Yields:
        FunctionInfo: Tool function with description for agent registration
    """
    
    # Ensure output directory exists
    output_path = Path(tool_config.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"[TEXT2IMAGE] Output directory: {output_path}")
    
    # Profiling metrics
    metrics = {
        "total_calls": 0,
        "successful_generations": 0,
        "failed_generations": 0,
        "total_latency": 0.0,
        "last_call_time": None,
        "total_images_generated": 0
    }
    
    # Valid dimensions for SD 3.5 Large
    VALID_DIMENSIONS = [768, 832, 896, 960, 1024, 1088, 1152, 1216, 1280, 1344]
    
    def validate_dimensions(height: int, width: int) -> tuple[int, int]:
        """Validate and adjust dimensions to nearest valid values."""
        if height not in VALID_DIMENSIONS:
            height = min(VALID_DIMENSIONS, key=lambda x: abs(x - height))
            logger.warning(f"[TEXT2IMAGE] Adjusted height to nearest valid value: {height}")
        if width not in VALID_DIMENSIONS:
            width = min(VALID_DIMENSIONS, key=lambda x: abs(x - width))
            logger.warning(f"[TEXT2IMAGE] Adjusted width to nearest valid value: {width}")
        return height, width
    
    async def _arun(inputs: str) -> str:
        """
        Process user input and generate an image from the text prompt.
        
        Args:
            inputs: Text prompt describing the image to generate
            
        Returns:
            String containing metadata about the generated image (not the image itself)
        """
        start_time = time.time()
        metrics["total_calls"] += 1
        
        try:
            logger.info(f"[TEXT2IMAGE] Processing prompt: {inputs[:100]}...")
            
            # Validate dimensions
            height, width = validate_dimensions(
                tool_config.default_height,
                tool_config.default_width
            )
            
            # Prepare API request
            payload = {
                "prompt": inputs,
                "height": height,
                "width": width
            }
            
            logger.info(f"[TEXT2IMAGE] Calling Stable Diffusion API at {tool_config.endpoint}")
            logger.info(f"[TEXT2IMAGE] Dimensions: {width}x{height}")
            
            # Call Stable Diffusion API
            async with httpx.AsyncClient(timeout=tool_config.timeout) as client:
                response = await client.post(
                    tool_config.endpoint,
                    json=payload
                )
                response.raise_for_status()
                
                # Parse response
                data = response.json()
                
                if "artifacts" not in data or not data["artifacts"]:
                    raise ValueError("No image artifacts in API response")
                
                artifact = data["artifacts"][0]
                img_base64 = artifact["base64"]
                seed = artifact.get("seed", "unknown")
                
                # Decode and save image
                img_binary = base64.b64decode(img_base64)
                
                # Generate filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"mercury_image_{timestamp}_{seed}.jpg"
                file_path = output_path / filename
                
                with open(file_path, "wb") as f:
                    f.write(img_binary)
                
                # Calculate metrics
                latency = time.time() - start_time
                metrics["total_latency"] += latency
                metrics["last_call_time"] = latency
                metrics["successful_generations"] += 1
                metrics["total_images_generated"] += 1
                
                img_size_kb = len(img_binary) // 1024
                
                logger.info(f"[TEXT2IMAGE] ✅ Image generated successfully!")
                logger.info(f"[TEXT2IMAGE] Saved to: {file_path}")
                logger.info(f"[TEXT2IMAGE] Size: {img_size_kb} KB")
                logger.info(f"[TEXT2IMAGE] Seed: {seed}")
                logger.info(f"[TEXT2IMAGE] Generation time: {latency:.2f}s")
                
                # Log profiling info if enabled
                if tool_config.profile:
                    avg_latency = metrics["total_latency"] / metrics["total_calls"]
                    success_rate = (metrics["successful_generations"] / metrics["total_calls"]) * 100
                    logger.info(
                        f"[PROFILE] Text2Image | "
                        f"Latency: {latency:.2f}s | "
                        f"Avg Latency: {avg_latency:.2f}s | "
                        f"Total Images: {metrics['total_images_generated']} | "
                        f"Success Rate: {success_rate:.1f}%"
                    )
                
                # Return metadata only (NAT multimodal pattern)
                # DO NOT return image data - only file path and metadata
                result = (
                    f"✅ Image generated successfully!\n"
                    f"📁 Location: {file_path}\n"
                    f"📝 Prompt: {inputs}\n"
                    f"🎲 Seed: {seed}\n"
                    f"📏 Size: {width}x{height} ({img_size_kb} KB)\n"
                    f"⏱️ Generation time: {latency:.2f}s"
                )
                
                logger.info(f"[TEXT2IMAGE] Returning metadata (not image data)")
                return result
                
        except httpx.HTTPStatusError as e:
            metrics["failed_generations"] += 1
            latency = time.time() - start_time
            logger.error(
                f"[TEXT2IMAGE] HTTP error {e.response.status_code}: {e.response.text}"
            )
            return (
                f"❌ Image generation failed (HTTP {e.response.status_code})\n"
                f"Error: {e.response.text[:200]}"
            )
            
        except httpx.TimeoutException:
            metrics["failed_generations"] += 1
            latency = time.time() - start_time
            logger.error(f"[TEXT2IMAGE] Request timed out after {tool_config.timeout}s")
            return (
                f"❌ Image generation timed out\n"
                f"The request took longer than {tool_config.timeout}s. "
                f"Try a simpler prompt or increase the timeout."
            )
            
        except Exception as e:
            metrics["failed_generations"] += 1
            latency = time.time() - start_time
            logger.error(
                f"[TEXT2IMAGE] Error generating image: {str(e)}",
                exc_info=True
            )
            return (
                f"❌ Image generation failed\n"
                f"Error: {str(e)}"
            )
    
    # Add metadata for profiling
    _arun.__profiling_enabled__ = tool_config.profile
    _arun.__tool_metrics__ = metrics
    
    yield FunctionInfo.from_fn(
        fn=_arun,
        description="Generate images from text descriptions using Stable Diffusion 3.5 Large. "
                    "Accepts a text prompt and returns the file path to the generated image. "
                    "Example: 'a serene mountain landscape at sunset, photorealistic'"
    )

