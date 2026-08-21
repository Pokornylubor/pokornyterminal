import streamlit as st
import pandas as pd
import yfinance as yf
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

st.set_page_config(page_title="Pokorny Terminal", page_icon="icon.png", layout="wide")

import menu
menu.vykresli_menu() 

t = {
    "CZ": {
        "title": "📈 Pokorny Terminal", "desc": "Tvůj osobní přehled v reálném čase.", "tab_port": "💼 Moje Portfolio",
        "tab_watch": "👀 Můj Watchlist", "tab_set": "⚙️ Nastavení seznamů", "empty_list": "Tento seznam je zatím prázdný.",
        "waiting": "Čekám na data...", "error_load": "Nelze načíst", "curr_pos": "Aktuálně držené pozice",
        "radar": "Radar / Čekám na lepší cenu", "edit_list": "### ✏️ Úprava seznamů",
        "edit_desc": "Pro přidání klikni na prázdný řádek a zmáčkni ENTER. Poté ulož.",
        "save_btn": "💾 ULOŽIT ZMĚNY VE VŠECH SEZNAMECH", "success_save": "✅ Úspěšně uloženo a synchronizováno!"
    },
    "EN": {
        "title": "📈 Pokorny Terminal", "desc": "Your personal real-time overview.", "tab_port": "💼 My Portfolio",
        "tab_watch": "👀 My Watchlist", "tab_set": "⚙️ List Settings", "empty_list": "This list is currently empty.",
        "waiting": "Waiting for data...", "error_load": "Failed to load", "curr_pos": "Currently Held Positions",
        "radar": "Radar / Waiting for better price", "edit_list": "### ✏️ Edit Lists",
        "edit_desc": "Click on empty row, type, press ENTER. Then save.",
        "save_btn": "💾 SAVE CHANGES", "success_save": "✅ Successfully saved and synced!"
    }
}
_ = t.get(st.session_state.lang, t["CZ"])

st.title(_["title"])
st.markdown(_["desc"])

def load_data():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list): return {"portfolio": data, "watchlist": [], "superinvestors": []}
                return data
        except: pass
    return {"portfolio": ["GOOGL", "AMZN", "MSFT", "AMAT", "ASML", "NVDA", "UBER", "SOFI"], "watchlist": [], "superinvestors": ["Mohnish Pabrai", "Li Lu", "Michael Burry"]}

def save_data(data):
    # 1. Lokální uložení (pro PC)
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(data, f, indent=4)
        
    # 2. Cloudové uložení (z webu přímo na GitHub)
    try:
        if "GITHUB_TOKEN" in st.secrets:
            token, owner, repo = st.secrets["GITHUB_TOKEN"], st.secrets["GITHUB_OWNER"], st.secrets["GITHUB_REPO"]
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/watchlist.json"
            headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
            
            sha = requests.get(url, headers=headers).json().get("sha")
            content_b64 = base64.b64encode(json.dumps(data, indent=4).encode("utf-8")).decode("utf-8")
            
            payload = {"message": "Cloud sync Watchlistu", "content": content_b64, "branch": "main"}
            if sha: payload["sha"] = sha
            requests.put(url, headers=headers, json=payload)
    except Exception:
        pass

data = load_data()

def display_tickers(ticker_list):
    if not ticker_list:
        st.info(_["empty_list"]); return
    cols = st.columns(4)
    for i, ticker in enumerate(ticker_list):
        col = cols[i % 4]
        try:
            hist = yf.Ticker(ticker).history(period="2d")
            if len(hist) >= 2:
                curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                col.metric(ticker, f"${curr:.2f}", f"{curr-prev:.2f} USD ({(curr-prev)/prev*100:.2f} %)")
            else: col.metric(ticker, _["waiting"])
        except: col.error(f"{_['error_load']} {ticker}")

tab1, tab2, tab3 = st.tabs([_["tab_port"], _["tab_watch"], _["tab_set"]])

with tab1:
    st.subheader(_["curr_pos"]); display_tickers(data.get("portfolio", []))
with tab2:
    st.subheader(_["radar"]); display_tickers(data.get("watchlist", []))
with tab3:
    st.markdown(_["edit_list"]); st.markdown(_["edit_desc"])
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{_['tab_port']}**")
        edit_port = st.data_editor(pd.DataFrame(data.get("portfolio", []), columns=["Ticker"]), num_rows="dynamic", use_container_width=True)
    with col2:
        st.markdown(f"**{_['tab_watch']}**")
        edit_watch = st.data_editor(pd.DataFrame(data.get("watchlist", []), columns=["Ticker"]), num_rows="dynamic", use_container_width=True)
        
    st.markdown("---")
    if st.button(_["save_btn"], use_container_width=True):
        data["portfolio"] = [t.strip().upper() for t in edit_port["Ticker"].dropna().astype(str).tolist() if t.strip()]
        data["watchlist"] = [t.strip().upper() for t in edit_watch["Ticker"].dropna().astype(str).tolist() if t.strip()]
        save_data(data)
        st.success(_["success_save"])
