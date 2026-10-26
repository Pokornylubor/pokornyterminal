import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os
import sys
import numpy as np

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
    "AI & Polovodiče": ["NVDA", "AMD", "TSM", "ASML", "AVGO", "MU"],
    "Cybersecurity": ["CRWD", "PANW", "FTNT", "PLTR", "ZS"],
    "Uran & Jádro": ["CCJ", "UEC", "NXE", "BWXT", "CEG"],
    "Zlato & Těžaři": ["GLD", "NEM", "GOLD", "AEM", "KGC"],
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
        # Hromadné stažení dat pro zrychlení
        df = yf.download(all_tickers, period="ytd", group_by="ticker", progress=False)
    except:
        return pd.DataFrame()

    results = []
    
    for theme, tickers in baskets_dict.items():
        theme_1d = []
        theme_1w = []
        theme_ytd = []
        up_count = 0
        down_count = 0
        top_mover_ticker = ""
        top_mover_perf = -999.0
        
        for tkr in tickers:
            try:
                if len(all_tickers) == 1:
                    tkr_data = df.dropna(subset=['Close'])
                else:
                    if tkr not in df.columns.levels[0]: continue
                    tkr_data = df[tkr].dropna(subset=['Close'])
                    
                if len(tkr_data) < 2: continue
                
                close_now = tkr_data['Close'].iloc[-1]
                close_1d = tkr_data['Close'].iloc[-2]
                
                perf_1d = ((close_now / close_1d) - 1) * 100
                theme_1d.append(perf_1d)
                
                if perf_1d > 0: up_count += 1
                elif perf_1d < 0: down_count += 1
                
                if perf_1d > top_mover_perf:
                    top_mover_perf = perf_1d
                    top_mover_ticker = tkr
                
                if len(tkr_data) >= 5:
                    close_1w = tkr_data['Close'].iloc[-5]
                    theme_1w.append(((close_now / close_1w) - 1) * 100)
                    
                close_ytd = tkr_data['Close'].iloc[0]
                theme_ytd.append(((close_now / close_ytd) - 1) * 100)
                
            except:
                continue
                
        if theme_1d:
            avg_1d = np.mean(theme_1d)
            avg_1w = np.mean(theme_1w) if theme_1w else 0
            avg_ytd = np.mean(theme_ytd) if theme_ytd else 0
            
            top_mover_str = f"{top_mover_ticker} ({top_mover_perf:+.2f}%)" if top_mover_ticker else "N/A"
            
            results.append({
                "Téma (Koš)": theme,
                "1D Δ": avg_1d,
                "1W Δ": avg_1w,
                "YTD Δ": avg_ytd,
                "Up / Down": f"{up_count} / {down_count}",
                "Top Mover (1D)": top_mover_str
            })
            
    return pd.DataFrame(results)

with st.spinner("Kalkulace výkonnosti sektorů..."):
    df_results = fetch_basket_data(baskets)

if not df_results.empty:
    df_results = df_results.sort_values(by="1D Δ", ascending=False)
    
    def style_dataframe(df):
        return df.style.format({
            "1D Δ": "{:+.2f} %",
            "1W Δ": "{:+.2f} %",
            "YTD Δ": "{:+.2f} %"
        }).map(
            lambda x: 'color: #26A69A; font-weight: bold;' if x > 0 else ('color: #EF5350; font-weight: bold;' if x < 0 else 'color: #787B86;'),
            subset=["1D Δ", "1W Δ", "YTD Δ"]
        )

    st.table(style_dataframe(df_results).hide(axis="index"))
    
    st.markdown("---")
    st.subheader("Editace košů")
    st.caption("Úpravy se uloží do souboru baskets.json.")
    
    edit_json = st.text_area("JSON Konfigurace:", value=json.dumps(baskets, indent=4), height=250)
    if st.button("Uložit změny"):
        try:
            new_baskets = json.loads(edit_json)
            with open(BASKETS_FILE, "w", encoding="utf-8") as f:
                json.dump(new_baskets, f, indent=4, ensure_ascii=False)
            st.success("Koše úspěšně aktualizovány. Obnovte stránku pro načtení nových dat.")
        except Exception as e:
            st.error(f"Chyba formátu JSON: {e}")
else:
    st.warning("Nepodařilo se stáhnout data. Zkontrolujte konfiguraci košů.")