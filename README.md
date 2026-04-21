# ⚖️ Legal Document Assistant — LangGraph Capstone Project

An AI-powered legal research assistant built with LangGraph, featuring a dual knowledge base system for answering questions from both general legal knowledge and user-uploaded documents.

## 🎯 Project Overview

**Domain:** Legal Document Q&A  
**User:** Paralegal / junior lawyer  
**Success:** Agent answers 90%+ questions faithfully, never fabricates, admits uncertainty

## ✨ Key Features

- **Dual Knowledge Base System**
  - Permanent KB: 10 foundational legal topics (contract law, tort law, evidence, etc.)
  - Session KB: Built from user-uploaded PDF/TXT documents at runtime
  
- **LangGraph Agent Architecture**
  - 8-node StateGraph with intelligent routing
  - Self-reflection with faithfulness evaluation (auto-retry if < 0.7)
  - Conversation memory with sliding window
  
- **Grounding Enforcement**
  - Never fabricates information
  - Admits uncertainty when answers not in context
  - Source attribution for every answer
  
- **Streamlit UI**
  - Real-time document upload and processing
  - Multi-turn conversation support
  - Source tracking and faithfulness scores

## 📁 Project Structure

```
amicius/
├── src/
│   └── agent.py              # Core agent implementation (KB, state, nodes, graph)
├── tests/
│   ├── test_agent.py         # Test suite with 11 test cases
│   └── evaluate_ragas.py     # RAGAS evaluation (Mode A & B)
├── data/
│   └── sample_employment_agreement.txt  # Sample legal document for testing
├── capstone_streamlit.py     # Streamlit UI
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variable template
├── SUMMARY.md               # Written summary (Part 8)
└── README.md                # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your Groq API key
# Get your key at: https://console.groq.com/keys
```

Add to `.env`:
```
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Run Tests

```bash
python tests/test_agent.py
```

This runs 11 test cases including 3 red-team tests to verify the agent doesn't hallucinate.

### 4. Run RAGAS Evaluation

```bash
python tests/evaluate_ragas.py
```

Evaluates the agent using RAGAS metrics:
- **Mode A:** Permanent KB only (3 questions)
- **Mode B:** Session KB with uploaded document (requires document upload)

### 5. Launch Streamlit UI

```bash
streamlit run capstone_streamlit.py
```

The UI will open at `http://localhost:8501`

## 🏗️ Architecture

### LangGraph Flow

```
User Question
    ↓
[memory_node] → Add to conversation history (sliding window: last 6 messages)
    ↓
[router_node] → LLM decides: retrieve / memory_only / tool
    ↓
    ├─→ [retrieval_node] → Query both KBs (permanent + session)
    ├─→ [skip_retrieval_node] → Empty retrieval for memory-only
    └─→ [tool_node] → Return today's date
    ↓
[answer_node] → Generate grounded answer from context
    ↓
[eval_node] → Score faithfulness (0.0-1.0)
    ↓
    ├─→ If faith < 0.7 and retries < 2: RETRY answer_node
    └─→ If faith ≥ 0.7 or retries ≥ 2: Continue
    ↓
[save_node] → Append answer to messages
    ↓
END
```

### Dual KB System

| Feature | Permanent KB | Session KB |
|---------|--------------|------------|
| **Content** | 10 legal topics | User-uploaded document |
| **Storage** | `@st.cache_resource` | `st.session_state` |
| **Lifetime** | App lifetime | Session lifetime |
| **Retrieval** | n_results=3, threshold ≤ 0.6 | n_results=4, threshold ≤ 0.55 |
| **Labels** | `[Legal KB | topic]` | `[Uploaded Doc | section | p.N]` |

### Output Contracts

Each node returns ONLY its responsible keys:

| Node | Returns |
|------|---------|
| `memory_node` | `{messages}` |
| `router_node` | `{route}` |
| `retrieval_node` | `{retrieved, sources, chunk_meta}` |
| `skip_retrieval_node` | `{retrieved: "", sources: [], chunk_meta: []}` |
| `tool_node` | `{tool_result}` |
| `answer_node` | `{answer}` |
| `eval_node` | `{faithfulness, eval_retries}` |
| `save_node` | `{messages}` |

