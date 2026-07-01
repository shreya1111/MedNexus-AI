# Conversation Engine - Phase 4B

## Overview

The **Conversation Engine** extends the Medical AI Assistant with intelligent multi-turn conversation capabilities, memory management, session handling, and advanced reasoning features including hallucination detection, confidence estimation, and output validation.

## Architecture

### Component Stack

```
┌─────────────────────────────────────────────────────────┐
│                 Medical Assistant (Phase 4A)            │
│              (Core RAG + LLM Generation)                │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────────┐
│            Conversation Engine (Phase 4B)               │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐   │
│  │ ConversationManager                             │   │
│  │ - Orchestrates sessions and memory              │   │
│  │ - Coordinates conversation flow                 │   │
│  └───────────┬─────────────────────────────────────┘   │
│              │                                           │
│  ┌───────────┴─────────────────┬────────────────────┐  │
│  │ MemoryManager               │ SessionManager      │  │
│  │ - Sliding window            │ - Session lifecycle │  │
│  │ - Context caching           │ - Persistence       │  │
│  │ - Summarization             │ - Expiration        │  │
│  └─────────────────────────────┴────────────────────┘  │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Intelligence Layer                              │   │
│  ├─────────────────────────────────────────────────┤   │
│  │ FollowupGenerator  │ Generate contextual Qs     │   │
│  │ HallucinationChecker│ Verify context grounding  │   │
│  │ OutputValidator    │ Ensure quality & safety    │   │
│  │ ConfidenceEstimator│ Multi-factor scoring       │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. MemoryManager

**Purpose**: Manages conversation history with sliding window and context caching.

**Features**:
- Sliding window memory (configurable size)
- Conversation summarization
- Context caching for efficiency
- Token budget management

**Configuration** (`config/assistant.yaml`):
```yaml
memory:
  type: "conversation_buffer_window"
  window_size: 10  # Number of messages to keep
  cache_retrieved_context: true
  context_cache_size: 100
```

**Usage**:
```python
from ai.assistant import MemoryManager

manager = MemoryManager(config)

# Add messages
manager.add_message('user', 'What causes diabetes?')
manager.add_message('assistant', 'Diabetes is caused by...')

# Get recent messages
recent = manager.get_recent_messages(n=5)

# Format for prompt
context = manager.format_for_prompt(max_messages=5)

# Clear memory
manager.clear()
```

### 2. SessionManager

**Purpose**: Manages conversation sessions with persistence and expiration.

**Features**:
- Session creation and retrieval
- Automatic persistence to disk
- Session expiration (timeout-based)
- Memory management per session

**Configuration**:
```yaml
memory:
  session_timeout: 3600  # 1 hour in seconds
  persist_sessions: true
  session_storage: "storage/sessions"
```

**Usage**:
```python
from ai.assistant import SessionManager

manager = SessionManager(config)

# Create session
session_id = manager.create_session()

# Get session
session = manager.get_session(session_id)

# Delete session
manager.delete_session(session_id)

# Cleanup expired
manager.cleanup_expired_sessions()
```

### 3. ConversationManager

**Purpose**: High-level orchestrator for multi-turn conversations.

**Features**:
- Session and memory coordination
- Conversation flow management
- Context assembly for prompts
- History tracking

**Usage**:
```python
from ai.assistant import ConversationManager

manager = ConversationManager(config)

# Start conversation
session_id = manager.start_conversation()

# Continue conversation
manager.continue_conversation(
    session_id=session_id,
    user_message="What causes diabetes?",
    assistant_response="Diabetes is caused by..."
)

# Get context for prompt
context = manager.get_context_for_prompt(session_id, max_messages=5)

# Get history
history = manager.get_conversation_history(session_id)

# Clear conversation
manager.clear_conversation(session_id)
```

### 4. FollowupGenerator

**Purpose**: Generates intelligent follow-up questions based on context and conversation.

**Features**:
- Context-aware question generation
- Category-based templates (treatment, symptoms, prevention, causes, etc.)
- Conversation analysis to avoid repetition
- Relevance ranking

**Categories**:
- **treatment**: Treatment options, medications
- **symptoms**: Signs, manifestations
- **prevention**: Preventive measures, lifestyle changes
- **causes**: Etiology, risk factors
- **diagnosis**: Tests, screening
- **complications**: Adverse effects, risks
- **management**: Long-term care
- **prognosis**: Outcomes, recovery

**Configuration**:
```yaml
followup:
  enabled: true
  max_questions: 3
  categories:
    - treatment
    - symptoms
    - prevention
    - causes
    - diagnosis
