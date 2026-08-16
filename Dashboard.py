import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os

st.set_page_config(page_title="Pokorny Terminal", page_icon="icon.png", layout="wide")

# --- NASTAVENÍ JAZYKA (PAMĚŤ) ---
if "lang" not in st.session_state:
    st.session_state.lang = "CZ" # Výchozí jazyk je čeština

with st.sidebar:
    st.markdown("🌐 **Jazyk / Language**")
    # Přepínač jazyka
    lang_choice = st.radio("Vyber jazyk / Select language:", ["CZ", "EN"], index=0 if st.session_state.lang == "CZ" else 1)
    
    # Pokud uživatel jazyk změní, uložíme ho a bleskově obnovíme stránku
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        st.rerun()

# --- SLOVNÍK PŘEKLADŮ ---
t = {
    "CZ": {
        "title": "📈 Pokorny Terminal",
        "desc": "Tvůj osobní přehled v reálném čase. Hodnoty se načítají živě z burzy.",
        "tab_port": "💼 Moje Portfolio",
        "tab_watch": "👀 Můj Watchlist",
        "tab_set": "⚙️ Nastavení seznamů",
        "empty_list": "Tento seznam je zatím prázdný. Můžeš si akcie přidat v záložce Nastavení.",
        "waiting": "Čekám na data...",
        "error_load": "Nelze načíst",
        "curr_pos": "Aktuálně držené pozice",
        "radar": "Radar / Čekám na lepší cenu",
        "edit_list": "### ✏️ Úprava seznamů",
        "edit_desc": "Zde funguje **interaktivní tabulka**. Klikni do posledního prázdného řádku pro **přidání** nové akcie. Pro **smazání** označ řádek a zmáčkni klávesu Delete. Pro **změnu pořadí** buňky prostě přepiš.",
        "save_btn": "💾 ULOŽIT ZMĚNY VE VŠECH SEZNAMECH",
        "success_save": "✅ Úspěšně uloženo!"
    },
    "EN": {
        "title": "📈 Pokorny Terminal",
        "desc": "Your personal real-time overview. Live data loaded directly from the market.",
        "tab_port": "💼 My Portfolio",
        "tab_watch": "👀 My Watchlist",
        "tab_set": "⚙️ List Settings",
        "empty_list": "This list is currently empty. You can add stocks in the Settings tab.",
        "waiting": "Waiting for data...",
        "error_load": "Failed to load",
        "curr_pos": "Currently Held Positions",
        "radar": "Radar / Waiting for better price",
        "edit_list": "### ✏️ Edit Lists",
        "edit_desc": "This is an **interactive table**. Click the last empty row to **add** a new stock. To **delete**, select a row and press Delete. To **reorder**, just overwrite the cells.",
        "save_btn": "💾 SAVE CHANGES TO ALL LISTS",
        "success_save": "✅ Successfully saved!"
    }
}

# Pro zjednodušení si jazykový balíček uložíme do proměnné "_" (podtržítko)
_ = t[st.session_state.lang]

# --- VYKRESLENÍ TITULKU PŘES SLOVNÍK ---
st.title(_["title"])
st.markdown(_["desc"])

WATCHLIST_FILE = "watchlist.json"
DEFAULT_DATA = {"portfolio": ["GOOGL", "AMZN", "MSFT", "AMAT", "ASML", "NVDA", "UBER", "SOFI", "APP"], "watchlist": [], "superinvestors": ["Mohnish Pabrai", "Li Lu", "Michael Burry"]}

def load_data():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return {"portfolio": data, "watchlist": [], "superinvestors": []}
                return data
        except json.JSONDecodeError:
            return DEFAULT_DATA
    return DEFAULT_DATA

def save_data(data):
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

# --- FUNKCE PRO VYKRESLOVÁNÍ TICKERŮ ---
def display_tickers(ticker_list):
    if not ticker_list:
        st.info(_["empty_list"])
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
                col.metric(label=ticker, value=_["waiting"])
                
        except Exception:
            col.error(f"{_['error_load']} {ticker}")

# --- ZÁLOŽKY S PŘEKLADEM ---
tab1, tab2, tab3 = st.tabs([_["tab_port"], _["tab_watch"], _["tab_set"]])

with tab1:
    st.subheader(_["curr_pos"])
    display_tickers(data.get("portfolio", []))

with tab2:
    st.subheader(_["radar"])
    display_tickers(data.get("watchlist", []))

with tab3:
    st.markdown(_["edit_list"])
    st.markdown(_["edit_desc"])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**{_['tab_port']}**")
        df_port = pd.DataFrame(data.get("portfolio", []), columns=["Ticker"])
        edit_port = st.data_editor(df_port, num_rows="dynamic", key="port", use_container_width=True)
    
    with col2:
        st.markdown(f"**{_['tab_watch']}**")
        df_watch = pd.DataFrame(data.get("watchlist", []), columns=["Ticker"])
        edit_watch = st.data_editor(df_watch, num_rows="dynamic", key="watch", use_container_width=True)
        
    st.markdown("---")
    if st.button(_["save_btn"], use_container_width=True):
        novy_port = edit_port["Ticker"].dropna().astype(str).tolist()
        data["portfolio"] = [t.strip().upper() for t in novy_port if t.strip()]
        
        novy_watch = edit_watch["Ticker"].dropna().astype(str).tolist()
        data["watchlist"] = [t.strip().upper() for t in novy_watch if t.strip()]
        
        save_data(data)
            
        st.success(_["success_save"])
        st.rerun()
