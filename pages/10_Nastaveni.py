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

def save_settings_to_json(lang, provider, model):
    data = load_watchlist_data()
    
    # Bezpečné vytvoření bloku settings, pokud ještě neexistuje
    if "settings" not in data:
        data["settings"] = {}
        
    data["settings"]["lang"] = lang
    data["settings"]["ai_provider"] = provider
    data["settings"]["ai_model"] = model
    
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
    "CZ": {
        "title": "⚙️ GLOBÁLNÍ NASTAVENÍ",
        "desc": "SPRÁVA ROZHRANÍ A INFRASTRUKTURY TERMINÁLU.",
        "ui_h": "🎨 Uživatelské rozhraní",
        "lang_lbl": "Jazyk aplikace (Language):",
        "ai_h": "🧠 Umělá inteligence (Google Gemini)",
        "ai_desc": "Propojení aplikace s Google AI Studio pro datovou analýzu.",
        "api_lbl": "Dočasný API Klíč:",
        "prov_lbl": "Poskytovatel:",
        "mod_lbl": "Výchozí model:",
        "save_btn": "💾 Uložit veškeré nastavení a synchronizovat na GitHub",
        "saved_msg": "Globální konfigurace (jazyk, modely) bezpečně uložena na GitHub.",
        "no_models": "Klíč nenalezen. Vložte GOOGLE_API_KEY do Streamlit Secrets.",
        "future_h": "🔧 Budoucí moduly",
        "future_desc": "Připraveno pro napojení na brokery a webhooky."
    },
    "EN": {
        "title": "⚙️ GLOBAL SETTINGS",
        "desc": "TERMINAL INTERFACE AND INFRASTRUCTURE MANAGEMENT.",
        "ui_h": "🎨 User Interface",
        "lang_lbl": "App Language:",
        "ai_h": "🧠 Artificial Intelligence (Google Gemini)",
        "ai_desc": "Connection to Google AI Studio for data analysis.",
        "api_lbl": "Temporary API Key:",
        "prov_lbl": "Provider:",
        "mod_lbl": "Default Model:",
        "save_btn": "💾 Save All Settings & Sync to GitHub",
        "saved_msg": "Global configuration (language, models) safely saved to GitHub.",
        "no_models": "Key not found. Add GOOGLE_API_KEY to Streamlit Secrets.",
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
        if "google" in provider.lower() or "gemini" in provider.lower():
            # Připojení na Google AI Studio endpoint pro načtení dostupných modelů
            client = OpenAI(api_key=api_klic, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
            models = client.models.list().data
            llm_models = [m.id for m in models if "gemini" in m.id]
            return sorted(llm_models, reverse=True)
        else:
            return ["gemini-2.5-flash", "gemini-2.5-pro"]
    except:
        # Fallback seznam spolehlivých modelů, pokud selže živé načtení z API
        return ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash"]

col1, col2 = st.columns(2, gap="large")

with col1:
    with st.container(border=True):
        st.markdown(f"#### {_['ui_h']}")
        new_lang = st.radio(_["lang_lbl"], ["CZ", "EN"], index=0 if current_lang == "CZ" else 1, horizontal=True)
        
        # Plynulé přepnutí v UI hned po kliknutí
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
        if "ai_model" not in st.session_state: st.session_state.ai_model = saved_settings.get("ai_model", "gemini-2.5-flash")

        # Hledáme klíč pod klíčovými slovy pro Google/Gemini
        has_secret = "GOOGLE_API_KEY" in st.secrets or "GEMINI_API_KEY" in st.secrets
        if has_secret:
            st.success("✅ Google API Klíč je bezpečně načten z tajného trezoru Streamlit Cloud.")
            temp_api = st.secrets.get("GOOGLE_API_KEY", st.secrets.get("GEMINI_API_KEY", ""))
        else:
            temp_api = st.text_input(_["api_lbl"], type="password", placeholder="AIza...", help="Pouze pro tuto relaci. Pro trvalé uložení vložte GOOGLE_API_KEY do Secrets.")
            
        temp_prov = st.selectbox(_["prov_lbl"], ["Google Gemini"], index=0)
        
        models = fetch_available_models(temp_api, temp_prov)
        temp_model = None
        
        if temp_api:
            if models:
                idx = models.index(st.session_state.ai_model) if st.session_state.ai_model in models else 0
                temp_model = st.selectbox(_["mod_lbl"], models, index=idx)
            else:
                st.error("Neplatný klíč nebo výpadek Google API.")
        else:
            st.warning(_["no_models"])
            
        if st.button(_["save_btn"], type="primary", use_container_width=True):
            with st.spinner("Ukládám a synchronizuji s GitHubem..."):
                st.session_state.ai_provider = temp_prov
                if temp_model:
                    st.session_state.ai_model = temp_model
                
                # Zapsání jazyka i modelů natrvalo
                success = save_settings_to_json(st.session_state.lang, temp_prov, temp_model)
                if success:
                    st.success(_["saved_msg"])