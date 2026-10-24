import streamlit as st
import pandas as pd
import json
import os
import sys

# --- INITIAL SETUP ---
st.set_page_config(page_title="POKORNY TERMINAL | INSIDER", layout="wide", initial_sidebar_state="collapsed")

# --- DIRECTORY MANAGEMENT ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)
WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")
FILE_PATH = os.path.join(hlavni_slozka, "insider_4f_db.csv")

import menu
menu.vykresli_menu()

# --- DICTIONARY ---
t = {
    "CZ": {
        "title": "INSIDER TRANSAKCE (FORM 4)",
        "db_select": "DATABÁZE",
        "custom_tick": "VLASTNÍ TICKER",
        "no_db": "SYS ERR: DATABÁZE INSIDER_4F_DB.CSV NENALEZENA.",
        "no_data": "ŽÁDNÁ DATA.",
        "buy": "NÁKUP",
        "sell": "PRODEJ",
        "opt": "OPCE",
        "filter_type": "FILTR TRANSAKCÍ",
        "tot_buy": "CELKOVÉ NÁKUPY",
        "tot_sell": "CELKOVÉ PRODEJE"
    },
    "EN": {
        "title": "INSIDER TRANSACTIONS (FORM 4)",
        "db_select": "DATABASE",
        "custom_tick": "CUSTOM TICKER",
        "no_db": "SYS ERR: DATABASE INSIDER_4F_DB.CSV NOT FOUND.",
        "no_data": "NO DATA.",
        "buy": "BUY",
        "sell": "SELL",
        "opt": "OPTION",
        "filter_type": "TRANSACTION FILTER",
        "tot_buy": "TOTAL BUYS",
        "tot_sell": "TOTAL SELLS"
    }
}
_ = t.get(st.session_state.get("lang", "CZ"), t["CZ"])

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r") as f: return json.load(f)
        except: pass
    return {"portfolio": [], "watchlist": []}

data = load_watchlist()
all_tickers = list(dict.fromkeys(data.get("portfolio", []) + data.get("watchlist", [])))

st.title(_["title"])
st.markdown("---")

if not os.path.exists(FILE_PATH):
    st.error(_["no_db"])
else:
    df_all = pd.read_csv(FILE_PATH)
    
    # ODSTRANĚNÍ NEVIDITELNÝCH MEZER Z NÁZVŮ SLOUPCŮ (ZABRÁNÍ CHYBÁM)
    df_all.columns = df_all.columns.str.strip()
    
    c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
    sel_tick = c1.selectbox(_["db_select"], [""] + all_tickers)
    custom_tick = c2.text_input(_["custom_tick"], value="")
    
    final_tick = custom_tick.upper().strip() if custom_tick.strip() else sel_tick

    if final_tick:
        ticker_col = 'Ticker' if 'Ticker' in df_all.columns else df_all.columns[0]
        df_filtered = df_all[df_all[ticker_col] == final_tick].copy()
        
        if df_filtered.empty:
            st.caption(_["no_data"])
        else:
            # Převod částek na čistá čísla (odstraní vše kromě čísel a mínusu)
            for col in ['Price', 'Qty', 'Value']:
                if col in df_filtered.columns:
                    df_filtered[col] = pd.to_numeric(df_filtered[col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce')
            
            def preloz_typ(val):
                v = str(val).lower()
                if "purchase" in v or "buy" in v or "p - " in v: return _["buy"]
                if "sale" in v or "sell" in v or "s - " in v: return _["sell"]
                if "option" in v or "oe - " in v: return _["opt"]
                return str(val).upper()
            
            trade_col = 'Trade Type' if 'Trade Type' in df_filtered.columns else None
            
            if trade_col:
                df_filtered[trade_col] = df_filtered[trade_col].apply(preloz_typ)
            
            total_buy = 0
            total_sell = 0
            
            if trade_col and 'Value' in df_filtered.columns:
                total_buy = df_filtered[df_filtered[trade_col] == _["buy"]]['Value'].sum()
                total_sell = df_filtered[df_filtered[trade_col] == _["sell"]]['Value'].sum()
            
            mc1, mc2, mc3 = st.columns([2, 2, 2])
            mc1.metric(_["tot_buy"], f"${total_buy:,.0f}")
            # Prodeje bývají v tabulce jako mínusové hodnoty, do metriky dáme absolutní číslo pro lepší design
            mc2.metric(_["tot_sell"], f"${abs(total_sell):,.0f}")
            
            if trade_col:
                available_types = sorted(df_filtered[trade_col].dropna().unique().tolist())
                selected_types = mc3.multiselect(_["filter_type"], available_types, default=available_types, label_visibility="collapsed", placeholder=_["filter_type"])
                
                if selected_types:
                    df_filtered = df_filtered[df_filtered[trade_col].isin(selected_types)]
                else:
                    df_filtered = df_filtered.iloc[0:0]

            st.markdown("<br>", unsafe_allow_html=True)
            
            def style_trade(val):
                if val in [_["buy"], "BUY", "NÁKUP"]: return 'color: #26A69A; font-weight: bold;'
                if val in [_["sell"], "SELL", "PRODEJ"]: return 'color: #EF5350; font-weight: bold;'
                return 'color: #787B86;'
            
            format_dict = {}
            if 'Price' in df_filtered.columns: format_dict['Price'] = "${:,.2f}"
            if 'Qty' in df_filtered.columns: format_dict['Qty'] = "{:,.0f}"
            if 'Value' in df_filtered.columns: format_dict['Value'] = "${:,.0f}"
            
            st.dataframe(
                df_filtered.style.format(format_dict, na_rep="-").map(style_trade, subset=[trade_col] if trade_col else []), 
                use_container_width=True, 
                height=650,
                hide_index=True
            )