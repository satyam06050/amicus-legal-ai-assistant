"""
agent.py — Legal Document Assistant Agent
Core implementation with dual KB system, LangGraph nodes, and graph assembly.
"""

import os
import datetime
from typing import TypedDict, List
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import chromadb
from sentence_transformers import SentenceTransformer

load_dotenv()

# ============================================================
# Constants
# ============================================================
MAX_EVAL_RETRIES = 2
FAITHFULNESS_THRESHOLD = 0.7

# ============================================================
# Part 1: Knowledge Base
# ============================================================

# Permanent KB Documents (10 required legal topics)
PERMANENT_DOCUMENTS = [
    {
        "id": "doc_001",
        "topic": "Contract Formation",
        "text": """Contract formation requires four essential elements: offer, acceptance, consideration, and intention to create legal relations. An offer is a clear proposal made by one party to another, indicating willingness to enter into a contract on specific terms. Acceptance must be unconditional and communicated to the offeror — silence generally does not constitute acceptance. Consideration means each party must provide something of value (money, services, goods, or a promise) in exchange for what they receive. Past consideration is not valid. Both parties must intend for the agreement to be legally binding; social and domestic agreements are presumed not to have this intention, while commercial agreements are presumed to have it. Contracts can be written, oral, or implied by conduct, though certain types (like property transfers) must be in writing to be enforceable."""
    },
    {
        "id": "doc_002",
        "topic": "Breach of Contract",
        "text": """Breach of contract occurs when one party fails to perform their obligations under the agreement without lawful excuse. There are several types of breach: actual breach (failure to perform when due), anticipatory breach (indicating before the due date that performance will not occur), material breach (substantial failure going to the root of the contract), and minor breach (partial or imperfect performance). Remedies for breach include damages (monetary compensation), specific performance (court order to fulfill obligations), injunction (court order preventing certain actions), and rescission (cancellation of the contract). Damages are calculated to put the innocent party in the position they would have been in had the contract been performed. This includes expectation damages (loss of bargain), reliance damages (expenses incurred), and restitution damages (benefit conferred on breaching party). The innocent party has a duty to mitigate their losses."""
    },
    {
        "id": "doc_003",
        "topic": "Tort Law — Negligence",
        "text": """Negligence in tort law requires establishing four essential elements: duty of care, breach of duty, causation, and harm. Duty of care exists when the law recognizes a relationship between parties requiring one to act with reasonable care toward the other — established in Donoghue v Stevenson (the snail in the bottle case). The 'neighbour principle' states you must take reasonable care to avoid acts or omissions that could foreseeably injure your neighbour (persons closely and directly affected). Breach of duty occurs when the defendant's conduct falls below the standard of a reasonable person in similar circumstances. Causation has two parts: factual causation ('but for' test — would the harm have occurred but for the defendant's breach?) and legal causation (was the harm a reasonably foreseeable consequence?). Finally, the plaintiff must prove actual harm or damage, which can be physical injury, property damage, economic loss, or recognized psychiatric injury."""
    },
    {
        "id": "doc_004",
        "topic": "Evidence Law",
        "text": """Evidence law governs what information can be presented in court to prove or disprove facts in dispute. The burden of proof determines who must prove what: in civil cases, the plaintiff bears the burden and must prove their case on the 'balance of probabilities' (more likely than not); in criminal cases, the prosecution bears the burden and must prove guilt 'beyond reasonable doubt' (a much higher standard). Admissibility rules determine whether evidence can be considered by the court — evidence must be relevant, material, and competent. The hearsay rule generally excludes out-of-court statements offered to prove the truth of the matter asserted, as the original speaker cannot be cross-examined. However, numerous exceptions exist (dying declarations, business records, excited utterances). Real evidence (physical objects), documentary evidence, testimonial evidence (witness statements), and digital evidence each have specific authentication requirements. Privileged communications (lawyer-client, spouse-spouse) are protected from disclosure."""
    },
    {
        "id": "doc_005",
        "topic": "Civil Procedure",
        "text": """Civil procedure governs the process for resolving non-criminal legal disputes. Jurisdiction determines which court has authority to hear a case — based on subject matter (what type of dispute), territorial jurisdiction (where events occurred or defendants reside), and pecuniary jurisdiction (monetary value of the claim). Filing timelines are governed by statutes of limitations, which set maximum time periods after an event within which legal proceedings may be initiated — these vary by claim type (typically 1-6 years for civil matters). Pleadings are formal written statements filed by parties: the plaintiff files a complaint stating their claim, the defendant files an answer responding to each allegation, and may file counterclaims or cross-claims. The discovery process allows parties to obtain evidence from each other through interrogatories (written questions), depositions (oral questioning under oath), and requests for document production. Summary judgment may be granted when there is no genuine dispute of material fact and the moving party is entitled to judgment as a matter of law."""
    },
    {
        "id": "doc_006",
        "topic": "Criminal Procedure",
        "text": """Criminal procedure governs the process from investigation through sentencing. An FIR (First Information Report) is the first step — it is information about a cognizable offense given to police, which initiates investigation. The police investigate, collect evidence, and may arrest the suspect. Bail is the temporary release of an accused person awaiting trial — it can be anticipatory (before arrest) or regular (after arrest). Bail may be denied for serious offenses, flight risk, or witness tampering concerns. Trial rights include the right to be informed of charges, the right to legal representation, the right to present a defense, the right to cross-examine witnesses, the presumption of innocence, and protection against self-incrimination. The prosecution must prove guilt beyond reasonable doubt. Sentencing occurs after conviction and may include imprisonment, fines, probation, community service, or rehabilitation programs. Sentencing considers aggravating factors (prior convictions, violence, vulnerability of victim) and mitigating factors (first offense, remorse, cooperation). Appeals process allows convicted persons to challenge conviction or sentence on grounds of legal error or procedural irregularity."""
    },
    {
        "id": "doc_007",
        "topic": "Intellectual Property",
        "text": """Intellectual property law protects creations of the mind through three main mechanisms: copyright, trademark, and patent. Copyright protects original literary, artistic, musical, and dramatic works automatically upon creation — it protects the expression of ideas, not the ideas themselves. Copyright gives the owner exclusive rights to reproduce, distribute, perform, display, and create derivative works. Duration is typically the author's life plus 60-70 years depending on jurisdiction. Trademark protects words, phrases, symbols, or designs identifying and distinguishing goods or services of one source from others — examples include brand names, logos, and slogans. Trademarks must be distinctive and are registered for specific classes of goods/services. They can last indefinitely if renewed and actively used. Patents protect inventions (new, useful, and non-obvious processes, machines, manufactures, or compositions of matter) for a limited period, usually 20 years from filing. In exchange for disclosure, the patent holder gets exclusive rights to make, use, sell, and import the invention. Trade secrets protect confidential business information (formulas, practices, designs) that provide competitive advantage — protection lasts as long as secrecy is maintained."""
    },
    {
        "id": "doc_008",
        "topic": "Employment Law",
        "text": """Employment law governs the relationship between employers and employees. Wrongful termination occurs when an employee is dismissed in violation of employment contracts, labor laws, or public policy. Grounds for wrongful termination claims include discrimination (based on race, gender, age, religion, disability), retaliation (for whistleblowing or exercising legal rights), breach of employment contract, or violation of public policy. Notice period requirements depend on employment type and jurisdiction — typically ranging from one week to three months based on length of service. During notice period, employees are entitled to normal pay and benefits. Severance pay (also called termination pay or redundancy pay) is compensation provided to employees upon termination, often calculated based on years of service (e.g., one month's salary per year of service). Severance may be required by employment contract, company policy, or statutory law in cases of layoffs or retrenchment. Employees have rights to fair wages, safe working conditions, reasonable working hours, leave entitlements (sick leave, annual leave, maternity leave), and protection against harassment and discrimination. Independent contractors have different rights than employees and are generally not entitled to employment benefits."""
    },
    {
        "id": "doc_009",
        "topic": "Property Law",
        "text": """Property law governs ownership, use, and transfer of real and personal property. Ownership transfer in real property requires a valid deed (written legal document), proper execution (signed by grantor, witnessed, notarized), delivery and acceptance by the grantee, and recording with the appropriate government authority to provide notice to third parties. The chain of title must be clear — any liens, encumbrances, or disputes must be resolved before transfer. Easements are non-possessory rights to use another person's land for a specific purpose — examples include utility easements (power lines), right-of-way easements (access roads), and conservation easements. Easements can be express (created by written agreement), implied (necessary for land use), or prescriptive (acquired through long-term continuous use). Adverse possession allows a person to claim ownership of land they do not own by possessing it openly, notoriously, exclusively, continuously, and hostilely (without owner's permission) for a statutory period (typically 12-20 years depending on jurisdiction). The adverse possessor must pay property taxes and treat the land as their own. This doctrine exists to encourage productive use of land and resolve boundary disputes."""
    },
    {
        "id": "doc_010",
        "topic": "Case Citation and Precedent",
        "text": """Understanding case citations and the doctrine of precedent is fundamental to legal research. A case citation provides the information needed to locate a court decision — standard format is: Case Name, Volume Reporter Page (Court Year). For example, "Smith v Jones, 456 F.3d 123 (2d Cir. 2006)" means: Smith v Jones is the case name, 456 is the volume number, F.3d indicates Federal Reporter Third Series, 123 is the starting page, 2nd Circuit is the court, and 2006 is the year of decision. Different reporters exist: U.S. Reports (U.S.) for Supreme Court, Federal Reporter (F., F.2d, F.3d) for circuit courts, Federal Supplement (F.Supp.) for district courts, and regional reporters for state cases. Precedent (stare decisis) is the doctrine that courts should follow prior decisions when the same legal issues arise again. Binding precedent must be followed — decisions from higher courts in the same jurisdiction. Persuasive precedent (from other jurisdictions or lower courts) may be considered but is not mandatory. Courts distinguish cases when facts differ materially, overrule precedent when explicitly rejecting prior decisions, or abrogate when legislation supersedes case law. The hierarchy of courts determines which precedents are binding: Supreme Court decisions bind all lower courts; circuit court decisions bind district courts within that circuit."""
    }
]


