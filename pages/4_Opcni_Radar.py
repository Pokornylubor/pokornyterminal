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
        "desc": "Univerzální radar pro hledání opčních zdí 'Smart Money'. Vyhledej jakoukoliv akcii nebo vyber ze svých seznamů.",
        "h_univ": "🔍 Univerzální vyhledávač",
        "search_lbl": "Napiš jakýkoliv Ticker (např. TSLA, PLTR):",
        "btn_add_port": "💼 Přidat do Portfolia",
        "btn_add_watch": "👀 Přidat do Watchlistu",
        "succ_add": "✅ Ticker {} přidán!",
        "h_watch": "📂 Moje seznamy",
        "sel_tkr": "Rychlý výběr z mých akcií:",
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
        "desc": "Universal radar for finding 'Smart Money' option walls. Search any stock or select from your lists.",
        "h_univ": "🔍 Universal Search",
        "search_lbl": "Type any Ticker (e.g. TSLA, PLTR):",
        "btn_add_port": "💼 Add to Portfolio",
        "btn_add_watch": "👀 Add to Watchlist",
        "succ_add": "✅ Ticker {} added!",
        "h_watch": "📂 My Lists",
        "sel_tkr": "Quick select from my stocks:",
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

# --- Načtení dat ---
def load_data():
    try:
        with open(WATCHLIST_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"portfolio": [], "watchlist": [], "superinvestors": [], "cot_watchlist": []}

def save_data(data):
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()
my_tickers = list(set(data.get("portfolio", []) + data.get("watchlist", [])))

col1, col2 = st.columns(2)
vybrany_ticker = None

with col1:
    st.markdown(f"### {_['h_univ']}")
    search_tkr = st.text_input(_["search_lbl"], "").strip().upper()
    
    if search_tkr:
        vybrany_ticker = search_tkr
        
        # Tlačítka pro rychlé přidání, pokud ticker ještě nemáme uložený
        if search_tkr not in data.get("portfolio", []):
            if st.button(_["btn_add_port"]):
                data.setdefault("portfolio", []).append(search_tkr)
                save_data(data)
                st.success(_["succ_add"].format(search_tkr))
                st.rerun()
                
        if search_tkr not in data.get("watchlist", []):
            if st.button(_["btn_add_watch"]):
                data.setdefault("watchlist", []).append(search_tkr)
                save_data(data)
                st.success(_["succ_add"].format(search_tkr))
                st.rerun()

with col2:
    st.markdown(f"### {_['h_watch']}")
    if my_tickers:
        combo_tkr = st.selectbox(_["sel_tkr"], ["--- Vyber ---"] + sorted(my_tickers))
        if combo_tkr != "--- Vyber ---":
            # Pokud uživatel zrovna nic nehledá textem, použijeme výběr ze seznamu
            if not search_tkr: 
                vybrany_ticker = combo_tkr

st.markdown("---")

# --- Analýza a vykreslení opcí ---
if vybrany_ticker:
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
                    
                    total_call_oi = calls['openInterest'].sum()
                    total_put_oi = puts['openInterest'].sum()
                    
                    pcr_oi = total_put_oi / total_call_oi if total_call_oi > 0 else 0
                    
                    st.subheader(f"{_['exp']} {nearest_exp}")
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric(_["call_open"], f"{int(total_call_oi):,}")
                    c2.metric(_["put_open"], f"{int(total_put_oi):,}")
                    
                    sentiment = _["bear"] if pcr_oi > 1 else _["bull"]
                    c3.metric(_["pcr"], f"{pcr_oi:.2f}", sentiment)
                    
                    max_call_strike = calls.loc[calls['openInterest'].idxmax()]['strike']
                    max_put_strike = puts.loc[puts['openInterest'].idxmax()]['strike']
                    
                    st.markdown(_["walls_h"])
                    st.write(_["call_w"].format(max_call_strike))
                    st.write(_["put_w"].format(max_put_strike))

            except Exception as e:
                st.error(f"{_['err_opt']} {e}")
