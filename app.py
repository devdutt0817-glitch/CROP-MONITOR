"""
🌿 CropMonitor AI — Streamlit Dashboard
AI-powered smart crop monitoring and automated irrigation system.
"""
from __future__ import annotations
import os, sys, io, json, time, threading
from datetime import datetime

import streamlit as st

# ── Must be the very first Streamlit call ─────────────────────────────────────
st.set_page_config(
    page_title="CropMonitor AI — Smart Farming Dashboard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={"About": "🌿 CropMonitor AI — Smart Farming powered by Gemini Vision"},
)

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database as db

# ── Bootstrap: init DB + start FastAPI + start demo simulator (once per process) ──
@st.cache_resource(show_spinner=False)
def _bootstrap():
    db.init_db()
    try:
        import uvicorn
        from server import fastapi_app, start_demo_simulator

        def _run():
            uvicorn.run(fastapi_app, host="0.0.0.0", port=8502, log_level="error")

        threading.Thread(target=_run, daemon=True, name="fastapi-server").start()
        time.sleep(1.8)   # let uvicorn bind
        start_demo_simulator()
    except Exception as e:
        pass  # non-fatal — dashboard still works for AI analysis
    return True

_bootstrap()

# ── Imports that need the server running ──────────────────────────────────────
from server import get_state, set_state, MOISTURE_ON, MOISTURE_OFF  # type: ignore

# ── Gemini API key helper ─────────────────────────────────────────────────────
def _api_key() -> str:
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        try:
            key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            pass
    # Also inject into env so FastAPI server thread can access via os.getenv()
    if key and not os.getenv("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = key
    return key or ""

# Inject the key at module load time (before any API call is made)
_api_key()

GEMINI_MODELS = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-pro-preview",
    "gemini-flash-latest",
]

# ─────────────────────────────────────────────────────────────────────────────
# 🌐 LANGUAGE SUPPORT  (Streamlit-only addition — helps non-English-speaking farmers)
# ─────────────────────────────────────────────────────────────────────────────
LANGUAGES = {
    "English": "English",
    "हिंदी (Hindi)": "Hindi",
    "मराठी (Marathi)": "Marathi",
    "ਪੰਜਾਬੀ (Punjabi)": "Punjabi",
    "ગુજરાતી (Gujarati)": "Gujarati",
    "தமிழ் (Tamil)": "Tamil",
    "తెలుగు (Telugu)": "Telugu",
    "ಕನ್ನಡ (Kannada)": "Kannada",
    "বাংলা (Bengali)": "Bengali",
}

# Every user-facing label in the dashboard, in English. Translated on the fly
# (and cached) into the farmer's chosen language — nothing else about the UI
# changes, only these text strings.
UI_STRINGS = {
    "app_subtitle": "Smart Farming System",
    "demo_badge": "Demo Mode Active",
    "sec_live_sensor": "📡 Live Sensor Data",
    "waiting_data": "⏳ Waiting for first sensor reading…  (demo data starts in ~8 s)",
    "soil_moisture": "Soil Moisture",
    "temperature": "Temperature",
    "humidity": "Humidity",
    "irrigation_pump": "Irrigation Pump",
    "mode_auto": "Auto",
    "mode_manual": "Manual",
    "mode_prefix": "Mode",
    "moisture_critical": "🏜️ Critically dry",
    "moisture_low": "⚠️ Low moisture",
    "moisture_ok": "✅ Optimal range",
    "moisture_high": "💦 Well irrigated",
    "temp_cold": "🥶 Very cold",
    "temp_cool": "❄️ Cool",
    "temp_ok": "✅ Optimal",
    "temp_warm": "☀️ Warm",
    "temp_hot": "🔥 Very hot",
    "hum_very_dry": "🏜️ Very dry",
    "hum_dry": "☀️ Dry air",
    "hum_ok": "✅ Good humidity",
    "hum_humid": "💧 Humid",
    "hum_very_humid": "🌧️ Very humid",
    "live_caption": "🕐 Live (IST): **{time}**  ·  Pump ON below {on}%  ·  OFF above {off}%",
    "sec_trends": "📊 24-Hour Sensor Trends",
    "charts_info": "📊 Charts appear once sensor readings accumulate.",
    "tab_moisture": "💧 Soil Moisture",
    "tab_temp": "🌡️ Temperature",
    "tab_hum": "🌫️ Humidity",
    "sec_irrigation": "🚿 Irrigation Control",
    "irrig_pill_on": "ON &lt;",
    "irrig_pill_off": "OFF &gt;",
    "irrig_desc": "In <strong>Auto</strong> mode the pump activates automatically based on soil moisture thresholds. Switch to <strong>Manual</strong> to override and control the pump directly.",
    "pump_on_btn": "💦 Pump ON",
    "pump_off_btn": "⛔ Pump OFF",
    "sec_ai": "🤖 AI Crop Disease Detection",
    "ai_desc": "Upload a photo of your crop — Gemini Vision AI will analyse it for diseases, pest infestations and nutrient deficiencies.",
    "api_warning": "⚠️ Gemini API key not set. Add `GEMINI_API_KEY` to `.streamlit/secrets.toml`.",
    "uploader_label": "Drop a crop photo here",
    "analyse_btn": "🔬 Analyse with Gemini AI",
    "analysing_spinner": "🌿 Analysing with Gemini Vision AI…  (3–10 seconds)",
    "overall_health": "Overall Health",
    "urgency_label": "Urgency",
    "tab_diseases": "🦠 Diseases",
    "tab_pests": "🐛 Pests",
    "tab_nutrients": "🧪 Nutrients",
    "tab_actions": "✅ Actions",
    "none_detected": "✅ None detected",
    "no_recs": "✅ No specific recommendations.",
    "analysis_failed": "⚠️ Analysis failed: {error}",
    "history_expander": "📋 Analysis History  ({count} records)",
    "footer": "🌿 CropMonitor AI &nbsp;·&nbsp; Powered by Google Gemini Vision &nbsp;·&nbsp; ESP32 + DHT22 + Soil Sensor",
    "sidebar_lang_title": "🌐 Language",
    "sidebar_lang_help": "Choose the language you're comfortable with.",
    "sidebar_chat_title": "💬 Farm Assistant",
    "sidebar_chat_desc": "Ask about using this dashboard, or any farming question — I'll reply in your chosen language.",
    "chat_placeholder": "Type your question here…",
    "chat_welcome": "👋 Namaste! I'm your CropMonitor helper. Ask me how to use this dashboard, or any question about your crops, soil, or the weather — I'll answer in your language.",
    "chat_thinking": "Thinking…",
    "chat_clear_btn": "🗑️ Clear chat",
    "chat_error": "⚠️ Sorry, I couldn't reach the assistant right now. Please try again in a moment.",
    "health_good": "Good",
    "health_fair": "Fair",
    "health_poor": "Poor",
    "health_critical": "Critical",
    "health_unknown": "Unknown",
    "urgency_immediate": "Immediate",
    "urgency_week": "Within a week",
    "urgency_routine": "Routine monitoring",
    "urgency_unknown": "Unknown",
    "confidence_high": "High",
    "confidence_medium": "Medium",
    "confidence_low": "Low",
    "score_suffix": "/ 100",
    "ri_score_label": "Score",
    "confidence_word": "Confidence",
    "risk_word": "Risk",
    "deficiency_word": "Deficiency",
    "affected_area_label": "Affected area",
    "treatment_label": "Treatment",
    "signs_label": "Signs",
    "control_label": "Control",
    "symptoms_label": "Symptoms",
    "remedy_label": "Remedy",
}


