import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os

st.set_page_config(page_title="Pokorný Terminal", page_icon="📈", layout="wide")

st.title("📈 Pokorný Terminal - Přehled Trhu")
st.markdown("Tvůj osobní přehled v reálném čase. Hodnoty se načítají živě z burzy.")

WATCHLIST_FILE = "watchlist.json"

# Výchozí struktura (pro Portfolio, Watchlist a Superinvestory)
DEFAULT_DATA = {
    "portfolio": ["GOOGL", "AMZN", "MSFT", "AMAT", "ASML", "NVDA", "UBER", "SOFI", "APP"],
    "watchlist": [],
    "superinvestors": ["Mohnish Pabrai", "Li Lu", "Michael Burry"]
}

def load_data():
    """Načte data a zkontroluje, zda je JSON ve správném (novém) formátu."""
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r") as f:
                data = json.load(f)
                # Ochrana: Pokud je tam starý formát (jen seznam), převede ho na nový do portfolia
                if isinstance(data, list):
                    return {"portfolio": data, "watchlist": [], "superinvestors": []}
                return data
        except json.JSONDecodeError:
            return DEFAULT_DATA
    return DEFAULT_DATA

def save_data(data):
    """Uloží kompletní slovník zpět do souboru."""
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Načtení dat
data = load_data()

# --- FUNKCE PRO VYKRESLOVÁNÍ TICKERŮ ---
def display_tickers(ticker_list):
    """Vykreslí mřížku s živými cenami pro jakýkoliv seznam tickerů."""
    if not ticker_list:
        st.info("Tento seznam je zatím prázdný. Můžeš si akcie přidat v záložce Nastavení.")
        return

    cols = st.columns(4)
    for i, ticker in enumerate(ticker_list):
        col = cols[i % 4]
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d")
            
            if len(hist) >= 2:
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                change_usd = current_price - prev_price
                change_pct = (change_usd / prev_price) * 100
                
                col.metric(
                    label=ticker, 
                    value=f"${current_price:.2f}", 
                    delta=f"{change_usd:.2f} USD ({change_pct:.2f} %)"
                )
            else:
                col.metric(label=ticker, value="Čekám na data...")
                
        except Exception as e:
            col.error(f"Nelze načíst {ticker}")

# --- ROZDĚLENÍ OBRAZOVKY DO ZÁLOŽEK ---
tab1, tab2, tab3 = st.tabs(["💼 Moje Portfolio", "👀 Můj Watchlist", "⚙️ Nastavení seznamů"])

with tab1:
    st.subheader("Aktuálně držené pozice")
    display_tickers(data.get("portfolio", []))

with tab2:
    st.subheader("Radar / Čekám na lepší cenu")
    display_tickers(data.get("watchlist", []))

with tab3:
    st.markdown("### ✏️ Úprava seznamů")
    st.markdown("Zde funguje **interaktivní tabulka**. Klikni do posledního prázdného řádku pro **přidání** nové akcie. Pro **smazání** označ řádek a zmáčkni klávesu Delete. Pro **změnu pořadí** buňky prostě přepiš.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**💼 Moje Portfolio**")
        df_port = pd.DataFrame(data.get("portfolio", []), columns=["Ticker"])
        # num_rows="dynamic" je ta magie, co dovolí přidávat a mazat řádky!
        edit_port = st.data_editor(df_port, num_rows="dynamic", key="port", use_container_width=True)
    
    with col2:
        st.markdown("**👀 Můj Watchlist**")
        df_watch = pd.DataFrame(data.get("watchlist", []), columns=["Ticker"])
        edit_watch = st.data_editor(df_watch, num_rows="dynamic", key="watch", use_container_width=True)
        
    st.markdown("---")
    if st.button("💾 ULOŽIT ZMĚNY VE VŠECH SEZNAMECH", use_container_width=True):
        # Vezmeme data z obou interaktivních tabulek, očistíme od prázdných řádků a uložíme
        novy_port = edit_port["Ticker"].dropna().astype(str).tolist()
        data["portfolio"] = [t.strip().upper() for t in novy_port if t.strip()]
        
        novy_watch = edit_watch["Ticker"].dropna().astype(str).tolist()
        data["watchlist"] = [t.strip().upper() for t in novy_watch if t.strip()]
        
        # Superinvestory necháme tak, jak byli uloženi
        save_data(data)
            
        st.success("✅ Úspěšně uloženo!")
        st.rerun() # Stránka se bleskově obnoví, abys hned viděl nové grafy
