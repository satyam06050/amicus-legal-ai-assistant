"""Fix slow loading by adding progress indicators"""

with open('capstone_streamlit.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the load_agent function and initialization
old_code = '''# ── Load models and permanent KB (cached) ───────────────────────────
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
    st.stop()'''

new_code = '''# ── Load models and permanent KB (with progress) ───────────────────────────
@st.cache_resource(show_spinner=False)
def load_agent():
    """Load LLM, embedder, and build permanent KB."""
    from langchain_groq import ChatGroq
    
    with st.spinner("🤖 Loading Groq LLM..."):
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    
    with st.spinner("🧠 Loading embedding model (first time takes ~30s)..."):
        embedder, perm_collection = build_permanent_kb()
    
    with st.spinner("🔗 Building LangGraph agent..."):
        agent_app = build_graph(llm, embedder, perm_collection)
    
    return agent_app, embedder, perm_collection


with st.spinner("⏳ Initializing AI models and legal knowledge base..."):
    try:
        agent_app, embedder, perm_collection = load_agent()
    except Exception as e:
        st.error(f"❌ Failed to load agent: {e}")
        st.stop()

st.success(f"✅ Ready! Legal KB loaded with {perm_collection.count()} documents")'''

content = content.replace(old_code, new_code)

with open('capstone_streamlit.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Added loading progress indicators!")
print("\nNow the app will show:")
print("  - 🤖 Loading Groq LLM...")
print("  - 🧠 Loading embedding model...")
print("  - 🔗 Building LangGraph agent...")
print("  - ✅ Ready!")