```

**Usage**:
```python
from ai.assistant import FollowupGenerator

generator = FollowupGenerator(config)

questions = generator.generate_followup_questions(
    query="What is diabetes?",
    answer="Diabetes is a chronic condition...",
    retrieved_docs=retrieved_docs,
    conversation_history=history
)

# Returns: ["What are the treatment options?", "How can diabetes be prevented?", ...]
```

### 5. HallucinationChecker

**Purpose**: Detects unsupported claims and verifies context grounding.

**Features**:
- Context grounding verification
- Unsupported claim detection
- Citation verification
- Confidence scoring
- Hedging phrase analysis

**Configuration**:
```yaml
hallucination:
  enabled: true
  verify_context_usage: true
  verify_citations: true
  detect_unsupported_claims: true
  min_confidence: 0.3
  low_confidence_threshold: 0.5
```

**Usage**:
```python
from ai.assistant import HallucinationChecker

checker = HallucinationChecker(config)

result = checker.check_response(
    response=answer,
    context=retrieved_context,
    citations=citations,
    query=question
)

print(f"Grounded: {result.is_grounded}")
print(f"Confidence: {result.confidence:.2f}")
print(f"Unsupported claims: {result.unsupported_claims}")
```

**Result Fields**:
- `is_grounded`: Boolean indicating if response is grounded in context
- `confidence`: Confidence score (0-1)
- `unsupported_claims`: List of claims without context support
- `context_coverage`: Ratio of response covered by context
- `warnings`: List of warning messages

### 6. OutputValidator

**Purpose**: Validates response quality, safety, and completeness.

**Features**:
- Citation presence check
- Medical disclaimer verification
- Formatting validation
- Completeness assessment
- Emergency keyword detection
- Inappropriate diagnosis/treatment detection

**Checks**:
1. **Length**: Minimum/maximum bounds
2. **Citations**: Presence and coverage
3. **Disclaimer**: Medical advice disclaimer
4. **Formatting**: Structure and capitalization
5. **Completeness**: Query terms addressed
6. **Emergency handling**: Proper warnings for urgent situations
7. **No diagnosis**: Avoids direct diagnosis/treatment recommendations

**Configuration**:
```yaml
citations:
  enabled: true
  
safety:
  enabled: true
  
response:
  min_length: 100
  max_output_tokens: 2048
```

**Usage**:
```python
from ai.assistant import OutputValidator

validator = OutputValidator(config)

result = validator.validate_response(
    response=answer,
    citations=citations,
    query=question
)

print(f"Valid: {result.is_valid}")
print(f"Score: {result.score:.2f}")
print(f"Issues: {result.issues}")
print(f"Warnings: {result.warnings}")
```

### 7. ConfidenceEstimator

**Purpose**: Calculates multi-factor confidence scores for responses.

**Factors**:
1. **Retrieval Quality** (25%): Average similarity and document quality
2. **Context Completeness** (20%): Document count, diversity, content length
3. **Citation Coverage** (15%): Citation density and diversity
4. **Validation Score** (20%): Output validation result
5. **Hallucination Score** (20%): Hallucination check confidence

**Confidence Levels**:
- **HIGH** (≥75%): Well-supported with strong evidence
- **MEDIUM** (50-75%): Adequate support with some limitations
- **LOW** (<50%): Limited evidence or context

**Configuration**:
```yaml
hallucination:
  min_confidence: 0.3
  low_confidence_threshold: 0.5
```

**Usage**:
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

print(f"Confidence: {score.level.value} ({score.overall_score:.2%})")
print(f"Factors: {score.factors}")

# Check if warning needed
if estimator.should_warn_low_confidence(score):
    message = estimator.get_confidence_message(score)
    print(f"Warning: {message}")
```

## Integration with Medical Assistant

The Phase 4B components are fully integrated into `MedicalAssistant.ask()`:

