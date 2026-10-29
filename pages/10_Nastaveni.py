import streamlit as st
import json
import os
import sys

st.set_page_config(page_title="POKORNY TERMINAL | NASTAVENÍ", layout="wide")

aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)

import menu
menu.vykresli_menu()

WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")

def load_app_data():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {"portfolio": [], "watchlist": [], "settings": {}}

def save_app_data(data):
    with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

app_data = load_app_data()
saved_settings = app_data.get("settings", {})

st.title("⚙️ NASTAVENÍ TERMINÁLU")
st.markdown("---")

c1, c2 = st.columns(2)

with c1:
    st.subheader("Jazyk / Language")
    lang = st.radio("Vyberte jazyk:", ["CZ", "EN"], index=0 if saved_settings.get("lang", "CZ") == "CZ" else 1)
    
with c2:
    st.subheader("AI Engine")
    # Přepnuto pouze na Groq a Gemini
    provider = st.selectbox("AI Provider", ["Groq", "Gemini"], index=0 if saved_settings.get("ai_provider", "Groq") == "Groq" else 1)
    
    if provider == "Groq":
        models = ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"]
    else:
        models = ["gemini-1.5-flash", "gemini-1.5-pro"]
        
    default_model = saved_settings.get("ai_model", "")
    m_index = models.index(default_model) if default_model in models else 0
    model = st.selectbox("AI Model", models, index=m_index)

if st.button("💾 Uložit nastavení", use_container_width=True):
    app_data["settings"]["lang"] = lang
    app_data["settings"]["ai_provider"] = provider
    app_data["settings"]["ai_model"] = model
    save_app_data(app_data)
    
    st.session_state["lang"] = lang
    st.session_state["ai_provider"] = provider
    st.session_state["ai_model"] = model
    
    st.success("✅ Nastavení úspěšně uloženo.")