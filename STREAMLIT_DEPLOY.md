# Streamlit Cloud Deployment Guide

## Quick Steps:

1. **Go to** https://share.streamlit.io/
2. **Sign in** with GitHub
3. **Click "New app"**
4. **Configure:**
   - Repository: `satyam06050/amicus-legal-ai-assistant`
   - Branch: `main`
   - Main file path: `capstone_streamlit.py`

5. **IMPORTANT: Add Secrets**
   - After creating the app, go to **Settings** → **Secrets**
   - Add this:
   ```toml
   GROQ_API_KEY = "your_actual_groq_api_key_here"
   ```
   - Click **Save**

6. **Click Deploy!**

---

## Common Errors & Fixes:

### ❌ "No module named 'agent'"
**Solution:** This shouldn't happen since capstone_streamlit.py is self-contained. If you see this:
- Make sure you're deploying `capstone_streamlit.py` (not agent.py)
- Check that Main file path is exactly: `capstone_streamlit.py`

### ❌ "GROQ_API_KEY not found"
**Solution:** 
- You MUST add the secret in Streamlit Cloud Settings
- Go to Settings → Secrets → Add `GROQ_API_KEY`

### ❌ "ModuleNotFoundError: No module named 'X'"
**Solution:**
- Check requirements.txt has all dependencies
- Streamlit Cloud auto-installs from requirements.txt

### ❌ App crashes on startup
**Solution:**
- Check logs in Streamlit Cloud dashboard
- Common issue: Missing environment variables

---

## What Gets Deployed:

✅ **capstone_streamlit.py** - Self-contained app (has ALL agent code inside)
✅ **requirements.txt** - All dependencies
✅ **agent.py** - NOT needed for deployment (capstone_streamlit.py is independent)

---

## Testing Locally First:

```bash
# Make sure it works locally before deploying
streamlit run capstone_streamlit.py
```

If it works locally but not on Streamlit Cloud, the issue is:
1. Missing GROQ_API_KEY secret
2. Wrong main file path
3. Missing dependency in requirements.txt

---

## File Structure for Deployment:

```
amicus-legal-ai-assistant/
├── capstone_streamlit.py    ← DEPLOY THIS (self-contained)
├── requirements.txt         ← Auto-installed by Streamlit Cloud
├── agent.py                 ← Not needed for deployment
├── .gitignore
└── README.md
```

The `capstone_streamlit.py` file contains ALL the agent code inside it, so it doesn't need to import from `agent.py`.
