"""
CropMonitor AI — Smart Farming Dashboard (Streamlit)
Dashboard + AI Crop Analysis + Smart Assistant Chatbot (multi-language) + Irrigation Control
"""

import os
import io
import time
import random
import datetime as dt

import streamlit as st
import pandas as pd

# ---------------------------------------------------------------------------
# Optional AI backend (Gemini). App still works in DEMO MODE with no key.
# ---------------------------------------------------------------------------
DEMO_MODE = True
try:
    import google.generativeai as genai

    API_KEY = None
    try:
        API_KEY = st.secrets.get("GEMINI_API_KEY", None)
    except Exception:
        API_KEY = None
    API_KEY = API_KEY or os.environ.get("GEMINI_API_KEY")

    if API_KEY:
        genai.configure(api_key=API_KEY)
        TEXT_MODEL = genai.GenerativeModel("gemini-1.5-flash")
        VISION_MODEL = genai.GenerativeModel("gemini-1.5-flash")
        DEMO_MODE = False
except Exception:
    DEMO_MODE = True

# ---------------------------------------------------------------------------
# Page config + theme
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CropMonitor AI — Smart Farming Dashboard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .stApp {
        background: radial-gradient(circle at 10% 0%, #163a2b 0%, #0b1410 45%, #070b09 100%);
        color: #e9f5ee;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0e1c15 0%, #0a120d 100%);
        border-right: 1px solid rgba(120, 220, 160, 0.15);
    }

    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(120, 220, 160, 0.18);
        border-radius: 18px;
        padding: 1.1rem 1.3rem;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 24px rgba(0,0,0,0.25);
        margin-bottom: 0.9rem;
    }

    .metric-label { color: #9fd9b8; font-size: 0.85rem; letter-spacing: 0.04em; text-transform: uppercase; }
    .metric-value { font-size: 2.1rem; font-weight: 700; color: #f2fff6; }
    .badge-ok { color: #7CFFA0; font-weight: 600; }
    .badge-warn { color: #FFC15E; font-weight: 600; }
    .badge-bad { color: #FF6B6B; font-weight: 600; }

    .app-title { font-size: 1.6rem; font-weight: 800; color: #eafff2; }
    .app-sub { color: #8fb9a0; font-size: 0.85rem; margin-top: -6px;}

    .stButton>button {
        background: linear-gradient(135deg, #2f9e63, #1c6b45);
        color: white; border: none; border-radius: 12px;
        padding: 0.5rem 1.1rem; font-weight: 600;
    }
    .stButton>button:hover { background: linear-gradient(135deg, #38b876, #1f7a4f); color: white; }

    .demo-banner {
        background: rgba(255, 193, 94, 0.12);
        border: 1px solid rgba(255, 193, 94, 0.4);
        color: #FFC15E;
        border-radius: 12px;
        padding: 0.6rem 1rem;
        font-size: 0.85rem;
        margin-bottom: 1rem;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Languages for translation
# ---------------------------------------------------------------------------
LANGUAGES = [
    "English", "Hindi", "Hinglish (Hindi-English mix)", "Punjabi", "Marathi",
    "Gujarati", "Bengali", "Tamil", "Telugu", "Kannada", "Malayalam", "Odia",
    "Urdu", "Assamese", "Spanish", "French", "Arabic", "Other (type below)",
]

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
def init_state():
    ss = st.session_state
    ss.setdefault("language", "English")
    ss.setdefault("custom_language", "")
    ss.setdefault("chat_history", [])
    ss.setdefault("pump_mode", "Auto")
    ss.setdefault("pump_on", False)
    ss.setdefault("moisture_on_th", 30)
    ss.setdefault("moisture_off_th", 60)
    ss.setdefault("sensor_history", seed_history())
    ss.setdefault("last_analysis", None)

def seed_history(hours=24):
    now = dt.datetime.now()
    rows = []
    moisture, temp, hum = 55.0, 27.0, 65.0
    for i in range(hours, -1, -1):
        moisture = max(15, min(85, moisture + random.uniform(-4, 4)))
        temp = max(18, min(38, temp + random.uniform(-1, 1)))
        hum = max(30, min(90, hum + random.uniform(-3, 3)))
        rows.append({
            "time": now - dt.timedelta(hours=i),
            "moisture": round(moisture, 1),
            "temperature": round(temp, 1),
            "humidity": round(hum, 1),
        })
    return pd.DataFrame(rows)

init_state()

def active_language():
    if st.session_state.language == "Other (type below)" and st.session_state.custom_language.strip():
        return st.session_state.custom_language.strip()
    if st.session_state.language == "Hinglish (Hindi-English mix)":
        return "Hinglish (casual mixed Hindi and English, Latin script)"
    return st.session_state.language

# ---------------------------------------------------------------------------
# AI helpers (Gemini text + vision), with graceful demo fallback
# ---------------------------------------------------------------------------
FARMER_SYSTEM_PROMPT = """You are "Krishi Mitra", the friendly AI support assistant embedded inside the
CropMonitor AI smart farming dashboard. You help farmers with:
- Understanding soil moisture, temperature, humidity readings and irrigation status
- Crop disease, pest, and nutrient-deficiency questions
- How to use the dashboard (analysis tab, irrigation controls, alerts)
- General farming, fertilizer, watering-schedule, and government-scheme guidance (keep general, suggest
  contacting local Krishi Vigyan Kendra / agri officer for region-specific or legal advice)
Keep answers practical, short, and easy to follow for a farmer. Always respond ONLY in this language: {lang}.
"""

def gemini_chat(user_message, history):
    lang = active_language()
    if DEMO_MODE:
        return demo_bot_reply(user_message, lang)
    try:
        convo = TEXT_MODEL.start_chat(history=[])
        prompt = FARMER_SYSTEM_PROMPT.format(lang=lang) + "\n\nConversation so far:\n"
        for turn in history[-6:]:
            prompt += f"{turn['role']}: {turn['content']}\n"
        prompt += f"\nFarmer: {user_message}\nKrishi Mitra:"
        resp = convo.send_message(prompt)
        return resp.text.strip()
    except Exception as e:
        return f"(Assistant error, showing demo reply) {demo_bot_reply(user_message, lang)}"

def demo_bot_reply(user_message, lang):
    msg = user_message.lower()
    if "moistur" in msg or "water" in msg or "pani" in msg:
        base = ("Soil moisture 30% se neeche jaane par pump auto-ON hota hai, aur 60% cross karte hi "
                "auto-OFF ho jaata hai. Aap Irrigation tab se yeh thresholds manually bhi badal sakte ho.")
    elif "disease" in msg or "pest" in msg or "keeda" in msg or "bimari" in msg:
        base = ("Crop Analysis tab me photo upload karo — AI leaf spots, discoloration ya pest damage "
                "check karke disease/pest/nutrient issue batayega, saath me basic treatment suggestion bhi.")
    elif "scheme" in msg or "yojana" in msg or "sarkar" in msg:
        base = ("Government krishi yojanas ke liye apne nazdiki Krishi Vigyan Kendra (KVK) ya "
                "agriculture department office se sampark karein — woh region-specific schemes bata sakte hain.")
    else:
        base = ("Main CropMonitor AI ka smart assistant hoon — irrigation, sensor readings, crop disease "
                "ya dashboard use karne me kisi bhi help ke liye pooch sakte ho!")
    if lang.lower().startswith("english"):
        return base
    return f"[{lang}] {base}\n\n(Demo mode: connect a Gemini API key in secrets for live, fully translated AI replies.)"

def gemini_vision_analyze(image_bytes):
    lang = active_language()
    if DEMO_MODE:
        return demo_vision_reply(lang)
    try:
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        prompt = (
            f"You are an expert agronomist. Analyze this crop/leaf photo for disease, pest damage, or "
            f"nutrient deficiency. Give: 1) Likely issue 2) Confidence (low/med/high) 3) 2-3 line treatment "
            f"advice. Respond ONLY in {lang}."
        )
        resp = VISION_MODEL.generate_content([prompt, img])
        return resp.text.strip()
    except Exception:
        return demo_vision_reply(lang)

def demo_vision_reply(lang):
    text = (
        "**Likely issue:** Early-stage leaf blight (fungal)\n"
        "**Confidence:** Medium\n"
        "**Advice:** Affected leaves hata dein, copper-based fungicide spray karein, aur overhead "
        "watering se bachein taaki leaves dry rahe."
    )
    if not lang.lower().startswith("english"):
        text += f"\n\n_(Demo mode — {lang} translation available once a live Gemini API key is connected.)_"
    return text

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="app-title">🌿 CropMonitor AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-sub">Smart Farming Dashboard</div>', unsafe_allow_html=True)
    st.write("")

    page = st.radio(
        "Navigate",
        ["📊 Dashboard", "🔬 Crop Analysis", "💬 Smart Assistant", "🚿 Irrigation Control"],
        label_visibility="collapsed",
    )

    st.write("---")
    st.markdown("**🌐 Assistant Language**")
    st.selectbox("Language", LANGUAGES, key="language", label_visibility="collapsed")
    if st.session_state.language == "Other (type below)":
        st.text_input("Type your language", key="custom_language", placeholder="e.g. Bhojpuri, Chhattisgarhi...")

    st.write("---")
    st.markdown("**☎️ Farmer Support**")
    st.caption("Smart Assistant tab is available 24/7 for AI-guided help — disease queries, irrigation "
               "doubts, dashboard how-to, in your own language.")

    if DEMO_MODE:
        st.markdown(
            '<div class="demo-banner">⚠️ Running in <b>Demo Mode</b> — add <code>GEMINI_API_KEY</code> '
            'in Streamlit Secrets for live AI analysis & chat.</div>',
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Dashboard page
# ---------------------------------------------------------------------------
def status_badge(value, low, high):
    if value < low:
        return f'<span class="badge-bad">Low</span>'
    if value > high:
        return f'<span class="badge-warn">High</span>'
    return f'<span class="badge-ok">Normal</span>'

def render_dashboard():
    st.title("📊 Live Farm Dashboard")

    df = st.session_state.sensor_history
    latest = df.iloc[-1]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f'<div class="glass-card"><div class="metric-label">Soil Moisture</div>'
            f'<div class="metric-value">{latest.moisture}%</div>'
            f'{status_badge(latest.moisture, 30, 70)}</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(
            f'<div class="glass-card"><div class="metric-label">Temperature</div>'
            f'<div class="metric-value">{latest.temperature}°C</div>'
            f'{status_badge(latest.temperature, 15, 34)}</div>', unsafe_allow_html=True)
    with c3:
        st.markdown(
            f'<div class="glass-card"><div class="metric-label">Humidity</div>'
            f'<div class="metric-value">{latest.humidity}%</div>'
            f'{status_badge(latest.humidity, 35, 85)}</div>', unsafe_allow_html=True)
    with c4:
        pump_status = "🟢 ON" if st.session_state.pump_on else "⚪ OFF"
        st.markdown(
            f'<div class="glass-card"><div class="metric-label">Irrigation Pump</div>'
            f'<div class="metric-value">{pump_status}</div>'
            f'<span class="badge-ok">{st.session_state.pump_mode} mode</span></div>', unsafe_allow_html=True)

    st.write("")
    st.markdown("#### 24-Hour Trends")
    chart_df = df.set_index("time")[["moisture", "temperature", "humidity"]]
    st.line_chart(chart_df, height=320)

    st.write("")
    colA, colB = st.columns([1, 1])
    with colA:
        if st.button("🔄 Simulate new sensor reading"):
            row = df.iloc[-1].copy()
            row.time = dt.datetime.now()
            row.moisture = round(max(10, min(90, row.moisture + random.uniform(-6, 6))), 1)
            row.temperature = round(max(15, min(40, row.temperature + random.uniform(-1.5, 1.5))), 1)
            row.humidity = round(max(25, min(95, row.humidity + random.uniform(-4, 4))), 1)
            st.session_state.sensor_history = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            apply_auto_irrigation()
            st.rerun()
    with colB:
        st.caption("Real deployment: point your ESP32 firmware's `SERVER_URL` at this dashboard's "
                   "backend endpoint to feed live sensor data instead of simulated readings.")

    alerts = []
    if latest.moisture < 20:
        alerts.append("🔴 Critical: Soil moisture very low — irrigate soon.")
    if latest.temperature > 36:
        alerts.append("🟠 High temperature stress risk for crops.")
    if alerts:
        st.write("")
        st.markdown("#### 🔔 Alerts")
        for a in alerts:
            st.warning(a)

def apply_auto_irrigation():
    if st.session_state.pump_mode != "Auto":
        return
    latest = st.session_state.sensor_history.iloc[-1]
    if latest.moisture < st.session_state.moisture_on_th:
        st.session_state.pump_on = True
    elif latest.moisture > st.session_state.moisture_off_th:
        st.session_state.pump_on = False

# ---------------------------------------------------------------------------
# Crop analysis page
# ---------------------------------------------------------------------------
def render_analysis():
    st.title("🔬 AI Crop Analysis")
    st.caption("Upload a photo of a leaf or crop — AI checks for disease, pest damage, or nutrient deficiency.")

    uploaded = st.file_uploader("Upload crop / leaf photo", type=["jpg", "jpeg", "png"])
    if uploaded is not None:
        col1, col2 = st.columns([1, 1.3])
        with col1:
            st.image(uploaded, caption="Uploaded image", use_container_width=True)
        with col2:
            with st.spinner("Analyzing with AI..."):
                result = gemini_vision_analyze(uploaded.getvalue())
                st.session_state.last_analysis = result
            st.markdown(f'<div class="glass-card">{result}</div>', unsafe_allow_html=True)
            if st.button("💬 Ask Smart Assistant for more help on this"):
                st.session_state.chat_history.append(
                    {"role": "Farmer", "content": "Can you explain this crop analysis result more and tell me what to do next?"}
                )
                st.session_state._jump_to_chat = True
                st.rerun()

    if st.session_state.get("_jump_to_chat"):
        st.info("Analysis question added to Smart Assistant chat — open the 💬 Smart Assistant tab to continue.")
        st.session_state._jump_to_chat = False

# ---------------------------------------------------------------------------
# Smart Assistant (chatbot) page
# ---------------------------------------------------------------------------
def render_assistant():
    st.title("💬 Smart Assistant — Krishi Mitra")
    st.caption(f"AI-assisted farmer support, replying in **{active_language()}**. "
               "Ask about irrigation, disease, sensor readings, or how to use the dashboard.")

    quick_cols = st.columns(4)
    quick_prompts = [
        ("💧 Irrigation help", "How does the auto irrigation system decide when to turn the pump on or off?"),
        ("🐛 Disease/Pest help", "How do I check my crop for disease or pests using this dashboard?"),
        ("📈 Reading sensors", "How do I read the moisture, temperature and humidity values correctly?"),
        ("🏛️ Govt schemes", "Are there government schemes for smart irrigation I should know about?"),
    ]
    for col, (label, prompt) in zip(quick_cols, quick_prompts):
        if col.button(label):
            st.session_state.chat_history.append({"role": "Farmer", "content": prompt})

    st.write("")
    chat_box = st.container(height=420)
    with chat_box:
        for turn in st.session_state.chat_history:
            role = "user" if turn["role"] == "Farmer" else "assistant"
            with st.chat_message(role):
                st.markdown(turn["content"])

    user_input = st.chat_input("Type your question here...")
    if user_input:
        st.session_state.chat_history.append({"role": "Farmer", "content": user_input})

    # If last message is from farmer and has no reply yet, generate one
    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "Farmer":
        with chat_box:
            with st.chat_message("assistant"):
                with st.spinner("Krishi Mitra is typing..."):
                    reply = gemini_chat(st.session_state.chat_history[-1]["content"], st.session_state.chat_history)
                    st.markdown(reply)
        st.session_state.chat_history.append({"role": "Krishi Mitra", "content": reply})
        st.rerun()

# ---------------------------------------------------------------------------
# Irrigation control page
# ---------------------------------------------------------------------------
def render_irrigation():
    st.title("🚿 Irrigation Control")

    latest = st.session_state.sensor_history.iloc[-1]
    st.markdown(
        f'<div class="glass-card">Current soil moisture: <b>{latest.moisture}%</b> &nbsp;|&nbsp; '
        f'Pump: <b>{"ON" if st.session_state.pump_on else "OFF"}</b> &nbsp;|&nbsp; '
        f'Mode: <b>{st.session_state.pump_mode}</b></div>', unsafe_allow_html=True
    )

    mode = st.radio("Mode", ["Auto", "Manual"], horizontal=True,
                     index=0 if st.session_state.pump_mode == "Auto" else 1)
    st.session_state.pump_mode = mode

    if mode == "Auto":
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.moisture_on_th = st.slider("Turn pump ON below (%)", 5, 50, st.session_state.moisture_on_th)
        with c2:
            st.session_state.moisture_off_th = st.slider("Turn pump OFF above (%)", 40, 90, st.session_state.moisture_off_th)
        apply_auto_irrigation()
        st.info(f"Auto mode active — pump turns ON below {st.session_state.moisture_on_th}% moisture, "
                f"OFF above {st.session_state.moisture_off_th}%.")
    else:
        st.session_state.pump_on = st.toggle("Pump power", value=st.session_state.pump_on)
        st.caption("Manual override active — auto-irrigation logic is paused.")

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
if page == "📊 Dashboard":
    render_dashboard()
elif page == "🔬 Crop Analysis":
    render_analysis()
elif page == "💬 Smart Assistant":
    render_assistant()
elif page == "🚿 Irrigation Control":
    render_irrigation()
