import streamlit as st
import os
import sys
import json
import subprocess
from google import genai
from openai import OpenAI

# --- INITIAL SETUP ---
st.set_page_config(page_title="POKORNY TERMINAL | SETTINGS", layout="wide", initial_sidebar_state="collapsed")

aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)

import menu
menu.vykresli_menu()

current_lang = st.session_state.get("lang", "EN")
WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")

def load_watchlist_data():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {}

def save_settings_to_json(lang, provider, model):
    data = load_watchlist_data()
    
    if "settings" not in data:
        data["settings"] = {}
        
    data["settings"]["lang"] = lang
    data["settings"]["ai_provider"] = provider
    data["settings"]["ai_model"] = model
    
    with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    try:
        if "GITHUB_TOKEN" in st.secrets:
            token = st.secrets["GITHUB_TOKEN"].strip()
            owner = st.secrets["GITHUB_OWNER"].strip()
            repo = st.secrets["GITHUB_REPO"].strip()
            
            remote_url = f"https://{token}@github.com/{owner}/{repo}.git"
            
            subprocess.run(["git", "config", "--global", "user.email", "bot@pokornyterminal.cz"], capture_output=True)
            subprocess.run(["git", "config", "--global", "user.name", "Terminal Bot"], capture_output=True)
            subprocess.run(["git", "add", WATCHLIST_FILE], capture_output=True)
            subprocess.run(["git", "commit", "-m", "Automatická úprava globálního nastavení (Jazyk, AI)"], capture_output=True)
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
    "EN": {
        "title": "⚙️ GLOBAL SETTINGS",
        "desc": "TERMINAL INTERFACE AND INFRASTRUCTURE MANAGEMENT.",
        "ui_h": "🎨 User Interface",
        "lang_lbl": "App Language:",
        "ai_h": "🧠 Artificial Intelligence",
        "ai_desc": "Connection to Google AI Studio or Groq for data analysis.",
        "prov_lbl": "Provider:",
        "mod_lbl": "Default Model:",
        "save_btn": "💾 Save All Settings & Sync to GitHub",
        "saved_msg": "Global configuration safely saved to GitHub.",
        "future_h": "🔧 Future Modules",
        "future_desc": "Prepared for broker integration and webhooks."
    },
    "CZ": {
        "title": "⚙️ GLOBÁLNÍ NASTAVENÍ",
        "desc": "SPRÁVA ROZHRANÍ A INFRASTRUKTURY TERMINÁLU.",
        "ui_h": "🎨 Uživatelské rozhraní",
        "lang_lbl": "Jazyk aplikace (Language):",
        "ai_h": "🧠 Umělá inteligence",
        "ai_desc": "Propojení aplikace s Google AI Studio nebo Groq pro datovou analýzu.",
        "prov_lbl": "Poskytovatel (Provider):",
        "mod_lbl": "Výchozí model:",
        "save_btn": "💾 Uložit veškeré nastavení a synchronizovat na GitHub",
        "saved_msg": "Globální konfigurace bezpečně uložena na GitHub.",
        "future_h": "🔧 Budoucí moduly",
        "future_desc": "Připraveno pro napojení na brokery a webhooky."
    }
}
_ = t.get(current_lang, t["EN"])

st.title(_["title"])
st.caption(_["desc"])
st.markdown("---")

@st.cache_data(ttl=300)
def fetch_available_models(prov, api_klic):
    if not api_klic: return []
    if prov == "Groq":
        try:
            client = OpenAI(api_key=api_klic, base_url="[https://api.groq.com/openai/v1](https://api.groq.com/openai/v1)")
            models = client.models.list()
            return sorted([m.id for m in models.data], reverse=True)
        except:
            return ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"]
    else:
        try:
            client = genai.Client(api_key=api_klic)
            models = client.models.list()
            platne_modely = [m.name.replace('models/', '') for m in models if 'gemini' in m.name and 'streaming' not in m.name and 'robotics' not in m.name]
            return sorted(platne_modely, reverse=True)
        except:
            return ["gemini-3.8-flash", "gemini-3.8-pro", "gemini-2.5-flash"]

col1, col2 = st.columns(2, gap="large")

with col1:
    with st.container(border=True):
        st.markdown(f"#### {_['ui_h']}")
        new_lang = st.radio(_["lang_lbl"], ["EN", "CZ"], index=0 if current_lang == "EN" else 1, horizontal=True)
        
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
        
        if "ai_provider" not in st.session_state: st.session_state.ai_provider = saved_settings.get("ai_provider", "Google Gemini")
        if "ai_model" not in st.session_state: 
            st.session_state.ai_model = saved_settings.get("ai_model", "gemini-3.8-flash")
            if "llama" in st.session_state.ai_model: st.session_state.ai_model = "llama3-70b-8192"
            if "robotics" in st.session_state.ai_model or "streaming" in st.session_state.ai_model: st.session_state.ai_model = "gemini-3.8-flash"
        
        temp_prov = st.selectbox(_["prov_lbl"], ["Google Gemini", "Groq"], index=0 if st.session_state.ai_provider != "Groq" else 1)
        
        if temp_prov == "Groq":
            has_secret = "GROQ_API_KEY" in st.secrets
            temp_api = st.secrets.get("GROQ_API_KEY", "")
        else:
            has_secret = "GOOGLE_API_KEY" in st.secrets or "GEMINI_API_KEY" in st.secrets
            temp_api = st.secrets.get("GOOGLE_API_KEY", st.secrets.get("GEMINI_API_KEY", ""))

        if has_secret:
            st.success(f"✅ {temp_prov} API Klíč je bezpečně načten ze Streamlit Secrets.")
        else:
            st.error(f"⚠️ Klíč pro {temp_prov} nebyl nalezen v lokálních ani cloudových secrets.")

        models = fetch_available_models(temp_prov, temp_api)
        temp_model = None
        
        if temp_api and models:
            idx = models.index(st.session_state.ai_model) if st.session_state.ai_model in models else 0
            temp_model = st.selectbox(_["mod_lbl"], models, index=idx)
            
        if st.button(_["save_btn"], type="primary", use_container_width=True):
            with st.spinner("Ukládám a synchronizuji s GitHubem..." if current_lang == "CZ" else "Saving and syncing with GitHub..."):
                st.session_state.ai_provider = temp_prov
                if temp_model:
                    st.session_state.ai_model = temp_model
                
                success = save_settings_to_json(st.session_state.lang, temp_prov, temp_model)
                if success:
                    st.success(_["saved_msg"])