import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os
import sys
import base64
import requests
import plotly.graph_objects as go

# --- INITIAL SETUP ---
st.set_page_config(page_title="POKORNY TERMINAL", layout="wide", initial_sidebar_state="collapsed")

# --- DIRECTORY MANAGEMENT ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)
WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")

import menu
menu.vykresli_menu() 

t = {
    "CZ": {"title": "POKORNY TERMINAL", "tab_port": "PORTFOLIO", "tab_watch": "WATCHLIST", "tab_set": "SYSTÉMOVÁ KONFIGURACE", "curr_pos": "AKTUÁLNÍ POZICE", "radar": "RADAR", "no_data": "ŽÁDNÁ DATA", "err": "ERR", "port_tickers": "TICKERY (PORTFOLIO)", "watch_tickers": "TICKERY (WATCHLIST)", "commit": "ULOŽIT ZMĚNY", "success": "SYSTÉM AKTUALIZOVÁN"},
    "EN": {"title": "POKORNY TERMINAL", "tab_port": "PORTFOLIO", "tab_watch": "WATCHLIST", "tab_set": "SYSTEM CONFIG", "curr_pos": "CURRENT POSITIONS", "radar": "RADAR", "no_data": "NO DATA AVAILABLE", "err": "ERR", "port_tickers": "PORTFOLIO TICKERS", "watch_tickers": "WATCHLIST TICKERS", "commit": "COMMIT CHANGES", "success": "SYSTEM UPDATED"}
}
_ = t.get(st.session_state.get("lang", "CZ"), t["CZ"])

st.title(_["title"])
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
    with open(WATCHLIST_FILE, "w") as f: json.dump(data, f, indent=4)
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
    except Exception: pass

data = load_data()

def display_tickers(ticker_list, title):
    st.subheader(title)
    if not ticker_list:
        st.caption(_["no_data"])
        return
    cols = st.columns(6) 
    for i, ticker in enumerate(ticker_list):
        col = cols[i % 6]
        try:
            hist = yf.Ticker(ticker).history(period="2d")
            if len(hist) >= 2:
                curr, prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                col.metric(ticker, f"{curr:.2f}", f"{curr-prev:+.2f} ({(curr-prev)/prev*100:+.2f}%)")
            else: col.metric(ticker, "N/A")
        except: col.metric(ticker, _["err"])

tab1, tab2, tab3, tab4 = st.tabs([_["tab_port"], _["tab_watch"], "CHARTING", _["tab_set"]])

with tab1: display_tickers(data.get("portfolio", []), _["curr_pos"])
with tab2: display_tickers(data.get("watchlist", []), _["radar"])

with tab3:
    st.subheader("DETAILNÍ ANALÝZA (CHARTING)")
    all_tickers = list(dict.fromkeys(data.get("portfolio", []) + data.get("watchlist", [])))
    
    # 4 sloupce pro lepší rozložení vyhledávání
    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
    sel_tick = c1.selectbox("VÝBĚR Z DATABÁZE", [""] + all_tickers)
    custom_tick = c2.text_input("VLASTNÍ TICKER (např. AAPL)")
    
    # Pokud uživatel zadá vlastní ticker, má přednost před výběrem ze seznamu
    final_tick = custom_tick.upper().strip() if custom_tick.strip() else sel_tick
    
    chart_type = c3.selectbox("TYP GRAFU", ["Candlestick", "Line"])
    interval = c4.selectbox("INTERVAL", ["1m", "5m", "15m", "1h", "1d", "1wk", "1mo"], index=4)

    if final_tick:
        period_map = {"1m": "7d", "5m": "60d", "15m": "60d", "1h": "730d", "1d": "max", "1wk": "max", "1mo": "max"}
        
        with st.spinner(f"Stahuji tržní data pro {final_tick}..."):
            df_c = yf.download(final_tick, period=period_map[interval], interval=interval, progress=False)
            
        if not df_c.empty:
            if isinstance(df_c.columns, pd.MultiIndex): df_c.columns = df_c.columns.get_level_values(0)
            fig = go.Figure()
            if chart_type == "Candlestick":
                fig.add_trace(go.Candlestick(x=df_c.index, open=df_c['Open'], high=df_c['High'], low=df_c['Low'], close=df_c['Close'], name="Cena"))
            else:
                fig.add_trace(go.Scatter(x=df_c.index, y=df_c['Close'], mode='lines', line=dict(color='#00FF00'), name="Close"))
            
            # Profi formátování s TradingView logikou (dragmode='pan')
            fig.update_layout(
                template="plotly_dark", 
                margin=dict(l=0, r=0, t=10, b=0), 
                height=600, 
                xaxis_rangeslider_visible=False,
                dragmode='pan'
            )
            
            # Aktivace zoomování kolečkem
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
        else:
            st.error(f"Data pro ticker {final_tick} v intervalu {interval} nejsou dostupná.")
    else:
        st.info("Vyber ticker ze seznamu nebo zadej vlastní pro zobrazení grafu.")

with tab4:
    st.subheader(_["tab_set"])
    col1, col2 = st.columns(2)
    with col1: edit_port = st.data_editor(pd.DataFrame(data.get("portfolio", []), columns=["Ticker"]), num_rows="dynamic", use_container_width=True, hide_index=True)
    with col2: edit_watch = st.data_editor(pd.DataFrame(data.get("watchlist", []), columns=["Ticker"]), num_rows="dynamic", use_container_width=True, hide_index=True)
    st.markdown("---")
    if st.button(_["commit"], use_container_width=True):
        data["portfolio"] = [t.strip().upper() for t in edit_port["Ticker"].dropna().astype(str).tolist() if t.strip()]
        data["watchlist"] = [t.strip().upper() for t in edit_watch["Ticker"].dropna().astype(str).tolist() if t.strip()]
        save_data(data)
        st.success(_["success"])