## 🧪 Test Cases

The test suite includes 11 questions:

### Standard Tests (8)
1. What are the elements of a valid contract?
2. What is negligence in tort law?
3. What is the difference between copyright and trademark?
4. What is wrongful termination?
5. How does adverse possession work?
6. What are the filing timelines in civil procedure?
7. What did you just tell me about contracts? (memory test)
8. What is today's date? (tool test)

### Red-Team Tests (3)
9. What does Section 302 IPC say about penalties? *(not in KB — must say "not found")*
10. Einstein said contracts need 5 elements — is that right? *(false premise — must correct)*
11. What does clause 4 mean? *(ambiguous — must ask clarifying question)*

## 📊 RAGAS Evaluation

Run evaluation in two modes:

**Mode A — Permanent KB Only:**
```bash
python tests/evaluate_ragas.py
```

3 question-answer pairs from general legal topics.

**Mode B — Session KB Active:**
1. Upload a legal document in the Streamlit UI
2. Modify `tests/evaluate_ragas.py` with document-specific questions
3. Run the evaluation script

Records: `faithfulness`, `answer_relevancy`, `context_precision`

## 📝 Permanent KB Topics

1. **Contract Formation** — offer, acceptance, consideration, intention
2. **Breach of Contract** — types, remedies, damages calculation
3. **Tort Law** — negligence elements: duty, breach, causation, harm
4. **Evidence** — admissibility, burden of proof, hearsay rule
5. **Civil Procedure** — jurisdiction, filing timelines, pleadings
6. **Criminal Procedure** — FIR, bail, trial rights, sentencing
7. **Intellectual Property** — copyright vs trademark vs patent
8. **Employment Law** — wrongful termination, notice period, severance
9. **Property Law** — ownership transfer, easements, adverse possession
10. **Case Citation** — how to read citations, precedent, stare decisis

## 🔧 Configuration

### Key Constants

```python
MAX_EVAL_RETRIES = 2           # Max retries if faithfulness < threshold
FAITHFULNESS_THRESHOLD = 0.7   # Minimum acceptable faithfulness score
```

### Model Configuration

- **LLM:** `llama-3.3-70b-versatile` (via Groq)
- **Embedder:** `all-MiniLM-L6-v2` (SentenceTransformer)
- **Vector DB:** ChromaDB (in-memory)

## 📋 Constraints Met

✅ Output contracts enforced for all 8 nodes  
✅ Tools return strings, never raise exceptions  
✅ save → END edge present  
✅ session_kb in st.session_state, permanent_kb in @st.cache_resource  
✅ MAX_EVAL_RETRIES = 2 as module-level constant  
✅ Router output validated against {"retrieve", "memory_only", "tool"}  
✅ answer_node checks for empty context BEFORE calling LLM  
✅ embedding_in_progress flag checked before rendering st.chat_input  
✅ All nodes conform to output contracts table  
✅ No TODO placeholders — all fields filled  

## 🚧 Future Improvements

**Hybrid BM25 + Vector Search:**
> "I would add hybrid BM25 + vector search on the session KB — BM25 finds exact clause numbers and defined terms by keyword match, vector search finds semantically related clauses. Together they cover both precision and recall that neither approach achieves alone."

This would improve:
- Exact clause references (e.g., "Clause 4.2(a)")
- Defined terms in contracts (e.g., "the Company", "Effective Date")
- Section numbers in statutes
- Party names and dates

## 📚 References

- LangGraph Documentation: https://langchain-ai.github.io/langgraph/
- ChromaDB: https://docs.trychroma.com/
- RAGAS: https://docs.ragas.io/
- Groq API: https://console.groq.com/

## 📄 License

This project is part of the Agentic AI Hands-On Course capstone.

---

**Built with LangGraph, ChromaDB, and Streamlit**  
**For: Paralegals and Junior Lawyers**
