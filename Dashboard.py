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

# --- DICTIONARY ---
t = {
    "CZ": {
        "title": "POKORNY TERMINAL", "tab_port": "PORTFOLIO", "tab_watch": "WATCHLIST", 
        "tab_chart": "CHARTING", "tab_set": "SYSTÉMOVÁ KONFIGURACE", "curr_pos": "AKTUÁLNÍ POZICE", 
        "radar": "RADAR", "no_data": "ŽÁDNÁ DATA", "err": "ERR", "port_tickers": "TICKERY (PORTFOLIO)", 
        "watch_tickers": "TICKERY (WATCHLIST)", "commit": "ULOŽIT ZMĚNY", "success": "SYSTÉM AKTUALIZOVÁN",
        "db_select": "DATABÁZE", "custom_tick": "VLASTNÍ TICKER", "chart_type": "TYP GRAFU",
        "interval": "INTERVAL", "loading": "STAHOVÁNÍ DAT...", "err_data": "DATA NEJSOU DOSTUPNÁ."
    },
    "EN": {
        "title": "POKORNY TERMINAL", "tab_port": "PORTFOLIO", "tab_watch": "WATCHLIST", 
        "tab_chart": "CHARTING", "tab_set": "SYSTEM CONFIG", "curr_pos": "CURRENT POSITIONS", 
        "radar": "RADAR", "no_data": "NO DATA AVAILABLE", "err": "ERR", "port_tickers": "PORTFOLIO TICKERS", 
        "watch_tickers": "WATCHLIST TICKERS", "commit": "COMMIT CHANGES", "success": "SYSTEM UPDATED",
        "db_select": "DATABASE", "custom_tick": "CUSTOM TICKER", "chart_type": "CHART TYPE",
        "interval": "INTERVAL", "loading": "LOADING DATA...", "err_data": "DATA NOT AVAILABLE."
    }
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

tab1, tab2, tab3, tab4 = st.tabs([_["tab_port"], _["tab_watch"], _["tab_chart"], _["tab_set"]])

with tab1: display_tickers(data.get("portfolio", []), _["curr_pos"])
with tab2: display_tickers(data.get("watchlist", []), _["radar"])

with tab3:
    all_tickers = list(dict.fromkeys(data.get("portfolio", []) + data.get("watchlist", [])))
    
    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
    sel_tick = c1.selectbox(_["db_select"], [""] + all_tickers)
    custom_tick = c2.text_input(_["custom_tick"], value="")
    
    final_tick = custom_tick.upper().strip() if custom_tick.strip() else sel_tick
    
    chart_type = c3.selectbox(_["chart_type"], ["Candlestick", "Line"])
    interval_display = c4.selectbox(_["interval"], ["1M", "5M", "15M", "1H", "4H", "1D", "1W", "1MO"], index=5)

    if final_tick:
        yf_interval_map = {"1M": "1m", "5M": "5m", "15M": "15m", "1H": "1h", "4H": "1h", "1D": "1d", "1W": "1wk", "1MO": "1mo"}
        period_map = {"1m": "7d", "5m": "60d", "15m": "60d", "1h": "730d", "1d": "max", "1wk": "max", "1mo": "max"}
        
        yf_int = yf_interval_map[interval_display]
        
        with st.spinner(f"{_['loading']} {final_tick}..."):
            df_c = yf.download(final_tick, period=period_map[yf_int], interval=yf_int, progress=False)
            
        if not df_c.empty:
            if isinstance(df_c.columns, pd.MultiIndex): df_c.columns = df_c.columns.get_level_values(0)
            
            if interval_display == "4H":
                df_c = df_c.resample('4h').agg({
                    'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'
                }).dropna()

            fig = go.Figure()
            if chart_type == "Candlestick":
                fig.add_trace(go.Candlestick(
                    x=df_c.index, open=df_c['Open'], high=df_c['High'], low=df_c['Low'], close=df_c['Close'], 
                    name=final_tick,
                    increasing_line_color='#26A69A', decreasing_line_color='#EF5350'
                ))
            else:
                fig.add_trace(go.Scatter(x=df_c.index, y=df_c['Close'], mode='lines', line=dict(color='#2962FF'), name=final_tick))
            
            fig.update_layout(
                template="plotly_dark", 
                margin=dict(l=0, r=60, t=20, b=0), 
                height=650, 
                xaxis_rangeslider_visible=False,
                dragmode='pan',
                hovermode='x', # Změna pro správné uchycení kříže na konkrétní svíčku
                yaxis=dict(
                    side='right', 
                    fixedrange=False, 
                    tickformat=".2f",
                    showspikes=True,
                    spikemode='across',
                    spikethickness=1,
                    spikedash='solid',
                    spikecolor='#787B86'
                ),
                xaxis=dict(
                    fixedrange=False, 
                    showgrid=False,
                    showspikes=True,
                    spikemode='across',
                    spikethickness=1,
                    spikedash='solid',
                    spikecolor='#787B86'
                )
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})
            
            # --- VALUACE A FUNDAMENTY ---
            st.markdown("---")
            st.subheader(f"FUNDAMENTY & VALUACE: {final_tick}")
            
            try:
                tkr = yf.Ticker(final_tick)
                info = tkr.info
                
                v1, v2, v3, v4, v5, v6 = st.columns(6)
                
                pe = info.get('trailingPE')
                f_pe = info.get('forwardPE')
                peg = info.get('pegRatio')
                pb = info.get('priceToBook')
                mc = info.get('marketCap')
                pm = info.get('profitMargins')
                
                v1.metric("P/E (Trailing)", f"{pe:.2f}" if pe else "N/A")
                v2.metric("Forward P/E", f"{f_pe:.2f}" if f_pe else "N/A")
                v3.metric("PEG Ratio", f"{peg:.2f}" if peg else "N/A")
                v4.metric("Price / Book", f"{pb:.2f}" if pb else "N/A")
                v5.metric("Market Cap", f"${mc/1e9:.2f}B" if mc else "N/A")
                v6.metric("Profit Margin", f"{pm*100:.2f}%" if pm else "N/A")
            except:
                st.caption("Data o valuaci nejsou pro tento ticker aktuálně k dispozici.")
                
        else:
            st.error(_["err_data"])

with tab4:
    col1, col2 = st.columns(2)
    with col1: 
        port_text = st.text_area(_["port_tickers"], "\n".join(data.get("portfolio", [])), height=300)
    with col2: 
        watch_text = st.text_area(_["watch_tickers"], "\n".join(data.get("watchlist", [])), height=300)
        
    st.markdown("---")
    if st.button(_["commit"], use_container_width=True):
        data["portfolio"] = [t.strip().upper() for t in port_text.split('\n') if t.strip()]
        data["watchlist"] = [t.strip().upper() for t in watch_text.split('\n') if t.strip()]
        save_data(data)
        st.success(_["success"])
