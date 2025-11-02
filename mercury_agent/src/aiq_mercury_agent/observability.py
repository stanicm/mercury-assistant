"""
Observability integration for Mercury Agent using NAT telemetry.

This module provides integrations for:
- OpenTelemetry (base telemetry)
- Phoenix (Arize AI)
- Weights & Biases Weave
- Langfuse

Usage:
    from aiq_mercury_agent.observability import setup_observability
    
    # In your workflow or startup script
    setup_observability(
        service_name="mercury_agent",
        phoenix_enabled=True,
        weave_enabled=False,
        langfuse_enabled=False
    )
"""

# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def setup_opentelemetry(
    service_name: str = "mercury_agent",
    export_console: bool = True,
    export_endpoint: Optional[str] = None
):
    """
    Set up OpenTelemetry for basic telemetry.
    
    Args:
        service_name: Name of the service for telemetry
        export_console: Whether to export metrics to console
        export_endpoint: Optional OTLP endpoint for exporting traces
    """
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
        from opentelemetry.sdk.resources import Resource
        
        # Create a resource with service name
        resource = Resource(attributes={
            "service.name": service_name,
            "service.version": "1.0.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "development")
        })
        
        # Set up tracer provider
        provider = TracerProvider(resource=resource)
        
        # Add console exporter if requested
        if export_console:
            console_exporter = ConsoleSpanExporter()
            provider.add_span_processor(BatchSpanProcessor(console_exporter))
            logger.info("✅ OpenTelemetry console exporter enabled")
        
        # Add OTLP exporter if endpoint provided
        if export_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                otlp_exporter = OTLPSpanExporter(endpoint=export_endpoint)
                provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
                logger.info(f"✅ OpenTelemetry OTLP exporter enabled: {export_endpoint}")
            except ImportError:
                logger.warning("⚠️ opentelemetry-exporter-otlp not installed")
        
        # Set the global tracer provider
        trace.set_tracer_provider(provider)
        logger.info(f"✅ OpenTelemetry initialized for service: {service_name}")
        
    except ImportError as e:
        logger.warning(f"⚠️ OpenTelemetry not available: {e}")


def setup_phoenix(
    project_name: str = "mercury_agent",
    endpoint: str = "http://localhost:6006"
):
    """
    Set up Phoenix (Arize AI) for observability.
    
    Phoenix provides:
    - LLM trace visualization
    - Prompt engineering tools
    - Evaluation dashboards
    
    Args:
        project_name: Name of the Phoenix project
        endpoint: Phoenix server endpoint
    
    Installation:
        pip install arize-phoenix
    
    Running Phoenix:
        python -m phoenix.server.main serve
    """
    try:
        import phoenix as px
        from phoenix.trace.langchain import LangChainInstrumentor
        
        # Launch Phoenix if not already running
        try:
            session = px.launch_app(host="0.0.0.0", port=6006)
            logger.info(f"✅ Phoenix launched at: {session.url}")
        except Exception as e:
            logger.info(f"Phoenix already running or connection to existing instance: {e}")
        
        # Instrument LangChain for automatic tracing
        LangChainInstrumentor().instrument()
        logger.info("✅ Phoenix LangChain instrumentation enabled")
        
        # Set project name
        os.environ["PHOENIX_PROJECT_NAME"] = project_name
        logger.info(f"✅ Phoenix project: {project_name}")
        
        return True
        
    except ImportError:
        logger.warning(
            "⚠️ Phoenix not available. Install with: pip install arize-phoenix"
        )
        return False


def setup_weave(
    project_name: str = "mercury-agent",
    api_key: Optional[str] = None
):
    """
    Set up Weights & Biases Weave for observability.
    
    Weave provides:
    - Automatic LLM call tracking
    - Evaluation tools
    - Dataset versioning
    - Cost tracking
    
    Args:
        project_name: Name of the W&B project
        api_key: W&B API key (or set WANDB_API_KEY env var)
    
    Installation:
        pip install weave
    """
    try:
        import weave
        
        # Get API key from parameter or environment
        api_key = api_key or os.getenv("WANDB_API_KEY")
        
        if not api_key:
            logger.warning(
                "⚠️ Weave requires WANDB_API_KEY. "
                "Set it via environment variable or pass to setup_weave()"
            )
            return False
        
        # Initialize Weave
        weave.init(project_name)
        logger.info(f"✅ Weave initialized for project: {project_name}")
        
        return True
        
    except ImportError:
        logger.warning(
            "⚠️ Weave not available. Install with: pip install weave"
        )
        return False


