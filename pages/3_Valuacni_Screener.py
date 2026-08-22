import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os
import sys
import plotly.graph_objects as go

# --- INITIAL SETUP ---
st.set_page_config(page_title="POKORNY TERMINAL | VALUATION", layout="wide", initial_sidebar_state="collapsed")

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
        "title": "FUNDAMENTY & VALUACE",
        "desc": "HLOUBKOVÝ SCREENER FINANČNÍCH VÝKAZŮ A UKAZATELŮ.",
        "db_select": "DATABÁZE",
        "custom_tick": "VLASTNÍ TICKER",
        "loading": "STAHOVÁNÍ VÝKAZŮ...",
        "err_data": "DATA PRO TENTO TICKER NEJSOU DOSTUPNÁ."
    },
    "EN": {
        "title": "FUNDAMENTALS & VALUATION",
        "desc": "IN-DEPTH FINANCIAL STATEMENT AND RATIO SCREENER.",
        "db_select": "DATABASE",
        "custom_tick": "CUSTOM TICKER",
        "loading": "LOADING STATEMENTS...",
        "err_data": "DATA FOR THIS TICKER NOT AVAILABLE."
    }
}
_ = t.get(st.session_state.get("lang", "CZ"), t["CZ"])

st.title(_["title"])
st.caption(_["desc"])
st.markdown("---")

def load_data():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list): return {"portfolio": data, "watchlist": []}
                return data
        except: pass
    return {"portfolio": ["AAPL", "MSFT", "AMAT", "GOOGL"], "watchlist": []}

data = load_data()
all_tickers = list(dict.fromkeys(data.get("portfolio", []) + data.get("watchlist", [])))

# --- OVLÁDACÍ PANEL ---
c1, c2, c3 = st.columns([2, 2, 4])
sel_tick = c1.selectbox(_["db_select"], [""] + all_tickers)
custom_tick = c2.text_input(_["custom_tick"], value="")

final_tick = custom_tick.upper().strip() if custom_tick.strip() else sel_tick

if final_tick:
    with st.spinner(f"{_['loading']} {final_tick}..."):
        tkr = yf.Ticker(final_tick)
        info = tkr.info
        financials = tkr.financials
        
        # Získání metrik
        short_name = info.get("shortName", final_tick)
        pe = info.get("trailingPE")
        fwd_pe = info.get("forwardPE")
        peg = info.get("pegRatio")
        pb = info.get("priceToBook")
        ev_ebitda = info.get("enterpriseToEbitda")
        roe = info.get("returnOnEquity")
        roa = info.get("returnOnAssets")
        profit_margin = info.get("profitMargins")
        debt_eq = info.get("debtToEquity")
        
    if info:
        st.subheader(f"METRIKY: {short_name} ({final_tick})")
        
        # --- TABULKA VALUACE A RENTABILITY ---
        col1, col2, col3, col4 = st.columns(4)
        
        # Formátování metrik
        def fmt(val, is_pct=False):
            if val is None: return "N/A"
            if is_pct: return f"{val*100:.2f}%"
            return f"{val:.2f}"
            
        col1.metric("P/E (Trailing)", fmt(pe))
        col1.metric("Forward P/E", fmt(fwd_pe))
        
        col2.metric("PEG Ratio", fmt(peg))
        col2.metric("EV / EBITDA", fmt(ev_ebitda))
        
        col3.metric("Price / Book", fmt(pb))
        col3.metric("Debt / Equity", fmt(debt_eq))
        
        col4.metric("ROE (Rentabilita vl. jmění)", fmt(roe, True))
        col4.metric("Profit Margin (Čistá marže)", fmt(profit_margin, True))
        
        st.markdown("---")
        
        # --- VÝKAZ ZISKŮ A ZTRÁT (BAR CHART) ---
        st.subheader("VÝVOJ TRŽEB A ZISKU (Roční výkazy)")
        
        if not financials.empty:
            try:
                # Očištění dat z výkazů
                rev = financials.loc['Total Revenue'].dropna()[::-1]
                net_inc = financials.loc['Net Income'].dropna()[::-1]
                
                years = [str(date.year) for date in rev.index]
                
                fig = go.Figure()
                
                # Sloupce pro tržby (Modrá)
                fig.add_trace(go.Bar(
                    x=years, y=rev, name='Total Revenue (Tržby)', marker_color='#2962FF'
                ))
                
                # Sloupce pro čistý zisk (Zelená)
                fig.add_trace(go.Bar(
                    x=years, y=net_inc, name='Net Income (Čistý zisk)', marker_color='#26A69A'
                ))
                
                fig.update_layout(
                    template="plotly_dark",
                    barmode='group',
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=450,
                    hovermode='x unified',
                    yaxis=dict(fixedrange=False, showgrid=True, gridcolor='#2B2B2B'),
                    xaxis=dict(fixedrange=False, showgrid=False)
                )
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            except Exception as e:
                st.caption("Finanční výkazy pro tento ticker nejsou dostupné ve správném formátu.")
        else:
            st.caption("Data z výkazů chybí.")
            
    else:
        st.error(_["err_data"])