```python
from ai.assistant import MedicalAssistant

assistant = MedicalAssistant()

# Single-turn (Phase 4A style)
response = assistant.ask("What is diabetes?")

# Multi-turn with session (Phase 4B style)
session_id = assistant.start_conversation()

response1 = assistant.ask(
    query="What is diabetes?",
    session_id=session_id
)

response2 = assistant.ask(
    query="How is it treated?",
    session_id=session_id
)

# Access enhanced features
print(f"Follow-ups: {response2.followup_questions}")
print(f"Confidence: {response2.confidence:.2%}")
```

### Response Enhancement

Each response now includes:
- **Validation**: Output quality check
- **Hallucination detection**: Context grounding verification
- **Confidence scoring**: Multi-factor confidence estimate
- **Follow-up questions**: Intelligent suggestions (if enabled)
- **Low confidence warnings**: Automatic warnings for weak evidence
- **Session tracking**: Conversation history (if session provided)

## CLI Commands

### Interactive Chat

Start an interactive conversation:

```bash
# New session
python -m scripts.cli.main chat

# Resume session
python -m scripts.cli.main chat --session-id abc123
```

**Features**:
- Multi-turn conversation
- Session persistence
- Follow-up question suggestions
- Confidence warnings
- Exit with `quit` or `exit`

### View History

Show conversation history for a session:

```bash
python -m scripts.cli.main history SESSION_ID

# Limit messages
python -m scripts.cli.main history SESSION_ID --limit 10
```

### Clear History

Clear conversation history:

```bash
python -m scripts.cli.main clear-history SESSION_ID
```

### Session Status

View all active sessions:

```bash
python -m scripts.cli.main session-status
```

Shows:
- Session ID
- Created timestamp
- Last accessed timestamp
- Message count
- Metadata

## Memory Management

### Sliding Window

The sliding window keeps only the N most recent messages:

```
Window size: 5

[Msg 1] [Msg 2] [Msg 3] [Msg 4] [Msg 5]
                                         <-- Add Msg 6
[Msg 2] [Msg 3] [Msg 4] [Msg 5] [Msg 6]
         ^                                  Msg 1 dropped
```

### Context Caching

Retrieved contexts are cached per session:

```python
# First query: "diabetes symptoms"
# Context retrieved from vector DB
# Cached for session

# Second query: "diabetes symptoms" (exact match)
# Context returned from cache (instant)
```

### Session Expiration

Sessions automatically expire after inactivity:

```yaml
memory:
  session_timeout: 3600  # 1 hour
```

Expired sessions are cleaned up:
```python
assistant.cleanup()  # Removes expired sessions
```

## Conversation Flow

### Example: Multi-Turn Medical Question

```
USER: What is diabetes?

ASSISTANT: Diabetes is a chronic condition that affects how your body 
processes blood sugar (glucose)...

[Citations: 1, 2, 3]
[Confidence: HIGH (85%)]

💡 You might also want to ask:
   1. What are the treatment options for diabetes?
   2. What are the common symptoms of diabetes?
   3. How can diabetes be prevented?

---

USER: What are the symptoms?

ASSISTANT: Common symptoms of diabetes include frequent urination, 
increased thirst, unexplained weight loss...

[Memory context used: Previous question about diabetes]
[Citations: 1, 4, 5]
[Confidence: HIGH (82%)]

💡 You might also want to ask:
   1. When should someone be screened for diabetes?
   2. What are early warning signs of diabetes?
   3. What complications should be monitored?
```

## Sample Conversations

### Conversation 1: Disease Inquiry

```python
assistant = MedicalAssistant()
session_id = assistant.start_conversation()

# Turn 1
response1 = assistant.ask(
    query="What causes Type 2 diabetes?",
    session_id=session_id
)
# Answer includes causes, risk factors
# Follow-ups: symptoms, prevention, treatment

# Turn 2
response2 = assistant.ask(
    query="Can it be prevented?",  # "it" resolved via context
    session_id=session_id
)
# Answer includes prevention strategies
# Follow-ups: screening, lifestyle changes, risk assessment
```

### Conversation 2: Medication Inquiry

```python
# Turn 1
response1 = assistant.ask(
    query="What is metformin?",
    session_id=session_id
)
# Answer explains the medication
# Follow-ups: usage, side effects, interactions

# Turn 2
response2 = assistant.ask(
    query="What are the side effects?",
    session_id=session_id
)
# Answer lists common and serious side effects
# Context from previous question used
```

