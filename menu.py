import streamlit as st
import os
import json

def check_password():
    if st.session_state.get("password_correct", False):
        return True

    st.markdown("### POKORNY TERMINAL — UZAMČENO")
    
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
    aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
    watchlist_file = os.path.join(aktualni_slozka, "watchlist.json")
    if os.path.exists(watchlist_file):
        try:
            with open(watchlist_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("settings", {}).get("lang", "CZ")
        except:
            pass
    return "CZ"

def vykresli_menu():
    if not check_password():
        st.stop()

    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {display: none !important;}
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        if "lang" not in st.session_state:
            st.session_state.lang = load_global_lang()

        st.markdown("### POKORNY TERMINAL")
        
        if st.session_state.lang == "CZ":
            st.page_link("pages/10_Nastaveni.py", label="Nastavení", icon=":material/tune:")
        else:
            st.page_link("pages/10_Nastaveni.py", label="Settings", icon=":material/tune:")
            
        st.markdown("---")

        if st.session_state.lang == "CZ":
            st.page_link("Dashboard.py", label="Hlavní Dashboard", icon=":material/dashboard:")
            st.page_link("pages/3_Terminal.py", label="Terminal", icon=":material/monitoring:")
            st.page_link("pages/8_AI_Radar.py", label="AI Zprávy & Sentiment", icon=":material/article:")
            st.page_link("pages/6_Makro.py", label="Makro & Rizika", icon=":material/public:")
            st.page_link("pages/1_Insider_4F.py", label="Insider Tracker (4F)", icon=":material/person_search:")
            st.page_link("pages/2_SEC_13F_Radar.py", label="SEC 13F Radar", icon=":material/account_balance:")
            st.page_link("pages/4_Opcni_Radar.py", label="Opční Radar", icon=":material/candlestick_chart:")
            st.page_link("pages/5_COT_Reporty.py", label="COT Reporty", icon=":material/bar_chart:")
            st.page_link("pages/7_Baskets.py", label="Koše", icon=":material/workspaces:")
            st.page_link("pages/9_Aktualizace.py", label="Aktualizace Dat", icon=":material/sync:")
        else:
            st.page_link("Dashboard.py", label="Main Dashboard", icon=":material/dashboard:")
            st.page_link("pages/3_Terminal.py", label="Terminal", icon=":material/monitoring:")
            st.page_link("pages/8_AI_Radar.py", label="AI News & Sentiment", icon=":material/article:")
            st.page_link("pages/6_Makro.py", label="Macro & Risks", icon=":material/public:")
            st.page_link("pages/1_Insider_4F.py", label="Insider Tracker (4F)", icon=":material/person_search:")
            st.page_link("pages/2_SEC_13F_Radar.py", label="SEC 13F Radar", icon=":material/account_balance:")
            st.page_link("pages/4_Opcni_Radar.py", label="Options Radar", icon=":material/candlestick_chart:")
            st.page_link("pages/5_COT_Reporty.py", label="COT Reports", icon=":material/bar_chart:")
            st.page_link("pages/7_Baskets.py", label="Baskets", icon=":material/workspaces:")
            st.page_link("pages/9_Aktualizace.py", label="Data Update", icon=":material/sync:")