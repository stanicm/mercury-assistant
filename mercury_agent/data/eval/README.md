# Mercury Agent Evaluation

This directory contains evaluation datasets and results for the Mercury Agent system.

## Directory Structure

```
eval/
├── README.md                    # This file
├── rag_test_set.json           # Test cases for RAG evaluation
├── agent_test_set.json         # Test cases for agent workflow evaluation
└── results/                     # Evaluation results (generated)
    ├── rag_eval_YYYYMMDD.json
    └── agent_eval_YYYYMMDD.json
```

## RAG Evaluation

The RAG evaluation measures the quality of retrieval-augmented generation using these metrics:

### Metrics

1. **Answer Relevancy**: How relevant is the generated answer to the query?
2. **Faithfulness**: Does the answer stay faithful to the retrieved context?
3. **Context Precision**: Are the retrieved contexts relevant?
4. **Context Recall**: Are all relevant contexts retrieved?

### Test Set Format (`rag_test_set.json`)

```json
{
  "test_cases": [
    {
      "query": "What is Smoothed Particle Hydrodynamics?",
      "expected_answer": "SPH is a computational method used for simulating fluid flows...",
      "ground_truth_contexts": [
        "SPH is a mesh-free Lagrangian method...",
        "The method was originally developed for astrophysical problems..."
      ]
    }
  ]
}
```

## Agent Evaluation

The agent evaluation measures the overall system performance:

### Metrics

1. **Task Success Rate**: Did the agent complete the task successfully?
2. **Response Quality**: Is the response accurate and helpful?
3. **Tool Selection Accuracy**: Did the agent select the right tool?

### Test Set Format (`agent_test_set.json`)

```json
{
  "test_cases": [
    {
      "query": "Tell me about Albert Einstein",
      "expected_agent": "research",
      "expected_tool": "wikipedia_search",
      "evaluation_criteria": {
        "should_contain": ["physicist", "relativity"],
        "should_not_contain": ["error", "sorry"]
      }
    }
  ]
}
```

## Running Evaluations

### Using NAT CLI

```bash
# Evaluate RAG tool
nat evaluate --config configs/config_enhanced.yml \
             --eval-type rag \
             --test-set data/eval/rag_test_set.json

# Evaluate full agent workflow
nat evaluate --config configs/config_enhanced.yml \
             --eval-type agent \
             --test-set data/eval/agent_test_set.json
```

### Using Python Script

```python
from mercury_eval import run_rag_evaluation, run_agent_evaluation

# Run RAG evaluation
rag_results = await run_rag_evaluation(
    config_path="configs/config_enhanced.yml",
    test_set_path="data/eval/rag_test_set.json"
)

# Run agent evaluation  
agent_results = await run_agent_evaluation(
    config_path="configs/config_enhanced.yml",
    test_set_path="data/eval/agent_test_set.json"
)
```

## Interpreting Results

Evaluation results are saved as JSON files in the `results/` directory with timestamps.

### Sample Result Structure

```json
{
  "timestamp": "2025-11-02T10:30:00",
  "config_used": "config_enhanced.yml",
  "metrics": {
    "answer_relevancy": 0.87,
    "faithfulness": 0.92,
    "context_precision": 0.85,
    "context_recall": 0.78
  },
  "per_query_results": [
    {
      "query": "...",
      "score": 0.89,
      "passed": true
    }
  ]
}
```

## Creating Custom Test Sets

1. Create a JSON file following the format above
2. Add diverse test cases covering different scenarios:
   - General queries
   - Research questions (Wikipedia)
   - RAG queries (SPH knowledge base)
   - Edge cases (ambiguous queries, errors)

3. Include ground truth data:
   - Expected answers (for comparison)
   - Expected contexts (for retrieval quality)
   - Expected agent/tool selection

## Best Practices

1. **Diverse Test Cases**: Include queries for all agent types
2. **Regular Evaluation**: Run evals after each major change
3. **Baseline Comparison**: Compare results against baseline
4. **Error Analysis**: Review failed cases for improvement opportunities
5. **Continuous Monitoring**: Track metrics over time

## Integration with CI/CD

Add evaluation as a quality gate in your deployment pipeline:

```bash
#!/bin/bash
# run_evals.sh

echo "Running Mercury Agent Evaluations..."

nat evaluate --config configs/config_enhanced.yml \
             --eval-type all \
             --threshold 0.80

if [ $? -eq 0 ]; then
    echo "✅ All evaluations passed!"
    exit 0
else
    echo "❌ Evaluation threshold not met"
    exit 1
fi
```

## References

- [NAT Evaluation Guide](https://docs.nvidia.com/nat/evaluation)
- [Ragas Metrics](https://docs.ragas.io/en/latest/concepts/metrics/index.html)
- [Mercury Agent Documentation](../../README.md)

