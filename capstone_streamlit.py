
"""
capstone_streamlit.py — Legal Document Assistant
Run: streamlit run capstone_streamlit.py
"""
import streamlit as st
import uuid
import os
import chromadb
import datetime
from io import BytesIO
from dotenv import load_dotenv
from typing import TypedDict, List
from sentence_transformers import SentenceTransformer
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import fitz  # PyMuPDF

load_dotenv()

st.set_page_config(page_title="Legal Document Assistant", page_icon="⚖️", layout="wide")
st.title("⚖️ Legal Document Assistant")
st.caption("AI-powered Q&A for legal documents and case law — answers questions faithfully from your documents and the legal knowledge base.")

# ── Load models and permanent KB (cached) ───────────────────────────
@st.cache_resource
def load_agent():
    """Load LLM, embedder, and build permanent KB."""
    llm      = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    # Permanent KB — built once at startup
    client = chromadb.Client()
    try: client.delete_collection("permanent_kb")
    except: pass
    perm_collection = client.create_collection("permanent_kb")

    # Copy all 10 legal documents here
    DOCUMENTS = [
        {"id": "doc_001", "topic": "Contract formation", "text": """A valid contract requires four essential elements: (1) Offer — one party proposes specific terms, (2) Acceptance — the other party agrees to those exact terms, (3) Consideration — something of value is exchanged by both parties, (4) Intention to create legal relations — both parties intend the agreement to be binding. The offeror can withdraw an offer before acceptance is communicated. Acceptance must be unconditional and match the offer exactly (mirror image rule). Consideration must be something of real value, though it need not be monetary. Both parties must have legal capacity (age, sanity) and the contract's purpose must be legal. Once all elements are present, the contract becomes binding and enforceable in court."""},
        {"id": "doc_002", "topic": "Breach of contract", "text": """A breach of contract occurs when one party fails to perform their obligations under a valid contract. There are three types: (1) Anticipatory breach — the party signals before performance is due that they won't perform, (2) Material breach — failure goes to the heart of the contract making it substantially unperformed, (3) Minor breach — non-critical obligation left unperformed. When a material breach occurs, the innocent party can either terminate the contract or continue and sue for damages. Damages are typically measured as the difference between contract price and market value (expectation damages). Some contracts include liquidated damages clauses that pre-set compensation amounts. The injured party must mitigate damages by taking reasonable steps to minimize loss. Specific performance may be ordered for unique goods or services that can't be replaced by money damages."""},
        {"id": "doc_003", "topic": "Tort law", "text": """A tort is a civil wrong (not criminal) causing harm for which the injured party can claim damages. The most common tort is negligence, which requires proving four elements: (1) Duty — the defendant owed a legal duty of care to the plaintiff, (2) Breach — the defendant breached that duty through action or inaction, (3) Causation — the defendant's breach directly caused injury, (4) Damages — the plaintiff suffered measurable harm (physical, financial, emotional). Negligence applies to situations like car accidents, medical malpractice, and unsafe premises. Other major torts include battery (intentional harmful contact), assault (threat of contact), defamation (false statements damaging reputation), and false imprisonment. Defenses include assumption of risk, contributory negligence, and act of God. Damages in tort cases include compensatory damages (to make whole), and in egregious cases, punitive damages (to punish defendant and deter others)."""},
        {"id": "doc_004", "topic": "Evidence", "text": """Evidence is information presented in court to prove or disprove facts. For evidence to be admissible, it must be relevant (tends to prove or disprove a fact), probative (actually helps prove the point), and not unfairly prejudicial. The burden of proof varies by case type: in criminal cases, the prosecution must prove guilt 'beyond a reasonable doubt' (very high standard), in civil cases, the standard is 'preponderance of the evidence' (more likely than not). Hearsay — an out-of-court statement offered to prove its truth — is generally inadmissible because the original speaker can't be cross-examined. However, exceptions include excited utterances, statements against interest, and dying declarations. Documents must be authenticated (shown to be what they claim). Expert witnesses can give opinion testimony if qualified. Privileged communications (attorney-client, doctor-patient, spouse) are protected and not admissible."""},
        {"id": "doc_005", "topic": "Civil procedure", "text": """Civil procedure governs how lawsuits proceed from filing to judgment. Cases typically progress through these stages: (1) Pleadings — plaintiff files complaint stating claims, defendant files answer, (2) Discovery — parties exchange relevant documents and testimony, (3) Motion practice — parties ask court to rule on preliminary matters, (4) Trial — evidence presented and judgment rendered, (5) Appeal — losing party can request higher court review on legal grounds only. Jurisdiction — the court's power to hear a case — can be personal (defendant's location), subject matter (type of claim), or venue (proper county/district). Filing deadlines are strict and missing them forfeits claims. The statute of limitations sets time limits for filing suits (varies by claim type, usually 1-6 years). Pleadings must contain enough facts to state a plausible claim. Discovery includes interrogatories, requests for production, depositions, and requests for admission. Pre-trial conferences narrow issues and encourage settlement."""},
        {"id": "doc_006", "topic": "Criminal procedure", "text": """Criminal procedure protects defendants' rights while allowing prosecution of crimes. The process begins with a crime being reported and investigated. Once arrested, a suspect must be informed of Miranda rights (right to remain silent, that statements can be used against them, right to attorney, court-appointed if poor). A First Information Report (FIR) is filed with police, launching formal investigation. Bail determines if the accused is released pending trial; factors include flight risk and crime severity. Arraignment is the first court appearance where charges are read and plea entered (guilty, not guilty, or no contest). Discovery requires prosecution to share evidence including witness statements and physical evidence. The defendant has the right to confront witnesses (cross-examination). Trial proceeds with jury selection, opening statements, prosecution evidence, defense evidence, closing arguments, jury deliberation, and verdict. Sentencing follows conviction. Appeals review whether law was applied correctly but can't retry facts."""},
        {"id": "doc_007", "topic": "Intellectual property", "text": """Intellectual property (IP) protects creations of the mind. Copyright protects original works of authorship (books, songs, software, movies) for the author's life plus 70 years. Copyright arises automatically upon creation; registration strengthens protection. Trademark protects brand names, logos, and distinctive symbols used in commerce for distinguishing goods/services. Trademarks can last forever if continuously used and renewed. Patents protect novel, non-obvious inventions (utility patents for 20 years, design patents for 14 years). Patents require formal application with detailed specifications and claims. Trade secrets are confidential information (formulas, processes, customer lists) that derive value from non-disclosure; they're protected if reasonable security measures are taken. IP infringement occurs when someone reproduces, distributes, or uses protected work without permission. Remedies include injunctions (stop using), damages (compensation), and disgorgement of profits. Fair use in copyright allows limited use for criticism, commentary, news, teaching, and research."""},
        {"id": "doc_008", "topic": "Employment law", "text": """Employment law governs the relationship between employers and employees. Employment is typically 'at-will' meaning either party can terminate without cause (in most jurisdictions), but many protections exist. Wrongful termination occurs when firing violates law, public policy, or contract. Protected classes (race, color, religion, sex, national origin, age, disability) cannot be reasons for adverse employment actions; discrimination based on these grounds is illegal. Harassment based on protected characteristics creates hostile work environment. Wage and hour laws require minimum wage payment and overtime compensation. FMLA provides up to 12 weeks unpaid leave for serious health conditions. Workers' compensation covers injuries sustained during employment. Severance packages sometimes condition payment on non-disparagement and release of claims. Restrictive covenants (non-competes, NDAs) must be reasonable in scope, duration, and geography. At-will employment can be restricted by union contracts or implied contract from employee handbook."""},
        {"id": "doc_009", "topic": "Property law", "text": """Property law deals with ownership, transfer, and use of real and personal property. Ownership transfer requires a valid deed describing the property, executed by owner, delivered to recipient, and recorded in county records. Title is confirmed through title search and title insurance. Possession alone doesn't establish ownership; adverse possession can transfer title only after continuous, open possession for a statutory period (varies by jurisdiction, typically 7-21 years). Real property includes land and structures; personal property includes movable items. Easements are rights to use another's land (e.g., utilities crossing property). Covenants restrict how property can be used; they run with the land binding future owners. Mortgages are loans secured by property; lender can foreclose if borrower defaults. Landlord-tenant law governs rental arrangements; tenants have right to habitable premises, landlords can evict for non-payment or lease violation with proper notice. Property rights can be limited by zoning laws, environmental regulations, and HOA rules."""},
        {"id": "doc_010", "topic": "Case citation", "text": """Legal citations identify cases, statutes, and other authority. Case citations show where to find reported decisions. Standard format: Case Name v. Other Party, Volume Reporter Page (Court Year). Example: Miranda v. Arizona, 384 U.S. 436 (1966). The 'U.S.' means United States Supreme Court Reports. 'F.2d' means Federal Reporter (second series) for federal appeals courts. 'S.Ct.' means Supreme Court Reporter. Regional reporters cover state court decisions (e.g., 'N.E.' for Northeastern states). Statutes are cited as: Title Code Section. Example: 42 U.S.C. § 1983 (federal statute). Precedent means lower courts must follow decisions from higher courts in their jurisdiction. Stare decisis means standing by decided cases — courts follow precedent unless persuaded otherwise. Overruling occurs when a higher court reverses a lower court's decision or rejects earlier precedent. Dictum (non-binding statements) differs from holding (binding decision). Persuasive authority (from other jurisdictions) influences but doesn't bind courts."""},
    ]

    texts = [d["text"] for d in DOCUMENTS]
    embeddings = embedder.encode(texts).tolist()
    perm_collection.add(
        documents=texts, 
        embeddings=embeddings,
        ids=[d["id"] for d in DOCUMENTS],
        metadatas=[{"topic":d["topic"]} for d in DOCUMENTS]
    )

    # CapstoneState TypedDict
    class CapstoneState(TypedDict):
        question:      str
        messages:      List[dict]
        route:         str
        retrieved:     str
        sources:       List[str]
        tool_result:   str
        answer:        str
        faithfulness:  float
        eval_retries:  int
        doc_loaded:    bool

    # Node Functions
    def memory_node(state: CapstoneState) -> dict:
        msgs = state.get("messages", [])
        msgs = msgs + [{"role": "user", "content": state["question"]}]
        if len(msgs) > 6:
            msgs = msgs[-6:]
        return {"messages": msgs}

    def router_node(state: CapstoneState) -> dict:
        question = state["question"]
        messages = state.get("messages", [])
        recent   = "; ".join(f"{m['role']}: {m['content'][:60]}" for m in messages[-3:-1]) or "none"
        prompt = f"""You are a router for a legal document assistant.
Available options:
- retrieve: legal concepts, case facts, clauses, statutes, document content
- memory_only: refers to something already said in this conversation
- tool: asks about today's date, deadlines, or days between dates
Reply with ONLY one word: retrieve / memory_only / tool

Recent conversation: {recent}
Current question: {question}"""
        response = llm.invoke(prompt)
        decision = response.content.strip().lower()
        if "memory" in decision:       decision = "memory_only"
        elif "tool" in decision:       decision = "tool"
        else:                          decision = "retrieve"
        return {"route": decision}

    def retrieval_node(state: CapstoneState) -> dict:
        question = state["question"]
        q_emb = embedder.encode([question]).tolist()

        # Query permanent KB
        results_perm = perm_collection.query(query_embeddings=q_emb, n_results=2)
        chunks_perm = results_perm["documents"][0]
        topics_perm = [m["topic"] for m in results_perm["metadatas"][0]]

        # Query session KB if available
        context_parts = []
        all_sources = []

        for i, (chunk, topic) in enumerate(zip(chunks_perm, topics_perm)):
            context_parts.append(f"[Legal KB: {topic}]\n{chunk}")
            all_sources.append(f"{topic} [Legal KB]")

        # Check for session KB
        if st.session_state.get("session_kb") is not None:
            results_sess = st.session_state.session_kb.query(query_embeddings=q_emb, n_results=2)
            chunks_sess = results_sess["documents"][0]
            for chunk in chunks_sess:
                context_parts.append(f"[Uploaded Doc]\n{chunk}")
                all_sources.append("[Uploaded Doc]")

        context = "\n\n---\n\n".join(context_parts)
        return {"retrieved": context, "sources": all_sources}

    def skip_retrieval_node(state: CapstoneState) -> dict:
        return {"retrieved": "", "sources": []}

    def tool_node(state: CapstoneState) -> dict:
        try:
            today = datetime.date.today()
            tool_result = f"Today's date: {today.strftime('%B %d, %Y')} (ISO: {today.isoformat()})"
        except Exception as e:
            tool_result = f"[Tool error: {str(e)}]"
        return {"tool_result": tool_result}

    def answer_node(state: CapstoneState) -> dict:
        question    = state["question"]
        retrieved   = state.get("retrieved", "")
        tool_result = state.get("tool_result", "")
        messages    = state.get("messages", [])
        eval_retries= state.get("eval_retries", 0)

        context_parts = []
        if retrieved:
            context_parts.append(f"KNOWLEDGE BASE:\n{retrieved}")
        if tool_result:
            context_parts.append(f"TOOL RESULT:\n{tool_result}")
        context = "\n\n".join(context_parts)

        if context:
            system_content = """You are a legal research assistant. 
PRIMARY SOURCE: Use [Uploaded Doc] chunks first — these are the user's actual case documents.
SECONDARY SOURCE: Use [Legal KB] chunks for definitions and procedure only.
RULE: If neither source contains the answer, say exactly:
"I could not find that in the available documents. Please consult a qualified lawyer."
NEVER fabricate case names, statutes, sections, dates, or monetary figures.

""" + context
        else:
            system_content = """You are a legal research assistant. Answer based on the conversation history.
RULE: If you don't know the answer, say: "I could not find that in the available documents. Please consult a qualified lawyer." 
NEVER fabricate case names, statutes, sections, dates, or monetary figures."""

        if eval_retries > 0:
            system_content += "\n\nIMPORTANT: Your previous answer did not meet quality standards. Answer using ONLY information explicitly stated in the context above."

        lc_msgs = [SystemMessage(content=system_content)]
        for msg in messages[:-1]:
            lc_msgs.append(HumanMessage(content=msg["content"]) if msg["role"] == "user"
                           else AIMessage(content=msg["content"]))
        lc_msgs.append(HumanMessage(content=question))

        response = llm.invoke(lc_msgs)
        return {"answer": response.content}

    def eval_node(state: CapstoneState) -> dict:
        answer   = state.get("answer", "")
        context  = state.get("retrieved", "")[:500]
        retries  = state.get("eval_retries", 0)

        if not context:
            return {"faithfulness": 1.0, "eval_retries": retries + 1}

        prompt = f"""Rate faithfulness: does this answer use ONLY information from the context?
Reply with ONLY a number between 0.0 and 1.0.
1.0 = fully faithful. 0.5 = some hallucination. 0.0 = mostly hallucinated.

Context: {context}
Answer: {answer[:300]}"""

        result = llm.invoke(prompt).content.strip()
        try:
            score = float(result.split()[0].replace(",", "."))
            score = max(0.0, min(1.0, score))
        except:
            score = 0.5

        return {"faithfulness": score, "eval_retries": retries + 1}

    def save_node(state: CapstoneState) -> dict:
        messages = state.get("messages", [])
        messages = messages + [{"role": "assistant", "content": state["answer"]}]
        return {"messages": messages}

    # Graph Assembly
    def route_decision(state: CapstoneState) -> str:
        route = state.get("route", "retrieve")
        if route == "tool":        return "tool"
        if route == "memory_only": return "skip"
        return "retrieve"

    def eval_decision(state: CapstoneState) -> str:
        FAITHFULNESS_THRESHOLD = 0.7
        MAX_EVAL_RETRIES = 2
        score   = state.get("faithfulness", 1.0)
        retries = state.get("eval_retries", 0)
        if score >= FAITHFULNESS_THRESHOLD or retries >= MAX_EVAL_RETRIES:
            return "save"
        return "answer"

    graph = StateGraph(CapstoneState)
    graph.add_node("memory",    memory_node)
    graph.add_node("router",    router_node)
    graph.add_node("retrieve",  retrieval_node)
    graph.add_node("skip",      skip_retrieval_node)
    graph.add_node("tool",      tool_node)
    graph.add_node("answer",    answer_node)
    graph.add_node("eval",      eval_node)
    graph.add_node("save",      save_node)

    graph.set_entry_point("memory")
    graph.add_edge("memory",   "router")
    graph.add_conditional_edges("router", route_decision, {"retrieve": "retrieve", "skip": "skip", "tool": "tool"})
    graph.add_edge("retrieve", "answer")
    graph.add_edge("skip",     "answer")
    graph.add_edge("tool",     "answer")
    graph.add_edge("answer", "eval")
    graph.add_conditional_edges("eval", eval_decision, {"answer": "answer", "save": "save"})
    graph.add_edge("save", END)

    checkpointer = MemorySaver()
    agent_app = graph.compile(checkpointer=checkpointer)

    return agent_app, embedder, perm_collection


