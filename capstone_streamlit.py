"""
capstone_streamlit.py — Legal Document Assistant Streamlit UI
Run: streamlit run capstone_streamlit.py
"""
import streamlit as st
import uuid
import os
import datetime
from io import BytesIO
from dotenv import load_dotenv

# Import agent functions
from agent import build_permanent_kb, build_session_kb, build_graph, CapstoneState

load_dotenv()

st.set_page_config(page_title="Legal Document Assistant", page_icon="⚖️", layout="wide")

# Brutalist CSS with light colors
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');
    
    * {
        font-family: 'Space Mono', monospace !important;
    }
    
    .main .block-container {
        background-color: #f5f5f0;
        padding: 2rem;
    }
    
    h1, h2, h3 {
        font-weight: 700 !important;
        color: #1a1a1a !important;
        text-transform: uppercase;
        letter-spacing: -1px;
        border: 3px solid #1a1a1a;
        padding: 0.5rem 1rem;
        background: #fffff0;
        box-shadow: 6px 6px 0px #1a1a1a;
        margin-bottom: 1.5rem;
    }
    
    .stChatMessage {
        border: 3px solid #1a1a1a !important;
        box-shadow: 4px 4px 0px #1a1a1a !important;
        margin-bottom: 1rem;
        background: #ffffff !important;
    }
    
    .stButton button {
        border: 3px solid #1a1a1a !important;
        background: #ffffff !important;
        color: #1a1a1a !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        box-shadow: 4px 4px 0px #1a1a1a !important;
        transition: all 0.1s !important;
    }
    
    .stButton button:hover {
        box-shadow: 2px 2px 0px #1a1a1a !important;
        transform: translate(2px, 2px) !important;
        background: #fffff0 !important;
    }
    
    .stFileUploader {
        border: 3px dashed #1a1a1a !important;
        background: #ffffff !important;
        padding: 1rem !important;
    }
    
    .stTextInput input, textarea {
        border: 3px solid #1a1a1a !important;
        box-shadow: 3px 3px 0px #1a1a1a !important;
        background: #ffffff !important;
    }
    
    .stSuccess {
        border: 3px solid #00aa00 !important;
        background: #e6ffe6 !important;
        box-shadow: 3px 3px 0px #00aa00 !important;
    }
    
    .stError {
        border: 3px solid #cc0000 !important;
        background: #ffe6e6 !important;
        box-shadow: 3px 3px 0px #cc0000 !important;
    }
    
    .stInfo {
        border: 3px solid #0066cc !important;
        background: #e6f0ff !important;
        box-shadow: 3px 3px 0px #0066cc !important;
    }
    
    hr {
        border: 2px solid #1a1a1a !important;
        margin: 1.5rem 0 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚖️ LEGAL DOCUMENT ASSISTANT")
st.caption("AI-powered Q&A for legal documents — answers faithfully, never fabricates")

# ── Load models and permanent KB (cached) ───────────────────────────
@st.cache_resource
def load_agent():
    """Load LLM, embedder, and build permanent KB."""
    from langchain_groq import ChatGroq
    
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    embedder, perm_collection = build_permanent_kb()
    agent_app = build_graph(llm, embedder, perm_collection)
    
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

    st.subheader("📄 Upload Document")
    uploaded_file = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt"])

    if uploaded_file is not None:
        try:
            # Build session KB
            with st.spinner("Processing document..."):
                session_kb = build_session_kb(uploaded_file, embedder)
                
                if session_kb is not None:
                    st.session_state.session_kb = session_kb
                    st.session_state.doc_loaded = True
                    st.success(f"✅ Document loaded — {session_kb.count()} chunks")
                else:
                    st.error("Failed to process document. Please try a different file.")
        except Exception as e:
            st.error(f"Error loading document: {e}")

    if st.session_state.doc_loaded:
        if st.button("🗑️ Remove Document"):
            st.session_state.session_kb = None
            st.session_state.doc_loaded = False
            st.success("Document removed")
            st.rerun()

    st.divider()

    st.subheader("💬 Session Info")
    st.write(f"**Thread ID:** `{st.session_state.thread_id}`")
    st.write(f"**Messages:** {len(st.session_state.messages)}")
    
    if st.button("🔄 New Conversation"):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())[:8]
        st.rerun()

# ── Chat Interface ────────────────────────────────────────
st.subheader("💬 Chat")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User input
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
