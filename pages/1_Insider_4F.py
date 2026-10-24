import streamlit as st
import pandas as pd
import json
import os
import sys
import plotly.express as px

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
        "no_data": "ŽÁDNÁ DATA PRO TENTO TICKER.",
        "buy": "NÁKUP",
        "sell": "PRODEJ",
        "opt": "OPCE / JINÉ",
        "filter_type": "FILTR TRANSAKCÍ",
        "filter_name": "FILTR INSIDERŮ (Jména)",
        "tot_buy": "CELKOVÉ NÁKUPY",
        "tot_sell": "CELKOVÉ PRODEJE",
        "net_flow": "NET FLOW (Tok peněz)",
        "chart_title": "Historie toku peněz Insiderů (Smart Money)"
    },
    "EN": {
        "title": "INSIDER TRANSACTIONS (FORM 4)",
        "db_select": "DATABASE",
        "custom_tick": "CUSTOM TICKER",
        "no_db": "SYS ERR: DATABASE INSIDER_4F_DB.CSV NOT FOUND.",
        "no_data": "NO DATA FOR THIS TICKER.",
        "buy": "BUY",
        "sell": "SELL",
        "opt": "OPTION / OTHER",
        "filter_type": "TRANSACTION FILTER",
        "filter_name": "INSIDER FILTER (Names)",
        "tot_buy": "TOTAL BUYS",
        "tot_sell": "TOTAL SELLS",
        "net_flow": "NET FLOW",
        "chart_title": "Insider Money Flow History"
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
    
    # NEJDŮLEŽITĚJŠÍ OPRAVA: Tvrdé vymazání neviditelných mezer v názvech sloupců
    df_all.columns = df_all.columns.str.strip()
    
    c1, c2, c3 = st.columns([2, 2, 2])
    sel_tick = c1.selectbox(_["db_select"], [""] + all_tickers)
    custom_tick = c2.text_input(_["custom_tick"], value="")
    
    final_tick = custom_tick.upper().strip() if custom_tick.strip() else sel_tick

    if final_tick:
        ticker_col = 'Ticker' if 'Ticker' in df_all.columns else df_all.columns[0]
        df_filtered = df_all[df_all[ticker_col] == final_tick].copy()
        
        if df_filtered.empty:
            st.caption(_["no_data"])
        else:
            # 1. ČIŠTĚNÍ ČÍSELNÝCH HODNOT
            for col in ['Price', 'Qty', 'Value']:
                if col in df_filtered.columns:
                    df_filtered[col] = pd.to_numeric(df_filtered[col].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce').fillna(0)
            
            # 2. PŘEKLAD A SJEDNOCENÍ TYPŮ TRANSAKCÍ
            def preloz_typ(val):
                v = str(val).upper()
                if "PURCHASE" in v or "BUY" in v or "P -" in v: return _["buy"]
                if "SALE" in v or "SELL" in v or "S -" in v: return _["sell"]
                return _["opt"]
            
            if 'Trade Type' in df_filtered.columns:
                df_filtered['Trade Type'] = df_filtered['Trade Type'].apply(preloz_typ)
            
            # 3. FILTRACE
            f_col1, f_col2 = st.columns(2)
            
            avail_types = sorted(df_filtered['Trade Type'].dropna().unique().tolist()) if 'Trade Type' in df_filtered.columns else []
            sel_types = f_col1.multiselect(_["filter_type"], avail_types, default=avail_types)
            
            avail_names = sorted(df_filtered['Insider Name'].dropna().unique().tolist()) if 'Insider Name' in df_filtered.columns else []
            sel_names = f_col2.multiselect(_["filter_name"], avail_names, default=avail_names)
            
            if 'Trade Type' in df_filtered.columns and sel_types is not None:
                df_filtered = df_filtered[df_filtered['Trade Type'].isin(sel_types)]
            
            if 'Insider Name' in df_filtered.columns and sel_names is not None:
                df_filtered = df_filtered[df_filtered['Insider Name'].isin(sel_names)]
            
            # 4. VÝPOČET METRIK
            total_buy = 0
            total_sell = 0
            if 'Trade Type' in df_filtered.columns and 'Value' in df_filtered.columns:
                total_buy = df_filtered[df_filtered['Trade Type'] == _["buy"]]['Value'].sum()
                total_sell = df_filtered[df_filtered['Trade Type'] == _["sell"]]['Value'].sum()
            
            net_flow = total_buy + total_sell # Prodeje bývají záporné, proto se rovnou sčítá
            
            m1, m2, m3 = st.columns(3)
            m1.metric(_["tot_buy"], f"${total_buy:,.0f}")
            m2.metric(_["tot_sell"], f"${abs(total_sell):,.0f}")
            
            if net_flow > 0:
                m3.metric(_["net_flow"], f"${net_flow:,.0f}", "BULLISH (Kapitál přitéká)")
            elif net_flow < 0:
                m3.metric(_["net_flow"], f"${net_flow:,.0f}", "-BEARISH (Kapitál odtéká)")
            else:
                m3.metric(_["net_flow"], "$0", "NEUTRÁLNÍ", delta_color="off")
            
            st.markdown("---")
            
            # 5. VIZUALIZACE - GRAF TOKU PENĚZ
            if 'Trade Date' in df_filtered.columns and 'Value' in df_filtered.columns and not df_filtered.empty:
                df_chart = df_filtered.groupby(['Trade Date', 'Trade Type'])['Value'].sum().reset_index()
                df_chart = df_chart.sort_values(by='Trade Date')
                
                fig = px.bar(df_chart, x='Trade Date', y='Value', color='Trade Type',
                             color_discrete_map={_["buy"]: '#26A69A', _["sell"]: '#EF5350', _["opt"]: '#9E9E9E'},
                             title=_["chart_title"], template='plotly_dark')
                
                fig.update_layout(height=350, margin=dict(l=0, r=0, t=40, b=0), xaxis_title="", yaxis_title="Hodnota (USD)")
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            # 6. VYKRESLENÍ TABULKY
            def style_trade(val):
                if val == _["buy"]: return 'color: #26A69A; font-weight: bold;'
                if val == _["sell"]: return 'color: #EF5350; font-weight: bold;'
                return 'color: #787B86;'
            
            format_dict = {}
            if 'Price' in df_filtered.columns: format_dict['Price'] = "${:,.2f}"
            if 'Qty' in df_filtered.columns: format_dict['Qty'] = "{:,.0f}"
            if 'Value' in df_filtered.columns: format_dict['Value'] = "${:,.0f}"
            
            st.dataframe(
                df_filtered.style.format(format_dict, na_rep="-").map(style_trade, subset=['Trade Type'] if 'Trade Type' in df_filtered.columns else []), 
                use_container_width=True, 
                height=650,
                hide_index=True
            )