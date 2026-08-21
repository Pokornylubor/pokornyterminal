import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import os
import sys
from io import StringIO

# --- CENTRÁLNÍ PAMĚŤ A MENU ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)
WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")

st.set_page_config(page_title="Insider Tracker", page_icon="🕵️‍♂️", layout="wide")
import menu
menu.vykresli_menu()

t = {
    "CZ": {"title": "🕵️‍♂️ Insider Tracker", "desc": "4F reporty - nákupy a prodeje insiderů", "port": "💼 Moje pozice:", "watch": "👀 Můj Watchlist:", "search": "🔍 Vyhledat akcii:", "btn": "Stáhnout Insidery pro {}", "spin": "Stahuji data...", "succ": "✅ Data úspěšně nalezena!"},
    "EN": {"title": "🕵️‍♂️ Insider Tracker", "desc": "Form 4 reports - Insider activity", "port": "💼 My Portfolio:", "watch": "👀 My Watchlist:", "search": "🔍 Search ticker:", "btn": "Download Insiders for {}", "spin": "Downloading data...", "succ": "✅ Data successfully found!"}
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

col1, col2, col3 = st.columns(3)
with col1: vyber_port = st.selectbox(_["port"], ["--- Vyber ---"] + port_tickers)
with col2: vyber_watch = st.selectbox(_["watch"], ["--- Vyber ---"] + watch_tickers)
with col3: hledany_ticker = st.text_input(_["search"]).strip().upper()

aktualni_ticker = hledany_ticker if hledany_ticker else (vyber_watch if vyber_watch != "--- Vyber ---" else (vyber_port if vyber_port != "--- Vyber ---" else None))

if aktualni_ticker:
    if st.button(_["btn"].format(aktualni_ticker), type="primary"):
        with st.spinner(_["spin"]):
            url = f"http://openinsider.com/search?q={aktualni_ticker}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, 'html.parser')
                table = soup.find('table', {'class': 'tinytable'})
                if table:
                    try:
                        dfs = pd.read_html(StringIO(str(table)))
                        if dfs:
                            df = dfs[0]
                            clean_df = df.iloc[:, [2, 4, 5, 6, 7, 8, 11]].copy()
                            clean_df.columns = ["Datum", "Jméno", "Pozice", "Typ", "Cena ($)", "Kusy", "Hodnota (USD)"]
                            
                            # Bezpečný převod čísel - pokud je tam nesmysl, hodí prázdné políčko místo pádu aplikace
                            clean_df["Cena ($)"] = pd.to_numeric(clean_df["Cena ($)"].astype(str).str.replace('[\$,]', '', regex=True), errors='coerce')
                            clean_df["Hodnota (USD)"] = pd.to_numeric(clean_df["Hodnota (USD)"].astype(str).str.replace('[\$,]', '', regex=True), errors='coerce')
                            clean_df["Kusy"] = pd.to_numeric(clean_df["Kusy"].astype(str).str.replace(',', '').str.replace('+', ''), errors='coerce')
                            
                            def preloz_typ(val):
                                v = str(val).lower()
                                if "purchase" in v or "p - " in v: return "🟢 BUY" if st.session_state.lang == "EN" else "🟢 NÁKUP"
                                if "sale" in v or "s - " in v: return "🔴 SELL" if st.session_state.lang == "EN" else "🔴 PRODEJ"
                                return val
                            clean_df["Typ"] = clean_df["Typ"].apply(preloz_typ)
                            st.success(_["succ"])
                            
                            def style_trade(val):
                                if "🟢" in str(val): return 'color: #00ff00; font-weight: bold;'
                                if "🔴" in str(val): return 'color: #ff4b4b; font-weight: bold;'
                                return 'color: gray;'

                            # na_rep="-" zajistí, že prázdná/vadná políčka se zobrazí jako pomlčka
                            st.dataframe(clean_df.style.format({"Cena ($)": "${:,.2f}", "Kusy": "{:,.0f}", "Hodnota (USD)": "${:,.0f}"}, na_rep="-").map(style_trade, subset=["Typ"]), use_container_width=True)
                    except Exception as e: 
                        st.error(f"Chyba při zpracování dat z tabulky: {e}")
                else: 
                    st.info("Žádná data nebyly nalezeny pro tento ticker.")
            else: 
                st.error(f"Nelze se připojit na OpenInsider (Status kód: {res.status_code})")
