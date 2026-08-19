import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import os

st.set_page_config(page_title="Insider Tracker", page_icon="🕵️‍♂️", layout="wide")

WATCHLIST_FILE = "watchlist.json"

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, "r") as f:
            return json.load(f)
    return {"portfolio": [], "watchlist": []}

data = load_watchlist()
my_tickers = list(set(data.get("portfolio", []) + data.get("watchlist", [])))

st.title("🕵️‍♂️ Insider Tracker (Live)")
st.markdown("Vyber si akcii ze svého seznamu, nebo vyhledej jakýkoliv ticker. Data se stáhnou živě z OpenInsider.")

col1, col2 = st.columns(2)
with col1:
    vyber_ticker = st.selectbox("Vyber akcii z Portfolia / Watchlistu:", ["--- Vyber ---"] + sorted(my_tickers))
with col2:
    hledany_ticker = st.text_input("🔍 Nebo napiš jiný Ticker (např. MSFT, PLTR):").strip().upper()

# Určíme, jaký ticker se má hledat
aktualni_ticker = None
if hledany_ticker:
    aktualni_ticker = hledany_ticker
elif vyber_ticker != "--- Vyber ---":
    aktualni_ticker = vyber_ticker

if aktualni_ticker:
    if st.button(f"Stáhnout Insidery pro {aktualni_ticker}", type="primary"):
        with st.spinner("Stahuji data o insiderech..."):
            # Přímé vyhledání na OpenInsider
            url = f"http://openinsider.com/search?q={aktualni_ticker}"
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(url, headers=headers)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, 'html.parser')
                table = soup.find('table', {'class': 'tinytable'})
                
                if table:
                    # Rozluštění tabulky přes Pandas (umí číst HTML tabulky!)
                    dfs = pd.read_html(str(table))
                    if dfs:
                        df = dfs[0]
                        # Vezmeme jen to nejdůležitější, co nás zajímá
                        try:
                            # Názvy sloupců z OpenInsider se občas mění, bereme to bezpečně přes indexy
                            clean_df = df.iloc[:, [1, 3, 4, 5, 7, 8, 11]].copy()
                            clean_df.columns = ["Datum obchodu", "Ticker", "Jméno", "Pozice", "Typ transakce", "Ks Akcií", "Hodnota (USD)"]
                            
                            st.success(f"✅ Data pro {aktualni_ticker} úspěšně nalezena!")
                            
                            # Obarvení Nákupů a Prodejů
                            def style_trade(val):
                                val_str = str(val).lower()
                                if "purchase" in val_str or "buy" in val_str:
                                    return 'color: #00ff00; font-weight: bold;'
                                elif "sale" in val_str or "sell" in val_str:
                                    return 'color: #ff4b4b; font-weight: bold;'
                                return ''
                                
                            st.dataframe(clean_df.style.map(style_trade, subset=["Typ transakce"]), use_container_width=True)
                        except Exception as e:
                            st.error(f"Nepodařilo se zpracovat tabulku. {e}")
                else:
                    st.info("Tato společnost nemá za poslední dobu žádné hlášené transakce insiderů.")
            else:
                st.error("Chyba při spojení s OpenInsider.")
