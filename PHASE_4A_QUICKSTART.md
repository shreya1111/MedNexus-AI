# Phase 4A Quick Start Guide

**Get started with the Medical AI Assistant in minutes**

---

## Installation

```bash
# Install dependencies
pip install -r requirements-kb.txt

# Set up Gemini API key
set GEMINI_API_KEY=your_api_key_here  # Windows
export GEMINI_API_KEY=your_api_key_here  # Linux/Mac
```

---

## Basic Usage

### CLI Command

```bash
# Ask a medical question
python -m scripts.cli.main ask "What are the symptoms of diabetes?"
```

### Python API

```python
from ai.assistant import MedicalAssistant

# Initialize
assistant = MedicalAssistant()

# Ask question
response = assistant.ask("What causes diabetes?")

# Display answer
print(response.answer)

# Cleanup
assistant.cleanup()
```

---

## Common Commands

```bash
# Disease information
python -m scripts.cli.main ask "What is diabetes?"

# Symptoms
python -m scripts.cli.main ask "What are the symptoms of hypertension?"

# Medication
python -m scripts.cli.main ask "What is Metformin used for?"

# Treatment
python -m scripts.cli.main ask "How is diabetes treated?"

# Verbose (show metadata)
python -m scripts.cli.main ask "Explain diabetes" --verbose
```

---

## Configuration

### Quick Config (config/assistant.yaml)

```yaml
llm:
  model: "gemini-2.0-flash-exp"  # Fast and cheap
  temperature: 0.1  # Factual responses

retrieval:
  top_k: 5  # Documents to retrieve
  mode: "hybrid"  # Best accuracy

safety:
  enabled: true
  level: "strict"  # Maximum safety
```

---

## Key Features

### 1. Safety Guardrails

Automatically detects and handles:
- Emergencies → Provides 911 info
- Self-harm → Provides crisis resources
- Medication misuse → Refuses and redirects
- Diagnosis requests → Answers with disclaimers

### 2. Automatic Citations

Every claim is cited:
```
[Source: MedQuAD - Diabetes Overview]
```

### 3. Confidence Scoring

```
🟢 High Confidence (>70%)
🟡 Medium Confidence (40-70%)
🔴 Low Confidence (<40%)
```

### 4. Medical Disclaimers

Automatically added to all responses

---

## Example Output

```
================================================================================
MEDICAL AI ASSISTANT
================================================================================

Question: What are the symptoms of diabetes?

Answer:
Diabetes symptoms include frequent urination, excessive thirst, unexplained 
weight loss, increased hunger, fatigue, blurred vision, and slow-healing sores.
[Source: MedQuAD - Diabetes Information]

**Confidence**: 🟢 High Confidence (85%)

## 📚 Sources
- MedQuAD
- CDC

*Retrieved from 5 document(s)*

---
**Medical Disclaimer**: This information is for educational purposes only...
================================================================================
```

---

## Python API Examples

### Basic Usage

```python
from ai.assistant import MedicalAssistant

assistant = MedicalAssistant()
response = assistant.ask("What is diabetes?")
print(response.answer)
assistant.cleanup()
```

### Access Response Data

```python
response = assistant.ask("What causes diabetes?")

# Answer text
print(response.answer)

# Confidence
print(f"Confidence: {response.confidence:.0%}")

# Citations
for citation in response.citations:
    print(f"- {citation.source}")

# Metadata
print(f"Latency: {response.latency_ms:.0f}ms")
print(f"Tokens: {response.token_usage['total']}")
```

### Error Handling

```python
try:
    response = assistant.ask("What is diabetes?")
    print(response.answer)
except Exception as e:
    print(f"Error: {e}")
finally:
    assistant.cleanup()
```

---

## Testing

```bash
# Run all tests
pytest scripts/tests/test_assistant.py -v

# Run specific test class
pytest scripts/tests/test_assistant.py::TestSafetyGuardrails -v

# With coverage
pytest scripts/tests/test_assistant.py --cov=ai.assistant
```

---

## Troubleshooting

### Issue: "GEMINI_API_KEY not found"

**Solution**: Set environment variable
```bash
set GEMINI_API_KEY=your_key  # Windows
export GEMINI_API_KEY=your_key  # Linux/Mac
```

### Issue: Low confidence responses

**Solution**: Increase retrieval documents
```yaml
# config/assistant.yaml
retrieval:
  top_k: 10  # Increase from 5
```

### Issue: Slow responses

**Solution**: Use faster model
```yaml
# config/assistant.yaml
llm:
  model: "gemini-2.0-flash-exp"  # Faster than Pro
```

### Issue: Empty responses

**Solution**: Check embeddings are indexed
```bash
python -m scripts.cli.main index
python -m scripts.cli.main collection-status
```

---

## Performance Tips

### Faster Responses
- Use Gemini 2.0 Flash (not Pro)
- Reduce `retrieval.top_k` (try 3)
- Decrease `context.max_tokens` (try 2000)

### Better Quality
- Increase `retrieval.top_k` (try 10)
- Use hybrid retrieval mode
- Increase `context.max_tokens` (try 6000)

### Lower Cost
- Use Gemini 2.0 Flash (10x cheaper than Pro)
- Reduce max_output_tokens
- Enable response caching (Phase 4B)

---

## File Locations

### Configuration
- `config/assistant.yaml` - Main config
- `config/retrieval.yaml` - Retrieval settings
- `config/embedding.yaml` - Embedding settings

### Code
- `scripts/ai/assistant/` - Core modules
- `scripts/cli/main.py` - CLI interface
- `scripts/tests/test_assistant.py` - Tests

### Documentation
- `docs/medical_assistant_core.md` - Full guide
- `docs/sample_conversations.md` - Examples
- `PHASE_4A_COMPLETE.md` - Completion report

---

## Next Steps

1. **Try the examples** - Run sample queries
2. **Adjust configuration** - Tune for your needs
3. **Review documentation** - Learn advanced features
4. **Run tests** - Verify installation
5. **Build your application** - Integrate the assistant

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `ask` | Ask medical question |
| `--verbose` | Show metadata |
| `index` | Index embeddings |
| `collection-status` | Check collection |
| `pytest` | Run tests |

---

## Support

- [Full Documentation](docs/medical_assistant_core.md)
- [Sample Conversations](docs/sample_conversations.md)
- [Configuration Guide](config/assistant.yaml)
- [Complete Report](PHASE_4A_COMPLETE.md)

---

**Status**: ✅ Phase 4A Complete and Ready to Use!
