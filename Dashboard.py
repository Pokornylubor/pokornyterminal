import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os

st.set_page_config(page_title="Pokorný Terminal", page_icon="📈", layout="wide")

st.title("📈 Pokorný Terminal - Watchlist")
st.markdown("Tvůj osobní přehled trhu v reálném čase. Hodnoty se načítají živě z burzy.")

WATCHLIST_FILE = "watchlist.json"
# Tvůj výchozí seznam akcií (kdyby se JSON soubor ztratil)
DEFAULT_WATCHLIST = ["GOOGL", "AMZN", "MSFT", "AMAT", "ASML", "NVDA", "UBER", "SOFI", "APP"]

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return DEFAULT_WATCHLIST
    return DEFAULT_WATCHLIST

def save_watchlist(watchlist):
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(watchlist, f)

watchlist = load_watchlist()

with st.sidebar:
    st.header("⚙️ Správa Watchlistu")
    new_ticker = st.text_input("Přidej Ticker (např. AAPL, META):").upper()
    
    if st.button("Přidat do sledování"):
        if new_ticker and new_ticker not in watchlist:
            watchlist.append(new_ticker)
            save_watchlist(watchlist)
            st.success(f"Akcie {new_ticker} byla přidána!")
            st.rerun()
        elif new_ticker in watchlist:
            st.warning("Tuto akcii už sleduješ.")

if not watchlist:
    st.info("Tvůj Watchlist je zatím prázdný. Přidej si první akcii v levém menu.")
else:
    cols = st.columns(4)
    
    for i, ticker in enumerate(watchlist):
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

    st.markdown("---")
    st.markdown("### 🗑️ Odebrat akcii")
    to_remove = st.selectbox("Vyber akcii k odstranění ze sledování:", [""] + watchlist)
    if st.button("Smazat ze seznamu"):
        if to_remove in watchlist:
            watchlist.remove(to_remove)
            save_watchlist(watchlist)
            st.success(f"Akcie {to_remove} byla smazána.")
            st.rerun()