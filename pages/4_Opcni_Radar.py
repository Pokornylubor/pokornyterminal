import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os

st.set_page_config(page_title="Opční Radar", page_icon="🎲", layout="wide")

if "lang" not in st.session_state:
    st.session_state.lang = "CZ"

selected_lang = st.sidebar.radio("🌐 Jazyk / Language:", ["CZ", "EN"], index=0 if st.session_state.lang == "CZ" else 1)
if selected_lang != st.session_state.lang:
    st.session_state.lang = selected_lang
    st.rerun()

t = {
    "CZ": {
        "title": "🎲 Opční Sentiment & Zdi",
        "desc": "Sleduje nejbližší expiraci opcí a zkoumá, kde má 'Smart Money' zaparkováno nejvíce kapitálu.",
        "sel_tkr": "Vyber akcii pro opční analýzu:",
        "btn_opt": "Stáhnout Opce pro {}",
        "spin_opt": "Analyzuji opční řetězec...",
        "warn_opt": "Pro tuto akcii nejsou k dispozici žádná opční data.",
        "exp": "📅 Expirace:",
        "call_open": "Otevřené Call (Růst)",
        "put_open": "Otevřené Put (Pokles)",
        "bear": "🔴 Bearish (Pád)",
        "bull": "🟢 Bullish (Růst)",
        "pcr": "Put/Call Ratio (OI)",
        "walls_h": "### 🧱 Opční zdi (Kde leží největší peníze)",
        "call_w": "📈 **Nejsilnější odpor (Call Wall):** ${} (Pravděpodobně nepřekročí)",
        "put_w": "📉 **Nejsilnější podpora (Put Wall):** ${} (Pravděpodobně nespadne pod)",
        "err_opt": "Při stahování opcí nastala chyba:"
    },
    "EN": {
        "title": "🎲 Options Sentiment & Walls",
        "desc": "Tracks nearest options expiration to see where 'Smart Money' parked their capital.",
        "sel_tkr": "Select a stock for options analysis:",
        "btn_opt": "Download Options for {}",
        "spin_opt": "Analyzing option chain...",
        "warn_opt": "No options data available for this stock.",
        "exp": "📅 Expiration:",
        "call_open": "Open Calls (Bullish)",
        "put_open": "Open Puts (Bearish)",
        "bear": "🔴 Bearish (Drop)",
        "bull": "🟢 Bullish (Rise)",
        "pcr": "Put/Call Ratio (OI)",
        "walls_h": "### 🧱 Option Walls (Where the biggest money lies)",
        "call_w": "📈 **Strongest Resistance (Call Wall):** ${} (Unlikely to cross)",
        "put_w": "📉 **Strongest Support (Put Wall):** ${} (Unlikely to drop below)",
        "err_opt": "Error occurred while downloading options:"
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

vybrany_ticker = st.selectbox(_["sel_tkr"], sorted(my_tickers))

if st.button(_["btn_opt"].format(vybrany_ticker)):
    with st.spinner(_["spin_opt"]):
        try:
            tkr_obj = yf.Ticker(vybrany_ticker)
            expirations = tkr_obj.options
            
            if not expirations:
                st.warning(_["warn_opt"])
            else:
                nearest_exp = expirations[0]
                chain = tkr_obj.option_chain(nearest_exp)
                
                calls = chain.calls
                puts = chain.puts
                
                total_call_vol = calls['volume'].sum()
                total_put_vol = puts['volume'].sum()
                total_call_oi = calls['openInterest'].sum()
                total_put_oi = puts['openInterest'].sum()
                
                pcr_oi = total_put_oi / total_call_oi if total_call_oi > 0 else 0
                
                st.subheader(f"{_['exp']} {nearest_exp}")
                
                col1, col2, col3 = st.columns(3)
                col1.metric(_["call_open"], f"{int(total_call_oi):,}")
                col2.metric(_["put_open"], f"{int(total_put_oi):,}")
                
                sentiment = _["bear"] if pcr_oi > 1 else _["bull"]
                col3.metric(_["pcr"], f"{pcr_oi:.2f}", sentiment)
                
                max_call_strike = calls.loc[calls['openInterest'].idxmax()]['strike']
                max_put_strike = puts.loc[puts['openInterest'].idxmax()]['strike']
                
                st.markdown(_["walls_h"])
                st.write(_["call_w"].format(max_call_strike))
                st.write(_["put_w"].format(max_put_strike))

        except Exception as e:
            st.error(f"{_['err_opt']} {e}")
