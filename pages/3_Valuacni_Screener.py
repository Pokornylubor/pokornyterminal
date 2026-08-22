import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os
import sys
import plotly.graph_objects as go

# --- INITIAL SETUP ---
st.set_page_config(page_title="POKORNY TERMINAL | VALUATION", layout="wide", initial_sidebar_state="collapsed")

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
        "title": "VALUACE AKCIE",
        "desc": "HISTORICKÉ VALUAČNÍ NÁSOBKY A STATISTIKA.",
        "db_select": "DATABÁZE",
        "custom_tick": "VLASTNÍ TICKER",
        "metric": "VALUAČNÍ METRIKA",
        "period": "OBDOBÍ",
        "loading": "STAHOVÁNÍ DAT...",
        "err_data": "DATA PRO TENTO TICKER NEJSOU DOSTUPNÁ.",
        "err_metric": "FUNDAMENTÁLNÍ DATA PRO VÝPOČET TÉTO METRIKY CHYBÍ."
    },
    "EN": {
        "title": "STOCK VALUATION",
        "desc": "HISTORICAL VALUATION MULTIPLES AND STATISTICS.",
        "db_select": "DATABASE",
        "custom_tick": "CUSTOM TICKER",
        "metric": "VALUATION METRIC",
        "period": "PERIOD",
        "loading": "LOADING DATA...",
        "err_data": "DATA FOR THIS TICKER NOT AVAILABLE.",
        "err_metric": "FUNDAMENTAL DATA FOR THIS METRIC IS MISSING."
    }
}
_ = t.get(st.session_state.get("lang", "CZ"), t["CZ"])

st.title(_["title"])
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

# --- OVLÁDACÍ PANEL ---
c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
sel_tick = c1.selectbox(_["db_select"], [""] + all_tickers)
custom_tick = c2.text_input(_["custom_tick"], value="")
metric = c3.selectbox(_["metric"], ["Price to Earnings", "Price to Book", "Price to Sales"])
period = c4.selectbox(_["period"], ["1Y", "3Y", "5Y", "10Y"], index=2)

final_tick = custom_tick.upper().strip() if custom_tick.strip() else sel_tick

if final_tick:
    period_map = {"1Y": "1y", "3Y": "3y", "5Y": "5y", "10Y": "10y"}
    yf_period = period_map[period]

    with st.spinner(f"{_['loading']} {final_tick}..."):
        tkr = yf.Ticker(final_tick)
        hist = tkr.history(period=yf_period)
        info = tkr.info

    if not hist.empty:
        # Získání fundamentů z API
        eps = info.get("trailingEps")
        bv = info.get("bookValue")
        ps = info.get("revenuePerShare")
        
        fwd_pe = info.get("forwardPE")
        peg = info.get("pegRatio")
        short_name = info.get("shortName", final_tick)

        # Matematika pro vykreslení
        calc_series = None
        if metric == "Price to Earnings" and eps and eps > 0:
            calc_series = hist['Close'] / eps
        elif metric == "Price to Book" and bv and bv > 0:
            calc_series = hist['Close'] / bv
        elif metric == "Price to Sales" and ps and ps > 0:
            calc_series = hist['Close'] / ps

        if calc_series is not None:
            # Očištění o časová pásma
            if calc_series.index.tz is not None:
                calc_series.index = calc_series.index.tz_convert('Europe/Prague').tz_localize(None)

            # Statistiky
            val_current = calc_series.iloc[-1]
            val_median = calc_series.median()
            val_min = calc_series.min()
            val_max = calc_series.max()

            # --- GRAF ---
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=calc_series.index, 
                y=calc_series, 
                mode='lines', 
                line=dict(color='#2962FF', width=2), 
                name=metric,
                fill='tozeroy',
                fillcolor='rgba(41, 98, 255, 0.1)' # Jemné podbarvení jako v EquiSpot
            ))
            
            # Přidání linky pro medián
            fig.add_hline(y=val_median, line_dash="dash", line_color="#787B86", annotation_text="Median", annotation_position="bottom right")

            fig.update_layout(
                template="plotly_dark", 
                margin=dict(l=0, r=0, t=10, b=0), 
                height=450, 
                xaxis_rangeslider_visible=False,
                dragmode='pan',
                hovermode='x unified',
                yaxis=dict(side='right', fixedrange=False, showgrid=True, gridcolor='#2B2B2B'),
                xaxis=dict(fixedrange=False, showgrid=False)
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})

            # --- TABULKA S TVRDÝMI DATY (EquiSpot styl) ---
            st.markdown("<br>", unsafe_allow_html=True)
            
            table_data = [{
                "Akcie": f"{short_name} ({final_tick})",
                "Median": f"{val_median:.2f}",
                "Minimum": f"{val_min:.2f}",
                "Maximum": f"{val_max:.2f}",
                "Aktuální": f"{val_current:.2f}",
                "Forward P/E": f"{fwd_pe:.2f}" if fwd_pe else "N/A",
                "PEG": f"{peg:.2f}" if peg else "N/A"
            }]
            
            df_table = pd.DataFrame(table_data)
            
            # Skrytí indexu a roztažení
            st.dataframe(df_table, use_container_width=True, hide_index=True)

        else:
            st.warning(_["err_metric"])
    else:
        st.error(_["err_data"])
