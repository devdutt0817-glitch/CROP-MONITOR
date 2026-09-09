# CropMonitor AI — Streamlit Dashboard (with Smart Assistant)

## What's new in this version
- 💬 **Smart Assistant chatbot** ("Krishi Mitra") — Meta-AI-style farmer support bot, answers questions
  about irrigation, disease/pest, sensor readings, and how to use the dashboard.
- 🌐 **Translate to any language** — pick from the sidebar (Hindi, Punjabi, Tamil, Telugu, Marathi,
  Bengali, Urdu, and more) or type any custom language — the bot replies in that language.
- Works out of the box even **without an API key** (Demo Mode) so it never crashes on deploy —
  connect a free Gemini key any time for live AI replies.

## Files
```
app.py                          ← the whole app (single file, easy to deploy)
requirements.txt
.streamlit/secrets.toml.example ← rename to secrets.toml / paste into Streamlit Cloud secrets
```

## Deploy to get your live streamlit.app link (5 minutes)

1. **Push these files to a GitHub repo** (e.g. add them into your existing CropMonitor repo, or a new
   one — just make sure `app.py` and `requirements.txt` are at the root or note their folder).
2. Go to **https://share.streamlit.io** → sign in with GitHub → **"Create app"**.
3. Select your repo, branch, and set **Main file path** to `app.py`.
4. Click **"Advanced settings" → Secrets**, paste:
   ```
   GEMINI_API_KEY = "your_actual_key"
   ```
   (Get a free key from https://aistudio.google.com → "Create API key". Skip this step to run in
   Demo Mode — app still works, just with canned responses instead of live AI.)
5. Click **Deploy**. You'll get a link like `https://your-app-name.streamlit.app`.

## Run locally first (optional, to preview)
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes
- The dashboard currently **simulates** sensor readings (via the "Simulate new sensor reading" button)
  since Streamlit Cloud has no direct connection to your ESP32. To go fully live, point your ESP32's
  `SERVER_URL` at a small API endpoint (e.g. re-deploy `backend/server.js` on Render/Railway) and have
  this Streamlit app read from that instead of `seed_history()` — happy to wire that up next if you want.
- Demo Mode responses are intentionally simple so the app never breaks in front of your evaluators —
  once `GEMINI_API_KEY` is set, both the chatbot and crop-photo analysis go fully live and translate
  properly into whichever language is selected.
