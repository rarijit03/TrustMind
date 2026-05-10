# TrustMind — Production Setup

## Local Development

### 1. Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate      # Mac/Linux
pip install -r requirements.txt

# Create a .env file with your Groq key
echo GROQ_API_KEY=gsk_your_key_here > .env

python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Frontend
Open `frontend/index.html` in your browser.
`config.js` defaults to `localhost:8000` automatically — no changes needed for local dev.

---

## Production Deployment (Free)

### Step 1 — Deploy Backend to Render
1. Push this folder to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your repo, set:
   - Root directory: `backend`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Plan: Free
4. Under **Environment**, add: `GROQ_API_KEY` = your Groq key
5. Deploy → copy your URL e.g. `https://trustmind-api.onrender.com`

### Step 2 — Configure Frontend
Edit `frontend/config.js` — set your Render URL:
```js
window.TRUSTMIND_CONFIG = {
  BACKEND_URL: "https://trustmind-api.onrender.com",
};
```

### Step 3 — Deploy Frontend to Vercel
1. Go to [vercel.com](https://vercel.com) → New Project → import repo
2. Set root directory: `frontend`
3. Deploy — done!

---

## Get a Free Groq API Key
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (no credit card)
3. API Keys → Create → copy your `gsk_...` key
4. Paste into Render environment variable
