#!/usr/bin/env python3
"""
Proof-of-Concept Test Script for Enhanced Mercury Agent with NAT v1.3+ Features

This script demonstrates:
1. Enhanced profiling capabilities
2. Observability integration (Phoenix)
3. Performance metrics collection
4. Token usage tracking
5. Latency measurements
6. Error handling and monitoring

Usage:
    python test_enhanced_features.py
    
    # With observability
    python test_enhanced_features.py --phoenix
    
    # With specific test queries
    python test_enhanced_features.py --query "Tell me about Albert Einstein"
"""

# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def setup_environment():
    """Set up environment variables for testing."""
    # Check for required API keys
    if not os.getenv("NVIDIA_API_KEY"):
        logger.warning("⚠️ NVIDIA_API_KEY not set. Using cloud models may fail.")
    
    # Set default paths
    project_root = Path(__file__).parent
    os.environ.setdefault("MERCURY_CONFIG", str(project_root / "configs" / "config_enhanced.yml"))


async def test_basic_workflow():
    """Test basic workflow without enhancements."""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Basic Workflow (Original Config)")
    logger.info("="*60)
    
    from nat.cli.run import run_workflow
    
    config_path = "configs/config.yml"
    test_queries = [
        "Hello!",
        "What is quantum mechanics?",
    ]
    
    results = []
    for query in test_queries:
        logger.info(f"\n📝 Query: {query}")
        start = time.time()
        
        try:
            result = await run_workflow(
                config_file=config_path,
                input_message=query
            )
            elapsed = time.time() - start
            
            logger.info(f"✅ Response received in {elapsed:.2f}s")
            logger.info(f"📄 Response length: {len(result)} chars")
            
            results.append({
                "query": query,
                "response_length": len(result),
                "latency": elapsed,
                "success": True
            })
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            results.append({
                "query": query,
                "error": str(e),
                "success": False
            })
    
    return results


async def test_enhanced_workflow():
    """Test enhanced workflow with profiling."""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Enhanced Workflow (With Profiling)")
    logger.info("="*60)
    
    from nat.cli.run import run_workflow
    
    config_path = "configs/config_enhanced.yml"
    test_queries = [
        "Hello, how are you?",  # Should route to chitchat
        "Tell me about Python programming",  # Should route to research
        "What is SPH?",  # Should route to RAG (if server is running)
    ]
    
    results = []
    for query in test_queries:
        logger.info(f"\n📝 Query: {query}")
        start = time.time()
        
        try:
            result = await run_workflow(
                config_file=config_path,
                input_message=query
            )
            elapsed = time.time() - start
            
            logger.info(f"✅ Response received in {elapsed:.2f}s")
            logger.info(f"📄 Response length: {len(result)} chars")
            
            results.append({
                "query": query,
                "response_length": len(result),
                "latency": elapsed,
                "success": True
            })
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            results.append({
                "query": query,
                "error": str(e),
                "success": False
            })
    
    return results


