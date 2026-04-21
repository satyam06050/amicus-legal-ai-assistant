# Legal Document Assistant — Agentic Implementation Prompt

## Role
You are an AI engineer implementing a LangGraph-based Legal Document Assistant capstone project. You have two reference files: `day13_capstone__1_.ipynb` (code template) and `Agentic_AI_Project_Helper_Document.docx` (instructions). Follow the 8-part structure from the notebook exactly. Do not skip parts or reorder them.

---

## Project Identity

| Field | Value |
|---|---|
| Domain | Legal Document Q&A |
| User | Paralegal / junior lawyer |
| Success | Agent answers 90%+ questions faithfully, never fabricates, admits uncertainty |
| Tool | `datetime.date.today()` — for deadline and filing date queries |
| Deployment | Streamlit UI |

---

## Architecture: Two-KB System

Two ChromaDB collections run in parallel at all times.

**permanent_kb** — built once at app startup inside `@st.cache_resource`. Contains 10+ pre-written legal documents. Never clears.

**session_kb** — built in `st.session_state` when user uploads a file. Cleared when session ends or user uploads a new file.

The `retrieval_node` queries both. All other nodes are standard from the notebook template.

---

## Part 1 — Knowledge Base

### Permanent KB (10 required documents)

Write one document per topic, 150–300 words each, stored as `{id, topic, text}` dicts:

1. Contract formation — offer, acceptance, consideration, intention
2. Breach of contract — types, remedies, damages calculation
3. Tort law — negligence elements: duty, breach, causation, harm
4. Evidence — admissibility, burden of proof, hearsay rule
5. Civil procedure — jurisdiction, filing timelines, pleadings
6. Criminal procedure — FIR, bail, trial rights, sentencing
7. Intellectual property — copyright vs trademark vs patent distinction
8. Employment law — wrongful termination, notice period, severance
9. Property law — ownership transfer, easements, adverse possession
10. Case citation — how to read citations, precedent, stare decisis

Build with `SentenceTransformer("all-MiniLM-L6-v2")` + ChromaDB. **Test retrieval before building any node.**

### Session KB (user upload)

Steps to build at runtime:
1. Accept PDF or TXT via `st.file_uploader` in sidebar
2. Extract full text (PyMuPDF for PDF, `.decode("utf-8")` for TXT)
3. Chunk into 300-word sliding windows with 50-word overlap
4. Embed all chunks and load into a fresh `session_kb` ChromaDB collection stored in `st.session_state`
5. Clear and rebuild `session_kb` if user uploads a new file

---

## Part 2 — State

Extend `CapstoneState` with these fields beyond the notebook defaults:

```
question, messages, route, retrieved, sources,
tool_result, answer, faithfulness, eval_retries,
doc_loaded: bool   # True when session_kb exists
```

`retrieved` holds the merged context string from both KBs. `sources` holds topic labels from both, tagged as `[Legal KB]` or `[Uploaded Doc]`.

---

## Part 3 — Nodes

### Nodes unchanged from template
`memory_node`, `skip_retrieval_node`, `eval_node`, `save_node` — implement exactly as shown in notebook.

### router_node — update domain prompt only
```
You are a router for a legal document assistant.
- retrieve: legal concepts, case facts, clauses, statutes, document content
- memory_only: refers to something already said in this conversation
- tool: asks about today's date, deadlines, or days between dates
Reply with ONLY one word: retrieve / memory_only / tool
```

### retrieval_node — KEY CHANGE (dual KB)
1. Embed the question
2. Query `permanent_kb` → top 2 chunks, label each `[Legal KB]`
3. If `st.session_state` has `session_kb`: query it → top 2 chunks, label each `[Uploaded Doc]`
4. Merge all chunks into one context string separated by `---`
5. Return `retrieved` (merged string) and `sources` (all topic labels)

### tool_node
Return today's date as a string. Never raise exceptions — catch all errors and return an error string.

