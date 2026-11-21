import streamlit as st
import pandas as pd
import yfinance as yf
import requests
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

current_lang = st.session_state.get("lang", "CZ")

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
        "bear": "BEARISH (Trh se jistí Puts)",
        "bull": "BULLISH (Trh sází na Calls)",
        "neut": "NEUTRÁLNÍ",
        "no_sent": "NEDOSTATEK DAT",
        "tab_dash": "RADAR DASHBOARD",
        "tab_raw": "SUROVÝ OPČNÍ ŘETĚZEC (CHAIN)",
        "wall_call": "Call Wall (Rezistence)",
        "wall_put": "Put Wall (Support)",
        "chart_h": "DISTRIBUCE KONTRAKTŮ (Opční Zdi)",
        "leg_call": "Calls (Rezistence)",
        "leg_put": "Puts (Support)",
        "axis_x": "Strike Cena (USD)",
        "axis_y": "Objem kontraktů",
        "raw_call": "CALL OPCE (Právo nakoupit)",
        "raw_put": "PUT OPCE (Právo prodat)",
        "err_load": "Chyba při načítání opčního řetězce:",
        "src_lbl": "Zdroj dat:"
    },
    "EN": {
        "title": "OPTIONS RADAR & SENTIMENT",
        "desc": "OPTION CHAIN ANALYSIS, OPEN INTEREST AND WALL DETECTION (SMART MONEY).",
        "db_select": "DATABASE",
        "custom_tick": "CUSTOM TICKER",
        "loading": "LOADING OPTION CHAIN...",
        "err_data": "OPTIONS DATA FOR THIS TICKER NOT AVAILABLE.",
        "exp_lbl": "EXPIRATION DATE:",
        "bear": "BEARISH (Market hedging with Puts)",
        "bull": "BULLISH (Market betting on Calls)",
        "neut": "NEUTRAL",
        "no_sent": "INSUFFICIENT DATA",
        "tab_dash": "RADAR DASHBOARD",
        "tab_raw": "RAW OPTION CHAIN",
        "wall_call": "Call Wall (Resistance)",
        "wall_put": "Put Wall (Support)",
        "chart_h": "CONTRACT DISTRIBUTION (Option Walls)",
        "leg_call": "Calls (Resistance)",
        "leg_put": "Puts (Support)",
        "axis_x": "Strike Price (USD)",
        "axis_y": "Contract Volume",
        "raw_call": "CALL OPTIONS (Right to Buy)",
        "raw_put": "PUT OPTIONS (Right to Sell)",
        "err_load": "Error loading option chain:",
        "src_lbl": "Data source:"
    }
}
_ = t.get(current_lang, t["CZ"])

st.title(_["title"])
st.caption(_["desc"])
st.markdown("---")

def load_data():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return {"portfolio": data, "watchlist": []}
                return data
        except Exception as e:
            st.error(f"Kritická chyba při čtení watchlist.json: {e}")
            st.stop()
    st.error(f"Soubor watchlist.json nebyl nalezen na cestě: {WATCHLIST_FILE}")
    st.stop()

data = load_data()
all_tickers = list(dict.fromkeys(data.get("portfolio", []) + data.get("watchlist", [])))

c1, c2 = st.columns([4, 2])

ph_text = "Vyhledat..." if current_lang == "CZ" else "Search..."
ph_db = "Vybrat..." if current_lang == "CZ" else "Select..."

custom_tick = c1.text_input(_["custom_tick"], placeholder=ph_text)
sel_tick = c2.selectbox(_["db_select"], all_tickers, index=None, placeholder=ph_db)

final_tick = custom_tick.upper().strip() if custom_tick.strip() else sel_tick

@st.cache_data(ttl=300)
def fetch_cboe_options(ticker):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    for url in [
        f"https://cdn.cboe.com/api/global/delayed_quotes/options/{ticker}.json",
        f"https://cdn.cboe.com/api/global/delayed_quotes/options/_{ticker}.json"
    ]:
        try:
            r = requests.get(url, headers=headers, timeout=8)
            if r.status_code == 200:
                payload = r.json()
                opts = payload.get("data", {}).get("options", [])
                if not opts:
                    continue
                rows = []
                for o in opts:
                    sym = o.get("option", "")
                    tail = sym[-15:]
                    if len(tail) == 15 and tail[6] in ("C", "P"):
                        exp_raw = tail[:6]
                        exp_str = f"20{exp_raw[:2]}-{exp_raw[2:4]}-{exp_raw[4:6]}"
                        opt_type = tail[6]
                        strike = int(tail[7:]) / 1000.0
                        rows.append({
                            "expiration": exp_str,
                            "type": opt_type,
                            "strike": strike,
                            "lastPrice": o.get("last_trade_price", 0.0) or 0.0,
                            "bid": o.get("bid", 0.0) or 0.0,
                            "ask": o.get("ask", 0.0) or 0.0,
                            "volume": o.get("volume", 0) or 0,
                            "openInterest": o.get("open_interest", 0) or 0,
                            "impliedVolatility": o.get("iv", 0.0) or 0.0
                        })
                if rows:
                    return pd.DataFrame(rows)
        except Exception:
            continue
    return pd.DataFrame()

