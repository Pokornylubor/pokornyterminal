import streamlit as st
import pandas as pd
import json
import os
import sys
import base64
import requests

# --- CENTRÁLNÍ PAMĚŤ A MENU ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)
WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")

st.set_page_config(page_title="13F Superinvestors", page_icon="🐋", layout="wide")
import menu
menu.vykresli_menu()

t = {
    "CZ": {"title": "🐋 13F Superinvestoři", "desc": "Historická data portfolií (Dataroma).", "empty": "Databáze je prázdná.", "exp": "⭐ Nastavit oblíbené", "fav": "Moji oblíbenci:", "save": "💾 Uložit na Cloud", "all": "Zobrazit všechny", "sel": "Vyber superinvestora:"},
    "EN": {"title": "🐋 13F Superinvestors", "desc": "Historical portfolio data (Dataroma).", "empty": "Database is empty.", "exp": "⭐ Set Favorites", "fav": "My favorites:", "save": "💾 Save to Cloud", "all": "Show all", "sel": "Select superinvestor:"}
}
_ = t.get(st.session_state.lang, t["CZ"])

st.title(_["title"])
st.markdown(_["desc"])

def save_data(data):
    with open(WATCHLIST_FILE, "w") as f: json.dump(data, f, indent=4)
    try:
        if "GITHUB_TOKEN" in st.secrets:
            token, owner, repo = st.secrets["GITHUB_TOKEN"], st.secrets["GITHUB_OWNER"], st.secrets["GITHUB_REPO"]
            url, headers = f"https://api.github.com/repos/{owner}/{repo}/contents/watchlist.json", {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
            sha = requests.get(url, headers=headers).json().get("sha")
            payload = {"message": "Cloud sync 13F Favorites", "content": base64.b64encode(json.dumps(data, indent=4).encode("utf-8")).decode("utf-8"), "branch": "main"}
            if sha: payload["sha"] = sha
            requests.put(url, headers=headers, json=payload)
    except Exception: pass

FILE_PATH = os.path.join(hlavni_slozka, "superinvestors_db.csv")

if not os.path.exists(FILE_PATH): st.warning("⚠️ Data file not found. Run updater.py first.")
else:
    df = pd.read_csv(FILE_PATH)
    if df.empty: st.info(_["empty"])
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
        st.markdown("---")
        nabidka = investors if (not vychozi_vyber or st.checkbox(_["all"])) else vychozi_vyber
        selected = st.selectbox(_["sel"], nabidka)
        if selected:
            st.dataframe(df[df['Investor'] == selected].drop(columns=['Investor', 'Kvartal_Aktualizace', 'Investor_Code'], errors='ignore'), use_container_width=True)