def build_permanent_kb():
    """Build permanent knowledge base. Call once at startup."""
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.Client()
    
    try:
        client.delete_collection("permanent_kb")
    except:
        pass
    
    collection = client.create_collection("permanent_kb")
    
    texts = [d["text"] for d in PERMANENT_DOCUMENTS]
    ids = [d["id"] for d in PERMANENT_DOCUMENTS]
    metadatas = [{"topic": d["topic"]} for d in PERMANENT_DOCUMENTS]
    embeddings = embedder.encode(texts).tolist()
    
    collection.add(
        documents=texts,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas
    )
    
    return embedder, collection


def build_session_kb(file, embedder):
    """Build session knowledge base from uploaded file.
    
    Args:
        file: Streamlit UploadedFile object (PDF or TXT)
        embedder: SentenceTransformer model
    
    Returns:
        ChromaDB collection or None if failed
    """
    import fitz  # PyMuPDF
    
    try:
        filename = file.name.lower()
        
        # Extract text
        if filename.endswith('.pdf'):
            doc = fitz.open(stream=file.read(), filetype="pdf")
            full_text = ""
            for page_num in range(len(doc)):
                page = doc[page_num]
                full_text += page.get_text()
                full_text += "\n\n"  # Preserve page breaks
            doc.close()
        elif filename.endswith('.txt'):
            full_text = file.read().decode("utf-8")
        else:
            return None
        
        # Chunk at section boundaries
        chunks = []
        current_chunk_lines = []
        current_heading = ""
        page_number = 1
        
        lines = full_text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Check if line is a heading
            is_heading = False
            heading_patterns = ['Clause', 'Section', 'Article', 'Schedule', 'Annexure']
            
            if any(line.startswith(pattern) for pattern in heading_patterns):
                is_heading = True
            elif line and (line[0].isdigit() and len(line) < 20 and ('.' in line[:5] or line.endswith('.'))) or \
                 (line[0] == '(' and line[1].isalpha() and line.endswith(')')):
                # Patterns like "1.", "2.1", "(a)"
                is_heading = True
            
            if is_heading and current_chunk_lines:
                # Save current chunk
                chunk_text = '\n'.join(current_chunk_lines)
                word_count = len(chunk_text.split())
                
                if word_count >= 30:
                    chunks.append({
                        "text": chunk_text,
                        "heading": current_heading,
                        "page": page_number,
                        "word_count": word_count
                    })
                elif chunks:
                    # Merge with previous chunk
                    chunks[-1]["text"] += '\n' + chunk_text
                    chunks[-1]["word_count"] = len(chunks[-1]["text"].split())
                
                current_chunk_lines = []
                current_heading = line
            else:
                current_chunk_lines.append(line)
        
        # Don't forget the last chunk
        if current_chunk_lines:
            chunk_text = '\n'.join(current_chunk_lines)
            word_count = len(chunk_text.split())
            if word_count >= 30:
                chunks.append({
                    "text": chunk_text,
                    "heading": current_heading,
                    "page": page_number,
                    "word_count": word_count
                })
            elif chunks:
                chunks[-1]["text"] += '\n' + chunk_text
                chunks[-1]["word_count"] = len(chunks[-1]["text"].split())
        
        # Enforce size guard: split chunks > 400 words with 50-word overlap
        final_chunks = []
        for chunk in chunks:
            words = chunk["text"].split()
            if len(words) > 400:
                # Split with overlap
                overlap = 50
                for i in range(0, len(words), 400 - overlap):
                    sub_words = words[i:i + 400]
                    sub_text = ' '.join(sub_words)
                    final_chunks.append({
                        "text": sub_text,
                        "heading": chunk["heading"],
                        "page": chunk["page"],
                        "word_count": len(sub_words)
                    })
            else:
                final_chunks.append(chunk)
        
        # Build session KB
        client = chromadb.Client()
        try:
            client.delete_collection("session_kb")
        except:
            pass
        
        collection = client.create_collection("session_kb")
        
        if final_chunks:
            texts = [c["text"] for c in final_chunks]
            ids = [f"session_{i}" for i in range(len(final_chunks))]
            metadatas = [
                {
                    "chunk_id": ids[i],
                    "page_number": str(final_chunks[i]["page"]),
                    "section_heading": final_chunks[i]["heading"],
                    "word_count": str(final_chunks[i]["word_count"])
                }
                for i in range(len(final_chunks))
            ]
            embeddings = embedder.encode(texts).tolist()
            
            collection.add(
                documents=texts,
                embeddings=embeddings,
                ids=ids,
                metadatas=metadatas
            )
        
        return collection
    
    except Exception as e:
        print(f"Error building session KB: {e}")
        return None