@st.cache_data(ttl=300)
def get_yf_expirations(ticker):
    try:
        return list(yf.Ticker(ticker).options)
    except Exception:
        return []

@st.cache_data(ttl=300)
def get_yf_chain(ticker, exp_date):
    chain = yf.Ticker(ticker).option_chain(exp_date)
    return chain.calls.copy(), chain.puts.copy()

if final_tick:
    df_cboe = fetch_cboe_options(final_tick)
    source_name = "CBOE Delayed Feed"
    
    if not df_cboe.empty:
        expirations = sorted(df_cboe["expiration"].unique().tolist())
    else:
        source_name = "Yahoo Finance"
        expirations = get_yf_expirations(final_tick)
    
    if not expirations:
        st.error(_["err_data"])
    else:
        col_exp, col_src = st.columns([4, 1])
        selected_exp = col_exp.selectbox(_["exp_lbl"], expirations)
        col_src.caption(f"{_['src_lbl']} **{source_name}**")
        
        with st.spinner(f"{_['loading']} {selected_exp}"):
            try:
                if not df_cboe.empty:
                    sub = df_cboe[df_cboe["expiration"] == selected_exp]
                    calls = sub[sub["type"] == "C"].sort_values("strike").reset_index(drop=True)
                    puts = sub[sub["type"] == "P"].sort_values("strike").reset_index(drop=True)
                else:
                    calls, puts = get_yf_chain(final_tick, selected_exp)
                
                for df_opt in (calls, puts):
                    df_opt['openInterest'] = pd.to_numeric(df_opt.get('openInterest', 0), errors='coerce').fillna(0)
                    df_opt['volume'] = pd.to_numeric(df_opt.get('volume', 0), errors='coerce').fillna(0)
                
                total_call_oi = calls['openInterest'].sum()
                total_put_oi = puts['openInterest'].sum()
                
                use_volume = (total_call_oi == 0 or total_put_oi == 0) and (calls['volume'].sum() > 0 or puts['volume'].sum() > 0)
                metric_col = 'volume' if use_volume else 'openInterest'
                lbl_suffix = "(Volume)" if use_volume else "(OI)"
                
                total_call_metric = calls[metric_col].sum()
                total_put_metric = puts[metric_col].sum()
                
                if total_call_metric > 0 and total_put_metric > 0:
                    pcr_val = total_put_metric / total_call_metric
                    pcr_str = f"{pcr_val:.2f}"
                    if pcr_val > 1.2:
                        sentiment = _["bear"]
                    elif pcr_val < 0.8:
                        sentiment = _["bull"]
                    else:
                        sentiment = _["neut"]
                else:
                    pcr_str = "N/A"
                    sentiment = _["no_sent"]
                
                call_wall_strike = calls.loc[calls[metric_col].idxmax()]['strike'] if not calls.empty and total_call_metric > 0 else None
                put_wall_strike = puts.loc[puts[metric_col].idxmax()]['strike'] if not puts.empty and total_put_metric > 0 else None

                tab_dash, tab_raw = st.tabs([_["tab_dash"], _["tab_raw"]])
                
                with tab_dash:
                    st.subheader(f"{_['exp_lbl']} {selected_exp}")
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    col1.metric(f"Put/Call Ratio {lbl_suffix}", pcr_str, sentiment, delta_color="off")
                    col2.metric(f"Call {lbl_suffix}", f"{int(total_call_metric):,}")
                    col3.metric(f"Put {lbl_suffix}", f"{int(total_put_metric):,}")
                    col4.metric(_["wall_call"], f"${call_wall_strike:,.2f}" if call_wall_strike else "N/A")
                    col5.metric(_["wall_put"], f"${put_wall_strike:,.2f}" if put_wall_strike else "N/A")
                    
                    st.markdown("---")
                    
                    st.subheader(_["chart_h"])
                    fig = go.Figure()
                    
                    if not calls.empty and total_call_metric > 0:
                        fig.add_trace(go.Bar(
                            x=calls['strike'], y=calls[metric_col], 
                            name=_["leg_call"], marker_color='#26A69A', opacity=0.8
                        ))
                    
                    if not puts.empty and total_put_metric > 0:
                        fig.add_trace(go.Bar(
                            x=puts['strike'], y=puts[metric_col], 
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
                    cols_show = ['strike', 'lastPrice', 'bid', 'ask', 'volume', 'openInterest', 'impliedVolatility']
                    if not calls.empty:
                        st.subheader(_["raw_call"])
                        st.dataframe(
                            calls[cols_show].style.format(
                                {'strike': '${:.2f}', 'lastPrice': '${:.2f}', 'bid': '${:.2f}', 'ask': '${:.2f}', 'impliedVolatility': '{:.2%}'}
                            ), use_container_width=True, hide_index=True
                        )
                    
                    if not puts.empty:
                        st.subheader(_["raw_put"])
                        st.dataframe(
                            puts[cols_show].style.format(
                                {'strike': '${:.2f}', 'lastPrice': '${:.2f}', 'bid': '${:.2f}', 'ask': '${:.2f}', 'impliedVolatility': '{:.2%}'}
                            ), use_container_width=True, hide_index=True
                        )
                    
            except Exception as e:
                st.error(f"{_['err_load']} {str(e)}")