## Configuration

Full configuration in `config/assistant.yaml`:

```yaml
# Memory Configuration
memory:
  type: "conversation_buffer_window"
  window_size: 10
  session_timeout: 3600
  persist_sessions: true
  session_storage: "storage/sessions"
  cache_retrieved_context: true
  context_cache_size: 100

# Follow-up Configuration
followup:
  enabled: true
  max_questions: 3
  categories:
    - treatment
    - symptoms
    - prevention
    - causes
    - risk_factors
    - diagnosis

# Hallucination Detection
hallucination:
  enabled: true
  verify_context_usage: true
  verify_citations: true
  detect_unsupported_claims: true
  min_confidence: 0.3
  low_confidence_threshold: 0.5

# Output Validation
citations:
  enabled: true

safety:
  enabled: true

response:
  min_length: 100
  max_output_tokens: 2048
```

## Testing

Run Phase 4B tests:

```bash
# All conversation tests
python -m scripts.tests.test_conversation

# Specific test class
python -m scripts.tests.test_conversation TestMemoryManager
python -m scripts.tests.test_conversation TestConfidenceEstimator
```

## Best Practices

### 1. Session Management

```python
# Always use sessions for multi-turn conversations
session_id = assistant.start_conversation()

# Provide session_id with each query
response = assistant.ask(query, session_id=session_id)

# Cleanup when done
assistant.cleanup()
```

### 2. Memory Tuning

```yaml
# For short conversations
memory:
  window_size: 5

# For detailed medical discussions
memory:
  window_size: 20
```

### 3. Confidence Thresholds

```yaml
# Strict (high precision)
hallucination:
  min_confidence: 0.5
  low_confidence_threshold: 0.7

# Permissive (high recall)
hallucination:
  min_confidence: 0.2
  low_confidence_threshold: 0.4
```

### 4. Follow-up Customization

```python
# Generate follow-ups for specific categories
questions = followup_generator.generate_followup_questions(
    query=query,
    answer=answer,
    retrieved_docs=docs,
    categories=['treatment', 'complications']
)
```

## Performance

### Latency Impact

Phase 4B adds ~50-100ms per query:
- Memory operations: ~10ms
- Followup generation: ~20ms
- Hallucination check: ~30ms
- Output validation: ~15ms
- Confidence estimation: ~25ms

### Memory Usage

Per session:
- Memory buffer: ~10-50 KB (depending on window size)
- Context cache: ~100-500 KB (depending on cache size)
- Session metadata: ~1 KB

### Storage

Session persistence:
- ~10-50 KB per session file (JSON)
- Automatic cleanup of expired sessions

## Troubleshooting

### Issue: Low Confidence Warnings

**Symptom**: Frequent low confidence warnings

**Solutions**:
1. Increase retrieval `top_k`
2. Improve chunking strategy
3. Add more source documents
4. Lower confidence thresholds (if appropriate)

### Issue: Poor Follow-up Questions

**Symptom**: Irrelevant or repetitive follow-ups

**Solutions**:
1. Check conversation history analysis
2. Adjust category relevance
3. Customize question templates
4. Reduce `max_questions`

### Issue: Session Not Found

**Symptom**: Session ID not recognized

**Solutions**:
1. Check session expiration timeout
2. Verify `persist_sessions` enabled
3. Check storage path permissions
4. Ensure cleanup not too aggressive

## Phase 5 Preview

Phase 4B sets the foundation for Phase 5 features:

- **Streaming responses**: Real-time token generation
- **REST API**: HTTP endpoints for conversations
- **Authentication**: User-based session management
- **Multi-modal**: Image and PDF upload support
- **Advanced reasoning**: Chain-of-thought, self-correction

## Summary

Phase 4B enhances the Medical AI Assistant with:

✅ **Multi-turn conversations** with memory and sessions  
✅ **Intelligent follow-up questions** based on context  
✅ **Hallucination detection** for accuracy  
✅ **Output validation** for quality and safety  
✅ **Confidence estimation** with multi-factor scoring  
✅ **Interactive CLI** for chat and history management  
✅ **Comprehensive testing** with 40+ unit tests  

The system is production-ready for multi-turn medical Q&A with advanced conversation intelligence and safety features.