async def test_individual_tools():
    """Test individual enhanced tools directly."""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Individual Enhanced Tools")
    logger.info("="*60)
    
    from nat.builder.builder import Builder
    
    # Load configuration
    config_path = "configs/config_enhanced.yml"
    builder = Builder(config_path=config_path)
    
    results = {}
    
    # Test 1: Wikipedia Research Tool
    logger.info("\n🔍 Testing Wikipedia Research Tool...")
    try:
        from nat.builder.framework_enum import LLMFrameworkEnum
        
        research_tool = await builder.get_tool(
            fn_name="wikipedia_search",
            wrapper_type=LLMFrameworkEnum.LANGCHAIN
        )
        
        start = time.time()
        result = await research_tool.ainvoke("Albert Einstein")
        elapsed = time.time() - start
        
        # Extract metrics if available
        metrics = getattr(research_tool, '__profiling_metrics__', None)
        
        results['wikipedia_tool'] = {
            "success": True,
            "latency": elapsed,
            "response_length": len(result),
            "metrics": metrics
        }
        
        logger.info(f"✅ Wikipedia tool completed in {elapsed:.2f}s")
        if metrics:
            logger.info(f"📊 Metrics: {json.dumps(metrics, indent=2)}")
        
    except Exception as e:
        logger.error(f"❌ Wikipedia tool error: {e}")
        results['wikipedia_tool'] = {"success": False, "error": str(e)}
    
    # Test 2: RAG Tool (if server is available)
    logger.info("\n📚 Testing RAG Tool...")
    try:
        rag_tool = await builder.get_tool(
            fn_name="nvbp_rag",
            wrapper_type=LLMFrameworkEnum.LANGCHAIN
        )
        
        start = time.time()
        result = await rag_tool.ainvoke("What is SPH?")
        elapsed = time.time() - start
        
        metrics = getattr(rag_tool, '__profiling_metrics__', None)
        
        results['rag_tool'] = {
            "success": True,
            "latency": elapsed,
            "response_length": len(result),
            "metrics": metrics
        }
        
        logger.info(f"✅ RAG tool completed in {elapsed:.2f}s")
        if metrics:
            logger.info(f"📊 Metrics: {json.dumps(metrics, indent=2)}")
        
    except Exception as e:
        logger.warning(f"⚠️ RAG tool error (server may not be running): {e}")
        results['rag_tool'] = {"success": False, "error": str(e)}
    
    # Test 3: Chitchat Agent
    logger.info("\n💬 Testing Chitchat Agent...")
    try:
        chitchat_agent = await builder.get_tool(
            fn_name="haystack_chitchat_agent",
            wrapper_type=LLMFrameworkEnum.LANGCHAIN
        )
        
        start = time.time()
        result = await chitchat_agent.ainvoke("Hello, how are you?")
        elapsed = time.time() - start
        
        metrics = getattr(chitchat_agent, '__profiling_metrics__', None)
        
        results['chitchat_agent'] = {
            "success": True,
            "latency": elapsed,
            "response_length": len(result),
            "metrics": metrics
        }
        
        logger.info(f"✅ Chitchat agent completed in {elapsed:.2f}s")
        if metrics:
            logger.info(f"📊 Metrics: {json.dumps(metrics, indent=2)}")
        
    except Exception as e:
        logger.error(f"❌ Chitchat agent error: {e}")
        results['chitchat_agent'] = {"success": False, "error": str(e)}
    
    return results


async def test_profiling_metrics():
    """Test profiling metrics collection."""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: Profiling Metrics Collection")
    logger.info("="*60)
    
    # Run multiple queries to accumulate metrics
    from nat.cli.run import run_workflow
    
    config_path = "configs/config_enhanced.yml"
    queries = [
        "Hello!",
        "What is Python?",
        "Tell me about Mars",
        "Who was Shakespeare?",
    ]
    
    all_metrics = []
    
    for i, query in enumerate(queries, 1):
        logger.info(f"\n[{i}/{len(queries)}] Query: {query}")
        start = time.time()
        
        try:
            result = await run_workflow(
                config_file=config_path,
                input_message=query
            )
            elapsed = time.time() - start
            
            all_metrics.append({
                "query": query,
                "latency": elapsed,
                "response_length": len(result),
                "success": True
            })
            
            logger.info(f"✅ Completed in {elapsed:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            all_metrics.append({
                "query": query,
                "error": str(e),
                "success": False
            })
    
    # Calculate aggregate metrics
    successful_queries = [m for m in all_metrics if m.get("success")]
    if successful_queries:
        avg_latency = sum(m["latency"] for m in successful_queries) / len(successful_queries)
        total_latency = sum(m["latency"] for m in successful_queries)
        
        logger.info("\n📊 AGGREGATE METRICS:")
        logger.info(f"   Total Queries: {len(queries)}")
        logger.info(f"   Successful: {len(successful_queries)}")
        logger.info(f"   Failed: {len(queries) - len(successful_queries)}")
        logger.info(f"   Average Latency: {avg_latency:.2f}s")
        logger.info(f"   Total Time: {total_latency:.2f}s")
        logger.info(f"   Success Rate: {len(successful_queries)/len(queries)*100:.1f}%")
    
    return all_metrics


