import streamlit as st
import os
import json

def check_password():
    if st.session_state.get("password_correct", False):
        return True

    st.markdown("### 🔒 POKORNY TERMINAL - UZAMČENO")
    
    def overeni():
        if st.session_state["zadane_heslo"] == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["zadane_heslo"]
        else:
            st.session_state["password_correct"] = False

    st.text_input("Zadejte administrátorské heslo:", type="password", on_change=overeni, key="zadane_heslo")
    
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("Nesprávné heslo.")
        
    return False

def load_global_lang():
    # Načtení trvalého jazyka z watchlist.json při startu
    aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
    watchlist_file = os.path.join(aktualni_slozka, "watchlist.json")
    if os.path.exists(watchlist_file):
        try:
            with open(watchlist_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("settings", {}).get("lang", "CZ")
        except: pass
    return "CZ"

def vykresli_menu():
    if not check_password():
        st.stop()

    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {display: none;}
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        # Pokud relace právě začala, přečteme preferovaný jazyk z databáze
        if "lang" not in st.session_state:
            st.session_state.lang = load_global_lang()

        st.markdown("### 📊 POKORNY TERMINAL")
        
        if st.session_state.lang == "CZ":
            st.page_link("pages/10_Nastaveni.py", label="⚙️ Nastavení")
        else:
            st.page_link("pages/10_Nastaveni.py", label="⚙️ Settings")
            
        st.markdown("---")

        if st.session_state.lang == "CZ":
            st.page_link("Dashboard.py", label="🏠 Hlavní Dashboard")
            st.page_link("pages/1_Insider_4F.py", label="🧛 Insider Tracker (4F)")
            st.page_link("pages/2_SEC_13F_Radar.py", label="🏛️ SEC 13F Radar")
            st.page_link("pages/3_Terminal.py", label="📊 Terminal")
            st.page_link("pages/4_Opcni_Radar.py", label="🎲 Opční Radar")
            st.page_link("pages/5_COT_Reporty.py", label="🏛️ COT Reporty")
            st.page_link("pages/6_Makro.py", label="🌍 Makro & Rizika")
            st.page_link("pages/7_Baskets.py", label="🧺 Koše")
            st.page_link("pages/8_AI_Radar.py", label="🧠 AI Zprávy & Sentiment")
            st.page_link("pages/9_Aktualizace.py", label="🗄️ Aktualizace Dat")
        else:
            st.page_link("Dashboard.py", label="🏠 Main Dashboard")
            st.page_link("pages/1_Insider_4F.py", label="🧛 Insider Tracker (4F)")
            st.page_link("pages/2_SEC_13F_Radar.py", label="🏛️ SEC 13F Radar")
            st.page_link("pages/3_Terminal.py", label="📊 Terminal")
            st.page_link("pages/4_Opcni_Radar.py", label="🎲 Options Radar")
            st.page_link("pages/5_COT_Reporty.py", label="🏛️ COT Reports")
            st.page_link("pages/6_Makro.py", label="🌍 Macro & Risks")
            st.page_link("pages/7_Baskets.py", label="🧺 Baskets")
            st.page_link("pages/8_AI_Radar.py", label="🧠 AI News & Sentiment")
            st.page_link("pages/9_Aktualizace.py", label="🗄️ Data Update")