try:
    agent_app, embedder, perm_collection = load_agent()
    st.success(f"✅ Legal KB loaded — {perm_collection.count()} documents")
except Exception as e:
    st.error(f"Failed to load agent: {e}")
    st.stop()

# ── Session state ─────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())[:8]
if "session_kb" not in st.session_state:
    st.session_state.session_kb = None
if "doc_loaded" not in st.session_state:
    st.session_state.doc_loaded = False

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.header("⚖️ Knowledge Base")

    st.subheader("Legal Knowledge Base")
    st.write("**Topics covered:**")
    legal_topics = ["Contract formation", "Breach of contract", "Tort law", "Evidence", 
                    "Civil procedure", "Criminal procedure", "Intellectual property", 
                    "Employment law", "Property law", "Case citation"]
    for t in legal_topics:
        st.write(f"• {t}")

    st.divider()
    st.subheader("Your Document")

    uploaded_file = st.file_uploader("Upload a legal document (PDF or TXT):", type=["pdf", "txt"])

    if uploaded_file is not None:
        try:
            if uploaded_file.type == "application/pdf":
                pdf_doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                text = ""
                for page_num in range(len(pdf_doc)):
                    page = pdf_doc[page_num]; text += page.get_text(); text += "\n\n"
            else:  # txt
                text = uploaded_file.read().decode("utf-8")

            # Chunk into 300-word sliding windows with 50-word overlap
            words = text.split()
            chunks = []
            for i in range(0, len(words), 250):  # 300-word chunks with 50-word overlap
                chunk = " ".join(words[i:i+300])
                if len(chunk.split()) > 50:
                    chunks.append(chunk)

            # Build session KB
            client = chromadb.Client()
            try: client.delete_collection("session_kb")
            except: pass
            session_collection = client.create_collection("session_kb")

            embeddings = embedder.encode(chunks).tolist()
            session_collection.add(
                documents=chunks,
                embeddings=embeddings,
                ids=[f"chunk_{i}" for i in range(len(chunks))],
                metadatas=[{"source": uploaded_file.name} for _ in chunks]
            )

            st.session_state.session_kb = session_collection
            st.session_state.doc_loaded = True
            st.success(f"✅ Document loaded: {len(chunks)} chunks from {uploaded_file.name}")

        except Exception as e:
            st.error(f"Error processing file: {e}")

    if st.session_state.doc_loaded and st.button("🗑️ Clear Document"):
        st.session_state.session_kb = None
        st.session_state.doc_loaded = False
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())[:8]
        st.rerun()

    if not st.session_state.doc_loaded:
        st.info("No document uploaded — answers use Legal KB only")

    st.divider()
    if st.button("🔄 New conversation"):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())[:8]
        st.rerun()
    st.caption(f"Session: {st.session_state.thread_id}")

# ── Display history ───────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ── Chat input ────────────────────────────────────────────
if prompt := st.chat_input("Ask about legal topics or your document..."):
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role":"user","content":prompt})

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                config = {"configurable": {"thread_id": st.session_state.thread_id}}
                result = agent_app.invoke({"question": prompt}, config=config)
                answer = result.get("answer", "Sorry, I could not generate an answer.")
                faith = result.get("faithfulness", 0.0)
                sources = result.get("sources", [])

                st.write(answer)

                # Show sources and faithfulness
                source_str = ", ".join(sources[:3]) if sources else "general legal KB"
                st.caption(f"Faithfulness: {faith:.2f} | Sources: {source_str}")

                if not st.session_state.doc_loaded:
                    st.caption("*This answer is from the general legal knowledge base.*")

            except Exception as e:
                st.error(f"Error: {e}")
                answer = f"[Error: {str(e)}]"

    st.session_state.messages.append({"role":"assistant","content":answer})