async def run_all_tests(enable_phoenix: bool = False, custom_query: Optional[str] = None):
    """Run all test suites."""
    logger.info("\n" + "="*70)
    logger.info(" 🚀 MERCURY AGENT ENHANCED FEATURES TEST SUITE")
    logger.info("="*70)
    
    # Setup observability if requested
    if enable_phoenix:
        logger.info("\n🔍 Setting up Phoenix observability...")
        try:
            from aiq_mercury_agent.observability import setup_phoenix
            setup_phoenix()
        except ImportError:
            logger.warning("⚠️ Phoenix not available. Install with: pip install arize-phoenix")
    
    test_results = {}
    
    # Custom query test
    if custom_query:
        logger.info("\n" + "="*60)
        logger.info("CUSTOM QUERY TEST")
        logger.info("="*60)
        
        from nat.cli.run import run_workflow
        config_path = "configs/config_enhanced.yml"
        
        logger.info(f"📝 Query: {custom_query}")
        start = time.time()
        
        try:
            result = await run_workflow(
                config_file=config_path,
                input_message=custom_query
            )
            elapsed = time.time() - start
            
            logger.info(f"✅ Response received in {elapsed:.2f}s")
            logger.info(f"\n📄 Response:\n{result}\n")
            
            test_results['custom_query'] = {
                "query": custom_query,
                "response": result[:200] + "..." if len(result) > 200 else result,
                "latency": elapsed,
                "success": True
            }
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            test_results['custom_query'] = {"error": str(e), "success": False}
        
        return test_results
    
    # Run standard test suite
    try:
        # Test 1: Basic workflow
        test_results['basic_workflow'] = await test_basic_workflow()
    except Exception as e:
        logger.error(f"Basic workflow test failed: {e}")
        test_results['basic_workflow'] = {"error": str(e)}
    
    try:
        # Test 2: Enhanced workflow
        test_results['enhanced_workflow'] = await test_enhanced_workflow()
    except Exception as e:
        logger.error(f"Enhanced workflow test failed: {e}")
        test_results['enhanced_workflow'] = {"error": str(e)}
    
    try:
        # Test 3: Individual tools
        test_results['individual_tools'] = await test_individual_tools()
    except Exception as e:
        logger.error(f"Individual tools test failed: {e}")
        test_results['individual_tools'] = {"error": str(e)}
    
    try:
        # Test 4: Profiling metrics
        test_results['profiling_metrics'] = await test_profiling_metrics()
    except Exception as e:
        logger.error(f"Profiling metrics test failed: {e}")
        test_results['profiling_metrics'] = {"error": str(e)}
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info(" 📊 TEST SUMMARY")
    logger.info("="*70)
    
    for test_name, results in test_results.items():
        logger.info(f"\n{test_name.upper().replace('_', ' ')}:")
        if isinstance(results, dict) and "error" in results:
            logger.info(f"  ❌ FAILED: {results['error']}")
        elif isinstance(results, list):
            success_count = sum(1 for r in results if r.get("success"))
            logger.info(f"  ✅ Completed: {success_count}/{len(results)} queries")
        else:
            logger.info(f"  ✅ Completed")
    
    # Save results to file
    results_file = Path("test_results.json")
    with open(results_file, "w") as f:
        json.dump(test_results, f, indent=2, default=str)
    
    logger.info(f"\n💾 Results saved to: {results_file}")
    logger.info("\n" + "="*70)
    logger.info(" ✅ TEST SUITE COMPLETE")
    logger.info("="*70)
    
    return test_results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test enhanced Mercury Agent features with NAT v1.3+"
    )
    parser.add_argument(
        "--phoenix",
        action="store_true",
        help="Enable Phoenix observability"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Run a custom query instead of the full test suite"
    )
    
    args = parser.parse_args()
    
    # Setup environment
    setup_environment()
    
    # Run tests
    try:
        asyncio.run(run_all_tests(
            enable_phoenix=args.phoenix,
            custom_query=args.query
        ))
    except KeyboardInterrupt:
        logger.info("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

