# Medical AI Assistant - Core Engine

**Phase 4A: Core Medical AI Assistant Engine**

Complete RAG-based medical question answering system integrating retrieval, LLM generation, and safety guardrails.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [RAG Pipeline Flow](#rag-pipeline-flow)
4. [Components](#components)
5. [Prompt Templates](#prompt-templates)
6. [Safety Layer](#safety-layer)
7. [Configuration](#configuration)
8. [CLI Usage](#cli-usage)
9. [Code Examples](#code-examples)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The Medical AI Assistant is a production-grade RAG (Retrieval-Augmented Generation) system that:

- Retrieves relevant medical knowledge from ChromaDB
- Generates accurate, cited responses using Gemini LLM
- Applies safety guardrails to prevent unsafe responses
- Formats responses with citations and disclaimers
- Provides confidence scoring and metadata

**Key Features:**
- ✅ Hybrid retrieval (vector + BM25)
- ✅ 8 specialized prompt templates
- ✅ 5-category safety detection
- ✅ Automatic citation generation
- ✅ Context assembly with token budgeting
- ✅ Confidence scoring
- ✅ Medical disclaimers

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER QUERY                                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SAFETY GUARDRAILS                             │
│  • Emergency detection    • Self-harm detection                  │
│  • Medication misuse      • Diagnosis requests                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   QUERY PROCESSING                               │
│  • Lowercasing           • Whitespace normalization              │
│  • Abbreviation expansion • Validation                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  EMBEDDING GENERATION                            │
│  • Query vectorization using Sentence Transformers or Gemini    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   HYBRID RETRIEVAL                               │
│  • Vector search (cosine similarity)                             │
│  • BM25 search (keyword matching)                                │
│  • RRF fusion (Reciprocal Rank Fusion)                           │
│  • Top-K selection (default: 5 documents)                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CONTEXT BUILDER                                │
│  • Deduplication         • Relevance sorting                     │
│  • Token budgeting       • Section prioritization                │
│  • Metadata inclusion    • Context validation                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PROMPT BUILDER                                 │
│  • Template selection    • Context injection                     │
│  • System instructions   • Formatting                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   GEMINI LLM                                     │
│  • Model: Gemini 2.0 Flash / 1.5 Pro                            │
│  • Temperature: 0.1 (factual)                                    │
│  • Max tokens: 2048                                              │
│  • Token tracking & cost estimation                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CITATION MANAGER                               │
│  • Extract citations from retrieved documents                    │
│  • Format citations (inline/footnote/references)                 │
│  • Verify citation accuracy                                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   RESPONSE FORMATTER                             │
│  • Structure response sections                                   │
│  • Add confidence indicators                                     │
│  • Include sources and citations                                 │
│  • Append medical disclaimers                                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FINAL RESPONSE                              │
│  • Answer with citations                                         │
│  • Confidence score                                              │
│  • Sources list                                                  │
│  • Medical disclaimer                                            │
│  • Metadata (latency, tokens)                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## RAG Pipeline Flow

### 1. Input Processing

```python
query = "What are the symptoms of diabetes?"
↓
safety_check = safety_guardrails.check_safety(query)
↓
processed_query = query_processor.process(query)
# Output: "what are the symptoms of diabetes mellitus"
```

### 2. Retrieval

```python
query_embedding = embedder.embed([processed_query])
↓
retrieved_docs = hybrid_retriever.search(
    query_embedding=query_embedding,
    query_text=processed_query,
    top_k=5
)
# Returns 5 most relevant document chunks
```

### 3. Context Assembly

```python
context, metadata = context_builder.build_context(
    retrieved_docs,
    query=query
)
# Assembles context with token budget of 4000 tokens
```

### 4. Prompt Generation

```python
prompt = prompt_builder.build_prompt(
    query=query,
    context=context
)
# Uses appropriate template (disease_explanation detected)
```

### 5. LLM Generation

```python
response = gemini_llm.generate(prompt)
# Gemini 2.0 Flash generates factual answer
```

### 6. Post-Processing

```python
citations = citation_manager.generate_citations(retrieved_docs)
answer = citation_manager.embed_citations(response, citations)
answer = safety_guardrails.wrap_response(answer, safety_check)
formatted = response_formatter.format_response(answer, ...)
```

---

## Components

### MedicalAssistant

**Purpose**: Main orchestrator coordinating all components

**Key Methods**:
- `ask(query, conversation_history=None, stream=False)` - Process a medical question
- `cleanup()` - Clean up resources

**Example**:
```python
from ai.assistant import MedicalAssistant

assistant = MedicalAssistant()
response = assistant.ask("What causes diabetes?")
print(response.answer)
assistant.cleanup()
```

### PromptBuilder

**Purpose**: Build prompts from templates and context

**Features**:
- Automatic template detection
- Context injection
- System instruction management
- Token estimation

**Templates**:
1. `medical_qa` - General medical questions
2. `disease_explanation` - Disease information
3. `drug_information` - Medication details
4. `clinical_guidelines` - Clinical practices
5. `medical_definition` - Term definitions
6. `research_question` - Research synthesis
7. `conversation_continuation` - Follow-up questions

### ContextBuilder

**Purpose**: Assemble optimal context from retrieved documents

**Features**:
- Deduplication (removes duplicate documents)
- Relevance sorting (by similarity score)
- Token budgeting (max 4000 tokens)
- Section prioritization (clinical guidelines, WHO, CDC first)
- Metadata inclusion

**Algorithm**:
```
1. Remove duplicates by ID and content hash
2. Sort by relevance (similarity score)
3. Prioritize high-value sections
4. Assemble until token budget reached
5. Format with metadata headers
```

### CitationManager

**Purpose**: Generate and format citations

**Formats**:
- **Inline**: `[Source: MedQuAD - Diabetes Info]`
- **Footnote**: `[1]` with references at end
- **References**: Full citation list

**Example**:
```python
citations = citation_manager.generate_citations(retrieved_docs)
formatted = citation_manager.format_citations_section(citations)
```

### SafetyGuardrails

**Purpose**: Detect and handle unsafe queries

**Detection Categories**:
1. **Emergency** (critical): "chest pain", "can't breathe"
2. **Self-harm** (critical): "hurt myself", "suicide"
3. **Medication misuse** (high): "get high", "abuse"
4. **Diagnosis requests** (medium): "do I have diabetes?"
5. **Dosage requests** (medium): "how much to take?"

**Responses**:
- **Critical risks**: Refuse + provide crisis resources
- **High risks**: Refuse + redirect to professionals
- **Medium risks**: Answer with strong disclaimers

### ResponseFormatter

**Purpose**: Format responses for different outputs

**Formats**:
- **Markdown**: Rich formatting with emojis and sections
- **Plain**: Simple text format
- **JSON**: Structured data format

**Sections**:
- Answer text
- Confidence indicator (🟢 High / 🟡 Medium / 🔴 Low)
- Sources list
- Metadata (documents, tokens, latency)

---

## Prompt Templates

### Medical Q&A Template

```
Context Documents:
{context}

Question: {question}

Instructions:
- Answer based ONLY on the context provided
- Cite sources for every claim [Source: document_name]
- If information is incomplete, state what's missing
- Be concise but thorough
- Use clear, accessible language

Answer:
```

### Disease Explanation Template

```
Context Documents:
{context}

Question: Explain {disease_name}

Instructions:
- Provide a comprehensive overview based on the context
- Cover: definition, causes, symptoms, risk factors, prevention
- Cite sources for each section
- Organize information logically

Explanation:
```

### Drug Information Template

```
Context Documents:
{context}

Question: Provide information about {drug_name}

Instructions:
- Answer based ONLY on the context documents
- Cover: drug class, uses, mechanism, contraindications
- DO NOT provide dosage recommendations
- Emphasize the need for professional medical guidance

Information:
```

---

## Safety Layer

### Emergency Detection

**Patterns**:
- Chest pain, heart attack, stroke
- Severe bleeding
- Difficulty breathing, choking
- Overdose, poisoning
- Severe burns, major injuries

**Response**:
```
⚠️ EMERGENCY WARNING: If this is a medical emergency, please call 
emergency services immediately (911 in the US) or go to the nearest 
emergency room.
```

### Self-Harm Detection

**Patterns**:
- Kill myself, suicide
- Hurt myself, self-harm
- Don't want to live
- Suicidal thoughts

**Response**:
```
I'm concerned about your safety. Please reach out to:
- National Suicide Prevention Lifeline: 988
- Crisis Text Line: Text HOME to 741741
- Emergency Services: 911
```

### Diagnosis Request Handling

**Patterns**:
- "Do I have diabetes?"
- "Am I sick?"
- "What's wrong with me?"

**Response**:
Educational answer + strong disclaimer:
```
I can provide educational information, but I cannot diagnose conditions.
For accurate diagnosis, please consult a qualified healthcare professional.
```

---

## Configuration

### config/assistant.yaml

```yaml
# LLM Configuration
llm:
  provider: "gemini"
  model: "gemini-2.0-flash-exp"
  temperature: 0.1  # Low for factual responses
  max_output_tokens: 2048

# Retrieval Configuration
retrieval:
  top_k: 5
  mode: "hybrid"  # vector, bm25, hybrid

# Context Configuration
context:
  max_tokens: 4000
  deduplicate: true
  sort_by_relevance: true

# Safety Configuration
safety:
  enabled: true
  level: "strict"  # permissive, moderate, strict
  detect_emergency: true
  detect_self_harm: true

# Citation Configuration
citations:
  enabled: true
  format: "inline"  # inline, footnote, references
```

---

## CLI Usage

### Basic Usage

```bash
# Ask a medical question
python -m scripts.cli.main ask "What are the symptoms of diabetes?"

# With verbose output
python -m scripts.cli.main ask "Explain hypertension" --verbose

# Drug information
python -m scripts.cli.main ask "What is Metformin used for?"
```

### Example Output

```
================================================================================
MEDICAL AI ASSISTANT
================================================================================

Question: What are the symptoms of diabetes?

Answer:
Diabetes symptoms include frequent urination, excessive thirst, unexplained 
weight loss, increased hunger, fatigue, blurred vision, and slow-healing sores.
[Source: MedQuAD - Diabetes Information]

Type 1 diabetes symptoms often develop quickly, while Type 2 diabetes symptoms 
may develop gradually over years. [Source: CDC - Diabetes Basics]

**Confidence**: 🟢 High Confidence (85%)

## 📚 Sources

- MedQuAD
- CDC

*Retrieved from 5 document(s)*

---
**Medical Disclaimer**: This information is for educational purposes only...

================================================================================
```

### Verbose Output

```bash
python -m scripts.cli.main ask "What causes diabetes?" --verbose
```

Shows additional metadata:
- Latency: 1234ms
- Tokens: 450 in + 230 out
- Confidence: 82%
- Documents: 5
- Sources: MedQuAD, CDC, WHO
- Safety: safe (risk: low)

---

## Code Examples

### Basic Usage

```python
from ai.assistant import MedicalAssistant

# Initialize
assistant = MedicalAssistant()

# Ask question
response = assistant.ask("What are the symptoms of diabetes?")

# Display answer
print(response.answer)
print(f"Confidence: {response.confidence:.0%}")
print(f"Sources: {', '.join(response.context_metadata.get('sources', []))}")

# Cleanup
assistant.cleanup()
```

### With Custom Configuration

```python
assistant = MedicalAssistant(
    config_path="config/assistant.yaml",
    retrieval_config_path="config/retrieval.yaml",
    embedding_config_path="config/embedding.yaml"
)

response = assistant.ask(
    query="Explain hypertension",
    conversation_history=None,
    stream=False
)
```

### Accessing Response Data

```python
response = assistant.ask("What is Metformin?")

# Answer text
print(response.answer)

# Citations
for citation in response.citations:
    print(f"Source: {citation.source}")
    print(f"Chunk ID: {citation.chunk_id}")
    print(f"Relevance: {citation.similarity:.2%}")

# Metadata
print(f"Latency: {response.latency_ms:.0f}ms")
print(f"Input tokens: {response.token_usage['input']}")
print(f"Output tokens: {response.token_usage['output']}")
print(f"Confidence: {response.confidence:.2%}")

# Safety check
print(f"Safety category: {response.safety_check.category}")
print(f"Risk level: {response.safety_check.risk_level}")
```

---

## Troubleshooting

### Issue: Low Confidence Responses

**Symptoms**: Confidence score < 40%

**Causes**:
- Insufficient relevant documents retrieved
- Low similarity scores
- Few sources

**Solutions**:
- Increase `retrieval.top_k` in config (try 10)
- Check if embeddings are indexed
- Verify query preprocessing is working
- Review retrieved documents with `--verbose`

### Issue: Empty or Generic Responses

**Symptoms**: LLM provides vague answers

**Causes**:
- Context not reaching LLM
- Prompt template issues
- Token budget too restrictive

**Solutions**:
- Check context assembly in logs
- Increase `context.max_tokens` (try 6000)
- Verify prompt includes context
- Test with simpler queries

### Issue: Safety Refusal on Valid Questions

**Symptoms**: Legitimate questions blocked

**Causes**:
- Overly aggressive pattern matching
- Safety level too strict

**Solutions**:
- Set `safety.level` to "moderate" instead of "strict"
- Review safety patterns in code
- Add exceptions for specific terms

### Issue: Missing Citations

**Symptoms**: No sources in response

**Causes**:
- Citations disabled in config
- Citation format mismatch

**Solutions**:
- Set `citations.enabled: true`
- Check citation format setting
- Verify `citation_manager.embed_citations()` is called

### Issue: Slow Response Times

**Symptoms**: Latency > 5 seconds

**Causes**:
- Large context size
- Many retrieved documents
- Gemini API latency

**Solutions**:
- Reduce `retrieval.top_k` (try 3)
- Decrease `context.max_tokens` (try 2000)
- Enable caching in retrieval
- Use Gemini 2.0 Flash instead of Pro

---

## Performance Metrics

### Typical Performance

| Metric | Value | Notes |
|--------|-------|-------|
| Retrieval latency | <500ms | Hybrid search |
| Context assembly | <100ms | 5 documents |
| LLM generation | 1-3s | Gemini 2.0 Flash |
| Total latency | 2-4s | End-to-end |
| Token usage | 500-800 | Input + output |
| Cost per query | $0.0003-0.0006 | Gemini Flash pricing |

### Optimization Tips

1. **Reduce retrieval time**:
   - Enable search caching
   - Use vector-only mode (faster than hybrid)

2. **Reduce LLM time**:
   - Use Gemini 2.0 Flash (faster than Pro)
   - Decrease max_output_tokens

3. **Reduce token usage**:
   - Lower retrieval.top_k
   - Compress context
   - Use shorter prompt templates

---

## Next Steps (Phase 4B)

Phase 4A provides the core RAG engine. Future phases will add:

- **Conversation Memory**: Multi-turn dialogue support
- **Session Management**: Persistent conversations
- **Streaming Responses**: Real-time token streaming
- **REST API**: FastAPI endpoints
- **Advanced Features**: Follow-up questions, hallucination detection
- **Evaluation**: RAG metrics (faithfulness, relevancy)

---

For more information:
- [Vector Retrieval Guide](vector_retrieval.md)
- [Embedding Pipeline](embedding_pipeline.md)
- [Configuration Reference](../config/assistant.yaml)
