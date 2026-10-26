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

BASKETS_FILE = os.path.join(hlavni_slozka, "baskets.json")

# --- DEFAULT BASKETS ---
DEFAULT_BASKETS = {
    "Tržní Indexy": ["SPY", "QQQ", "IWM", "DIA"],
    "AI & Polovodiče": ["NVDA", "AMD", "TSM", "ASML", "AVGO", "MU", "ARM"],
    "Software & Cloud": ["MSFT", "CRM", "ADBE", "ORCL", "NOW", "PLTR"],
    "Cybersecurity": ["CRWD", "PANW", "FTNT", "ZS", "CHKP"],
    "Krypto & Těžaři": ["IBIT", "MSTR", "COIN", "MARA", "RIOT"],
    "Zdravotnictví (Weight Loss)": ["LLY", "NVO", "VRTX", "UNH"],
    "Zlato & Stříbro": ["GLD", "SLV", "NEM", "GOLD", "AEM"],
    "Uran & Jádro": ["CCJ", "UEC", "NXE", "BWXT", "CEG", "URA"],
    "Obranný průmysl": ["LMT", "RTX", "NOC", "GD", "BA"]
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

st.title("SEKTOROVÁ ROTACE & TEMATICKÉ KOŠE")
st.caption("SLEDOVÁNÍ TOKU LIKVIDITY, VÝKONNOSTI SEKTORŮ A TRENDŮ (BASKETS).")
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
        df = yf.download(all_tickers, period="5y", progress=False)
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
        
        theme_perf = {"1D": [], "1W": [], "1M": [], "YTD": [], "1Y": [], "3Y": [], "5Y": []}
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
            if len(s) >= 1260: theme_perf["5Y"].append((c_now / s.iloc[-1260] - 1) * 100)
            
        avg_perfs = {k: np.mean(v) if v else None for k, v in theme_perf.items()}
        top_mover_str = f"{top_mover_ticker} ({top_mover_perf:+.2f}%)" if top_mover_ticker else "N/A"
        
        results.append({
            "Téma (Koš)": theme,
            "1D": avg_perfs["1D"],
            "1W": avg_perfs["1W"],
            "1M": avg_perfs["1M"],
            "YTD": avg_perfs["YTD"],
            "1Y": avg_perfs["1Y"],
            "3Y": avg_perfs["3Y"],
            "5Y": avg_perfs["5Y"],
            "Up/Down": f"{up_count} / {down_count}",
            "Top Mover (1D)": top_mover_str
        })
    return pd.DataFrame(results)

with st.spinner("Stahování historie (5 let) a kalkulace metrik..."):
    df_raw = fetch_basket_data(baskets)

if not df_raw.empty:
    # 1. GRAFICKÁ VIZUALIZACE (CHART)
    st.subheader("Výkonnost sektorů v čase")
    
    col_chart_sel, col_chart_time = st.columns([3, 1])
    available_baskets = list(baskets.keys())
    
    default_sel = [b for b in ["Tržní Indexy", "AI & Polovodiče"] if b in available_baskets]
    if not default_sel and available_baskets:
        default_sel = [available_baskets[0]]
        
    selected_baskets = col_chart_sel.multiselect("Vyberte koše k porovnání:", available_baskets, default=default_sel, label_visibility="collapsed")
    period = col_chart_time.radio("Timeframe grafu:", ["1M", "6M", "YTD", "1Y", "3Y", "5Y"], index=3, horizontal=True, label_visibility="collapsed")
    
    if selected_baskets:
        fig = go.Figure()
        for theme in selected_baskets:
            tickers = baskets.get(theme, [])
            valid_tickers = [t for t in tickers if t in df_raw.columns]
            if not valid_tickers: continue
            
            df_theme = df_raw[valid_tickers].dropna(how='all').ffill()
            
            if period == "YTD":
                df_theme = df_theme[df_theme.index.year == datetime.now().year]
            else:
                days_map = {"1M": 21, "6M": 126, "1Y": 252, "3Y": 756, "5Y": 1260}
                df_theme = df_theme.tail(days_map.get(period, 252))
                
            if df_theme.empty: continue
            
            first_vals = df_theme.bfill().iloc[0]
            pct_df = (df_theme / first_vals - 1) * 100
            basket_series = pct_df.mean(axis=1) 
            
            fig.add_trace(go.Scatter(x=basket_series.index, y=basket_series, mode='lines', name=theme, line=dict(width=2)))
            
        fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=10, b=0), hovermode='x unified', yaxis_ticksuffix="%")
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.markdown("---")
    
    # 2. TABULKA VÝKONNOSTI
    st.subheader("Matice agregované výkonnosti")
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
            "YTD": format_val, "1Y": format_val, "3Y": format_val, "5Y": format_val
        }).map(style_val, subset=["1D", "1W", "1M", "YTD", "1Y", "3Y", "5Y"]).hide(axis="index")

        st.table(styled_df)
    
    st.markdown("---")
    
    # 3. EDITACE KOŠŮ
    with st.expander("⚙️ Nastavení a editace košů (JSON)"):
        st.caption("Můžete přidávat vlastní koše a tickery. V případě potíží můžete tabulku resetovat na původní strukturu.")
        
        col_json, col_btn = st.columns([4, 1])
        edit_json = col_json.text_area("JSON Konfigurace:", value=json.dumps(baskets, indent=4), height=300, label_visibility="collapsed")
        
        if col_btn.button("💾 Uložit změny", use_container_width=True):
            try:
                new_baskets = json.loads(edit_json)
                with open(BASKETS_FILE, "w", encoding="utf-8") as f:
                    json.dump(new_baskets, f, indent=4, ensure_ascii=False)
                st.success("Uloženo! Obnovte stránku (F5).")
            except Exception as e:
                st.error(f"Chyba formátu JSON: {e}")
                
        if col_btn.button("🔄 Tovární nastavení", use_container_width=True):
            with open(BASKETS_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_BASKETS, f, indent=4, ensure_ascii=False)
            st.success("Tovární nastavení obnoveno! Obnovte stránku (F5).")

else:
    st.warning("Nepodařilo se stáhnout data. Zkontrolujte připojení nebo ticker symboly.")