def setup_langfuse(
    public_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    host: str = "https://cloud.langfuse.com"
):
    """
    Set up Langfuse for observability.
    
    Langfuse provides:
    - LLM observability
    - Prompt management
    - User feedback collection
    - Cost tracking
    
    Args:
        public_key: Langfuse public key (or set LANGFUSE_PUBLIC_KEY)
        secret_key: Langfuse secret key (or set LANGFUSE_SECRET_KEY)
        host: Langfuse host URL
    
    Installation:
        pip install langfuse
    """
    try:
        from langfuse import Langfuse
        from langfuse.callback import CallbackHandler
        
        # Get keys from parameters or environment
        public_key = public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
        secret_key = secret_key or os.getenv("LANGFUSE_SECRET_KEY")
        
        if not (public_key and secret_key):
            logger.warning(
                "⚠️ Langfuse requires LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY. "
                "Set them via environment variables or pass to setup_langfuse()"
            )
            return False
        
        # Initialize Langfuse
        langfuse = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host
        )
        
        # Create callback handler for LangChain integration
        callback_handler = CallbackHandler(
            public_key=public_key,
            secret_key=secret_key,
            host=host
        )
        
        # Store globally for use in workflows
        os.environ["LANGFUSE_ENABLED"] = "true"
        
        logger.info(f"✅ Langfuse initialized at: {host}")
        
        return callback_handler
        
    except ImportError:
        logger.warning(
            "⚠️ Langfuse not available. Install with: pip install langfuse"
        )
        return False


def setup_observability(
    service_name: str = "mercury_agent",
    phoenix_enabled: bool = False,
    phoenix_endpoint: str = "http://localhost:6006",
    weave_enabled: bool = False,
    weave_project: str = "mercury-agent",
    langfuse_enabled: bool = False,
    opentelemetry_enabled: bool = True,
    console_export: bool = True
):
    """
    One-stop setup for all observability integrations.
    
    Args:
        service_name: Name of the service
        phoenix_enabled: Enable Phoenix (Arize AI)
        phoenix_endpoint: Phoenix server endpoint
        weave_enabled: Enable W&B Weave
        weave_project: Weave project name
        langfuse_enabled: Enable Langfuse
        opentelemetry_enabled: Enable OpenTelemetry
        console_export: Export traces to console
    
    Returns:
        dict: Status of each integration
    """
    results = {}
    
    logger.info("=" * 60)
    logger.info("🔍 Setting up Mercury Agent Observability")
    logger.info("=" * 60)
    
    # OpenTelemetry (base layer)
    if opentelemetry_enabled:
        setup_opentelemetry(
            service_name=service_name,
            export_console=console_export
        )
        results["opentelemetry"] = True
    
    # Phoenix (Arize AI)
    if phoenix_enabled:
        results["phoenix"] = setup_phoenix(
            project_name=service_name,
            endpoint=phoenix_endpoint
        )
    
    # W&B Weave
    if weave_enabled:
        results["weave"] = setup_weave(
            project_name=weave_project
        )
    
    # Langfuse
    if langfuse_enabled:
        langfuse_handler = setup_langfuse()
        results["langfuse"] = bool(langfuse_handler)
    
    logger.info("=" * 60)
    logger.info("✅ Observability setup complete")
    logger.info(f"   Active integrations: {[k for k, v in results.items() if v]}")
    logger.info("=" * 60)
    
    return results


# Quick setup functions for common configurations

def setup_development_observability():
    """Quick setup for development: Console + Phoenix."""
    return setup_observability(
        phoenix_enabled=True,
        console_export=True
    )


def setup_production_observability():
    """Quick setup for production: All integrations."""
    return setup_observability(
        phoenix_enabled=True,
        weave_enabled=True,
        langfuse_enabled=True,
        console_export=False
    )


# Example usage
if __name__ == "__main__":
    # Development setup
    print("\n=== Development Setup ===")
    setup_development_observability()
    
    # Production setup (requires API keys)
    # print("\n=== Production Setup ===")
    # setup_production_observability()

