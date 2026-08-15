import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os

st.set_page_config(page_title="Valuační Screener", page_icon="📊", layout="wide")

if "lang" not in st.session_state:
    st.session_state.lang = "CZ"

selected_lang = st.sidebar.radio("🌐 Jazyk / Language:", ["CZ", "EN"], index=0 if st.session_state.lang == "CZ" else 1)
if selected_lang != st.session_state.lang:
    st.session_state.lang = selected_lang
    st.rerun()

t = {
    "CZ": {
        "title": "📊 Valuační Screener",
        "desc": "Rychlé srovnání fundamentů a valuací (Zelená = Levné/Dobré, Červená = Drahé/Slabé).",
        "btn_val": "Spustit Valuační Skenování (Bude trvat pár vteřin)",
        "spin_val": "Stahuji data z finančních výkazů...",
        "cap_val": "💡 Vysvětlivka: U P/E a PEG je lepší nižší hodnota (zelená). U Marží je lepší vyšší hodnota (zelená)."
    },
    "EN": {
        "title": "📊 Valuation Screener",
        "desc": "Quick fundamental and valuation comparison (Green = Cheap/Strong, Red = Expensive/Weak).",
        "btn_val": "Run Valuation Scan (Takes a few seconds)",
        "spin_val": "Downloading data from financial statements...",
        "cap_val": "💡 Note: Lower values are better for P/E & PEG (Green). Higher values are better for Margins (Green)."
    }
}
_ = t[st.session_state.lang]

st.title(_["title"])
st.markdown(_["desc"])

WATCHLIST_FILE = "watchlist.json"
try:
    with open(WATCHLIST_FILE, "r") as f:
        data = json.load(f)
        my_tickers = list(set(data.get("portfolio", []) + data.get("watchlist", [])))
except Exception:
    my_tickers = ["AAPL", "MSFT", "AMAT"]

if st.button(_["btn_val"]):
    with st.spinner(_["spin_val"]):
        val_data = []
        for tkr in my_tickers:
            try:
                info = yf.Ticker(tkr).info
                val_data.append({
                    "Ticker": tkr,
                    "P/E (Current)": info.get("trailingPE", None),
                    "Forward P/E": info.get("forwardPE", None),
                    "PEG Ratio": info.get("pegRatio", None),
                    "EV/EBITDA": info.get("enterpriseToEbitda", None),
                    "Gross Margin %": info.get("grossMargins", 0) * 100 if info.get("grossMargins") else None,
                    "Profit Margin %": info.get("profitMargins", 0) * 100 if info.get("profitMargins") else None,
                })
            except Exception:
                continue
        
        if val_data:
            df_val = pd.DataFrame(val_data).set_index("Ticker")
            formatted_df = df_val.style.format(precision=2) \
                .background_gradient(subset=["P/E (Current)", "Forward P/E", "PEG Ratio", "EV/EBITDA"], cmap="RdYlGn_r") \
                .background_gradient(subset=["Gross Margin %", "Profit Margin %"], cmap="RdYlGn")
            
            st.dataframe(formatted_df, use_container_width=True)
            st.caption(_["cap_val"])
