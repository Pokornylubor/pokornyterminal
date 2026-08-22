import streamlit as st
import pandas as pd
import json
import os
import sys
import base64
import requests

# --- INITIAL SETUP ---
st.set_page_config(page_title="POKORNY TERMINAL | 13F", layout="wide", initial_sidebar_state="collapsed")

# --- DIRECTORY MANAGEMENT ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)
WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")

import menu
menu.vykresli_menu()

# --- DICTIONARY ---
t = {
    "CZ": {
        "title": "SUPERINVESTOŘI (13F)", 
        "desc": "HISTORICKÁ DATA PORTFOLIÍ (DATAROMA).", 
        "empty": "DATABÁZE JE PRÁZDNÁ.", 
        "exp": "SYSTÉMOVÁ KONFIGURACE: OBLÍBENÍ", 
        "fav": "OBLÍBENÍ SUPERINVESTOŘI:", 
        "save": "ULOŽIT ZMĚNY", 
        "all": "ZOBRAZIT VŠECHNY Z DATABÁZE", 
        "sel": "VÝBĚR SUPERINVESTORA",
        "no_db": "SYS ERR: DATABÁZE SUPERINVESTORS_DB.CSV NENALEZENA."
    },
    "EN": {
        "title": "SUPERINVESTORS (13F)", 
        "desc": "HISTORICAL PORTFOLIO DATA (DATAROMA).", 
        "empty": "DATABASE IS EMPTY.", 
        "exp": "SYSTEM CONFIG: FAVORITES", 
        "fav": "FAVORITE SUPERINVESTORS:", 
        "save": "COMMIT CHANGES", 
        "all": "SHOW ALL FROM DATABASE", 
        "sel": "SELECT SUPERINVESTOR",
        "no_db": "SYS ERR: DATABASE SUPERINVESTORS_DB.CSV NOT FOUND."
    }
}
_ = t.get(st.session_state.get("lang", "CZ"), t["CZ"])

st.title(_["title"])
st.caption(_["desc"])
st.markdown("---")

def save_data(data):
    with open(WATCHLIST_FILE, "w") as f: json.dump(data, f, indent=4)
    try:
        if "GITHUB_TOKEN" in st.secrets:
            token, owner, repo = st.secrets["GITHUB_TOKEN"], st.secrets["GITHUB_OWNER"], st.secrets["GITHUB_REPO"]
            url, headers = f"https://api.github.com/repos/{owner}/{repo}/contents/watchlist.json", {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
            sha = requests.get(url, headers=headers).json().get("sha")
            payload = {"message": "SYS: Cloud sync 13F Favorites", "content": base64.b64encode(json.dumps(data, indent=4).encode("utf-8")).decode("utf-8"), "branch": "main"}
            if sha: payload["sha"] = sha
            requests.put(url, headers=headers, json=payload)
    except Exception: pass

FILE_PATH = os.path.join(hlavni_slozka, "superinvestors_db.csv")

if not os.path.exists(FILE_PATH): 
    st.error(_["no_db"])
else:
    df = pd.read_csv(FILE_PATH)
    if df.empty: 
        st.info(_["empty"])
    else:
        investors = sorted(df['Investor'].dropna().unique())
        try:
            with open(WATCHLIST_FILE, "r") as f: data = json.load(f)
        except: data = {"superinvestors": []}
        
        vychozi_vyber = [inv for inv in data.get("superinvestors", []) if inv in investors]
        
        with st.expander(_["exp"], expanded=False):
            vybrani = st.multiselect(_["fav"], options=investors, default=vychozi_vyber)
            if st.button(_["save"], use_container_width=True):
                data["superinvestors"] = vybrani
                save_data(data)
                st.rerun()
                
        # --- FILTRACE A VÝBĚR ---
        c1, c2 = st.columns([1, 4])
        with c1:
            # Checkbox posunutý lehce níže, aby lícoval s roletkou
            st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
            zobrazit_vse = st.checkbox(_["all"], value=False if vychozi_vyber else True)
            
        nabidka = investors if (not vychozi_vyber or zobrazit_vse) else vychozi_vyber
        
        with c2:
            selected = st.selectbox(_["sel"], nabidka)
            
        if selected:
            # Odstranění nepotřebných sloupců a vykreslení čisté tabulky
            df_view = df[df['Investor'] == selected].drop(columns=['Investor', 'Kvartal_Aktualizace', 'Investor_Code'], errors='ignore')
            st.dataframe(df_view, use_container_width=True, height=650, hide_index=True)