def _get_json_translation(target_language: str, strings: dict) -> dict:
    """One-off Gemini call that translates every UI_STRINGS value. Cached below."""
    try:
        from google import genai
        from google.genai import types

        api_key = _api_key()
        if not api_key:
            return strings

        client = genai.Client(api_key=api_key)
        prompt = (
            f"Translate every value of this JSON object into simple, natural {target_language}, "
            "written for a rural farmer using a farming dashboard app. Keep translations short "
            "and easy to understand. Do NOT translate, remove, or alter any text inside curly "
            "braces such as {time}, {on}, {off}, {error}, {count} — copy those tokens exactly "
            "as they appear. Keep any HTML tags like <strong> exactly as-is. Keep emoji symbols "
            "exactly as-is. Keep the JSON keys unchanged. Return ONLY the JSON object — no "
            "markdown fences, no extra commentary.\n\n" + json.dumps(strings, ensure_ascii=False)
        )
        for model_name in GEMINI_MODELS:
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=[prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        http_options=types.HttpOptions(timeout=15000),
                    ),
                )
                raw = resp.text.strip().replace("```json", "").replace("```", "").strip()
                translated = json.loads(raw)
                merged = dict(strings)
                for k, v in translated.items():
                    if k in strings and isinstance(v, str) and v.strip():
                        merged[k] = v
                return merged
            except Exception:
                continue
        return strings
    except Exception:
        return strings


@st.cache_data(show_spinner=False)
def _cached_translation(target_language: str) -> dict:
    if target_language == "English":
        return UI_STRINGS
    return _get_json_translation(target_language, UI_STRINGS)


if "lang_choice" not in st.session_state:
    st.session_state.lang_choice = "English"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

_TXT = _cached_translation(st.session_state.lang_choice)


def t(key: str, **kwargs) -> str:
    s = _TXT.get(key, UI_STRINGS.get(key, key))
    if kwargs:
        try:
            return s.format(**kwargs)
        except Exception:
            return UI_STRINGS.get(key, key).format(**kwargs)
    return s


# ─────────────────────────────────────────────────────────────────────────────
# 💬 CHATBOT  (Streamlit-only addition — help for farmers, in their language)
# ─────────────────────────────────────────────────────────────────────────────
APP_CONTEXT_FOR_BOT = """You are the built-in help assistant inside "CropMonitor AI", a smart-farming
dashboard. Speak simply and warmly, like helping a farmer who may not be familiar with technology.
Keep answers short (2-6 sentences), practical, and avoid jargon.

What the dashboard has, in case the farmer asks how to use it:
- "Live Sensor Data" section: shows current soil moisture %, temperature °C, humidity %, and whether the
  irrigation pump is ON or OFF. It refreshes automatically every few seconds.
- "24-Hour Sensor Trends": three tabs with line charts of moisture, temperature, humidity over the last day.
- "Irrigation Control": a toggle between "Auto" mode (pump turns on automatically when soil is too dry,
  and off once watered enough) and "Manual" mode (farmer presses "Pump ON" / "Pump OFF" buttons themselves).
- "AI Crop Disease Detection": farmer uploads a photo of a crop/leaf, clicks "Analyse with Gemini AI", and
  gets a health score, detected diseases, pests, nutrient deficiencies, and recommended actions.
- "Analysis History": past photo analyses, expandable at the bottom.
- A language dropdown in the sidebar lets the farmer switch the whole dashboard's language.

You can also answer general farming questions (irrigation timing, common crop diseases, soil health,
fertilizer basics, weather-related farming advice) using your general agricultural knowledge, even if
unrelated to this specific dashboard. If you are not sure about something specific to their exact farm
or region, say so honestly and suggest they also check with a local agricultural officer."""


