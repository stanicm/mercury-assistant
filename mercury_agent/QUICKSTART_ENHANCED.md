# 🚀 Mercury Agent Enhanced - Quick Start

Get up and running with NAT v1.3+ enhanced features in 5 minutes!

## ⚡ Fast Track Installation

```bash
cd mercury_agent

# Step 1: Update dependencies
pip install -e ".[all]"

# Step 2: Verify installation
python -c "import nat; print(f'NAT version: {nat.__version__}')"

# Step 3: Test enhanced features
python test_enhanced_features.py
```

## 🎯 Quick Examples

### Example 1: Basic Query with Profiling

```bash
nat run --config_file=configs/config_enhanced.yml \
        --input "Tell me about Albert Einstein"
```

**Output includes:**
```
[PROFILE] Wikipedia Research | Time: 2.45s | Tokens: 3456
✅ Response received in 2.45s
```

### Example 2: With Visual Observability

```bash
# Terminal 1: Launch Phoenix
pip install arize-phoenix
python -c "import phoenix as px; px.launch_app()"

# Terminal 2: Run query
python test_enhanced_features.py --phoenix --query "What is quantum mechanics?"

# Terminal 3: Open browser
# Navigate to http://localhost:6006 to see traces!
```

### Example 3: Run Evaluation

```bash
# Test RAG quality
nat evaluate --config configs/config_enhanced.yml \
             --eval-type rag \
             --test-set data/eval/rag_test_set.json
```

## 🎨 Visual Architecture

```
User Query
    ↓
┌─────────────────────────────────────────┐
│  Mercury Agent (Enhanced)               │
│  ┌─────────────────────────────────┐   │
│  │ Router (Supervisor)              │   │
│  │ ↓                                │   │
│  │ ┌──────┐  ┌───────┐  ┌──────┐  │   │
│  │ │Chitchat│ │Research│ │ RAG  │  │   │
│  │ │ Tool   │ │  Tool  │ │ Tool │  │   │
│  │ └───┬────┘ └────┬───┘ └───┬──┘  │   │
│  └─────│───────────│─────────│─────┘   │
│        │           │         │          │
│    ┌───▼───────────▼─────────▼───┐     │
│    │   Profiling & Metrics       │     │
│    │   - Latency tracking        │     │
│    │   - Token counting          │     │
│    │   - Error monitoring        │     │
│    └──────────────┬──────────────┘     │
└───────────────────┼────────────────────┘
                    ↓
        ┌───────────────────────┐
        │ Observability         │
        │ - Phoenix (visual)    │
        │ - Weave (experiments) │
        │ - Langfuse (prod)     │
        └───────────────────────┘
```

## 📊 What You Get

### 1. Profiling Metrics

Every tool call now tracks:

| Metric | Example Value | Use Case |
|--------|---------------|----------|
| Latency | 2.45s | Performance optimization |
| Tokens | 3,456 | Cost estimation |
| TTFT | 0.23s | Streaming optimization |
| Success Rate | 98.5% | Reliability monitoring |

### 2. Visual Observability (Phoenix)

See LLM calls in real-time:
- Timeline view of all tool calls
- Token usage per call
- Latency heatmaps
- Error traces

### 3. Automated Evaluation

Quality metrics for your RAG:
- Answer Relevancy: 87%
- Faithfulness: 92%
- Context Precision: 85%

## 🔄 Backward Compatibility

✅ **Your existing code still works!**

```bash
# Original config - still works
nat run --config_file=configs/config.yml --input "Hello"

# Enhanced config - with profiling
nat run --config_file=configs/config_enhanced.yml --input "Hello"
```

## 🎓 Learning Path

### Level 1: Basic Profiling (5 min)
```bash
# Use enhanced config
nat run --config_file=configs/config_enhanced.yml --input "Test query"
# ✅ See metrics in console
```

### Level 2: Visual Observability (10 min)
```python
from aiq_mercury_agent.observability import setup_phoenix
setup_phoenix()
# ✅ Open http://localhost:6006
```

### Level 3: Evaluation (15 min)
```bash
nat evaluate --config configs/config_enhanced.yml \
             --eval-type agent \
             --test-set data/eval/agent_test_set.json
# ✅ See accuracy scores
```

### Level 4: Production Setup (30 min)
```python
from aiq_mercury_agent.observability import setup_production_observability
setup_production_observability()
# ✅ Full monitoring stack
```

## 🛠️ Common Tasks

### Add Profiling to Existing Tool

**Before:**
```yaml
functions:
  my_tool:
    _type: my_tool_type
```

**After:**
```yaml
functions:
  my_tool:
    _type: my_tool_type
    profile: true  # Add this line
    tags: ["custom", "important"]
```

### Access Metrics Programmatically

```python
from nat.builder.builder import Builder

builder = Builder(config_path="configs/config_enhanced.yml")
tool = await builder.get_tool(fn_name="wikipedia_search")

# Use tool
result = await tool.ainvoke("Python")

# Get metrics
metrics = tool.__profiling_metrics__
print(f"Calls: {metrics['total_calls']}")
print(f"Avg time: {metrics['total_latency']/metrics['total_calls']:.2f}s")
```

### Create Custom Test Case

Edit `data/eval/agent_test_set.json`:

```json
{
  "test_cases": [
    {
      "id": "my_test_001",
      "query": "Your custom query",
      "expected_agent": "research",
      "evaluation_criteria": {
        "should_contain": ["keyword"],
        "min_length": 50
      }
    }
  ]
}
```

## 📈 Next Steps

1. **Run the test suite**: `python test_enhanced_features.py`
2. **Try with Phoenix**: `python test_enhanced_features.py --phoenix`
3. **Check the full guide**: [NAT_ENHANCED_GUIDE.md](./NAT_ENHANCED_GUIDE.md)
4. **Integrate with your Node.js interface**: No changes needed!

## 🆘 Need Help?

**Common Issues:**

| Issue | Solution |
|-------|----------|
| Metrics not showing | Check `profile: true` in config |
| Phoenix won't start | `pip install arize-phoenix` |
| Import errors | `pip install -e ".[all]"` |
| RAG eval fails | RAG server must be running |

**Resources:**
- Full Guide: [NAT_ENHANCED_GUIDE.md](./NAT_ENHANCED_GUIDE.md)
- Evaluation: [data/eval/README.md](./data/eval/README.md)
- Main README: [../README.md](../README.md)

## 🎉 Success Checklist

- [ ] Dependencies installed
- [ ] Test suite runs successfully
- [ ] Profiling metrics visible in logs
- [ ] Phoenix UI accessible (optional)
- [ ] Evaluation tests pass (optional)
- [ ] Node.js interface still works

**All done? You're ready to go! 🚀**

---

**Questions?** Check [NAT_ENHANCED_GUIDE.md](./NAT_ENHANCED_GUIDE.md) or open an issue.

