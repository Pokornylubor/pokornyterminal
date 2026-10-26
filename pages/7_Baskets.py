import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os
import sys
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# --- INITIAL SETUP ---
st.set_page_config(page_title="POKORNY TERMINAL | BASKETS", layout="wide", initial_sidebar_state="collapsed")

aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)

import menu
menu.vykresli_menu()

# --- DICTIONARY ---
t = {
    "CZ": {
        "title": "KOŠE",
        "desc": "SLEDOVÁNÍ TOKU LIKVIDITY A VÝKONNOSTI SEKTORŮ.",
        "spin": "Stahování maximální dostupné historie a kalkulace metrik (může chvíli trvat)...",
        "chart_h": "Výkonnost sektorů v čase",
        "chart_sel": "Vyberte koše k porovnání:",
        "chart_tf": "Časový horizont grafu:",
        "table_h": "Matice agregované výkonnosti",
        "col_theme": "Téma (Koš)",
        "col_ud": "Růst / Pokles",
        "col_top": "Top Mover (1D)",
        "exp_h": "⚙️ Nastavení a editace košů (JSON)",
        "exp_c": "Úpravy se uloží přímo do souboru watchlist.json v sekci 'baskets'. Zbytek dat zůstane nedotčen.",
        "json_lbl": "Konfigurace košů (sekce 'baskets'):",
        "btn_save": "💾 Uložit změny",
        "msg_save": "Uloženo do watchlist.json! Obnovte stránku (F5).",
        "msg_err": "Chyba formátu JSON:",
        "msg_nodata": "Nepodařilo se stáhnout data. Zkontrolujte připojení nebo ticker symboly."
    },
    "EN": {
        "title": "BASKETS",
        "desc": "TRACKING LIQUIDITY FLOW AND SECTOR PERFORMANCE.",
        "spin": "Downloading max available history and calculating metrics (may take a while)...",
        "chart_h": "Sector Performance Over Time",
        "chart_sel": "Select baskets to compare:",
        "chart_tf": "Chart Timeframe:",
        "table_h": "Aggregated Performance Matrix",
        "col_theme": "Theme (Basket)",
        "col_ud": "Up / Down",
        "col_top": "Top Mover (1D)",
        "exp_h": "⚙️ Baskets Setup & Editing (JSON)",
        "exp_c": "Modifications will be saved to watchlist.json in the 'baskets' section. Other data remains intact.",
        "json_lbl": "Baskets configuration:",
        "btn_save": "💾 Save Changes",
        "msg_save": "Saved to watchlist.json! Refresh the page (F5).",
        "msg_err": "JSON format error:",
        "msg_nodata": "Failed to download data. Check connection or ticker symbols."
    }
}
_ = t.get(st.session_state.get("lang", "CZ"), t["CZ"])

WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")

def get_full_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {"portfolio": [], "watchlist": [], "baskets": {}}

def load_baskets():
    data = get_full_watchlist()
    return data.get("baskets", {})

baskets = load_baskets()

st.title(_["title"])
st.caption(_["desc"])
st.markdown("---")

