import streamlit as st
import os
import sys
import json
import subprocess
from openai import OpenAI

# --- INITIAL SETUP ---
st.set_page_config(page_title="POKORNY TERMINAL | SETTINGS", layout="wide", initial_sidebar_state="collapsed")

aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)

import menu
menu.vykresli_menu()

current_lang = st.session_state.get("lang", "CZ")
WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")

def load_watchlist_data():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {}

def save_settings_to_json(provider, model):
    data = load_watchlist_data()
    data["settings"] = {
        "ai_provider": provider,
        "ai_model": model
    }
    
    with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    try:
        if "GITHUB_TOKEN" in st.secrets:
            token = st.secrets["GITHUB_TOKEN"]
            owner = st.secrets["GITHUB_OWNER"]
            repo = st.secrets["GITHUB_REPO"]
            remote_url = f"https://{owner}:{token}@github.com/{owner}/{repo}.git"
            
            subprocess.run(["git", "config", "--global", "user.email", "bot@pokornyterminal.cz"], capture_output=True)
            subprocess.run(["git", "config", "--global", "user.name", "Terminal Bot"], capture_output=True)
            subprocess.run(["git", "add", WATCHLIST_FILE], capture_output=True)
            subprocess.run(["git", "commit", "-m", "Automatická úprava AI konfigurace (Bez API klíče)"], capture_output=True)
            subprocess.run(["git", "pull", "--rebase", remote_url, "main"], capture_output=True)
            push_res = subprocess.run(["git", "push", remote_url, "HEAD:main"], capture_output=True, text=True)
            
            if push_res.returncode != 0:
                st.error(f"Chyba synchronizace s GitHubem: {push_res.stderr}")
                return False
            return True
    except Exception as e:
        st.error(f"Kritická chyba spojení: {e}")
        return False

# --- DICTIONARY ---
t = {
    "CZ": {
        "title": "⚙️ GLOBÁLNÍ NASTAVENÍ",
        "desc": "SPRÁVA ROZHRANÍ A INFRASTRUKTURY TERMINÁLU.",
        "ui_h": "🎨 Uživatelské rozhraní",
        "lang_lbl": "Jazyk aplikace (Language):",
        "ai_h": "🧠 Umělá inteligence",
        "ai_desc": "Propojení aplikace s LLM servery pro datovou analýzu.",
        "api_lbl": "Dočasný API Klíč:",
        "prov_lbl": "Poskytovatel:",
        "mod_lbl": "Výchozí model:",
        "save_btn": "💾 Uložit model a synchronizovat na GitHub",
        "saved_msg": "Výchozí model a poskytovatel uloženi na GitHub.",
        "no_models": "Klíč nenalezen. Vložte GROQ_API_KEY do Streamlit Secrets.",
        "future_h": "🔧 Budoucí moduly",
        "future_desc": "Připraveno pro napojení na brokery a webhooky."
    },
    "EN": {
        "title": "⚙️ GLOBAL SETTINGS",
        "desc": "TERMINAL INTERFACE AND INFRASTRUCTURE MANAGEMENT.",
        "ui_h": "🎨 User Interface",
        "lang_lbl": "App Language:",
        "ai_h": "🧠 Artificial Intelligence",
        "ai_desc": "Connection to LLM servers for data analysis.",
        "api_lbl": "Temporary API Key:",
        "prov_lbl": "Provider:",
        "mod_lbl": "Default Model:",
        "save_btn": "💾 Save Model & Sync to GitHub",
        "saved_msg": "Default model and provider saved to GitHub.",
        "no_models": "Key not found. Add GROQ_API_KEY to Streamlit Secrets.",
        "future_h": "🔧 Future Modules",
        "future_desc": "Prepared for broker integration and webhooks."
    }
}
_ = t.get(current_lang, t["CZ"])

st.title(_["title"])
st.caption(_["desc"])
st.markdown("---")

@st.cache_data(ttl=300)
def fetch_available_models(api_klic, provider):
    if not api_klic: return []
    try:
        if provider == "Groq":
            client = OpenAI(api_key=api_klic, base_url="https://api.groq.com/openai/v1")
            models = client.models.list().data
            llm_models = [m.id for m in models if "whisper" not in m.id and "tool-use" not in m.id]
            return sorted(llm_models, reverse=True)
        else:
            return ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
    except:
        return []

col1, col2 = st.columns(2, gap="large")

with col1:
    with st.container(border=True):
        st.markdown(f"#### {_['ui_h']}")
        new_lang = st.radio(_["lang_lbl"], ["CZ", "EN"], index=0 if current_lang == "CZ" else 1, horizontal=True)
        if new_lang != st.session_state.lang:
            st.session_state.lang = new_lang
            st.rerun()

    with st.container(border=True):
        st.markdown(f"#### {_['future_h']}")
        st.info(_["future_desc"])

with col2:
    with st.container(border=True):
        st.markdown(f"#### {_['ai_h']}")
        st.caption(_["ai_desc"])
        
        app_data = load_watchlist_data()
        saved_settings = app_data.get("settings", {})
        
        if "ai_provider" not in st.session_state: st.session_state.ai_provider = saved_settings.get("ai_provider", "Groq")
        if "ai_model" not in st.session_state: st.session_state.ai_model = saved_settings.get("ai_model", "")

        # Bezpečná správa API klíče
        has_secret = "GROQ_API_KEY" in st.secrets
        if has_secret:
            st.success("✅ API Klíč je bezpečně načten z tajného trezoru Streamlit Cloud.")
            temp_api = st.secrets["GROQ_API_KEY"]
        else:
            temp_api = st.text_input(_["api_lbl"], type="password", placeholder="gsk_...", help="Pouze pro tuto relaci. Pro trvalé uložení vložte GROQ_API_KEY do Secrets.")
            
        temp_prov = st.selectbox(_["prov_lbl"], ["Groq", "OpenAI"], index=0 if st.session_state.ai_provider == "Groq" else 1)
        
        models = fetch_available_models(temp_api, temp_prov)
        temp_model = None
        
        if temp_api:
            if models:
                idx = models.index(st.session_state.ai_model) if st.session_state.ai_model in models else 0
                temp_model = st.selectbox(_["mod_lbl"], models, index=idx)
            else:
                st.error("Neplatný klíč nebo výpadek API.")
        else:
            st.warning(_["no_models"])
            
        if st.button(_["save_btn"], type="primary", use_container_width=True):
            with st.spinner("Ukládám a synchronizuji s GitHubem..."):
                st.session_state.ai_provider = temp_prov
                if temp_model:
                    st.session_state.ai_model = temp_model
                
                success = save_settings_to_json(temp_prov, temp_model)
                if success:
                    st.success(_["saved_msg"])