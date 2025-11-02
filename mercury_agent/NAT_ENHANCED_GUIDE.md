# Mercury Agent - NAT v1.3+ Enhanced Features Guide

This guide explains how to use the enhanced Mercury Agent with NeMo Agent Toolkit (NAT) v1.3+ features including profiling, observability, and evaluation.

## 📋 Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Enhanced Features](#enhanced-features)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Profiling](#profiling)
- [Observability](#observability)
- [Evaluation](#evaluation)
- [Migration from Original](#migration-from-original)
- [Troubleshooting](#troubleshooting)

## 🌟 Overview

The enhanced Mercury Agent adds powerful production-ready features on top of your existing NAT implementation:

### What's New

| Feature | Description | Benefit |
|---------|-------------|---------|
| **Profiling** | Track latency, tokens, costs per tool/agent | Optimize performance & costs |
| **Observability** | Phoenix, Weave, Langfuse integration | Debug & monitor in production |
| **Evaluation** | Automated RAG & agent quality metrics | Ensure accuracy |
| **Enhanced Tools** | Profiling-enabled versions of all tools | Detailed performance insights |

### Architecture

```
Mercury Agent (Enhanced)
├── Original Tools (backward compatible)
│   ├── haystack_agent.py
│   ├── langchain_research_tool.py
│   └── nvbp_rag_tool.py
│
├── Enhanced Tools (with profiling)
│   ├── haystack_agent_enhanced.py
│   ├── langchain_research_tool_enhanced.py
│   └── nvbp_rag_tool_enhanced.py
│
├── New Capabilities
│   ├── observability.py (Phoenix/Weave/Langfuse)
│   ├── config_enhanced.yml (profiling config)
│   └── Evaluation datasets & metrics
│
└── Backward Compatible!
```

## 🚀 Installation

### Step 1: Update Dependencies

```bash
cd mercury_agent

# Reinstall with new dependencies
pip install -e .

# Or install with all optional features
pip install -e ".[all]"
```

### Step 2: Install Optional Packages

```bash
# For observability
pip install ".[observability]"

# For evaluation
pip install ".[evaluation]"

# For development tools
pip install ".[dev]"
```

### Step 3: Verify Installation

```bash
# Check NAT version
python -c "import nat; print(nat.__version__)"

# Should be >= 1.3.0
```

## ✨ Enhanced Features

### 1. Profiling

Track detailed metrics for every tool and agent:

- **Latency**: Total time, TTFT (Time To First Token)
- **Token Usage**: Input/output tokens, cost estimation
- **Success Rates**: Error tracking and timeouts
- **Throughput**: Tokens per second for streaming

#### Example Output

```
[PROFILE SUMMARY] Wikipedia Research
  Current Call:
    Total Time: 2.456s
    Topic Extraction: 0.234s
    Wikipedia Search: 1.123s
    Est. Tokens: 3456
  Cumulative Stats:
    Total Calls: 15
    Avg Latency: 2.123s
    Avg Tokens/Second: 450.5
    Errors: 0
```

### 2. Observability

#### Phoenix (Arize AI)

Visual LLM tracing and debugging:

```python
from aiq_mercury_agent.observability import setup_phoenix

# Launch Phoenix server
setup_phoenix()

# Access UI at http://localhost:6006
```

#### Weights & Biases Weave

Track experiments and evaluations:

```python
from aiq_mercury_agent.observability import setup_weave

setup_weave(project_name="mercury-agent")
```

#### Langfuse

Production observability:

```python
from aiq_mercury_agent.observability import setup_langfuse

setup_langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY")
)
```

### 3. Evaluation

Automated quality metrics for RAG and agents:

```bash
# Run RAG evaluation
nat evaluate --config configs/config_enhanced.yml \
             --eval-type rag \
             --test-set data/eval/rag_test_set.json

# Run agent evaluation
nat evaluate --config configs/config_enhanced.yml \
             --eval-type agent \
             --test-set data/eval/agent_test_set.json
```

## ⚙️ Configuration

### Basic Configuration (Original)

`configs/config.yml` - Your existing configuration (still works!)

### Enhanced Configuration

`configs/config_enhanced.yml` - New configuration with profiling

Key additions:

```yaml
# Enable telemetry
telemetry:
  _type: opentelemetry
  enabled: true
  service_name: mercury_agent
  export_console: true

# Enable profiling
profiler:
  enabled: true
  track_tokens: true
  track_latency: true
  track_cost: true

# Enable evaluation
evaluation:
  enabled: false  # Set to true when ready
  rag_eval:
    metrics: [answer_relevancy, faithfulness]
```

### Per-Tool Configuration

Enable profiling for specific tools:

```yaml
functions:
  wikipedia_search:
    _type: langchain_researcher_tool_enhanced  # Use enhanced version
    llm_name: nim_llm
    profile: true  # Enable profiling
    tags: ["research", "wikipedia"]  # For categorization
```

## 📚 Usage Examples

### Example 1: Basic Usage (No Changes Needed)

Your existing code still works:

```bash
cd mercury_agent
nat run --config_file=configs/config.yml --input "Hello!"
```

### Example 2: With Profiling

Use enhanced configuration:

```bash
nat run --config_file=configs/config_enhanced.yml --input "Tell me about Einstein"
```

Output includes profiling metrics:

```
[PROFILE] Wikipedia Research | Time: 2.45s | Tokens: 3456 | Avg: 2.12s
```

### Example 3: With Observability

```python
import asyncio
from aiq_mercury_agent.observability import setup_development_observability
from nat.cli.run import run_workflow

async def main():
    # Setup Phoenix for visualization
    setup_development_observability()
    
    # Run query
    result = await run_workflow(
        config_file="configs/config_enhanced.yml",
        input_message="What is quantum mechanics?"
    )
    
    print(f"Result: {result}")
    # Check Phoenix UI at http://localhost:6006 for traces!

asyncio.run(main())
```

### Example 4: Running Test Suite

```bash
# Run comprehensive test suite
python test_enhanced_features.py

# With Phoenix observability
python test_enhanced_features.py --phoenix

# Custom query
python test_enhanced_features.py --query "Tell me about Mars"
```

### Example 5: Programmatic Access to Metrics

```python
from nat.builder.builder import Builder
from nat.builder.framework_enum import LLMFrameworkEnum

async def get_tool_metrics():
    builder = Builder(config_path="configs/config_enhanced.yml")
    
    # Get enhanced tool
    tool = await builder.get_tool(
        fn_name="wikipedia_search",
        wrapper_type=LLMFrameworkEnum.LANGCHAIN
    )
    
    # Use the tool
    result = await tool.ainvoke("Python programming")
    
    # Access metrics
    metrics = tool.__profiling_metrics__
    print(f"Total calls: {metrics['total_calls']}")
    print(f"Avg latency: {metrics['total_latency']/metrics['total_calls']:.2f}s")
```

## 📊 Profiling

### Metrics Collected

#### Per-Tool Metrics

| Metric | Description | Use Case |
|--------|-------------|----------|
| `total_calls` | Number of invocations | Usage tracking |
| `total_latency` | Cumulative time | Performance monitoring |
| `total_tokens` | Token usage | Cost estimation |
| `errors` | Error count | Reliability tracking |
| `avg_tokens_per_second` | Streaming rate | Throughput analysis |

#### RAG-Specific Metrics

- **Connection Latency**: Time to connect to RAG server
- **TTFT**: Time to first token (streaming)
- **Contexts Retrieved**: Number of knowledge base chunks
- **Token Streaming Rate**: Tokens per second

#### Research Tool Metrics

- **Topic Extraction Time**: LLM time to extract query topic
- **Wikipedia Search Time**: External API latency
- **Content Size**: Retrieved document size

### Accessing Metrics

Metrics are automatically logged and also available programmatically:

```python
# After running a tool
metrics = tool.__profiling_metrics__

# Example: Calculate cost
estimated_cost = metrics['total_tokens'] * COST_PER_TOKEN
```

### Custom Metrics

Add your own metrics to enhanced tools:

```python
# In your enhanced tool
metrics["custom_metric"] = value
logger.info(f"Custom metric: {value}")
```

## 🔍 Observability

### Phoenix Setup

```bash
# Install Phoenix
pip install arize-phoenix

# In your code
from aiq_mercury_agent.observability import setup_phoenix
setup_phoenix()

# Access UI at http://localhost:6006
```

**Phoenix Features:**
- Visual trace timeline
- LLM call inspection
- Prompt/completion viewer
- Token counting
- Latency heatmaps

### Weave Setup

```bash
# Install Weave
pip install weave

# Set API key
export WANDB_API_KEY="your-key"

# In your code
from aiq_mercury_agent.observability import setup_weave
setup_weave(project_name="mercury-agent")
```

**Weave Features:**
- Automatic call tracking
- Dataset versioning
- Cost tracking
- Custom evaluations

### Langfuse Setup

```bash
# Install Langfuse
pip install langfuse

# Set keys
export LANGFUSE_PUBLIC_KEY="pk-..."
export LANGFUSE_SECRET_KEY="sk-..."

# In your code
from aiq_mercury_agent.observability import setup_langfuse
setup_langfuse()
```

**Langfuse Features:**
- Production tracing
- User feedback collection
- Prompt management
- Cost analytics

### All-in-One Setup

```python
from aiq_mercury_agent.observability import setup_observability

# Enable everything
setup_observability(
    phoenix_enabled=True,
    weave_enabled=True,
    langfuse_enabled=True
)
```

## 📈 Evaluation

### RAG Evaluation

Tests retrieval quality and answer accuracy:

**Metrics:**
- **Answer Relevancy**: Is the answer relevant to the question?
- **Faithfulness**: Does the answer stay true to retrieved context?
- **Context Precision**: Are retrieved contexts relevant?
- **Context Recall**: Are all relevant contexts retrieved?

**Running Evaluation:**

```bash
nat evaluate --config configs/config_enhanced.yml \
             --eval-type rag \
             --test-set data/eval/rag_test_set.json \
             --output data/eval/results/
```

### Agent Evaluation

Tests agent routing and tool selection:

**Metrics:**
- **Task Success Rate**: Did the agent complete the task?
- **Response Quality**: Is the response accurate?
- **Tool Selection Accuracy**: Was the right tool chosen?

### Creating Custom Test Sets

Edit `data/eval/rag_test_set.json`:

```json
{
  "test_cases": [
    {
      "id": "custom_001",
      "query": "Your test query",
      "expected_answer": "Expected response",
      "evaluation_criteria": {
        "should_contain": ["keyword1", "keyword2"],
        "should_not_contain": ["error"],
        "min_length": 50
      }
    }
  ]
}
```

## 🔄 Migration from Original

### Backward Compatibility

✅ **All existing code continues to work!**

```bash
# Original config still works
nat run --config_file=configs/config.yml --input "Hello"

# Node.js interface unchanged
cd ../mercury_interface
node server.js
```

### Gradual Migration Path

**Phase 1: Add Profiling** (No code changes)
```yaml
# In config_enhanced.yml
profiler:
  enabled: true
```

**Phase 2: Enhanced Tools** (Optional)
```yaml
# Switch to enhanced versions
functions:
  wikipedia_search:
    _type: langchain_researcher_tool_enhanced  # Add "_enhanced"
```

**Phase 3: Add Observability** (When ready)
```python
from aiq_mercury_agent.observability import setup_phoenix
setup_phoenix()
```

**Phase 4: Enable Evaluation** (For production)
```yaml
evaluation:
  enabled: true
```

### Side-by-Side Comparison

| Aspect | Original | Enhanced |
|--------|----------|----------|
| Config | `config.yml` | `config_enhanced.yml` |
| Tools | `haystack_agent.py` | `haystack_agent_enhanced.py` |
| Profiling | ❌ | ✅ |
| Observability | ❌ | ✅ |
| Evaluation | ❌ | ✅ |
| Backward Compatible | ✅ | ✅ |

## 🐛 Troubleshooting

### Issue: Profiling metrics not showing

**Solution:**
```yaml
# In config_enhanced.yml, ensure:
profiler:
  enabled: true
  print_summary: true  # Add this
```

### Issue: Phoenix won't start

**Solution:**
```bash
# Install Phoenix
pip install arize-phoenix

# Check if port 6006 is available
lsof -i :6006

# Kill existing process if needed
kill $(lsof -t -i :6006)
```

### Issue: RAG evaluation fails

**Cause:** RAG server not running

**Solution:**
```bash
# Check if RAG server is running
curl http://localhost:8081/v1/health

# Or skip RAG tests
nat evaluate --config configs/config_enhanced.yml \
             --eval-type agent  # Only agent eval
```

### Issue: Import errors

**Solution:**
```bash
# Reinstall package
cd mercury_agent
pip uninstall aiq_mercury_agent
pip install -e ".[all]"

# Verify installation
python -c "from aiq_mercury_agent import observability; print('OK')"
```

### Issue: Metrics showing zero tokens

**Cause:** Using original tools, not enhanced versions

**Solution:**
```yaml
# Switch to enhanced tools in config_enhanced.yml
functions:
  wikipedia_search:
    _type: langchain_researcher_tool_enhanced  # Not langchain_researcher_tool
```

## 📖 Additional Resources

- **NAT Documentation**: https://docs.nvidia.com/nat/
- **Phoenix Docs**: https://docs.arize.com/phoenix
- **Weave Docs**: https://docs.wandb.ai/guides/weave
- **Langfuse Docs**: https://langfuse.com/docs
- **Ragas Metrics**: https://docs.ragas.io/

## 🤝 Contributing

Found a bug or want to add features? Please:

1. Test with `test_enhanced_features.py`
2. Run linters: `ruff check .`
3. Update this guide if needed
4. Submit PR with profiling metrics included

## 📝 License

Same as Mercury Agent: Apache License 2.0

---

**Questions?** Open an issue or check the main [README.md](../README.md)