def _chat_with_assistant(user_message: str, language: str, history: list) -> str:
    from google import genai
    from google.genai import types

    api_key = _api_key()
    if not api_key:
        return "⚠️ The assistant needs a Gemini API key to work. Please ask the app owner to add GEMINI_API_KEY."

    client = genai.Client(api_key=api_key)

    convo = ""
    for turn in history[-6:]:
        role = "Farmer" if turn["role"] == "user" else "Assistant"
        convo += f"{role}: {turn['content']}\n"
    convo += f"Farmer: {user_message}\nAssistant:"

    lang_instruction = (
        f"\n\nIMPORTANT: Reply ONLY in {language}, even if the farmer's question mixes languages."
        if language != "English" else ""
    )

    full_prompt = APP_CONTEXT_FOR_BOT + lang_instruction + "\n\nConversation so far:\n" + convo

    last_err = None
    for model_name in GEMINI_MODELS:
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=[full_prompt],
                config=types.GenerateContentConfig(http_options=types.HttpOptions(timeout=15000)),
            )
            return resp.text.strip()
        except Exception as e:
            last_err = e
            continue
    return t("chat_error")


def _render_sidebar():
    with st.sidebar:
        st.markdown(f"### {t('sidebar_lang_title')}")
        st.caption(t("sidebar_lang_help"))
        choice = st.selectbox(
            "Language",
            options=list(LANGUAGES.keys()),
            index=list(LANGUAGES.keys()).index(st.session_state.lang_choice)
            if st.session_state.lang_choice in LANGUAGES else 0,
            label_visibility="collapsed",
            key="lang_selectbox",
        )
        if choice != st.session_state.lang_choice:
            st.session_state.lang_choice = choice
            st.rerun()

        st.markdown("---")
        st.markdown(f"### {t('sidebar_chat_title')}")
        st.caption(t("sidebar_chat_desc"))

        chat_box = st.container(height=380)
        with chat_box:
            if not st.session_state.chat_history:
                with st.chat_message("assistant"):
                    st.markdown(t("chat_welcome"))
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        user_q = st.chat_input(t("chat_placeholder"))
        if st.session_state.chat_history and st.button(t("chat_clear_btn"), use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

        if user_q:
            st.session_state.chat_history.append({"role": "user", "content": user_q})
            with chat_box:
                with st.chat_message("user"):
                    st.markdown(user_q)
                with st.chat_message("assistant"):
                    with st.spinner(t("chat_thinking")):
                        reply = _chat_with_assistant(
                            user_q, LANGUAGES.get(st.session_state.lang_choice, "English"),
                            st.session_state.chat_history,
                        )
                    st.markdown(reply)
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            st.rerun()


_render_sidebar()

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS — Cyberpunk terminal theme (neon cyan/magenta on void-black, circuit grid)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

/* ── Root: dark terminal void with faint circuit grid ── */
.stApp {
    background:
        radial-gradient(ellipse 900px 500px at 12% -8%, rgba(0,229,255,0.08), transparent 60%),
        radial-gradient(ellipse 700px 500px at 100% 10%, rgba(255,46,166,0.06), transparent 55%),
        repeating-linear-gradient(0deg, rgba(0,229,255,0.028) 0px, rgba(0,229,255,0.028) 1px, transparent 1px, transparent 42px),
        repeating-linear-gradient(90deg, rgba(0,229,255,0.028) 0px, rgba(0,229,255,0.028) 1px, transparent 1px, transparent 42px),
        #05070d !important;
    font-family: 'Space Grotesk', sans-serif !important;
    min-height: 100vh;
}
.stApp > header { background: transparent !important; }
#MainMenu, footer, .stDeployButton, [data-testid="manage-app-button"] { display: none !important; }
.block-container { padding: 1.2rem 2.5rem 4rem !important; max-width: 1380px !important; background: transparent; }

/* ── Custom Header ── */
.cm-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 1.4rem 0 1.6rem;
    border-bottom: 1px solid rgba(0,229,255,0.18);
    margin-bottom: 2rem;
}
.cm-logo { display: flex; align-items: center; gap: 1rem; }
.cm-logo-icon { font-size: 2.4rem; filter: drop-shadow(0 0 10px rgba(0,229,255,0.55)); }
.cm-logo-title { font-family: 'JetBrains Mono', monospace; font-size: 1.5rem; font-weight: 800; color: #d8f3ff; letter-spacing: -0.4px; line-height: 1.1; }
.cm-logo-title span { color: #00e5ff; text-shadow: 0 0 14px rgba(0,229,255,0.65); }
.cm-logo-sub { font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; color: #4d6b7a; font-weight: 600; letter-spacing: 0.14em; text-transform: uppercase; margin-top: 4px; }
.cm-badge {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 0.72rem; font-family: 'JetBrains Mono', monospace; font-weight: 600;
    padding: 6px 14px; border-radius: 4px; letter-spacing: 0.05em;
}
.cm-badge-live  { color: #39ff88; border: 1px solid rgba(57,255,136,0.4); background: rgba(57,255,136,0.06); box-shadow: 0 0 14px rgba(57,255,136,0.12); }
.cm-badge-demo  { color: #ffb020; border: 1px solid rgba(255,176,32,0.4); background: rgba(255,176,32,0.06); box-shadow: 0 0 14px rgba(255,176,32,0.12); }
.cm-dot { width: 7px; height: 7px; border-radius: 50%; animation: blink 1.6s infinite; }
.cm-dot-live { background: #39ff88; box-shadow: 0 0 8px #39ff88; }
.cm-dot-demo { background: #ffb020; box-shadow: 0 0 8px #ffb020; }
@keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }

/* ── Section titles ── */
.sec-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase;
    color: #4d6b7a; margin: 2rem 0 1.1rem;
    display: flex; align-items: center; gap: 0.6rem;
}
.sec-title::before { content: '//'; color: #00e5ff; opacity: 0.7; }
.sec-title::after { content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, rgba(0,229,255,0.25), transparent); margin-left: 0.4rem; }

/* ── Sensor cards ── */
.s-card {
    background: linear-gradient(180deg, rgba(0,229,255,0.035), rgba(255,255,255,0.01)), #0a0f1a;
    border: 1px solid rgba(0,229,255,0.18);
    border-radius: 10px;
    padding: 1.3rem 1.5rem 1.1rem;
    box-shadow: 0 0 0 1px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.02);
    transition: border-color .2s ease, box-shadow .2s ease, transform .2s ease;
    min-height: 168px;
}
.s-card:hover { border-color: rgba(0,229,255,0.55); box-shadow: 0 0 24px rgba(0,229,255,0.14); transform: translateY(-2px); }
.sc-header { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.5rem; }
.sc-icon { font-size: 1.25rem; filter: drop-shadow(0 0 6px rgba(0,229,255,0.4)); }
.sc-label { font-family: 'JetBrains Mono', monospace; font-size: 0.66rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: #4d6b7a; }
.sc-value { font-size: 2.6rem; font-weight: 800; color: #eaffff; font-family: 'JetBrains Mono', monospace; line-height: 1.05; margin: 0.15rem 0; text-shadow: 0 0 18px rgba(0,229,255,0.25); }
.sc-unit { font-size: 1.1rem; font-weight: 400; color: #4d6b7a; margin-left: 3px; }
.sc-bar-track { height: 4px; background: rgba(0,229,255,0.08); border-radius: 2px; margin: 0.65rem 0 0.5rem; overflow: hidden; }
.sc-bar { height: 100%; border-radius: 2px; transition: width 1.2s ease; }
.bar-moisture { background: linear-gradient(90deg, #00b8d4, #00e5ff); box-shadow: 0 0 8px rgba(0,229,255,0.6); }
.bar-temp     { background: linear-gradient(90deg, #ff8a00, #ffb020); box-shadow: 0 0 8px rgba(255,176,32,0.6); }
.bar-hum      { background: linear-gradient(90deg, #ff2ea6, #ff6fc7); box-shadow: 0 0 8px rgba(255,46,166,0.5); }
.sc-status { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #39ff88; font-weight: 600; }

/* ── Pump card ── */
.pump-card { text-align: center; }
.pump-wrap { display: flex; flex-direction: column; align-items: center; gap: 0.4rem; margin: 0.2rem 0 0.4rem; }
.pump-ring {
    width: 76px; height: 76px; border-radius: 50%;
    border: 2px solid rgba(0,229,255,0.2);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;
    color: #4d6b7a; transition: all 0.5s ease;
}
.pump-ring.on {
    border-color: #39ff88;
    box-shadow: 0 0 24px rgba(57,255,136,0.35);
    color: #39ff88; background: rgba(57,255,136,0.05);
    animation: pump-pulse 2.2s ease-in-out infinite;
}
@keyframes pump-pulse {
    0%,100% { box-shadow: 0 0 18px rgba(57,255,136,0.25); }
    50%      { box-shadow: 0 0 34px rgba(57,255,136,0.55); }
}
.pump-mode { font-family: 'JetBrains Mono', monospace; font-size: 0.66rem; color: #4d6b7a; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; }

/* ── Info box ── */
.glass-box {
    background: rgba(0,229,255,0.03);
    border: 1px solid rgba(0,229,255,0.15);
    border-radius: 10px; padding: 1.4rem 1.6rem;
}

/* ── Irrigation thresholds ── */
.thresh-pill {
    display: inline-block; font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; font-weight: 600;
    padding: 4px 12px; border-radius: 4px; margin-right: 6px;
}
.thresh-on  { background: rgba(255,56,96,0.08); color: #ff3860; border: 1px solid rgba(255,56,96,0.35); }
.thresh-off { background: rgba(57,255,136,0.08); color: #39ff88; border: 1px solid rgba(57,255,136,0.35); }
.irrig-desc { font-size: 0.81rem; color: #7d97a5; line-height: 1.65; margin: 0.5rem 0 0; }

/* ── AI result cards ── */
.health-row {
    display: flex; align-items: center; gap: 1.4rem;
    background: rgba(0,229,255,0.04); border-radius: 10px;
    border: 1px solid rgba(0,229,255,0.2); padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
}
.hs-score { font-size: 3rem; font-weight: 900; font-family: 'JetBrains Mono', monospace; line-height: 1; }
.hs-label { font-family: 'JetBrains Mono', monospace; font-size: 0.66rem; color: #4d6b7a; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; }
.hs-health { font-size: 1.2rem; font-weight: 700; margin-top: 2px; }
.hs-urgency { font-size: 0.7rem; color: #4d6b7a; margin-top: 4px; }
.hc-good     { color: #39ff88; text-shadow: 0 0 12px rgba(57,255,136,0.4); }
.hc-fair     { color: #ffb020; text-shadow: 0 0 12px rgba(255,176,32,0.4); }
.hc-poor     { color: #ff8a3d; text-shadow: 0 0 12px rgba(255,138,61,0.4); }
.hc-critical { color: #ff3860; text-shadow: 0 0 12px rgba(255,56,96,0.4); }

.result-item {
    background: rgba(255,255,255,0.015);
    border: 1px solid rgba(0,229,255,0.12);
    border-radius: 8px; padding: 0.85rem 1rem; margin-bottom: 0.55rem;
}
.ri-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.4rem; }
.ri-name { font-weight: 600; color: #d8f3ff; font-size: 0.86rem; font-family: 'JetBrains Mono', monospace; }
.ri-body { font-size: 0.76rem; color: #7d97a5; line-height: 1.65; }
.ri-body strong { color: #b8e6f0; }
.rbadge { font-family: 'JetBrains Mono', monospace; font-size: 0.6rem; font-weight: 700; padding: 2px 9px; border-radius: 4px; }
.rbadge-high   { background: rgba(255,56,96,0.08); color: #ff3860; border: 1px solid rgba(255,56,96,0.35); }
.rbadge-medium { background: rgba(255,176,32,0.08); color: #ffb020; border: 1px solid rgba(255,176,32,0.35); }
.rbadge-low    { background: rgba(57,255,136,0.08); color: #39ff88; border: 1px solid rgba(57,255,136,0.35); }
.no-issue { font-size: 0.8rem; color: #4d6b7a; padding: 0.6rem; text-align: center; }
.rec-item { font-size: 0.78rem; color: #b8e6f0; line-height: 1.65; padding: 0.2rem 0; }
.rec-item::before { content: '> '; color: #00e5ff; font-weight: 700; font-family: 'JetBrains Mono', monospace; }

/* ── Streamlit widget overrides ── */
div[data-testid="stButton"] > button {
    background: rgba(0,229,255,0.05) !important;
    border: 1px solid rgba(0,229,255,0.4) !important;
    color: #00e5ff !important; border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600 !important; font-size: 0.82rem !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stButton"] > button:hover {
    background: rgba(0,229,255,0.12) !important;
    border-color: #00e5ff !important;
    box-shadow: 0 0 18px rgba(0,229,255,0.3) !important;
    transform: translateY(-1px) !important;
}
div[data-testid="stFileUploader"] {
    background: rgba(0,229,255,0.02) !important;
    border: 2px dashed rgba(0,229,255,0.35) !important;
    border-radius: 10px !important;
}
div[data-testid="stFileUploader"]:hover { border-color: #00e5ff !important; }
div[data-testid="stTabs"] [role="tablist"] button {
    font-family: 'JetBrains Mono', monospace !important;
    color: #4d6b7a !important; font-weight: 600 !important; font-size: 0.8rem !important;
}
div[data-testid="stTabs"] [role="tablist"] button[aria-selected="true"] {
    color: #00e5ff !important; border-bottom-color: #00e5ff !important;
    text-shadow: 0 0 10px rgba(0,229,255,0.5) !important;
}
div[data-testid="stTabs"] [role="tablist"] { border-bottom-color: rgba(0,229,255,0.15) !important; }
div[data-testid="stRadio"] label { color: #b8e6f0 !important; font-size: 0.84rem !important; }
div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p { color: #b8e6f0 !important; }
.stSpinner > div { border-top-color: #00e5ff !important; }
.stAlert { border-radius: 8px !important; background: rgba(0,229,255,0.04) !important; }
div[data-testid="stImage"] { border-radius: 8px; overflow: hidden; border: 1px solid rgba(0,229,255,0.2); }
[data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace !important; color: #eaffff !important; text-shadow: 0 0 12px rgba(0,229,255,0.3) !important; }
[data-testid="stMetricLabel"] { color: #4d6b7a !important; font-size: 0.7rem !important; text-transform: uppercase !important; letter-spacing: 0.08em !important; font-family: 'JetBrains Mono', monospace !important; }
div.stMarkdown p { color: #b8e6f0 !important; }
::selection { background: rgba(0,229,255,0.3); }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _fmt(ts: str) -> str:
    if not ts: return "--"
    try:
        return datetime.fromisoformat(ts).strftime("%H:%M")
    except Exception:
        return ts[:5] if len(ts) >= 5 else "--"

def _moisture_desc(v: float) -> str:
    if v < 20:  return t("moisture_critical")
    if v < 35:  return t("moisture_low")
    if v < 65:  return t("moisture_ok")
    return t("moisture_high")

def _temp_desc(v: float) -> str:
    if v < 10:  return t("temp_cold")
    if v < 18:  return t("temp_cool")
    if v < 28:  return t("temp_ok")
    if v < 36:  return t("temp_warm")
    return t("temp_hot")

def _hum_desc(v: float) -> str:
    if v < 20:  return t("hum_very_dry")
    if v < 40:  return t("hum_dry")
    if v < 70:  return t("hum_ok")
    if v < 85:  return t("hum_humid")
    return t("hum_very_humid")

def _health_cls(h: str) -> str:
    return {"Good":"hc-good","Fair":"hc-fair","Poor":"hc-poor","Critical":"hc-critical"}.get(h, "hc-fair")

def _health_emoji(h: str) -> str:
    return {"Good":"💚","Fair":"💛","Poor":"🟠","Critical":"🔴"}.get(h, "⚪")

def _health_label(h: str) -> str:
    key = {"Good":"health_good","Fair":"health_fair","Poor":"health_poor","Critical":"health_critical"}.get(h, "health_unknown")
    return t(key)

def _urgency_label(u: str) -> str:
    key = {"Immediate":"urgency_immediate","Within a week":"urgency_week",
           "Routine monitoring":"urgency_routine"}.get(u, "urgency_unknown")
    return t(key)

def _confidence_label(level: str) -> str:
    key = {"High":"confidence_high","Medium":"confidence_medium","Low":"confidence_low"}.get(level, "confidence_low")
    return t(key)

def _badge_cls(level: str) -> str:
    return {"High":"rbadge-high","Medium":"rbadge-medium","Low":"rbadge-low"}.get(level, "rbadge-low")

def _render_items(items: list, kind: str) -> str:
    if not items:
        return f'<div class="no-issue">{t("none_detected")}</div>'
    out = []
    for item in items:
        if kind == "disease":
            conf = item.get("confidence", "Low")
            out.append(f"""<div class="result-item">
              <div class="ri-head">
                <span class="ri-name">🦠 {item.get('name','—')}</span>
                <span class="rbadge {_badge_cls(conf)}">{_confidence_label(conf)} {t('confidence_word')}</span>
              </div>
              <div class="ri-body">
                <strong>{t('affected_area_label')}:</strong> {item.get('affected_area','N/A')}<br>
                <strong>{t('treatment_label')}:</strong> {item.get('treatment','N/A')}
              </div>
            </div>""")
        elif kind == "pest":
            risk = item.get("risk_level", "Low")
            out.append(f"""<div class="result-item">
              <div class="ri-head">
                <span class="ri-name">🐛 {item.get('name','—')}</span>
                <span class="rbadge {_badge_cls(risk)}">{_confidence_label(risk)} {t('risk_word')}</span>
              </div>
              <div class="ri-body">
                <strong>{t('signs_label')}:</strong> {item.get('signs','N/A')}<br>
                <strong>{t('control_label')}:</strong> {item.get('control','N/A')}
              </div>
            </div>""")
        elif kind == "nutrient":
            out.append(f"""<div class="result-item">
              <div class="ri-head"><span class="ri-name">🧪 {item.get('type','—')} {t('deficiency_word')}</span></div>
              <div class="ri-body">
                <strong>{t('symptoms_label')}:</strong> {item.get('symptoms','N/A')}<br>
                <strong>{t('remedy_label')}:</strong> {item.get('remedy','N/A')}
              </div>
            </div>""")
    return "".join(out)

# ─────────────────────────────────────────────────────────────────────────────
# AI ANALYSIS (direct Gemini call — no FastAPI round-trip needed)
# ─────────────────────────────────────────────────────────────────────────────
ANALYSIS_PROMPT = """You are an expert plant pathologist and agronomist. Analyse this crop image thoroughly.

IMPORTANT RULES:
- Always populate ALL fields, even for healthy plants
- For healthy plants: list common risks for this crop type and growth stage as "Low" risk items
- For pests: always list at least 2 common pests that affect this type of plant (even if not currently visible), with risk_level "Low" if not detected
- For nutrient_deficiency: always assess and list common deficiencies for this crop (e.g., Nitrogen, Iron, Magnesium), even if mild or at risk

Return ONLY a valid JSON object, no markdown, no extra text:
{
  "overall_health": "Good|Fair|Poor|Critical",
  "health_score": <integer 0-100>,
  "diseases": [{"name":"...","confidence":"High|Medium|Low","affected_area":"...","treatment":"..."}],
  "pests": [{"name":"...","risk_level":"High|Medium|Low","signs":"...","control":"..."}],
  "nutrient_deficiency": [{"type":"...","symptoms":"...","remedy":"..."}],
  "recommendations": ["at least 3 specific actionable recommendations"],
  "urgency": "Immediate|Within a week|Routine monitoring"
}"""


def _run_analysis(image_bytes: bytes, filename: str) -> dict:
    from google import genai
    from google.genai import types

    api_key = _api_key()
    if not api_key:
        raise ValueError("Gemini API key not configured. Add it to .streamlit/secrets.toml.")

    client = genai.Client(api_key=api_key)

    language = LANGUAGES.get(st.session_state.get("lang_choice", "English"), "English")
    prompt = ANALYSIS_PROMPT
    if language != "English":
        prompt += (
            f"\n\nIMPORTANT: Write all text VALUES in the JSON (names, descriptions, treatments, "
            f"symptoms, remedies, recommendations, etc.) in {language}. Keep the JSON keys "
            f"(overall_health, health_score, diseases, name, confidence, etc.) in English exactly "
            f"as shown, and keep 'overall_health' and 'urgency' and 'confidence'/'risk_level' values "
            f"as one of the exact English enum words given (Good/Fair/Poor/Critical, High/Medium/Low, "
            f"Immediate/Within a week/Routine monitoring), so the app can still read them correctly."
        )

    last_err: Exception | None = None
    for attempt in range(3):          # up to 3 full passes over all models
        for model_name in GEMINI_MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        prompt,
                        types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        http_options=types.HttpOptions(timeout=15000),
                    ),
                )
                raw      = response.text.strip().replace("```json", "").replace("```", "").strip()
                analysis = json.loads(raw)
                db.insert_analysis(filename, analysis.get("overall_health", "Unknown"), json.dumps(analysis))
                return analysis
            except Exception as e:
                last_err = e
                err_str = str(e)
                if "404" in err_str or "NOT_FOUND" in err_str:
                    continue          # model unavailable — skip instantly
                time.sleep(0.3)
                continue
        # All models failed this pass — wait before retrying
        if attempt < 2:
            time.sleep(4)

    raise ValueError(f"Gemini is overloaded right now. Please try again in a moment. ({last_err})")


# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
irrig_header = get_state()
is_demo = True  # will update below

latest_check = db.get_latest_reading()
has_data     = latest_check is not None

st.markdown(f"""
<div class="cm-header">
  <div class="cm-logo">
    <div class="cm-logo-icon">🌿</div>
    <div>
      <div class="cm-logo-title">CropMonitor <span>AI</span></div>
      <div class="cm-logo-sub">{t('app_subtitle')}</div>
    </div>
  </div>
  <div style="display:flex;gap:0.6rem;align-items:center;">
    <span class="cm-badge cm-badge-demo">
      <span class="cm-dot cm-dot-demo"></span>{t('demo_badge')}
    </span>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — LIVE SENSOR DATA  (auto-refreshes every 3 s)
# ─────────────────────────────────────────────────────────────────────────────
@st.fragment(run_every=3)
def _sensor_section():
    data  = db.get_latest_reading()
    state = get_state()

    st.markdown(f'<div class="sec-title">{t("sec_live_sensor")}</div>', unsafe_allow_html=True)

    if not data:
        st.info(t("waiting_data"))
        return

    m       = float(data.get("moisture",    0))
    temp_c  = float(data.get("temperature", 0))
    h       = float(data.get("humidity",    0))
    p       = bool(data.get("pump_state",   0))
    ts      = data.get("timestamp", "")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        bar_w = min(m, 100)
        st.markdown(f"""<div class="s-card">
          <div class="sc-header"><span class="sc-icon">💧</span><span class="sc-label">{t('soil_moisture')}</span></div>
          <div class="sc-value">{m:.1f}<span class="sc-unit">%</span></div>
          <div class="sc-bar-track"><div class="sc-bar bar-moisture" style="width:{bar_w:.0f}%"></div></div>
          <div class="sc-status">{_moisture_desc(m)}</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        bar_w = min((temp_c / 50) * 100, 100)
        st.markdown(f"""<div class="s-card">
          <div class="sc-header"><span class="sc-icon">🌡️</span><span class="sc-label">{t('temperature')}</span></div>
          <div class="sc-value">{temp_c:.1f}<span class="sc-unit">°C</span></div>
          <div class="sc-bar-track"><div class="sc-bar bar-temp" style="width:{bar_w:.0f}%"></div></div>
          <div class="sc-status">{_temp_desc(temp_c)}</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        bar_w = min(h, 100)
        st.markdown(f"""<div class="s-card">
          <div class="sc-header"><span class="sc-icon">🌫️</span><span class="sc-label">{t('humidity')}</span></div>
          <div class="sc-value">{h:.1f}<span class="sc-unit">%</span></div>
          <div class="sc-bar-track"><div class="sc-bar bar-hum" style="width:{bar_w:.0f}%"></div></div>
          <div class="sc-status">{_hum_desc(h)}</div>
        </div>""", unsafe_allow_html=True)

    with c4:
        pump_cls = "on" if p else ""
        pump_txt = "ON" if p else "OFF"
        mode_lbl = t("mode_manual") if state.get("mode") == "manual" else t("mode_auto")
        st.markdown(f"""<div class="s-card pump-card">
          <div class="sc-header" style="justify-content:center">
            <span class="sc-icon">🚿</span><span class="sc-label">{t('irrigation_pump')}</span>
          </div>
          <div class="pump-wrap">
            <div class="pump-ring {pump_cls}">{pump_txt}</div>
            <div class="pump-mode">{t('mode_prefix')}: {mode_lbl}</div>
          </div>
        </div>""", unsafe_allow_html=True)

    if ts:
        from datetime import timezone, timedelta
        IST = timezone(timedelta(hours=5, minutes=30))
        ist_time = datetime.now(IST).strftime("%H:%M")
        st.caption(t("live_caption", time=ist_time, on=MOISTURE_ON, off=MOISTURE_OFF))

_sensor_section()


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — 24-HOUR CHARTS  (refreshes every 10 s)
# ─────────────────────────────────────────────────────────────────────────────
@st.fragment(run_every=10)
def _chart_section():
    import plotly.graph_objects as go

    st.markdown(f'<div class="sec-title">{t("sec_trends")}</div>', unsafe_allow_html=True)

    rows = db.get_recent_readings()
    if not rows:
        st.info(t("charts_info"))
        return

    labels   = [_fmt(r.get("timestamp", "")) for r in rows]
    moisture = [r.get("moisture",    0) for r in rows]
    temp     = [r.get("temperature", 0) for r in rows]
    hum      = [r.get("humidity",    0) for r in rows]

    LAYOUT = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono, monospace", color="#4d6b7a", size=10),
        margin=dict(l=48, r=16, t=16, b=48), height=240,
        xaxis=dict(
            showgrid=True, gridcolor="rgba(0,229,255,0.08)",
            linecolor="rgba(0,229,255,0.12)", tickfont=dict(size=9),
            nticks=8,
        ),
        yaxis=dict(
            showgrid=True, gridcolor="rgba(0,229,255,0.08)",
            linecolor="rgba(0,229,255,0.12)", tickfont=dict(size=9),
        ),
        showlegend=False,
        hovermode="x unified",
        hoverlabel=dict(bgcolor="rgba(5,10,15,0.95)", bordercolor="rgba(0,229,255,0.3)",
                        font=dict(color="#d8f3ff", size=11)),
    )

    def _chart(y, color, fill_color, name):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=labels, y=y, name=name, mode="lines",
            line=dict(color=color, width=2.2, shape="spline", smoothing=0.8),
            fill="tozeroy", fillcolor=fill_color,
            hovertemplate=f"<b>{name}</b>: %{{y:.1f}}<extra></extra>",
        ))
        fig.update_layout(**LAYOUT)
        return fig

    t1, t2, t3 = st.tabs([t("tab_moisture"), t("tab_temp"), t("tab_hum")])
    with t1:
        st.plotly_chart(_chart(moisture, "#00e5ff", "rgba(0,229,255,0.12)", "Moisture (%)"),
                        use_container_width=True, config={"displayModeBar": False})
    with t2:
        st.plotly_chart(_chart(temp, "#ffb020", "rgba(255,176,32,0.12)", "Temperature (°C)"),
                        use_container_width=True, config={"displayModeBar": False})
    with t3:
        st.plotly_chart(_chart(hum, "#ff2ea6", "rgba(255,46,166,0.12)", "Humidity (%)"),
                        use_container_width=True, config={"displayModeBar": False})

_chart_section()


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — IRRIGATION CONTROL
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f'<div class="sec-title">{t("sec_irrigation")}</div>', unsafe_allow_html=True)

irrig = get_state()

col_info, col_ctrl = st.columns([2, 1], gap="large")

with col_info:
    st.markdown(f"""<div class="glass-box">
      <div style="margin-bottom:0.7rem">
        <span class="thresh-pill thresh-on">{t('irrig_pill_on')} <strong>{MOISTURE_ON}</strong>%</span>
        <span class="thresh-pill thresh-off">{t('irrig_pill_off')} <strong>{MOISTURE_OFF}</strong>%</span>
      </div>
      <div class="irrig-desc">
        {t('irrig_desc')}
      </div>
    </div>""", unsafe_allow_html=True)

with col_ctrl:
    st.markdown('<div class="glass-box">', unsafe_allow_html=True)

    current_mode = irrig.get("mode", "auto")
    mode_options = [f"⚡ {t('mode_auto')}", f"🖐 {t('mode_manual')}"]
    mode_choice  = st.radio(
        "Mode",
        options=mode_options,
        index=0 if current_mode == "auto" else 1,
        horizontal=True,
        key="mode_radio",
        label_visibility="collapsed",
    )
    selected_mode = "auto" if mode_choice == mode_options[0] else "manual"

    if selected_mode != current_mode:
        set_state(mode=selected_mode)
        db.insert_override(selected_mode, int(get_state()["pump_on"]))
        st.rerun()

    if selected_mode == "manual":
        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button(t("pump_on_btn"),  key="pump_on_btn",  use_container_width=True):
                set_state(pump_on=True)
                db.insert_override("manual", 1)
                st.rerun()
        with bc2:
            if st.button(t("pump_off_btn"), key="pump_off_btn", use_container_width=True):
                set_state(pump_on=False)
                db.insert_override("manual", 0)
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — AI CROP DISEASE DETECTION
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f'<div class="sec-title">{t("sec_ai")}</div>', unsafe_allow_html=True)
st.markdown(
    f'<p style="font-size:0.82rem;color:#7d97a5;margin:-0.4rem 0 1rem;">{t("ai_desc")}</p>',
    unsafe_allow_html=True,
)

# Check API key once
raw_key = _api_key()
api_key_ok = bool(raw_key)
if not api_key_ok:
    st.warning(t("api_warning"), icon="⚠️")

uploaded = st.file_uploader(
    t("uploader_label"),
    type=["jpg", "jpeg", "png", "webp"],
    key="crop_upload",
    label_visibility="collapsed",
    disabled=not api_key_ok,
)

if uploaded:
    img_bytes = uploaded.read()

    col_img, col_btn = st.columns([3, 1], gap="medium")
    with col_img:
        st.image(img_bytes, use_container_width=True, caption=uploaded.name)
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        run_analysis = st.button(t("analyse_btn"), key="analyse_btn", use_container_width=True)

    if run_analysis:
        with st.spinner(t("analysing_spinner")):
            try:
                result = _run_analysis(img_bytes, uploaded.name)

                score  = result.get("health_score", 0)
                health = result.get("overall_health", "Unknown")
                urgency= result.get("urgency", "Unknown")
                hcls   = _health_cls(health)

                # ── Health overview ───────────────────────────────────────────
                st.markdown(f"""<div class="health-row">
                  <div style="text-align:center;min-width:80px">
                    <div class="hs-score {hcls}">{score}</div>
                    <div class="hs-label">{t('score_suffix')}</div>
                  </div>
                  <div>
                    <div class="hs-label">{t('overall_health')}</div>
                    <div class="hs-health {hcls}">{_health_emoji(health)} {_health_label(health)}</div>
                    <div class="hs-urgency">{t('urgency_label')}: {_urgency_label(urgency)}</div>
                  </div>
                </div>""", unsafe_allow_html=True)

                # ── Result tabs ───────────────────────────────────────────────
                rt1, rt2, rt3, rt4 = st.tabs([t("tab_diseases"), t("tab_pests"), t("tab_nutrients"), t("tab_actions")])

                with rt1:
                    st.markdown(_render_items(result.get("diseases", []), "disease"), unsafe_allow_html=True)
                with rt2:
                    st.markdown(_render_items(result.get("pests", []), "pest"), unsafe_allow_html=True)
                with rt3:
                    st.markdown(_render_items(result.get("nutrient_deficiency", []), "nutrient"), unsafe_allow_html=True)
                with rt4:
                    recs = result.get("recommendations", [])
                    if recs:
                        for r in recs:
                            st.markdown(f'<div class="rec-item">{r}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="no-issue">{t("no_recs")}</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(t("analysis_failed", error=e), icon="⚠️")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — ANALYSIS HISTORY  (collapsible)
# ─────────────────────────────────────────────────────────────────────────────
history_rows = db.get_recent_analyses()
if history_rows:
    with st.expander(t("history_expander", count=len(history_rows)), expanded=False):
        for row in history_rows:
            try:
                result = json.loads(row.get("result_json", "{}"))
                health = row.get("overall_health", "—")
                hcls   = _health_cls(health)
                st.markdown(f"""<div class="result-item">
                  <div class="ri-head">
                    <span class="ri-name">{_health_emoji(health)} {row.get('image_name','—')}</span>
                    <span class="rbadge {hcls.replace('hc-','rbadge-')}" style="font-size:0.7rem;padding:3px 10px;">{_health_label(health)}</span>
                  </div>
                  <div class="ri-body">
                    {t('ri_score_label')}: <strong>{result.get('health_score','—')}/100</strong> ·
                    {t('urgency_label')}: <strong>{_urgency_label(result.get('urgency','—'))}</strong> ·
                    {_fmt(row.get('timestamp',''))}
                  </div>
                </div>""", unsafe_allow_html=True)
            except Exception:
                continue


# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-top:3rem;padding-top:1.2rem;border-top:1px solid rgba(0,229,255,0.15);
            text-align:center;font-size:0.7rem;color:#4d6b7a;font-family:'JetBrains Mono',monospace;">
  {t('footer')}
</div>
""", unsafe_allow_html=True)
