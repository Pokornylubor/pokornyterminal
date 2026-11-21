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
            .nav-brand {
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.92rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                color: #F4F4F5;
                padding: 4px 0 14px 4px;
                border-bottom: 1px solid #1F2227;
                margin-bottom: 14px;
            }
            .nav-sec {
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.66rem;
                font-weight: 600;
                letter-spacing: 0.12em;
                color: #71717A;
                text-transform: uppercase;
                padding: 12px 0 4px 6px;
            }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        if "lang" not in st.session_state:
            st.session_state.lang = load_global_lang()

        lang = st.session_state.lang

        labels = {
            "CZ": {
                "sec_term": "TERMINÁL",
                "sec_data": "TOKY & MAKRO",
                "sec_sys": "SYSTÉM",
                "dash": "Hlavní Dashboard",
                "term": "Terminal",
                "baskets": "Koše",
                "ai": "AI Zprávy & Sentiment",
                "ins": "Insider Tracker (4F)",
                "sec": "SEC 13F Radar",
                "opt": "Opční Radar",
                "cot": "COT Reporty",
                "makro": "Makro & Rizika",
                "upd": "Aktualizace Dat",
                "set": "Nastavení"
            },
            "EN": {
                "sec_term": "TERMINAL",
                "sec_data": "FLOWS & MACRO",
                "sec_sys": "SYSTEM",
                "dash": "Main Dashboard",
                "term": "Terminal",
                "baskets": "Baskets",
                "ai": "AI News & Sentiment",
                "ins": "Insider Tracker (4F)",
                "sec": "SEC 13F Radar",
                "opt": "Options Radar",
                "cot": "COT Reports",
                "makro": "Macro & Risks",
                "upd": "Data Update",
                "set": "Settings"
            }
        }
        L = labels.get(lang, labels["CZ"])

        st.markdown('<div class="nav-brand">POKORNY TERMINAL</div>', unsafe_allow_html=True)

        st.markdown(f'<div class="nav-sec">{L["sec_term"]}</div>', unsafe_allow_html=True)
        st.page_link("Dashboard.py", label=L["dash"], icon=":material/dashboard:")
        st.page_link("pages/3_Terminal.py", label=L["term"], icon=":material/monitoring:")
        st.page_link("pages/7_Baskets.py", label=L["baskets"], icon=":material/workspaces:")
        st.page_link("pages/8_AI_Radar.py", label=L["ai"], icon=":material/article:")

        st.markdown(f'<div class="nav-sec">{L["sec_data"]}</div>', unsafe_allow_html=True)
        st.page_link("pages/1_Insider_4F.py", label=L["ins"], icon=":material/person_search:")
        st.page_link("pages/2_SEC_13F_Radar.py", label=L["sec"], icon=":material/account_balance:")
        st.page_link("pages/4_Opcni_Radar.py", label=L["opt"], icon=":material/candlestick_chart:")
        st.page_link("pages/5_COT_Reporty.py", label=L["cot"], icon=":material/bar_chart:")
        st.page_link("pages/6_Makro.py", label=L["makro"], icon=":material/public:")

        st.markdown(f'<div class="nav-sec">{L["sec_sys"]}</div>', unsafe_allow_html=True)
        st.page_link("pages/9_Aktualizace.py", label=L["upd"], icon=":material/sync:")
        st.page_link("pages/10_Nastaveni.py", label=L["set"], icon=":material/tune:")