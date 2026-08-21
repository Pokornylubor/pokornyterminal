import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os
import sys

# --- CENTRÁLNÍ PAMĚŤ A MENU ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)
WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")

st.set_page_config(page_title="Valuační Screener", page_icon="📊", layout="wide")
import menu
menu.vykresli_menu()

t = {
    "CZ": {"title": "📊 Valuační Screener", "desc": "Srovnání fundamentů (Zelená = Dobré, Červená = Slabé).", "btn": "Spustit Skenování"},
    "EN": {"title": "📊 Valuation Screener", "desc": "Fundamentals (Green = Good, Red = Weak).", "btn": "Run Scan"}
}
_ = t.get(st.session_state.lang, t["CZ"])

st.title(_["title"])
st.markdown(_["desc"])

try:
    with open(WATCHLIST_FILE, "r") as f:
        data = json.load(f)
        my_tickers = list(set(data.get("portfolio", []) + data.get("watchlist", [])))
except: my_tickers = ["AAPL", "MSFT", "AMAT"]

if st.button(_["btn"]):
    with st.spinner("..."):
        val_data = []
        for tkr in my_tickers:
            try:
                info = yf.Ticker(tkr).info
                val_data.append({
                    "Ticker": tkr, "P/E": info.get("trailingPE"), "Fwd P/E": info.get("forwardPE"),
                    "PEG": info.get("pegRatio"), "EV/EBITDA": info.get("enterpriseToEbitda"),
                    "Gross Margin %": info.get("grossMargins", 0) * 100 if info.get("grossMargins") else None
                })
            except: continue
        
        if val_data:
            df_val = pd.DataFrame(val_data).set_index("Ticker")
            st.dataframe(df_val.style.format(precision=2).background_gradient(subset=["P/E", "Fwd P/E", "PEG", "EV/EBITDA"], cmap="RdYlGn_r").background_gradient(subset=["Gross Margin %"], cmap="RdYlGn"), use_container_width=True)
