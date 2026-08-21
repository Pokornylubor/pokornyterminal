import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os
import sys
import requests
import base64

# --- CENTRÁLNÍ PAMĚŤ A MENU ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)
WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")

st.set_page_config(page_title="Opční Radar", page_icon="🎲", layout="wide")
import menu
menu.vykresli_menu()

t = {
    "CZ": {
        "title": "🎲 Opční Sentiment & Zdi", "desc": "Univerzální radar pro hledání opčních zdí 'Smart Money'.",
        "sel_port": "💼 Moje pozice:", "sel_watch": "👀 Můj Watchlist:", "search_lbl": "🔍 Vyhledat akcii:",
        "btn_add_port": "💼 Uložit do Portfolia", "btn_add_watch": "👀 Uložit do Watchlistu", "succ_add": "✅ Uloženo a posláno do cloudu!",
        "btn_opt": "Stáhnout Opce pro {}", "spin_opt": "Analyzuji řetězec...", "warn_opt": "Žádná opční data.",
        "exp": "📅 Expirace:", "call_open": "Otevřené Call", "put_open": "Otevřené Put",
        "bear": "🔴 Bearish", "bull": "🟢 Bullish", "pcr": "Put/Call Ratio",
        "walls_h": "### 🧱 Opční zdi", "call_w": "📈 Nejsilnější Call Wall: ${}", "put_w": "📉 Nejsilnější Put Wall: ${}", "err_opt": "Chyba:"
    },
    "EN": {
        "title": "🎲 Options Sentiment & Walls", "desc": "Universal radar for finding 'Smart Money' option walls.",
        "sel_port": "💼 My Portfolio:", "sel_watch": "👀 My Watchlist:", "search_lbl": "🔍 Search ticker:",
        "btn_add_port": "💼 Add to Portfolio", "btn_add_watch": "👀 Add to Watchlist", "succ_add": "✅ Saved and synced!",
        "btn_opt": "Download Options for {}", "spin_opt": "Analyzing chain...", "warn_opt": "No options data.",
        "exp": "📅 Expiration:", "call_open": "Open Calls", "put_open": "Open Puts",
        "bear": "🔴 Bearish", "bull": "🟢 Bullish", "pcr": "Put/Call Ratio",
        "walls_h": "### 🧱 Option Walls", "call_w": "📈 Strongest Call Wall: ${}", "put_w": "📉 Strongest Put Wall: ${}", "err_opt": "Error:"
    }
}
_ = t.get(st.session_state.lang, t["CZ"])

st.title(_["title"])
st.markdown(_["desc"])

def save_data(data):
    with open(WATCHLIST_FILE, "w") as f: json.dump(data, f, indent=4)
    try:
        if "GITHUB_TOKEN" in st.secrets:
            token, owner, repo = st.secrets["GITHUB_TOKEN"], st.secrets["GITHUB_OWNER"], st.secrets["GITHUB_REPO"]
            url, headers = f"https://api.github.com/repos/{owner}/{repo}/contents/watchlist.json", {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
            sha = requests.get(url, headers=headers).json().get("sha")
            payload = {"message": "Cloud sync z Opcniho Radaru", "content": base64.b64encode(json.dumps(data, indent=4).encode("utf-8")).decode("utf-8"), "branch": "main"}
            if sha: payload["sha"] = sha
            requests.put(url, headers=headers, json=payload)
    except Exception: pass

def load_data():
    try:
        with open(WATCHLIST_FILE, "r") as f: return json.load(f)
    except: return {"portfolio": [], "watchlist": []}

data = load_data()
port_tickers = sorted(list(set(data.get("portfolio", []))))
watch_tickers = sorted(list(set(data.get("watchlist", []))))

st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1: vyber_port = st.selectbox(_["sel_port"], ["---"] + port_tickers)
with col2: vyber_watch = st.selectbox(_["sel_watch"], ["---"] + watch_tickers)
with col3: hledany_ticker = st.text_input(_["search_lbl"]).strip().upper()

vybrany_ticker = hledany_ticker if hledany_ticker else (vyber_watch if vyber_watch != "---" else (vyber_port if vyber_port != "---" else None))

if hledany_ticker:
    c1, c2, c3 = st.columns([1, 1, 2])
    if hledany_ticker not in data.get("portfolio", []) and c1.button(_["btn_add_port"]):
        data.setdefault("portfolio", []).append(hledany_ticker)
        save_data(data); st.success(_["succ_add"]); st.rerun()
    if hledany_ticker not in data.get("watchlist", []) and c2.button(_["btn_add_watch"]):
        data.setdefault("watchlist", []).append(hledany_ticker)
        save_data(data); st.success(_["succ_add"]); st.rerun()

@st.cache_data(ttl=900, show_spinner=False)
def fetch_options_cached(ticker):
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"})
    tkr_obj = yf.Ticker(ticker, session=session)
    expirations = tkr_obj.options
    if not expirations: return None, None, None
    nearest_exp = expirations[0]
    chain = tkr_obj.option_chain(nearest_exp)
    return nearest_exp, chain.calls, chain.puts

if vybrany_ticker and st.button(_["btn_opt"].format(vybrany_ticker), type="primary"):
    with st.spinner(_["spin_opt"]):
        try:
            nearest_exp, calls, puts = fetch_options_cached(vybrany_ticker)
            if nearest_exp is None: st.warning(_["warn_opt"])
            else:
                total_call_oi, total_put_oi = calls['openInterest'].sum(), puts['openInterest'].sum()
                pcr_oi = total_put_oi / total_call_oi if total_call_oi > 0 else 0
                
                st.subheader(f"{_['exp']} {nearest_exp}")
                c1, c2, c3 = st.columns(3)
                c1.metric(_["call_open"], f"{int(total_call_oi):,}")
                c2.metric(_["put_open"], f"{int(total_put_oi):,}")
                c3.metric(_["pcr"], f"{pcr_oi:.2f}", _["bear"] if pcr_oi > 1 else _["bull"])
                
                if not calls.empty and not puts.empty:
                    st.markdown(_["walls_h"])
                    st.write(_["call_w"].format(calls.loc[calls['openInterest'].idxmax()]['strike']))
                    st.write(_["put_w"].format(puts.loc[puts['openInterest'].idxmax()]['strike']))
        except Exception as e:
            st.error(f"{_['err_opt']} {e}")
