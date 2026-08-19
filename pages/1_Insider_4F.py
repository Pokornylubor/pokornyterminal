import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import os
from io import StringIO

st.set_page_config(page_title="Insider Tracker", page_icon="🕵️‍♂️", layout="wide")

WATCHLIST_FILE = "watchlist.json"

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"portfolio": [], "watchlist": []}

data = load_watchlist()
my_tickers = list(set(data.get("portfolio", []) + data.get("watchlist", [])))

st.title("🕵️‍♂️ Insider Tracker (Live)")
st.markdown("4F reporty - nákupy a prodeje insiderů")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    vyber_ticker = st.selectbox("Vyber akcii ze seznamu:", ["--- Vyber ---"] + sorted(my_tickers))
with col2:
    hledany_ticker = st.text_input("🔍 Nebo napiš jiný Ticker (např. MSFT, PLTR):").strip().upper()

# Určíme, jaký ticker se má hledat
aktualni_ticker = hledany_ticker if hledany_ticker else (vyber_ticker if vyber_ticker != "--- Vyber ---" else None)

if aktualni_ticker:
    if st.button(f"Stáhnout Insidery pro {aktualni_ticker}", type="primary"):
        with st.spinner("Stahuji a čistím data o insiderech..."):
            url = f"http://openinsider.com/search?q={aktualni_ticker}"
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(url, headers=headers)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, 'html.parser')
                table = soup.find('table', {'class': 'tinytable'})
                
                if table:
                    try:
                        dfs = pd.read_html(StringIO(str(table)))
                        if dfs:
                            df = dfs[0]
                            
                            # Správné indexy z OpenInsideru: 2=Datum, 4=Jméno, 5=Pozice, 6=Buy/Sell, 7=Cena, 8=Kusy, 11=Hodnota
                            clean_df = df.iloc[:, [2, 4, 5, 6, 7, 8, 11]].copy()
                            clean_df.columns = ["Datum", "Jméno", "Pozice", "Typ (Buy/Sell)", "Cena za ks ($)", "Počet kusů", "Hodnota (USD)"]
                            
                            # Očištění čísel od znaků dolarů a čárek, aby se daly formátovat
                            clean_df["Cena za ks ($)"] = clean_df["Cena za ks ($)"].replace('[\$,]', '', regex=True).astype(float)
                            clean_df["Hodnota (USD)"] = clean_df["Hodnota (USD)"].replace('[\$,]', '', regex=True).astype(float)
                            clean_df["Počet kusů"] = clean_df["Počet kusů"].astype(str).str.replace(',', '').str.replace('+', '').astype(float)
                            
                            # Překlad a vizualizace typu transakce
                            def preloz_typ(val):
                                v = str(val).lower()
                                if "purchase" in v or "p - " in v: return "🟢 NÁKUP"
                                if "sale" in v or "s - " in v: return "🔴 PRODEJ"
                                if "option" in v or "oe - " in v: return "⚪ OPCE (Execute)"
                                return val
                                
                            clean_df["Typ (Buy/Sell)"] = clean_df["Typ (Buy/Sell)"].apply(preloz_typ)
                            
                            st.success(f"✅ Data pro {aktualni_ticker} úspěšně nalezena!")
                            
                            # Barvičkář a formátování
                            def style_trade(val):
                                if "🟢" in str(val): return 'color: #00ff00; font-weight: bold;'
                                if "🔴" in str(val): return 'color: #ff4b4b; font-weight: bold;'
                                return 'color: gray;'

                            formatted_df = clean_df.style.format({
                                "Cena za ks ($)": "${:,.2f}",
                                "Počet kusů": "{:,.0f}",
                                "Hodnota (USD)": "${:,.0f}"
                            }).map(style_trade, subset=["Typ (Buy/Sell)"])
                            
                            st.dataframe(formatted_df, use_container_width=True, height=500)
                    except Exception as e:
                        st.error(f"Nepodařilo se zpracovat tabulku. {e}")
                else:
                    st.info(f"Pro společnost {aktualni_ticker} nejsou za poslední dobu hlášené žádné transakce insiderů.")
            else:
                st.error("Chyba při spojení s OpenInsider.")
