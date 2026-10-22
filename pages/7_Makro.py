import streamlit as st
import pandas as pd
import yfinance as yf
import os
import sys
import requests
import plotly.graph_objects as go
from datetime import datetime

# --- INITIAL SETUP ---
st.set_page_config(page_title="POKORNY TERMINAL | MACRO", layout="wide", initial_sidebar_state="collapsed")

aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)

import menu
menu.vykresli_menu()

# --- BYPASS YAHOO BLOCKING ---
session = requests.Session()
session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'

# --- DICTIONARY ---
t = {
    "CZ": {
        "title": "🌍 MAKROEKONOMICKÝ PANEL & RIZIKA",
        "desc": "SLEDOVÁNÍ VÝNOSOVÉ KŘIVKY, VOLATILITY, INFLAČNÍCH TLAKŮ A SÍLY DOLARU.",
        "tab_dash": "🧭 MAKRO DASHBOARD",
        "tab_curve": "📉 VÝNOSOVÁ KŘIVKA",
        "tab_com": "🛢️ KOMODITY & INFLACE",
        "h_eval": "Automatické vyhodnocení tržního prostředí",
        "eval_yc": "Zploštění / Inverze výnosové křivky",
        "eval_yc_inv": "Křivka je v INVERZI (10Y < 3M). Historicky silný signál blížící se ekonomické recese. Úvěrový trh je pod tlakem.",
        "eval_yc_norm": "Křivka je NORMÁLNÍ (10Y > 3M). Zdravé ekonomické prostředí, trh oceňuje budoucí růst.",
        "eval_vix": "Index strachu (VIX)",
        "eval_vix_low": "Nízká volatilita. Na trhu vládne klid a možná až přílišná sebejistota (Greed).",
        "eval_vix_mid": "Normální tržní volatilita. Prostředí bez extrémních výkyvů.",
        "eval_vix_high": "Zvýšená nervozita a strach. Investoři kupují zajištění.",
        "eval_vix_panic": "Extrémní PANIKA. Trh prudce vyprodává (často ukazuje na nákupní příležitosti pro dlouhodobý kapitál).",
        "eval_dxy": "Síla amerického dolaru (DXY)",
        "eval_dxy_high": "Silný dolar. Působí jako protivítr pro americké nadnárodní korporace a tlačí dolů ceny komodit.",
        "eval_dxy_low": "Slabší dolar. Podporuje ceny komodit a zisky nadnárodních společností v USA.",
        "metrics_h": "Živá makro data",
        "m_10y": "10-Year Treasury Yield",
        "m_3m": "3-Month T-Bill Yield",
        "m_vix": "VIX (Volatilita)",
        "m_dxy": "DXY (US Dolar Index)",
        "m_oil": "Ropa WTI (Inflační proxy)",
        "chart_yc": "Spread výnosové křivky (10Y minus 3M) - Riziko recese",
        "chart_vix": "Historie VIX (Poslední rok)",
        "loading": "Načítání makroekonomických dat..."
    },
    "EN": {
        "title": "🌍 MACROECONOMIC DASHBOARD & RISK",
        "desc": "TRACKING YIELD CURVE, VOLATILITY, INFLATION PRESSURES, AND DOLLAR STRENGTH.",
        "tab_dash": "🧭 MACRO DASHBOARD",
        "tab_curve": "📉 YIELD CURVE",
        "tab_com": "🛢️ COMMODITIES & INFLATION",
        "h_eval": "Automated Market Environment Evaluation",
        "eval_yc": "Yield Curve Steepness / Inversion",
        "eval_yc_inv": "Curve is INVERTED (10Y < 3M). Historically strong signal of approaching economic recession. Credit market under pressure.",
        "eval_yc_norm": "Curve is NORMAL (10Y > 3M). Healthy economic environment, market pricing in future growth.",
        "eval_vix": "Fear Index (VIX)",
        "eval_vix_low": "Low volatility. Market is calm, potentially complacent (Greed).",
        "eval_vix_mid": "Normal market volatility. Environment without extreme swings.",
        "eval_vix_high": "Elevated nervousness and fear. Investors buying protection.",
        "eval_vix_panic": "Extreme PANIC. Market selling off sharply (often indicates buying opportunities for long-term capital).",
        "eval_dxy": "US Dollar Strength (DXY)",
        "eval_dxy_high": "Strong dollar. Acts as a headwind for US multinational corporations and pressures commodity prices.",
        "eval_dxy_low": "Weaker dollar. Supports commodity prices and US multinational earnings.",
        "metrics_h": "Live Macro Data",
        "m_10y": "10-Year Treasury Yield",
        "m_3m": "3-Month T-Bill Yield",
        "m_vix": "VIX (Volatility)",
        "m_dxy": "DXY (US Dollar Index)",
        "m_oil": "WTI Crude Oil (Inflation Proxy)",
        "chart_yc": "Yield Curve Spread (10Y minus 3M) - Recession Risk",
        "chart_vix": "VIX History (Last Year)",
        "loading": "Loading macroeconomic data..."
    }
}
_ = t.get(st.session_state.get("lang", "CZ"), t["CZ"])

st.title(_["title"])
st.caption(_["desc"])
st.markdown("---")

# Tickers pro makro
MACRO_TICKERS = {
    "10Y": "^TNX",
    "3M": "^IRX",
    "VIX": "^VIX",
    "DXY": "DX-Y.NYB",
    "OIL": "CL=F",
    "GOLD": "GC=F"
}

