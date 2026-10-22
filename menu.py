import streamlit as st
import os

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

def vykresli_menu():
    if not check_password():
        st.stop()

    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {display: none;}
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### ⚙️ Nastavení / Settings")
        if "lang" not in st.session_state:
            st.session_state.lang = "CZ"

        selected_lang = st.radio("🌐 Jazyk / Language:", ["CZ", "EN"], index=0 if st.session_state.lang == "CZ" else 1)
        if selected_lang != st.session_state.lang:
            st.session_state.lang = selected_lang
            st.rerun()

        st.markdown("---")

        # Neprůstřelné vykreslování odkazů (vykreslí jen to, co fyzicky existuje)
        def bezpecny_odkaz(cesta, label_cz, label_en):
            if os.path.exists(cesta):
                lbl = label_cz if st.session_state.lang == "CZ" else label_en
                st.page_link(cesta, label=lbl)

        # Volání jednotlivých stránek (aplikace nespadne, i když nějaká chybí)
        bezpecny_odkaz("Dashboard.py", "🏠 Hlavní Dashboard", "🏠 Main Dashboard")
        bezpecny_odkaz("pages/1_Insider_4F.py", "🧛 Insider Tracker (4F)", "🧛 Insider Tracker (4F)")
        bezpecny_odkaz("pages/2_SEC_13F_Radar.py", "🏛️ SEC 13F Radar", "🏛️ SEC 13F Radar")
        bezpecny_odkaz("pages/3_Terminal.py", "📊 Terminal", "📊 Terminal")
        bezpecny_odkaz("pages/4_Opcni_Radar.py", "🎲 Opční Radar", "🎲 Options Radar")
        bezpecny_odkaz("pages/5_COT_Reporty.py", "🏛️ COT Reporty", "🏛️ COT Reports")
        
        # Pokrývá variantu 6 i 7, ať už máš soubor pojmenovaný jakkoliv
        bezpecny_odkaz("pages/6_Makro.py", "🌍 Makro & Rizika", "🌍 Macro & Risks")
        bezpecny_odkaz("pages/7_Makro.py", "🌍 Makro & Rizika", "🌍 Macro & Risks")
        bezpecny_odkaz("pages/6_Aktualizace.py", "🗄️ Aktualizace Dat", "🗄️ Data Update")
        bezpecny_odkaz("pages/7_Aktualizace.py", "🗄️ Aktualizace Dat", "🗄️ Data Update")