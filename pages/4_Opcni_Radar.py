import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os
import sys
import plotly.graph_objects as go

# --- INITIAL SETUP ---
st.set_page_config(page_title="POKORNY TERMINAL | OPTIONS", layout="wide", initial_sidebar_state="collapsed")

# --- DIRECTORY MANAGEMENT ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)
WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")

import menu
menu.vykresli_menu()

# --- DICTIONARY ---
t = {
    "CZ": {
        "title": "OPČNÍ RADAR & SENTIMENT",
        "desc": "ANALÝZA OPČNÍCH ŘETĚZCŮ, OPEN INTEREST A DETEKCE OPČNÍCH ZDÍ (SMART MONEY).",
        "db_select": "DATABÁZE",
        "custom_tick": "VLASTNÍ TICKER",
        "loading": "STAHOVÁNÍ OPČNÍHO ŘETĚZCE...",
        "err_data": "OPČNÍ DATA PRO TENTO TICKER NEJSOU DOSTUPNÁ."
    },
    "EN": {
        "title": "OPTIONS RADAR & SENTIMENT",
        "desc": "OPTION CHAIN ANALYSIS, OPEN INTEREST AND WALL DETECTION (SMART MONEY).",
        "db_select": "DATABASE",
        "custom_tick": "CUSTOM TICKER",
        "loading": "LOADING OPTION CHAIN...",
        "err_data": "OPTIONS DATA FOR THIS TICKER NOT AVAILABLE."
    }
}
_ = t.get(st.session_state.get("lang", "CZ"), t["CZ"])

st.title(_["title"])
st.caption(_["desc"])
st.markdown("---")

def load_data():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list): return {"portfolio": data, "watchlist": []}
                return data
        except: pass
    return {"portfolio": ["AAPL", "MSFT", "AMAT", "GOOGL"], "watchlist": []}

data = load_data()
all_tickers = list(dict.fromkeys(data.get("portfolio", []) + data.get("watchlist", [])))

# --- OVLÁDACÍ PANEL (Sjednocený) ---
c1, c2 = st.columns([2, 4])
sel_tick = c1.selectbox(_["db_select"], [""] + all_tickers)
custom_tick = c2.text_input(_["custom_tick"], value="")

final_tick = custom_tick.upper().strip() if custom_tick.strip() else sel_tick

if final_tick:
    tkr_obj = yf.Ticker(final_tick)
    expirations = tkr_obj.options
    
    if not expirations:
        st.error(_["err_data"])
    else:
        # Dynamický výběr expirace
        selected_exp = st.selectbox("EXPIRAČNÍ DATUM:", expirations)
        
        with st.spinner(f"{_['loading']} {selected_exp}"):
            try:
                chain = tkr_obj.option_chain(selected_exp)
                calls = chain.calls.copy()
                puts = chain.puts.copy()
                
                # Očištění o NaN v Open Interest
                calls['openInterest'] = calls['openInterest'].fillna(0)
                puts['openInterest'] = puts['openInterest'].fillna(0)
                
                # Výpočty metrik
                total_call_oi = calls['openInterest'].sum()
                total_put_oi = puts['openInterest'].sum()
                pcr_oi = total_put_oi / total_call_oi if total_call_oi > 0 else 0
                
                call_wall_strike = calls.loc[calls['openInterest'].idxmax()]['strike'] if not calls.empty and total_call_oi > 0 else None
                put_wall_strike = puts.loc[puts['openInterest'].idxmax()]['strike'] if not puts.empty and total_put_oi > 0 else None
                
                # Sentiment logika
                if pcr_oi > 1.2: sentiment = "🔴 BEARISH (Trh se jistí Puts)"
                elif pcr_oi < 0.8: sentiment = "🟢 BULLISH (Trh sází na Calls)"
                else: sentiment = "⚪ NEUTRÁLNÍ"

                tab_dash, tab_raw = st.tabs(["📊 RADAR DASHBOARD", "🗄️ SUROVÝ OPČNÍ ŘETĚZEC (CHAIN)"])
                
                with tab_dash:
                    st.subheader(f"EXPIRACE: {selected_exp}")
                    
                    # --- METRIKY ---
                    col1, col2, col3, col4, col5 = st.columns(5)
                    col1.metric("Put/Call Ratio (OI)", f"{pcr_oi:.2f}", sentiment, delta_color="off")
                    col2.metric("Otevřené Call (OI)", f"{int(total_call_oi):,}")
                    col3.metric("Otevřené Put (OI)", f"{int(total_put_oi):,}")
                    col4.metric("📈 Call Wall (Rezistence)", f"${call_wall_strike:,.2f}" if call_wall_strike else "N/A")
                    col5.metric("📉 Put Wall (Support)", f"${put_wall_strike:,.2f}" if put_wall_strike else "N/A")
                    
                    st.markdown("---")
                    
                    # --- VIZUALIZACE OPEN INTEREST (PLOTLY BAR CHART) ---
                    st.subheader("DISTRIBUCE OPEN INTEREST (Opční Zdi)")
                    
                    fig = go.Figure()
                    
                    # Zelené sloupce pro Calls
                    if not calls.empty:
                        fig.add_trace(go.Bar(
                            x=calls['strike'], y=calls['openInterest'], 
                            name='Calls (Rezistence)', marker_color='#26A69A', opacity=0.8
                        ))
                    
                    # Červené sloupce pro Puts
                    if not puts.empty:
                        fig.add_trace(go.Bar(
                            x=puts['strike'], y=puts['openInterest'], 
                            name='Puts (Support)', marker_color='#EF5350', opacity=0.8
                        ))
                        
                    fig.update_layout(
                        template="plotly_dark",
                        barmode='group',
                        margin=dict(l=0, r=0, t=10, b=0),
                        height=500,
                        hovermode='x unified',
                        xaxis_title="Strike Cena (USD)",
                        yaxis_title="Open Interest (Objem kontraktů)",
                        yaxis=dict(fixedrange=False, showgrid=True, gridcolor='#2B2B2B'),
                        xaxis=dict(fixedrange=False, showgrid=False, tickformat=".0f")
                    )
                    
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                    
                with tab_raw:
                    st.subheader("CALL OPCE (Právo nakoupit)")
                    st.dataframe(
                        calls[['strike', 'lastPrice', 'bid', 'ask', 'volume', 'openInterest', 'impliedVolatility']].style.format(
                            {'strike': '${:.2f}', 'lastPrice': '${:.2f}', 'bid': '${:.2f}', 'ask': '${:.2f}', 'impliedVolatility': '{:.2%}'}
                        ), use_container_width=True, hide_index=True
                    )
                    
                    st.subheader("PUT OPCE (Právo prodat)")
                    st.dataframe(
                        puts[['strike', 'lastPrice', 'bid', 'ask', 'volume', 'openInterest', 'impliedVolatility']].style.format(
                            {'strike': '${:.2f}', 'lastPrice': '${:.2f}', 'bid': '${:.2f}', 'ask': '${:.2f}', 'impliedVolatility': '{:.2%}'}
                        ), use_container_width=True, hide_index=True
                    )
                    
            except Exception as e:
                st.error(f"Chyba při načítání opčního řetězce: {str(e)}")