# ============================================================
# Part 2: State Design
# ============================================================

class CapstoneState(TypedDict):
    # Input
    question: str
    
    # Memory
    messages: List[dict]
    
    # Routing
    route: str
    
    # RAG
    retrieved: str
    sources: List[str]
    
    # Tool
    tool_result: str
    
    # Answer
    answer: str
    
    # Quality control
    faithfulness: float
    eval_retries: int
    
    # Domain-specific fields
    doc_loaded: bool  # True when session_kb exists
    chunk_meta: List[dict]  # [{source, topic, chunk_id, page_number, section_heading, distance}]


# ============================================================
# Part 3: Node Functions
# ============================================================

def memory_node(state: CapstoneState) -> dict:
    """Add question to conversation history with sliding window."""
    msgs = state.get("messages", [])
    msgs = msgs + [{"role": "user", "content": state["question"]}]
    if len(msgs) > 6:  # Keep last 3 turns
        msgs = msgs[-6:]
    return {"messages": msgs}


def router_node(state: CapstoneState, llm: ChatGroq) -> dict:
    """Route question to retrieve, memory_only, or tool."""
    question = state["question"]
    messages = state.get("messages", [])
    recent = "; ".join(
        f"{m['role']}: {m['content'][:60]}" 
        for m in messages[-3:-1]
    ) or "none"
    
    prompt = f"""You are a router for a legal document assistant.

Routes:
- retrieve: question about legal concepts, case facts, clauses, statutes, document content, or ANY combination of these
- memory_only: question refers ONLY to something already said in this exact conversation (e.g. "what did you mean by that?", "say that again")
- tool: question asks ONLY about today's date, a deadline date, or days between two dates

IMPORTANT EDGE CASES:
- Mixed queries (e.g. "based on what you said, what does clause 4 mean?") → retrieve
- Ambiguous clause reference with no document uploaded → retrieve (agent will handle gracefully)
- Any doubt → retrieve

Recent conversation: {recent}
Current question: {question}

Reply with ONLY one word: retrieve / memory_only / tool"""
    
    response = llm.invoke(prompt)
    decision = response.content.strip().lower()
    
    # Validate against allowed routes
    if decision not in {"retrieve", "memory_only", "tool"}:
        decision = "retrieve"  # Default to retrieve on unrecognised output
    
    return {"route": decision}