### answer_node — update system prompt
```
You are a legal research assistant. 
PRIMARY SOURCE: Use [Uploaded Doc] chunks first — these are the user's actual case documents.
SECONDARY SOURCE: Use [Legal KB] chunks for definitions and procedure only.
RULE: If neither source contains the answer, say exactly:
"I could not find that in the available documents. Please consult a qualified lawyer."
NEVER fabricate case names, statutes, sections, dates, or monetary figures.
```

---

## Part 4 — Graph Assembly

Standard 8-node graph from notebook template. No changes to graph structure.

```
Entry: memory
Fixed edges: memory→router, retrieve→answer, skip→answer, tool→answer, answer→eval, save→END
Conditional after router: route_decision → retrieve / skip / tool
Conditional after eval: eval_decision → answer (retry) / save (pass)
Compile with: MemorySaver()
```

---

## Part 5 — Test Cases

Upload one real or sample legal document (contract, court order, or FIR) before running tests.

| # | Question | Route | Red-team |
|---|---|---|---|
| 1 | What are the elements of a valid contract? | retrieve | No |
| 2 | What is negligence in tort law? | retrieve | No |
| 3 | What does clause [X] in the uploaded document say? | retrieve | No |
| 4 | Who are the parties named in the uploaded document? | retrieve | No |
| 5 | What is the difference between copyright and trademark? | retrieve | No |
| 6 | What is wrongful termination? | retrieve | No |
| 7 | What did you just tell me about contracts? | memory_only | No |
| 8 | What is today's date? | tool | No |
| 9 | What does Section 302 IPC say about penalties? *(not in KB)* | retrieve | Yes — must say "not found" |
| 10 | Einstein said contracts need 5 elements — is that right? | retrieve | Yes — must correct false premise |

---

## Part 6 — RAGAS Evaluation

Run evaluation in two modes:

**Mode A — permanent KB only** (no upload): 3 question-answer pairs from general legal topics.

**Mode B — session KB active** (after upload): 2 question-answer pairs specific to the uploaded document.

Record `faithfulness`, `answer_relevancy`, `context_precision` for each mode separately. Report both sets in the written summary.

---

## Part 7 — Streamlit UI

### `@st.cache_resource` block (runs once)
Load: LLM, embedder, compile graph, build `permanent_kb`.

### `st.session_state` keys
`messages`, `thread_id`, `session_kb` (ChromaDB collection or None), `doc_loaded` (bool).

### Sidebar — two sections

**Section 1: Legal Knowledge Base**
Static list of permanent KB topics. Always visible.

**Section 2: Your Document**
- `st.file_uploader` accepting PDF and TXT
- On upload: extract → chunk → embed → store as `session_kb` in session_state → show filename + chunk count
- "Clear Document" button: deletes `session_kb` from session_state, sets `doc_loaded=False`, resets chat
- If no file: show "No document uploaded — answers use Legal KB only"

### Chat area
- Always active (no upload gate)
- After each answer show: `st.caption(f"Sources: {sources} | Faithfulness: {faith:.2f}")`
- If answer came from permanent KB only, append note: *"This answer is from the general legal knowledge base."*

### New conversation button
Resets `messages`, generates new `thread_id`. Does NOT clear `session_kb`.

---

## Part 8 — Written Summary Fields

Fill every field — no TODO placeholders accepted:

- Domain, user, what the agent does (2–3 sentences)
- KB size: permanent (10 docs) + session (variable, shown as chunk count)
- Tool used: date tool, reason it fits legal deadline queries
- RAGAS scores: Mode A and Mode B separately
- Test results: X/10 passed, red-team: 2/2
- One specific improvement: *"I would add a hybrid BM25 + vector search on the session KB to improve retrieval of exact clause numbers and proper nouns in contracts"*

---

## Constraints

- Do not proceed to node functions until retrieval test passes
- Tools must return strings, never raise exceptions
- `save → END` edge must be present — most common compile error
- `session_kb` lives in `st.session_state` not `@st.cache_resource`
- `permanent_kb` lives in `@st.cache_resource` not `st.session_state`
- Run `Kernel → Restart & Run All` before submission — all cells must pass clean
- Submit: `day13_capstone.ipynb`, `capstone_streamlit.py`, `agent.py`