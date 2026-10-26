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
        "chart_tf": "Timeframe grafu:",
        "table_h": "Matice agregované výkonnosti",
        "col_theme": "Téma (Koš)",
        "col_ud": "Růst / Pokles",
        "col_top": "Top Mover (1D)",
        "exp_h": "⚙️ Nastavení a editace košů (JSON)",
        "exp_c": "Můžete přidávat vlastní koše a tickery. V případě potíží můžete tabulku resetovat na původní strukturu.",
        "json_lbl": "JSON Konfigurace:",
        "btn_save": "💾 Uložit změny",
        "btn_reset": "🔄 Tovární nastavení",
        "msg_save": "Uloženo! Obnovte stránku (F5).",
        "msg_err": "Chyba formátu JSON:",
        "msg_reset": "Tovární nastavení obnoveno! Obnovte stránku (F5).",
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
        "exp_c": "You can add custom baskets and tickers. In case of issues, you can factory reset the structure.",
        "json_lbl": "JSON Configuration:",
        "btn_save": "💾 Save Changes",
        "btn_reset": "🔄 Factory Reset",
        "msg_save": "Saved! Refresh the page (F5).",
        "msg_err": "JSON format error:",
        "msg_reset": "Factory settings restored! Refresh the page (F5).",
        "msg_nodata": "Failed to download data. Check connection or ticker symbols."
    }
}
_ = t.get(st.session_state.get("lang", "CZ"), t["CZ"])

BASKETS_FILE = os.path.join(hlavni_slozka, "baskets.json")

# --- MASIVNÍ DEFAULTNÍ KOŠE (180+ Akcií) ---
DEFAULT_BASKETS = {
    "Indexes & Sector ETFs": ["SPY", "QQQ", "IWM", "DIA", "XLK", "XLF", "XLV", "XLE", "XLI", "XLY", "XLP", "XLU", "XLB", "SMH", "ARKK"],
    "AI, Semiconductors & Hardware": ["NVDA", "AMD", "TSM", "ASML", "AVGO", "MU", "ARM", "INTC", "QCOM", "TXN", "AMAT", "LRCX", "KLAC", "MRVL", "SNPS", "CDNS", "MPWR", "SWKS", "ANET", "SMCI", "VRT", "DELL", "HPE", "WDC", "STX"],
    "Software, Cloud & Cyber": ["MSFT", "CRM", "ADBE", "ORCL", "NOW", "PLTR", "CRWD", "PANW", "FTNT", "ZS", "CHKP", "NET", "DDOG", "SNOW", "MDB", "TEAM", "WDAY", "INTU", "ROP", "TYL", "PTC", "OKTA", "PATH", "U"],
    "Big Tech, Internet & Media": ["AAPL", "GOOGL", "META", "AMZN", "NFLX", "TSLA", "SPOT", "ROKU", "PINS", "SNAP", "TTD", "MTCH", "DIS", "WBD", "CMCSA", "UBER", "ABNB", "DASH"],
    "Finance, Banks & FinTech": ["JPM", "BAC", "WFC", "C", "GS", "MS", "V", "MA", "AXP", "PYPL", "SQ", "SOFI", "AFRM", "HOOD", "COF", "DFS", "SCHW", "IBKR", "BLK", "BX", "KKR"],
    "Healthcare (Pharma & Biotech)": ["LLY", "NVO", "VRTX", "UNH", "JNJ", "MRK", "ABBV", "AMGN", "PFE", "GILD", "BIIB", "REGN", "ISRG", "SYK", "BSX", "MDT", "ZTS", "TMO", "DHR", "ILMN"],
    "Crypto, Miners & Blockchain": ["IBIT", "MSTR", "COIN", "MARA", "RIOT", "CLSK", "HUT", "CIFR", "ARBK", "HIVE", "BITF", "WULF", "CORZ", "IREN"],
    "Uranium, Nuclear & Green Energy": ["CCJ", "UEC", "NXE", "BWXT", "CEG", "URA", "URNM", "VST", "TLN", "ENPH", "FSLR", "SEDG", "RUN", "PLUG", "NEE", "BEP", "CWEN", "DNN", "UUUU", "URG"],
    "Gold, Silver & Commodities": ["GLD", "SLV", "NEM", "GOLD", "AEM", "KGC", "WPM", "FNV", "AGI", "PAAS", "CDE", "HL", "EXK", "SSRM", "AU", "GFI", "HMY", "COPX", "FCX", "SCCO"],
    "Defense & Aerospace": ["LMT", "RTX", "NOC", "GD", "BA", "LHX", "HII", "TDY", "TXT", "SPR", "RKLB", "SPCE", "PL", "LDOS", "CACI"]
}

def load_baskets():
    if not os.path.exists(BASKETS_FILE):
        with open(BASKETS_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_BASKETS, f, indent=4, ensure_ascii=False)
        return DEFAULT_BASKETS
    try:
        with open(BASKETS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return DEFAULT_BASKETS

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
        # Změna z "5y" na "max" pro stahování celé dostupné historie
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
        
        # Přidán klíč MAX, odstraněn klíč 5Y
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
            
            # Kalkulace absolutního výnosu od prvního dostupného datového bodu tickeru
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

if not df_raw.empty:
    st.subheader(_["chart_h"])
    
    col_chart_sel, col_chart_time = st.columns([3, 1])
    available_baskets = list(baskets.keys())
    
    default_sel = [b for b in ["Indexes & Sector ETFs", "AI, Semiconductors & Hardware"] if b in available_baskets]
    if not default_sel and available_baskets:
        default_sel = [available_baskets[0]]
        
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
        
        col_json, col_btn = st.columns([4, 1])
        edit_json = col_json.text_area(_["json_lbl"], value=json.dumps(baskets, indent=4), height=300, label_visibility="collapsed")
        
        if col_btn.button(_["btn_save"], use_container_width=True):
            try:
                new_baskets = json.loads(edit_json)
                with open(BASKETS_FILE, "w", encoding="utf-8") as f:
                    json.dump(new_baskets, f, indent=4, ensure_ascii=False)
                st.success(_["msg_save"])
            except Exception as e:
                st.error(f"{_['msg_err']} {e}")
                
        if col_btn.button(_["btn_reset"], use_container_width=True):
            with open(BASKETS_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_BASKETS, f, indent=4, ensure_ascii=False)
            st.success(_["msg_reset"])

else:
    st.warning(_["msg_nodata"])