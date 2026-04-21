# 🚀 Deployment Guide — Legal Document Assistant

## Option 1: Streamlit Cloud (FREE & EASIEST) ⭐ RECOMMENDED

**Best for:** Quick demo, portfolio, capstone submission

### Steps:

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Legal Document Assistant"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/legal-document-assistant.git
   git push -u origin main
   ```

2. **Go to Streamlit Cloud**
   - Visit: https://share.streamlit.io/
   - Sign in with GitHub
   - Click "New app"

3. **Configure**
   - **Repository:** `your-username/legal-document-assistant`
   - **Branch:** `main`
   - **Main file path:** `capstone_streamlit.py`

4. **Add Secrets**
   - In Streamlit Cloud dashboard, click "Settings" → "Secrets"
   - Add:
     ```toml
     GROQ_API_KEY = "your_actual_groq_api_key_here"
     ```

5. **Deploy!**
   - Click "Deploy"
   - Wait 2-3 minutes
   - Your app is live at: `https://your-app-name.streamlit.app`

### Pros:
- ✅ 100% FREE
- ✅ Auto-deploys on git push
- ✅ HTTPS included
- ✅ Easy sharing

### Cons:
- ⚠️ Goes to sleep after inactivity
- ⚠️ Limited compute resources

---

## Option 2: Railway (FREE TIER)

**Best for:** More control, always-on

### Steps:

1. **Create `Procfile`**
   ```
   web: streamlit run capstone_streamlit.py --server.port $PORT --server.enableCORS false
   ```

2. **Create `runtime.txt`**
   ```
   python-3.12.10
   ```

3. **Push to GitHub**

4. **Deploy on Railway**
   - Visit: https://railway.app/
   - Sign in with GitHub
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repo

5. **Add Environment Variables**
   - Go to Variables tab
   - Add: `GROQ_API_KEY=your_key_here`

6. **Deploy!**

### Pros:
- ✅ $5 free credit/month
- ✅ Always-on option
- ✅ More resources

### Cons:
- ⚠️ Free tier has limits

---

## Option 3: Render (FREE TIER)

**Best for:** Simple deployment, good performance

### Steps:

1. **Create `render.yaml`**
   ```yaml
   services:
     - type: web
       name: legal-assistant
       env: python
       buildCommand: pip install -r requirements.txt
       startCommand: streamlit run capstone_streamlit.py --server.port $PORT
       envVars:
         - key: GROQ_API_KEY
           sync: false
   ```

2. **Push to GitHub**

3. **Deploy on Render**
   - Visit: https://render.com/
   - Sign up with GitHub
   - Click "New +" → "Blueprint"
   - Select your repo

4. **Add Environment Variable**
   - Add `GROQ_API_KEY` in dashboard

5. **Deploy!**

### Pros:
- ✅ Free tier available
- ✅ Auto-deploys
- ✅ Good performance

### Cons:
- ⚠️ Sleeps after 15 min inactivity (free tier)

---

## Option 4: Hugging Face Spaces (FREE)

**Best for:** AI/ML projects, community visibility

### Steps:

1. **Go to Hugging Face**
   - Visit: https://huggingface.co/spaces
   - Click "Create new Space"

2. **Configure**
   - **Space name:** `legal-document-assistant`
   - **License:** MIT
   - **SDK:** Gradio (we'll override with Streamlit)

3. **Add Files**
   - Create `app.py` (rename from capstone_streamlit.py)
   - Upload `requirements.txt`
   - Add `README.md`

4. **Add Secrets**
   - Go to Settings → Repository secrets
   - Add `GROQ_API_KEY`

5. **Deploy!**

### Pros:
- ✅ FREE
- ✅ AI community
- ✅ GPU options (not needed here)

### Cons:
- ⚠️ Requires file rename
- ⚠️ Slower cold start

---

## Option 5: Self-Hosted (VPS)

**Best for:** Production, full control

### Recommended Providers:
- DigitalOcean ($4-6/month)
- Linode ($5/month)
- AWS EC2 (free tier for 12 months)
- Hetzner (cheap, ~€3/month)

### Steps:

1. **Create VPS**
   ```bash
   # SSH into your server
   ssh root@your-server-ip
   ```

2. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv nginx -y
   ```

3. **Clone & Setup**
   ```bash
   git clone https://github.com/YOUR_USERNAME/legal-document-assistant.git
   cd legal-document-assistant
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Create `.env`**
   ```bash
   echo "GROQ_API_KEY=your_key_here" > .env
   ```

5. **Run with systemd**
   ```bash
   sudo nano /etc/systemd/system/legal-assistant.service
   ```
   
   Add:
   ```ini
   [Unit]
   Description=Legal Document Assistant
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/path/to/legal-document-assistant
   ExecStart=/path/to/legal-document-assistant/venv/bin/streamlit run capstone_streamlit.py --server.port 8501 --server.enableCORS false
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

6. **Start Service**
   ```bash
   sudo systemctl enable legal-assistant
   sudo systemctl start legal-assistant
   ```

7. **Setup Nginx Reverse Proxy**
   ```bash
   sudo nano /etc/nginx/sites-available/legal-assistant
   ```
   
   Add:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8501;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

8. **Enable & Restart**
   ```bash
   sudo ln -s /etc/nginx/sites-available/legal-assistant /etc/nginx/sites-enabled/
   sudo systemctl restart nginx
   ```

### Pros:
- ✅ Full control
- ✅ Always-on
- ✅ Scalable

### Cons:
- ⚠️ Requires server management
- ⚠️ Monthly cost

---

## 🔒 Security Best Practices

1. **Never commit `.env`** - Already in `.gitignore`
2. **Use environment variables** for all secrets
3. **Enable HTTPS** - Streamlit Cloud/Railway do this automatically
4. **Rate limiting** - Add if deploying publicly
5. **Authentication** - Add login if handling sensitive documents

---

## 📊 Cost Comparison

| Platform | Cost | Sleep | Custom Domain | Best For |
|----------|------|-------|---------------|----------|
| **Streamlit Cloud** | FREE | Yes | No | Demos, portfolios |
| **Railway** | $5/mo | Optional | Yes | Always-on apps |
| **Render** | FREE | Yes | No | Simple deploys |
| **Hugging Face** | FREE | Yes | No | AI projects |
| **VPS** | $4-6/mo | No | Yes | Production |

---

## 🎯 Quick Start (5 minutes)

```bash
# 1. Initialize git
git init
git add .
git commit -m "Initial commit"

# 2. Create GitHub repo
# Go to GitHub → New Repository → Create

# 3. Push
git remote add origin https://github.com/YOUR_USERNAME/legal-document-assistant.git
git push -u origin main

# 4. Deploy to Streamlit Cloud
# Visit: https://share.streamlit.io/
# Click "New app" → Select repo → Deploy!
```

---

## 🐛 Troubleshooting

### "Module not found" error
- Ensure `requirements.txt` has all dependencies
- Check Python version (3.10+)

### "GROQ_API_KEY missing"
- Add to platform's secret/environment variable manager
- Never commit to git

### App too slow
- Upgrade plan on hosting platform
- Optimize embedding model (use smaller model)

### PDF upload fails
- Check file size limits (Streamlit Cloud: 200MB)
- Ensure PyMuPDF is in requirements.txt

---

## 📞 Need Help?

- **Streamlit Cloud:** https://docs.streamlit.io/streamlit-community-cloud
- **Railway:** https://docs.railway.app/
- **Render:** https://render.com/docs
- **General:** Check `README.md` and `SUMMARY.md`

---

**Ready to deploy!** 🚀
