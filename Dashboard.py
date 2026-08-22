import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os
import sys
import base64
import requests

# --- INITIAL SETUP ---
st.set_page_config(
    page_title="POKORNY TERMINAL",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- DIRECTORY MANAGEMENT ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)
WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")

import menu
menu.vykresli_menu() 

st.title("POKORNÝ TERMINAL")
st.markdown("---")

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
    # Lokální záloha
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(data, f, indent=4)
        
    # Cloud sync
    try:
        if "GITHUB_TOKEN" in st.secrets:
            token, owner, repo = st.secrets["GITHUB_TOKEN"], st.secrets["GITHUB_OWNER"], st.secrets["GITHUB_REPO"]
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/watchlist.json"
            headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
            
            sha = requests.get(url, headers=headers).json().get("sha")
            content_b64 = base64.b64encode(json.dumps(data, indent=4).encode("utf-8")).decode("utf-8")
            
            payload = {"message": "SYS: Watchlist Update", "content": content_b64, "branch": "main"}
            if sha: payload["sha"] = sha
            requests.put(url, headers=headers, json=payload)
    except Exception:
        pass

data = load_data()

def display_tickers(ticker_list, title):
    st.subheader(title)
    if not ticker_list:
        st.caption("NO DATA AVAILABLE")
        return
    
    # Zvýšená informační hustota (6 sloupců)
    cols = st.columns(6) 
    for i, ticker in enumerate(ticker_list):
        col = cols[i % 6]
        try:
            hist = yf.Ticker(ticker).history(period="2d")
            if len(hist) >= 2:
                curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                diff = curr - prev
                pct = (diff / prev) * 100
                col.metric(ticker, f"{curr:.2f}", f"{diff:+.2f} ({pct:+.2f}%)")
            else: 
                col.metric(ticker, "N/A")
        except: 
            col.metric(ticker, "ERR")

tab1, tab2, tab3 = st.tabs(["PORTFOLIO", "WATCHLIST", "SYSTEM CONFIG"])

with tab1:
    display_tickers(data.get("portfolio", []), "CURRENT POSITIONS")
with tab2:
    display_tickers(data.get("watchlist", []), "RADAR")
with tab3:
    st.subheader("SYSTEM LIST CONFIGURATION")
    col1, col2 = st.columns(2)
    with col1:
        st.caption("PORTFOLIO TICKERS")
        edit_port = st.data_editor(pd.DataFrame(data.get("portfolio", []), columns=["Ticker"]), num_rows="dynamic", use_container_width=True, hide_index=True)
    with col2:
        st.caption("WATCHLIST TICKERS")
        edit_watch = st.data_editor(pd.DataFrame(data.get("watchlist", []), columns=["Ticker"]), num_rows="dynamic", use_container_width=True, hide_index=True)
        
    st.markdown("---")
    if st.button("COMMIT CHANGES", use_container_width=True):
        data["portfolio"] = [t.strip().upper() for t in edit_port["Ticker"].dropna().astype(str).tolist() if t.strip()]
        data["watchlist"] = [t.strip().upper() for t in edit_watch["Ticker"].dropna().astype(str).tolist() if t.strip()]
        save_data(data)
        st.success("SYSTEM UPDATED")
