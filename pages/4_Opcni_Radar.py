import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os
import requests

st.set_page_config(page_title="Opční Radar", page_icon="🎲", layout="wide")

# --- CENTRÁLNÍ PEVNÁ PAMĚŤ NAPOŘÁD ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(aktualni_slozka) == "pages":
    hlavni_slozka = os.path.dirname(aktualni_slozka)
else:
    hlavni_slozka = aktualni_slozka

WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")
# -------------------------------------

if "lang" not in st.session_state:
    st.session_state.lang = "CZ"

selected_lang = st.sidebar.radio("🌐 Jazyk / Language:", ["CZ", "EN"], index=0 if st.session_state.lang == "CZ" else 1)
if selected_lang != st.session_state.lang:
    st.session_state.lang = selected_lang
    st.rerun()

t = {
    "CZ": {
        "title": "🎲 Opční Radar",
        "desc": "Opční Radar pro hledání opčních zdí.",
        "sel_port": "💼 Moje pozice:",
        "sel_watch": "👀 Můj Watchlist:",
        "search_lbl": "🔍 Vyhledat akcii :",
        "btn_add_port": "💼 Uložit do Portfolia",
        "btn_add_watch": "👀 Uložit do Watchlistu",
        "succ_add": "✅ Ticker {} přidán a uložen napořád!",
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
        "sel_port": "💼 My Portfolio:",
        "sel_watch": "👀 My Watchlist:",
        "search_lbl": "🔍 Search ticker (e.g. TSLA):",
        "btn_add_port": "💼 Add to Portfolio",
        "btn_add_watch": "👀 Add to Watchlist",
        "succ_add": "✅ Ticker {} permanently added!",
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
_ = t.get(st.session_state.lang, t["CZ"])

st.title(_["title"])
st.markdown(_["desc"])

# --- Načtení dat a rozdělení seznamů ---
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
port_tickers = sorted(list(set(data.get("portfolio", []))))
watch_tickers = sorted(list(set(data.get("watchlist", []))))

st.markdown("---")

# --- Tři sjednocené sloupce pro výběr ---
col1, col2, col3 = st.columns(3)
with col1:
    vyber_port = st.selectbox(_["sel_port"], ["--- Vyber ---"] + port_tickers)
with col2:
    vyber_watch = st.selectbox(_["sel_watch"], ["--- Vyber ---"] + watch_tickers)
with col3:
    hledany_ticker = st.text_input(_["search_lbl"], "").strip().upper()

vybrany_ticker = None
if hledany_ticker:
    vybrany_ticker = hledany_ticker
elif vyber_watch != "--- Vyber ---":
    vybrany_ticker = vyber_watch
elif vyber_port != "--- Vyber ---":
    vybrany_ticker = vyber_port

if hledany_ticker:
    st.write("") 
    c1, c2, c3 = st.columns([1, 1, 2])
    
    if hledany_ticker not in data.get("portfolio", []):
        if c1.button(_["btn_add_port"]):
            data.setdefault("portfolio", []).append(hledany_ticker)
            save_data(data)
            st.success(_["succ_add"].format(hledany_ticker))
            st.rerun()
            
    if hledany_ticker not in data.get("watchlist", []):
        if c2.button(_["btn_add_watch"]):
            data.setdefault("watchlist", []).append(hledany_ticker)
            save_data(data)
            st.success(_["succ_add"].format(hledany_ticker))
            st.rerun()

st.markdown("---")

# ==========================================
# PROFESIONÁLNÍ CACHING A MASKOVÁNÍ (PROTI YAHOO BANŮM)
# ==========================================
@st.cache_data(ttl=900, show_spinner=False)
def fetch_options_cached(ticker):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    
    tkr_obj = yf.Ticker(ticker, session=session)
    expirations = tkr_obj.options
    
    if not expirations:
        return None, None, None
    
    nearest_exp = expirations[0]
    chain = tkr_obj.option_chain(nearest_exp)
    return nearest_exp, chain.calls, chain.puts

# --- Analýza a vykreslení opcí ---
if vybrany_ticker:
    if st.button(_["btn_opt"].format(vybrany_ticker), type="primary"):
        with st.spinner(_["spin_opt"]):
            try:
                nearest_exp, calls, puts = fetch_options_cached(vybrany_ticker)
                
                if nearest_exp is None:
                    st.warning(_["warn_opt"])
                else:
                    total_call_oi = calls['openInterest'].sum()
                    total_put_oi = puts['openInterest'].sum()
                    
                    pcr_oi = total_put_oi / total_call_oi if total_call_oi > 0 else 0
                    
                    st.subheader(f"{_['exp']} {nearest_exp}")
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric(_["call_open"], f"{int(total_call_oi):,}")
                    c2.metric(_["put_open"], f"{int(total_put_oi):,}")
                    
                    sentiment = _["bear"] if pcr_oi > 1 else _["bull"]
                    c3.metric(_["pcr"], f"{pcr_oi:.2f}", sentiment)
                    
                    if not calls.empty and not puts.empty:
                        max_call_strike = calls.loc[calls['openInterest'].idxmax()]['strike']
                        max_put_strike = puts.loc[puts['openInterest'].idxmax()]['strike']
                        
                        st.markdown(_["walls_h"])
                        st.write(_["call_w"].format(max_call_strike))
                        st.write(_["put_w"].format(max_put_strike))
                    else:
                        st.write("Nedostatek dat pro výpočet opčních zdí u této expirace.")

            except Exception as e:
                if "Too Many Requests" in str(e):
                    st.error("Yahoo Finance má stále dočasně zablokovanou tvou IP. Dej si na pár minut pauzu, maskovací kód už je nasazený.")
                else:
                    st.error(f"{_['err_opt']} {e}")