def retrieval_node(state: CapstoneState, embedder, permanent_kb, session_kb=None) -> dict:
    """Query both permanent and session KBs with quality controls."""
    try:
        question = state["question"]
        q_emb = embedder.encode([question]).tolist()
        
        all_chunks = []
        all_sources = []
        all_meta = []
        
        # Query permanent_kb
        try:
            perm_results = permanent_kb.query(query_embeddings=q_emb, n_results=3)
            for i, (doc, meta, dist) in enumerate(zip(
                perm_results["documents"][0],
                perm_results["metadatas"][0],
                perm_results["distances"][0]
            )):
                if dist <= 0.6:  # Distance threshold
                    label = f"[Legal KB | {meta['topic']}]"
                    all_chunks.append(f"{label}\n{doc}")
                    all_sources.append(label)
                    all_meta.append({
                        "source": "Legal KB",
                        "topic": meta["topic"],
                        "chunk_id": perm_results["ids"][0][i],
                        "distance": dist
                    })
        except Exception as e:
            all_sources.append(f"[Error querying Legal KB: {str(e)}]")
        
        # Query session_kb if it exists
        if session_kb is not None:
            try:
                sess_results = session_kb.query(query_embeddings=q_emb, n_results=4)
                for i, (doc, meta, dist) in enumerate(zip(
                    sess_results["documents"][0],
                    sess_results["metadatas"][0],
                    sess_results["distances"][0]
                )):
                    if dist <= 0.55:  # Tighter threshold for session KB
                        heading = meta.get("section_heading", "Unknown")
                        page = meta.get("page_number", "?")
                        label = f"[Uploaded Doc | {heading} | p.{page}]"
                        all_chunks.insert(0, f"{label}\n{doc}")  # Session chunks first
                        all_sources.insert(0, label)
                        all_meta.insert(0, {
                            "source": "Uploaded Doc",
                            "topic": heading,
                            "chunk_id": meta.get("chunk_id", sess_results["ids"][0][i]),
                            "page_number": page,
                            "section_heading": heading,
                            "distance": dist
                        })
            except Exception as e:
                all_sources.append(f"[Error querying Uploaded Doc: {str(e)}]")
        
        # Merge: session chunks first, then permanent, separated by ---
        retrieved = "\n\n---\n\n".join(all_chunks) if all_chunks else ""
        
        return {
            "retrieved": retrieved,
            "sources": all_sources,
            "chunk_meta": all_meta
        }
    
    except Exception as e:
        return {
            "retrieved": "",
            "sources": [f"[Retrieval error: {str(e)}]"],
            "chunk_meta": []
        }