@st.cache_data(ttl=3600)
def fetch_macro_data():
    data = {}
    history = {}
    for key, ticker in MACRO_TICKERS.items():
        try:
            tkr = yf.Ticker(ticker, session=session)
            hist = tkr.history(period="1y")
            if not hist.empty:
                data[key] = hist['Close'].iloc[-1]
                prev = hist['Close'].iloc[-2] if len(hist) > 1 else data[key]
                data[f"{key}_change"] = data[key] - prev
                history[key] = hist[['Close']]
        except:
            data[key] = None
            data[f"{key}_change"] = None
    return data, history

with st.spinner(_["loading"]):
    macro_data, macro_history = fetch_macro_data()

if macro_data:
    tab_dash, tab_curve, tab_com = st.tabs([_["tab_dash"], _["tab_curve"], _["tab_com"]])

    with tab_dash:
        st.subheader(_["metrics_h"])
        c1, c2, c3, c4, c5 = st.columns(5)
        
        def fmt(val, is_pct=False, is_curr=False):
            if val is None or pd.isna(val): return "N/A"
            if is_pct: return f"{val:.2f} %"
            if is_curr: return f"${val:.2f}"
            return f"{val:.2f}"

        y10 = macro_data.get("10Y")
        y3m = macro_data.get("3M")
        vix = macro_data.get("VIX")
        dxy = macro_data.get("DXY")
        oil = macro_data.get("OIL")

        c1.metric(_["m_10y"], fmt(y10, is_pct=True), f"{macro_data.get('10Y_change', 0):+.2f} bp" if y10 else None)
        c2.metric(_["m_3m"], fmt(y3m, is_pct=True), f"{macro_data.get('3M_change', 0):+.2f} bp" if y3m else None)
        c3.metric(_["m_vix"], fmt(vix), f"{macro_data.get('VIX_change', 0):+.2f}" if vix else None)
        c4.metric(_["m_dxy"], fmt(dxy), f"{macro_data.get('DXY_change', 0):+.2f}" if dxy else None)
        c5.metric(_["m_oil"], fmt(oil, is_curr=True), f"{macro_data.get('OIL_change', 0):+.2f}" if oil else None)

        st.markdown("---")
        st.subheader(_["h_eval"])
        
        ec1, ec2 = st.columns(2)
        
        with ec1:
            st.markdown(f"**{_['eval_yc']}**")
            if y10 is not None and y3m is not None:
                spread = y10 - y3m
                if spread < 0:
                    st.error(f"⚠️ {_['eval_yc_inv']} (Spread: {spread:.2f} %)")
                else:
                    st.success(f"✅ {_['eval_yc_norm']} (Spread: +{spread:.2f} %)")
            else:
                st.info("Data pro výnosovou křivku nejsou k dispozici.")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"**{_['eval_vix']}**")
            if vix is not None:
                if vix < 15:
                    st.success(f"🟢 {_['eval_vix_low']} (VIX: {vix:.2f})")
                elif 15 <= vix < 25:
                    st.info(f"🔵 {_['eval_vix_mid']} (VIX: {vix:.2f})")
                elif 25 <= vix < 35:
                    st.warning(f"🟠 {_['eval_vix_high']} (VIX: {vix:.2f})")
                else:
                    st.error(f"🔴 {_['eval_vix_panic']} (VIX: {vix:.2f})")

        with ec2:
            st.markdown(f"**{_['eval_dxy']}**")
            if dxy is not None:
                if dxy > 105:
                    st.warning(f"🦅 {_['eval_dxy_high']} (DXY: {dxy:.2f})")
                else:
                    st.success(f"🕊️ {_['eval_dxy_low']} (DXY: {dxy:.2f})")

    with tab_curve:
        st.subheader(_["chart_yc"])
        if "10Y" in macro_history and "3M" in macro_history:
            df_10y = macro_history["10Y"].rename(columns={"Close": "10Y"})
            df_3m = macro_history["3M"].rename(columns={"Close": "3M"})
            df_spread = df_10y.join(df_3m).dropna()
            df_spread["Spread"] = df_spread["10Y"] - df_spread["3M"]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_spread.index, y=df_spread["Spread"], mode='lines', name='10Y - 3M Spread', line=dict(color='#2962FF', width=2)))
            fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Hranice inverze (0%)", annotation_position="bottom right")
            
            fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=30, b=0), hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            st.subheader(_["chart_vix"])
            df_vix = macro_history["VIX"]
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df_vix.index, y=df_vix["Close"], mode='lines', name='VIX', line=dict(color='#FFA726', width=2)))
            fig2.add_hline(y=25, line_dash="dash", line_color="red", annotation_text="Hranice strachu (25)", annotation_position="top right")
            fig2.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=30, b=0), hovermode='x unified')
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

    with tab_com:
        st.subheader("Cenový vývoj - Ropa WTI (CL=F)")
        if "OIL" in macro_history:
            df_oil = macro_history["OIL"]
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=df_oil.index, y=df_oil["Close"], mode='lines', name='Ropa WTI', line=dict(color='#EF5350', width=2)))
            fig3.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=30, b=0), hovermode='x unified')
            st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})
            
        st.subheader("Cenový vývoj - Zlato (GC=F)")
        if "GOLD" in macro_history:
            df_gold = macro_history["GOLD"]
            fig4 = go.Figure()
            fig4.add_trace(go.Scatter(x=df_gold.index, y=df_gold["Close"], mode='lines', name='Zlato', line=dict(color='#FFD54F', width=2)))
            fig4.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=30, b=0), hovermode='x unified')
            st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar': False})