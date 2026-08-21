import streamlit as st

def vykresli_menu():
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
        
        if st.session_state.lang == "CZ":
            st.page_link("Dashboard.py", label="🏠 Hlavní Dashboard")
            st.page_link("pages/1_Insider_4F.py", label="🕵️‍♂️ Insider Tracker (4F)")
            st.page_link("pages/2_Superinvestors_13F.py", label="🐋 13F Superinvestoři")
            st.page_link("pages/3_Valuacni_Screener.py", label="📊 Valuační Screener")
            st.page_link("pages/4_Opcni_Radar.py", label="🎲 Opční Radar")
            st.page_link("pages/5_COT_Reporty.py", label="🏛️ COT Reporty")
            st.page_link("pages/6_SEC_13F_Radar.py", label="🏛️ SEC 13F Radar")
            st.page_link("pages/7_Aktualizace.py", label="🎛️ Aktualizace Dat")
        else:
            st.page_link("Dashboard.py", label="🏠 Main Dashboard")
            st.page_link("pages/1_Insider_4F.py", label="🕵️‍♂️ Insider Tracker (4F)")
            st.page_link("pages/2_Superinvestors_13F.py", label="🐋 13F Superinvestors")
            st.page_link("pages/3_Valuacni_Screener.py", label="📊 Valuation Screener")
            st.page_link("pages/4_Opcni_Radar.py", label="🎲 Options Radar")
            st.page_link("pages/5_COT_Reporty.py", label="🏛️ COT Reports")
            st.page_link("pages/6_SEC_13F_Radar.py", label="🏛️ SEC 13F Radar")
            st.page_link("pages/7_Aktualizace.py", label="🎛️ Data Update")