def skip_retrieval_node(state: CapstoneState) -> dict:
    """Return empty retrieval for memory-only queries."""
    return {"retrieved": "", "sources": [], "chunk_meta": []}


def tool_node(state: CapstoneState) -> dict:
    """Return today's date for deadline and filing date queries."""
    try:
        today = datetime.date.today()
        return {"tool_result": f"Today's date is {today.strftime('%A, %B %d, %Y')}."}
    except Exception as e:
        return {"tool_result": f"Error retrieving date: {str(e)}"}


def answer_node(state: CapstoneState, llm: ChatGroq) -> dict:
    """Generate answer with grounding enforcement."""
    question = state["question"]
    retrieved = state.get("retrieved", "")
    tool_result = state.get("tool_result", "")
    messages = state.get("messages", [])
    eval_retries = state.get("eval_retries", 0)
    
    # Check if both retrieved and tool_result are empty
    if not retrieved and not tool_result:
        return {
            "answer": "I have no source material to answer from. Please upload a document or ask a question covered by the Legal KB."
        }
    
    # Build context section
    context_parts = []
    if retrieved:
        context_parts.append(f"CONTEXT:\n{retrieved}")
    if tool_result:
        context_parts.append(f"TOOL RESULT:\n{tool_result}")
    context = "\n\n".join(context_parts)
    
    # System prompt with grounding rules
    system_content = f"""You are a legal research assistant.

CONTEXT is provided below, tagged by source.
PRIMARY: [Uploaded Doc] tags — the user's actual case document. Use these first.
SECONDARY: [Legal KB] tags — general legal knowledge. Use only for definitions and procedure.

GROUNDING RULES (non-negotiable):
1. Every factual claim in your answer must be traceable to a tagged chunk in CONTEXT.
2. If a specific clause, name, date, or figure is not in CONTEXT, do not state it.
3. If CONTEXT does not contain the answer, output exactly:
   "I could not find that in the available documents. Please consult a qualified lawyer."
4. If the question references a clause or section that exists in CONTEXT but is ambiguous,
   ask one clarifying question before answering.
5. NEVER fabricate: case names, section numbers, monetary figures, party names, dates.

{context}"""
    
    # Add retry instruction if eval failed
    if eval_retries > 0:
        system_content += "\n\nIMPORTANT: Your previous answer did not meet quality standards. Answer using ONLY information explicitly stated in the CONTEXT above."
    
    # Build message list
    lc_msgs = [SystemMessage(content=system_content)]
    for msg in messages[:-1]:  # Exclude current question (already in context)
        if msg["role"] == "user":
            lc_msgs.append(HumanMessage(content=msg["content"]))
        else:
            lc_msgs.append(AIMessage(content=msg["content"]))
    
    lc_msgs.append(HumanMessage(content=question))
    
    response = llm.invoke(lc_msgs)
    return {"answer": response.content}


