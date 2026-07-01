# Phase 4B Quickstart Guide

## 🚀 Quick Setup

### 1. Install Dependencies

Already included in `requirements-kb.txt` from Phase 4A. No additional dependencies needed.

### 2. Configuration

Phase 4B is configured via `config/assistant.yaml`. Default settings work out-of-the-box.

### 3. Test Installation

```bash
# Run Phase 4B tests
python -m scripts.tests.test_conversation

# Expected: All tests pass
```

---

## 💬 Basic Usage

### Simple Single-Turn Query

```python
from ai.assistant import MedicalAssistant

assistant = MedicalAssistant()

response = assistant.ask("What is diabetes?")
print(response.answer)

# Cleanup
assistant.cleanup()
```

### Multi-Turn Conversation

```python
from ai.assistant import MedicalAssistant

assistant = MedicalAssistant()

# Start conversation
session_id = assistant.start_conversation()

# Turn 1
response1 = assistant.ask(
    query="What causes Type 2 diabetes?",
    session_id=session_id
)
print(response1.answer)
print(f"Follow-ups: {response1.followup_questions}")

# Turn 2 (uses conversation history automatically)
response2 = assistant.ask(
    query="What are the symptoms?",
    session_id=session_id
)
print(response2.answer)
print(f"Confidence: {response2.confidence:.0%}")

# Cleanup
assistant.cleanup()
```

### Interactive Chat (CLI)

```bash
# Start interactive chat
python -m scripts.cli.main chat

# Type your questions, get answers with follow-ups
# Exit with 'quit' or 'exit'
```

---

## 🔧 Key APIs

### ConversationManager

```python
from ai.assistant import ConversationManager

manager = ConversationManager(config)

# Start conversation
session_id = manager.start_conversation()

# Add messages
manager.continue_conversation(
    session_id=session_id,
    user_message="Hello",
    assistant_response="Hi there"
)

# Get history
history = manager.get_conversation_history(session_id)

# Get context for prompt
context = manager.get_context_for_prompt(session_id, max_messages=5)

# Clear history
manager.clear_conversation(session_id)
```

### FollowupGenerator

```python
from ai.assistant import FollowupGenerator

generator = FollowupGenerator(config)

questions = generator.generate_followup_questions(
    query="What is diabetes?",
    answer="Diabetes is...",
    retrieved_docs=docs,
    conversation_history=history
)

print(questions)
# ["What are the treatment options?", "What are the symptoms?", ...]
```

### HallucinationChecker

```python
from ai.assistant import HallucinationChecker

checker = HallucinationChecker(config)

result = checker.check_response(
    response=answer,
    context=context,
    citations=citations,
    query=query
)

if not result.is_grounded:
    print(f"Warning: {result.warnings}")
    print(f"Unsupported claims: {result.unsupported_claims}")
```

### OutputValidator

```python
from ai.assistant import OutputValidator

validator = OutputValidator(config)

result = validator.validate_response(
    response=answer,
    citations=citations,
    query=query
)

if not result.is_valid:
    print(f"Issues: {result.issues}")
print(f"Score: {result.score:.2f}")
```

### ConfidenceEstimator

```python
from ai.assistant import ConfidenceEstimator, ConfidenceLevel

estimator = ConfidenceEstimator(config)

score = estimator.estimate_confidence(
    retrieved_docs=docs,
    citations=citations,
    validation_result=validation,
    hallucination_result=hallucination_check,
    response_length=len(answer)
)

print(f"Confidence: {score.level.value} ({score.overall_score:.0%})")

if score.level == ConfidenceLevel.LOW:
    message = estimator.get_confidence_message(score)
    print(f"Warning: {message}")
```

---

## ⚙️ Configuration Examples

### High Memory (Detailed Conversations)

```yaml
memory:
  window_size: 20  # Keep 20 messages
  context_cache_size: 200  # Larger cache
```

### Low Memory (Resource Constrained)

```yaml
memory:
  window_size: 5  # Keep 5 messages
  context_cache_size: 20  # Smaller cache
  cache_retrieved_context: false  # Disable caching
```

### Strict Quality Control

```yaml
hallucination:
  min_confidence: 0.5  # Higher threshold
  low_confidence_threshold: 0.7  # Stricter warnings

citations:
  enabled: true
  verify_citations: true

safety:
  enabled: true
  level: "strict"
```

### Permissive Mode

```yaml
hallucination:
  min_confidence: 0.2
  low_confidence_threshold: 0.4

followup:
  enabled: false  # Disable follow-ups
```

---

## 🖥️ CLI Quick Reference

```bash
# Interactive chat
python -m scripts.cli.main chat

# Resume session
python -m scripts.cli.main chat --session-id <SESSION_ID>

# View history
python -m scripts.cli.main history <SESSION_ID>

# Clear history
python -m scripts.cli.main clear-history <SESSION_ID>

# Session status
python -m scripts.cli.main session-status

# Single question
python -m scripts.cli.main ask "What is diabetes?"
```

---

## 🧪 Testing

### Run All Tests

```bash
python -m scripts.tests.test_conversation
```

### Run Specific Test Class

```bash
python -m scripts.tests.test_conversation TestMemoryManager
python -m scripts.tests.test_conversation TestConfidenceEstimator
```

### Enable Verbose Output

```bash
python -m scripts.tests.test_conversation -v
```

---

## 🐛 Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or in config/assistant.yaml:
logging:
  level: "DEBUG"
```

### Common Issues

#### 1. Session Not Found
- Check session_id is correct
- Verify session hasn't expired (default: 1 hour)
- Check `persist_sessions` is enabled

#### 2. Low Confidence Warnings
- Increase retrieval `top_k`
- Check knowledge base has relevant documents
- Lower confidence thresholds if appropriate

#### 3. No Follow-up Questions
- Check `followup.enabled: true`
- Verify categories are configured
- Ensure conversation history is available

---

## 📚 Further Reading

- **Full Documentation**: `docs/conversation_engine.md`
- **Completion Report**: `docs/knowledge_base/PHASE_4B_COMPLETE.md`
- **Phase 4A Guide**: `docs/medical_assistant_core.md`
- **API Reference**: Check docstrings in source files

---

## 💡 Pro Tips

1. **Use sessions for multi-turn**: Always provide `session_id` for related questions
2. **Monitor confidence**: Low confidence may indicate missing knowledge
3. **Customize templates**: Edit followup templates for domain-specific questions
4. **Tune thresholds**: Adjust confidence and validation thresholds based on use case
5. **Cache aggressively**: Enable context caching for better performance
6. **Session cleanup**: Call `assistant.cleanup()` to remove expired sessions

---

## 🎯 Next Steps

1. **Explore Examples**: Try the sample conversations in the docs
2. **Customize Configuration**: Tune for your specific use case
3. **Integrate into Application**: Use the APIs in your own code
4. **Monitor Performance**: Track latency and confidence scores
5. **Contribute**: Add new followup categories or validation checks

---

## 🤝 Need Help?

- Check `docs/conversation_engine.md` for detailed information
- Review test cases in `scripts/tests/test_conversation.py`
- Enable DEBUG logging for troubleshooting
- Verify configuration in `config/assistant.yaml`

---

**Phase 4B Quickstart Complete** - Happy Coding! 🚀
