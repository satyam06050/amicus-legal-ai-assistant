"""Add brutalist CSS to capstone_streamlit.py"""

# Read the file
with open('capstone_streamlit.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the CSS
css_code = '''
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
'''

# Replace the title line
old_line = 'st.title("⚖️ Legal Document Assistant")'
new_lines = css_code + '\nst.title("⚖️ LEGAL DOCUMENT ASSISTANT")\nst.caption("AI-powered Q&A for legal documents — answers faithfully, never fabricates")'

content = content.replace(old_line, new_lines)

# Also update the caption if it exists
content = content.replace(
    'st.caption("AI-powered Q&A for legal documents and case law — answers questions faithfully from your documents and the legal knowledge base.")',
    ''
)

# Write back
with open('capstone_streamlit.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Brutalist CSS added to capstone_streamlit.py")