def eval_node(state: CapstoneState, llm: ChatGroq) -> dict:
    """Evaluate faithfulness of answer."""
    answer = state.get("answer", "")
    context = state.get("retrieved", "")[:500]
    retries = state.get("eval_retries", 0)
    
    # If no retrieved context, skip faithfulness check
    if not context:
        return {"faithfulness": 1.0, "eval_retries": retries + 1}
    
    prompt = f"""Rate faithfulness: does this answer use ONLY information from the context?
Reply with ONLY a number between 0.0 and 1.0.
1.0 = fully faithful. 0.5 = some hallucination. 0.0 = mostly hallucinated.

Context: {context}
Answer: {answer[:300]}"""
    
    try:
        result = llm.invoke(prompt).content.strip()
        score = float(result.split()[0].replace(",", "."))
        score = max(0.0, min(1.0, score))
    except:
        score = 0.5
    
    return {"faithfulness": score, "eval_retries": retries + 1}


def save_node(state: CapstoneState) -> dict:
    """Append assistant answer to messages history."""
    messages = state.get("messages", [])
    messages = messages + [{"role": "assistant", "content": state["answer"]}]
    return {"messages": messages}


# ============================================================
# Part 4: Graph Assembly
# ============================================================

def route_decision(state: CapstoneState) -> str:
    """After router_node: decide which retrieval path to take."""
    route = state.get("route", "retrieve")
    if route == "tool":
        return "tool"
    if route == "memory_only":
        return "skip"
    return "retrieve"


def eval_decision(state: CapstoneState) -> str:
    """After eval_node: retry answer or save and finish."""
    score = state.get("faithfulness", 1.0)
    retries = state.get("eval_retries", 0)
    retrieved = state.get("retrieved", "")
    
    # If no retrieved context, skip faithfulness check
    if not retrieved:
        return "save"
    
    if score >= FAITHFULNESS_THRESHOLD or retries >= MAX_EVAL_RETRIES:
        return "save"  # Pass or give up — never loop forever
    return "answer"  # Retry


def build_graph(llm: ChatGroq, embedder, permanent_kb, session_kb=None):
    """Build and compile the LangGraph."""
    graph = StateGraph(CapstoneState)
    
    # Add all nodes
    graph.add_node("memory", memory_node)
    graph.add_node("router", lambda state: router_node(state, llm))
    graph.add_node("retrieve", lambda state: retrieval_node(state, embedder, permanent_kb, session_kb))
    graph.add_node("skip", skip_retrieval_node)
    graph.add_node("tool", tool_node)
    graph.add_node("answer", lambda state: answer_node(state, llm))
    graph.add_node("eval", lambda state: eval_node(state, llm))
    graph.add_node("save", save_node)
    
    # Entry point and fixed edges
    graph.set_entry_point("memory")
    graph.add_edge("memory", "router")
    
    # Router decides: retrieve, skip, or tool
    graph.add_conditional_edges(
        "router",
        route_decision,
        {"retrieve": "retrieve", "skip": "skip", "tool": "tool"}
    )
    
    # All paths converge at answer
    graph.add_edge("retrieve", "answer")
    graph.add_edge("skip", "answer")
    graph.add_edge("tool", "answer")
    
    # Eval gate: retry or save
    graph.add_edge("answer", "eval")
    graph.add_conditional_edges(
        "eval",
        eval_decision,
        {"answer": "answer", "save": "save"}
    )
    graph.add_edge("save", END)
    
    # Compile with MemorySaver
    checkpointer = MemorySaver()
    app = graph.compile(checkpointer=checkpointer)
    
    return app
