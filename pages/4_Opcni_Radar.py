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
        "err_data": "OPČNÍ DATA PRO TENTO TICKER NEJSOU DOSTUPNÁ.",
        "exp_lbl": "EXPIRAČNÍ DATUM:",
        "bear": "🔴 BEARISH (Trh se jistí Puts)",
        "bull": "🟢 BULLISH (Trh sází na Calls)",
        "neut": "⚪ NEUTRÁLNÍ",
        "tab_dash": "📊 RADAR DASHBOARD",
        "tab_raw": "🗄️ SUROVÝ OPČNÍ ŘETĚZEC (CHAIN)",
        "pcr": "Put/Call Ratio (OI)",
        "oi_call": "Otevřené Call (OI)",
        "oi_put": "Otevřené Put (OI)",
        "wall_call": "📈 Call Wall (Rezistence)",
        "wall_put": "📉 Put Wall (Support)",
        "chart_h": "DISTRIBUCE OPEN INTEREST (Opční Zdi)",
        "leg_call": "Calls (Rezistence)",
        "leg_put": "Puts (Support)",
        "axis_x": "Strike Cena (USD)",
        "axis_y": "Open Interest (Objem kontraktů)",
        "raw_call": "CALL OPCE (Právo nakoupit)",
        "raw_put": "PUT OPCE (Právo prodat)",
        "err_load": "Chyba při načítání opčního řetězce:"
    },
    "EN": {
        "title": "OPTIONS RADAR & SENTIMENT",
        "desc": "OPTION CHAIN ANALYSIS, OPEN INTEREST AND WALL DETECTION (SMART MONEY).",
        "db_select": "DATABASE",
        "custom_tick": "CUSTOM TICKER",
        "loading": "LOADING OPTION CHAIN...",
        "err_data": "OPTIONS DATA FOR THIS TICKER NOT AVAILABLE.",
        "exp_lbl": "EXPIRATION DATE:",
        "bear": "🔴 BEARISH (Market hedging with Puts)",
        "bull": "🟢 BULLISH (Market betting on Calls)",
        "neut": "⚪ NEUTRAL",
        "tab_dash": "📊 RADAR DASHBOARD",
        "tab_raw": "🗄️ RAW OPTION CHAIN",
        "pcr": "Put/Call Ratio (OI)",
        "oi_call": "Open Calls (OI)",
        "oi_put": "Open Puts (OI)",
        "wall_call": "📈 Call Wall (Resistance)",
        "wall_put": "📉 Put Wall (Support)",
        "chart_h": "OPEN INTEREST DISTRIBUTION (Option Walls)",
        "leg_call": "Calls (Resistance)",
        "leg_put": "Puts (Support)",
        "axis_x": "Strike Price (USD)",
        "axis_y": "Open Interest (Contract Volume)",
        "raw_call": "CALL OPTIONS (Right to Buy)",
        "raw_put": "PUT OPTIONS (Right to Sell)",
        "err_load": "Error loading option chain:"
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
        selected_exp = st.selectbox(_["exp_lbl"], expirations)
        
        with st.spinner(f"{_['loading']} {selected_exp}"):
            try:
                chain = tkr_obj.option_chain(selected_exp)
                calls = chain.calls.copy()
                puts = chain.puts.copy()
                
                calls['openInterest'] = calls['openInterest'].fillna(0)
                puts['openInterest'] = puts['openInterest'].fillna(0)
                
                total_call_oi = calls['openInterest'].sum()
                total_put_oi = puts['openInterest'].sum()
                pcr_oi = total_put_oi / total_call_oi if total_call_oi > 0 else 0
                
                call_wall_strike = calls.loc[calls['openInterest'].idxmax()]['strike'] if not calls.empty and total_call_oi > 0 else None
                put_wall_strike = puts.loc[puts['openInterest'].idxmax()]['strike'] if not puts.empty and total_put_oi > 0 else None
                
                if pcr_oi > 1.2: sentiment = _["bear"]
                elif pcr_oi < 0.8: sentiment = _["bull"]
                else: sentiment = _["neut"]

                tab_dash, tab_raw = st.tabs([_["tab_dash"], _["tab_raw"]])
                
                with tab_dash:
                    st.subheader(f"{_['exp_lbl']} {selected_exp}")
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    col1.metric(_["pcr"], f"{pcr_oi:.2f}", sentiment, delta_color="off")
                    col2.metric(_["oi_call"], f"{int(total_call_oi):,}")
                    col3.metric(_["oi_put"], f"{int(total_put_oi):,}")
                    col4.metric(_["wall_call"], f"${call_wall_strike:,.2f}" if call_wall_strike else "N/A")
                    col5.metric(_["wall_put"], f"${put_wall_strike:,.2f}" if put_wall_strike else "N/A")
                    
                    st.markdown("---")
                    
                    st.subheader(_["chart_h"])
                    fig = go.Figure()
                    
                    if not calls.empty:
                        fig.add_trace(go.Bar(
                            x=calls['strike'], y=calls['openInterest'], 
                            name=_["leg_call"], marker_color='#26A69A', opacity=0.8
                        ))
                    
                    if not puts.empty:
                        fig.add_trace(go.Bar(
                            x=puts['strike'], y=puts['openInterest'], 
                            name=_["leg_put"], marker_color='#EF5350', opacity=0.8
                        ))
                        
                    fig.update_layout(
                        template="plotly_dark",
                        barmode='group',
                        margin=dict(l=0, r=0, t=10, b=0),
                        height=500,
                        hovermode='x unified',
                        xaxis_title=_["axis_x"],
                        yaxis_title=_["axis_y"],
                        yaxis=dict(fixedrange=False, showgrid=True, gridcolor='#2B2B2B'),
                        xaxis=dict(fixedrange=False, showgrid=False, tickformat=".0f")
                    )
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                    
                with tab_raw:
                    st.subheader(_["raw_call"])
                    st.dataframe(
                        calls[['strike', 'lastPrice', 'bid', 'ask', 'volume', 'openInterest', 'impliedVolatility']].style.format(
                            {'strike': '${:.2f}', 'lastPrice': '${:.2f}', 'bid': '${:.2f}', 'ask': '${:.2f}', 'impliedVolatility': '{:.2%}'}
                        ), use_container_width=True, hide_index=True
                    )
                    
                    st.subheader(_["raw_put"])
                    st.dataframe(
                        puts[['strike', 'lastPrice', 'bid', 'ask', 'volume', 'openInterest', 'impliedVolatility']].style.format(
                            {'strike': '${:.2f}', 'lastPrice': '${:.2f}', 'bid': '${:.2f}', 'ask': '${:.2f}', 'impliedVolatility': '{:.2%}'}
                        ), use_container_width=True, hide_index=True
                    )
                    
            except Exception as e:
                st.error(f"{_['err_load']} {str(e)}")