@st.cache_data(ttl=3600)
def fetch_basket_data(baskets_dict):
    all_tickers = []
    for tickers in baskets_dict.values():
        all_tickers.extend(tickers)
    all_tickers = list(set(all_tickers))
    
    if not all_tickers:
        return pd.DataFrame()
        
    try:
        df = yf.download(all_tickers, period="max", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            if 'Close' in df.columns.levels[0]:
                df_close = df['Close']
            else:
                return pd.DataFrame()
        else:
            df_close = pd.DataFrame(df['Close'])
            if len(all_tickers) == 1:
                df_close.columns = all_tickers
        return df_close
    except:
        return pd.DataFrame()

def calculate_metrics(df_close, baskets_dict):
    results = []
    current_year = datetime.now().year
    
    for theme, tickers in baskets_dict.items():
        valid_tickers = [t for t in tickers if t in df_close.columns]
        if not valid_tickers: continue
        
        theme_perf = {"1D": [], "1W": [], "1M": [], "YTD": [], "1Y": [], "3Y": [], "MAX": []}
        up_count = 0
        down_count = 0
        top_mover_ticker = ""
        top_mover_perf = -9999.0
        
        for tkr in valid_tickers:
            s = df_close[tkr].dropna()
            if len(s) < 2: continue
            
            c_now = s.iloc[-1]
            
            p_1d = (c_now / s.iloc[-2] - 1) * 100
            theme_perf["1D"].append(p_1d)
            if p_1d > 0: up_count += 1
            elif p_1d < 0: down_count += 1
            if p_1d > top_mover_perf:
                top_mover_perf = p_1d
                top_mover_ticker = tkr
                
            if len(s) >= 5: theme_perf["1W"].append((c_now / s.iloc[-5] - 1) * 100)
            if len(s) >= 21: theme_perf["1M"].append((c_now / s.iloc[-21] - 1) * 100)
            
            s_ytd = s[s.index.year == current_year]
            if len(s_ytd) > 0: theme_perf["YTD"].append((c_now / s_ytd.iloc[0] - 1) * 100)
            
            if len(s) >= 252: theme_perf["1Y"].append((c_now / s.iloc[-252] - 1) * 100)
            if len(s) >= 756: theme_perf["3Y"].append((c_now / s.iloc[-756] - 1) * 100)
            if len(s) > 0: theme_perf["MAX"].append((c_now / s.iloc[0] - 1) * 100)
            
        avg_perfs = {k: np.mean(v) if v else None for k, v in theme_perf.items()}
        top_mover_str = f"{top_mover_ticker} ({top_mover_perf:+.2f}%)" if top_mover_ticker else "N/A"
        
        results.append({
            _["col_theme"]: theme,
            "1D": avg_perfs["1D"],
            "1W": avg_perfs["1W"],
            "1M": avg_perfs["1M"],
            "YTD": avg_perfs["YTD"],
            "1Y": avg_perfs["1Y"],
            "3Y": avg_perfs["3Y"],
            "MAX": avg_perfs["MAX"],
            _["col_ud"]: f"{up_count} / {down_count}",
            _["col_top"]: top_mover_str
        })
    return pd.DataFrame(results)

with st.spinner(_["spin"]):
    df_raw = fetch_basket_data(baskets)

if not df_raw.empty and baskets:
    st.subheader(_["chart_h"])
    
    col_chart_sel, col_chart_time = st.columns([3, 1])
    available_baskets = list(baskets.keys())
    
    default_sel = [available_baskets[0]] if available_baskets else []
        
    selected_baskets = col_chart_sel.multiselect(_["chart_sel"], available_baskets, default=default_sel, label_visibility="collapsed", placeholder=_["chart_sel"])
    period = col_chart_time.radio(_["chart_tf"], ["1M", "6M", "YTD", "1Y", "3Y", "MAX"], index=3, horizontal=True, label_visibility="collapsed")
    
    if selected_baskets:
        fig = go.Figure()
        for theme in selected_baskets:
            tickers = baskets.get(theme, [])
            valid_tickers = [t for t in tickers if t in df_raw.columns]
            if not valid_tickers: continue
            
            df_theme = df_raw[valid_tickers].dropna(how='all').ffill()
            
            if period == "YTD":
                df_theme = df_theme[df_theme.index.year == datetime.now().year]
            elif period != "MAX":
                days_map = {"1M": 21, "6M": 126, "1Y": 252, "3Y": 756}
                df_theme = df_theme.tail(days_map.get(period, 252))
                
            if df_theme.empty: continue
            
            first_vals = df_theme.bfill().iloc[0]
            pct_df = (df_theme / first_vals - 1) * 100
            basket_series = pct_df.mean(axis=1) 
            
            fig.add_trace(go.Scatter(x=basket_series.index, y=basket_series, mode='lines', name=theme, line=dict(width=2)))
            
        fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=10, b=0), hovermode='x unified', yaxis_ticksuffix="%")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.markdown("---")
    
    st.subheader(_["table_h"])
    df_metrics = calculate_metrics(df_raw, baskets)
    
    if not df_metrics.empty:
        df_metrics = df_metrics.sort_values(by="1D", ascending=False)
        
        def format_val(val):
            if pd.isna(val) or val is None: return "-"
            return f"{val:+.2f} %"

        def style_val(val):
            if pd.isna(val) or val is None: return 'color: #787B86;'
            if val > 0: return 'color: #26A69A; font-weight: bold;'
            elif val < 0: return 'color: #EF5350; font-weight: bold;'
            return 'color: #787B86;'
            
        styled_df = df_metrics.style.format({
            "1D": format_val, "1W": format_val, "1M": format_val, 
            "YTD": format_val, "1Y": format_val, "3Y": format_val, "MAX": format_val
        }).map(style_val, subset=["1D", "1W", "1M", "YTD", "1Y", "3Y", "MAX"]).hide(axis="index")

        st.table(styled_df)
    
    st.markdown("---")
    
    with st.expander(_["exp_h"]):
        st.caption(_["exp_c"])
        
        edit_json = st.text_area(_["json_lbl"], value=json.dumps(baskets, indent=4), height=300, label_visibility="collapsed")
        
        if st.button(_["btn_save"], use_container_width=True):
            try:
                new_baskets = json.loads(edit_json)
                full_data = get_full_watchlist()
                full_data["baskets"] = new_baskets
                with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
                    json.dump(full_data, f, indent=4, ensure_ascii=False)
                st.success(_["msg_save"])
            except Exception as e:
                st.error(f"{_['msg_err']} {e}")

else:
    if not baskets:
        st.info("Nejsou definovány žádné koše. Přidejte je v souboru watchlist.json.")
    else:
        st.warning(_["msg_nodata"])