import streamlit as st
import os
import sys
from openai import OpenAI

# --- INITIAL SETUP ---
st.set_page_config(page_title="POKORNY TERMINAL | SETTINGS", layout="wide", initial_sidebar_state="collapsed")

aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)

import menu
menu.vykresli_menu()

current_lang = st.session_state.get("lang", "CZ")

# --- DICTIONARY ---
t = {
    "CZ": {
        "title": "⚙️ GLOBÁLNÍ NASTAVENÍ",
        "desc": "SPRÁVA ROZHRANÍ A INFRASTRUKTURY TERMINÁLU.",
        "ui_h": "🎨 Uživatelské rozhraní",
        "lang_lbl": "Jazyk aplikace (Language):",
        "ai_h": "🧠 Umělá inteligence",
        "ai_desc": "Propojení aplikace s LLM servery pro datovou analýzu.",
        "api_lbl": "API Klíč (Groq / OpenAI):",
        "prov_lbl": "Poskytovatel:",
        "mod_lbl": "Výchozí model:",
        "save_btn": "💾 Uložit konfiguraci AI",
        "saved_msg": "Konfigurace byla úspěšně uložena pro aktuální relaci.",
        "no_models": "Zadejte platný API klíč pro načtení modelů.",
        "future_h": "🔧 Budoucí moduly",
        "future_desc": "Tato sekce je připravena pro přidání napojení na brokery, upozornění (Webhooky) či exporty."
    },
    "EN": {
        "title": "⚙️ GLOBAL SETTINGS",
        "desc": "TERMINAL INTERFACE AND INFRASTRUCTURE MANAGEMENT.",
        "ui_h": "🎨 User Interface",
        "lang_lbl": "App Language:",
        "ai_h": "🧠 Artificial Intelligence",
        "ai_desc": "Connection to LLM servers for data analysis.",
        "api_lbl": "API Key (Groq / OpenAI):",
        "prov_lbl": "Provider:",
        "mod_lbl": "Default Model:",
        "save_btn": "💾 Save AI Configuration",
        "saved_msg": "Configuration successfully saved for the current session.",
        "no_models": "Enter a valid API key to fetch models.",
        "future_h": "🔧 Future Modules",
        "future_desc": "This section is reserved for broker integrations, webhooks, or data exports."
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

# LEVÝ SLOUPEC - UI & BUDOUCNOST
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

# PRAVÝ SLOUPEC - AI KONFIGURACE
with col2:
    with st.container(border=True):
        st.markdown(f"#### {_['ai_h']}")
        st.caption(_["ai_desc"])
        
        # Inicializace proměnných v session_state
        if "ai_api_key" not in st.session_state: st.session_state.ai_api_key = ""
        if "ai_provider" not in st.session_state: st.session_state.ai_provider = "Groq"
        if "ai_model" not in st.session_state: st.session_state.ai_model = ""

        # Formulářové prvky (čtou hodnotu ze session_state)
        temp_api = st.text_input(_["api_lbl"], value=st.session_state.ai_api_key, type="password", placeholder="gsk_... / sk-...")
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
            st.session_state.ai_api_key = temp_api
            st.session_state.ai_provider = temp_prov
            if temp_model:
                st.session_state.ai_model = temp_model
            st.success(_["saved_msg"])