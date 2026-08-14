import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os

st.set_page_config(page_title="Valuation & Options", page_icon="🔎", layout="wide")

if "lang" not in st.session_state:
    st.session_state.lang = "CZ"

selected_lang = st.sidebar.radio("🌐 Jazyk / Language:", ["CZ", "EN"], index=0 if st.session_state.lang == "CZ" else 1)
if selected_lang != st.session_state.lang:
    st.session_state.lang = selected_lang
    st.rerun()

t = {
    "CZ": {
        "title": "🔎 Valuační Rentgen & Opční Sentiment",
        "desc": "Hloubková analýza fundamentů a sledování 'Smart Money' přes opční řetězce.",
        "sec1_h": "📊 1. Fundamentální Screener",
        "sec1_d": "Rychlé srovnání valuací (Zelená = Levné/Dobré, Červená = Drahé/Slabé)",
        "btn_val": "Spustit Valuační Skenování (Bude trvat pár vteřin)",
        "spin_val": "Stahuji data z finančních výkazů...",
        "cap_val": "💡 Vysvětlivka: U P/E a PEG je lepší nižší hodnota (zelená). U Marží je lepší vyšší hodnota (zelená).",
        "sec2_h": "🎲 2. Opční Sentiment (Put/Call Ratio)",
        "sec2_d": "Sleduje nejbližší expiraci opcí a zkoumá, kde je 'zaparkováno' nejvíce peněz.",
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
        "title": "🔎 Valuation X-Ray & Options Sentiment",
        "desc": "In-depth fundamental analysis and 'Smart Money' tracking via option chains.",
        "sec1_h": "📊 1. Fundamental Screener",
        "sec1_d": "Quick valuation comparison (Green = Cheap/Strong, Red = Expensive/Weak)",
        "btn_val": "Run Valuation Scan (Takes a few seconds)",
        "spin_val": "Downloading data from financial statements...",
        "cap_val": "💡 Note: Lower values are better for P/E & PEG (Green). Higher values are better for Margins (Green).",
        "sec2_h": "🎲 2. Options Sentiment (Put/Call Ratio)",
        "sec2_d": "Tracks nearest options expiration and examines where money is 'parked'.",
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
        "call_w": "📈 **Strongest Resistance (Call Wall):** ${} (Unlikely to cross by Friday)",
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

st.header(_["sec1_h"])
st.markdown(_["sec1_d"])

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

st.markdown("---")
st.header(_["sec2_h"])
st.markdown(_["sec2_d"])

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