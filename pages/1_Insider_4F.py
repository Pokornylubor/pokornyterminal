import streamlit as st
import pandas as pd
import json
import os
import sys

# --- CENTRÁLNÍ PAMĚŤ A MENU ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)
WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")
FILE_PATH = os.path.join(hlavni_slozka, "insider_4f_db.csv")

st.set_page_config(page_title="Insider Tracker", page_icon="🕵️‍♂️", layout="wide")
import menu
menu.vykresli_menu()

t = {
    "CZ": {"title": "🕵️‍♂️ Insider Tracker (Offline DB)", "desc": "4F reporty - bleskové vyhledávání v lokální databázi.", "port": "💼 Moje pozice:", "watch": "👀 Můj Watchlist:", "search": "🔍 Vyhledat akcii:"},
    "EN": {"title": "🕵️‍♂️ Insider Tracker (Offline DB)", "desc": "Form 4 reports - lightning fast search in local database.", "port": "💼 My Portfolio:", "watch": "👀 My Watchlist:", "search": "🔍 Search ticker:"}
}
_ = t.get(st.session_state.lang, t["CZ"])

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r") as f: return json.load(f)
        except: pass
    return {"portfolio": [], "watchlist": []}

data = load_watchlist()
port_tickers = sorted(list(set(data.get("portfolio", []))))
watch_tickers = sorted(list(set(data.get("watchlist", []))))

st.title(_["title"])
st.markdown(_["desc"])
st.markdown("---")

if not os.path.exists(FILE_PATH):
    st.warning("⚠️ Databáze insider_4f_db.csv nebyla nalezena. Spusť nejprve updater.py.")
else:
    df_all = pd.read_csv(FILE_PATH)
    
    col1, col2, col3 = st.columns(3)
    with col1: vyber_port = st.selectbox(_["port"], ["--- Vyber ---"] + port_tickers)
    with col2: vyber_watch = st.selectbox(_["watch"], ["--- Vyber ---"] + watch_tickers)
    with col3: hledany_ticker = st.text_input(_["search"]).strip().upper()

    aktualni_ticker = hledany_ticker if hledany_ticker else (vyber_watch if vyber_watch != "--- Vyber ---" else (vyber_port if vyber_port != "--- Vyber ---" else None))

    if aktualni_ticker:
        # Blesková filtrace tickeru z CSV
        df_filtered = df_all[df_all['Ticker'] == aktualni_ticker].copy()
        
        if df_filtered.empty:
            st.info(f"Žádná nedávná data pro {aktualni_ticker} v databázi.")
        else:
            # Převedeme číselné sloupce na správný formát pro barvičky
            for col in ['Price', 'Qty', 'Value']:
                if col in df_filtered.columns:
                    df_filtered[col] = pd.to_numeric(df_filtered[col].astype(str).str.replace('[\$,+]', '', regex=True), errors='coerce')
            
            def preloz_typ(val):
                v = str(val).lower()
                if "purchase" in v or "p - " in v: return "🟢 BUY" if st.session_state.lang == "EN" else "🟢 NÁKUP"
                if "sale" in v or "s - " in v: return "🔴 SELL" if st.session_state.lang == "EN" else "🔴 PRODEJ"
                if "option" in v or "oe - " in v: return "⚪ OPCE"
                return val
            
            if 'Trade Type' in df_filtered.columns:
                df_filtered['Trade Type'] = df_filtered['Trade Type'].apply(preloz_typ)
            
            def style_trade(val):
                if "🟢" in str(val): return 'color: #00ff00; font-weight: bold;'
                if "🔴" in str(val): return 'color: #ff4b4b; font-weight: bold;'
                return 'color: gray;'
            
            format_dict = {}
            if 'Price' in df_filtered.columns: format_dict['Price'] = "${:,.2f}"
            if 'Qty' in df_filtered.columns: format_dict['Qty'] = "{:,.0f}"
            if 'Value' in df_filtered.columns: format_dict['Value'] = "${:,.0f}"
            
            st.success(f"✅ Bleskově načteno z lokální databáze!")
            st.dataframe(df_filtered.style.format(format_dict, na_rep="-").map(style_trade, subset=['Trade Type'] if 'Trade Type' in df_filtered.columns else []), use_container_width=True, height=600)
