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
        "desc": "SLEDOVÁNÍ VÝNOSOVÉ KŘIVKY, INDEXŮ, VOLATILITY, INFLAČNÍCH TLAKŮ A LIKVIDITY.",
        "tab_dash": "🧭 MAKRO DASHBOARD",
        "tab_curve": "📉 DLUHOPISY & FED",
        "tab_com": "🛢️ KOMODITY & KRYPTO",
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
        "eval_fed": "Tržní očekávání sazeb FEDu (Z Q-Futures)",
        "metrics_h1": "Dluhopisový trh & FED",
        "metrics_h2": "Akciové indexy",
        "metrics_h3": "Riziko, Komodity & Likvidita",
        "m_10y": "10Y Treasury Yield",
        "m_30y": "30Y Treasury Yield",
        "m_3m": "3M T-Bill Yield",
        "m_fed": "Implikovaná sazba FEDu",
        "m_sp500": "S&P 500",
        "m_nasdaq": "NASDAQ",
        "m_rsp": "S&P 500 Equal Weight (RSP)",
        "m_rut": "Russell 2000",
        "m_vix": "VIX (Volatilita)",
        "m_dxy": "DXY (Dolar Index)",
        "m_wti": "Ropa WTI",
        "m_brent": "Ropa Brent",
        "m_gold": "Zlato",
        "m_btc": "Bitcoin (Risk-On proxy)",
        "chart_yc": "Spread výnosové křivky (10Y minus 3M) - Riziko recese",
        "chart_vix": "Historie VIX (Poslední rok)",
        "chart_wti": "Ropa WTI (CL=F) s SMA",
        "chart_brent": "Ropa Brent (BZ=F) s SMA",
        "chart_gold": "Zlato (GC=F) s SMA",
        "chart_btc": "Bitcoin (BTC-USD) s SMA",
        "loading": "Načítání a agregace makroekonomických dat..."
    },
    "EN": {
        "title": "🌍 MACROECONOMIC DASHBOARD & RISK",
        "desc": "TRACKING YIELD CURVE, INDICES, VOLATILITY, INFLATION, AND LIQUIDITY.",
        "tab_dash": "🧭 MACRO DASHBOARD",
        "tab_curve": "📉 BONDS & FED",
        "tab_com": "🛢️ COMMODITIES & CRYPTO",
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
        "eval_fed": "Market FED Rate Expectations (From Q-Futures)",
        "metrics_h1": "Bond Market & FED",
        "metrics_h2": "Equity Indices",
        "metrics_h3": "Risk, Commodities & Liquidity",
        "m_10y": "10Y Treasury Yield",
        "m_30y": "30Y Treasury Yield",
        "m_3m": "3M T-Bill Yield",
        "m_fed": "Implied FED Rate",
        "m_sp500": "S&P 500",
        "m_nasdaq": "NASDAQ",
        "m_rsp": "S&P 500 Equal Weight (RSP)",
        "m_rut": "Russell 2000",
        "m_vix": "VIX (Volatility)",
        "m_dxy": "DXY (US Dollar Index)",
        "m_wti": "WTI Crude Oil",
        "m_brent": "Brent Crude Oil",
        "m_gold": "Gold",
        "m_btc": "Bitcoin (Risk-On proxy)",
        "chart_yc": "Yield Curve Spread (10Y minus 3M) - Recession Risk",
        "chart_vix": "VIX History (Last Year)",
        "chart_wti": "WTI Crude Oil (CL=F) with SMAs",
        "chart_brent": "Brent Crude (BZ=F) with SMAs",
        "chart_gold": "Gold (GC=F) with SMAs",
        "chart_btc": "Bitcoin (BTC-USD) with SMAs",
        "loading": "Loading and aggregating macroeconomic data..."
    }
}
_ = t.get(st.session_state.get("lang", "CZ"), t["CZ"])

st.title(_["title"])
st.caption(_["desc"])
st.markdown("---")

# Agregace tickerů
MACRO_TICKERS = {
    "10Y": "^TNX",
    "30Y": "^TYX",
    "3M": "^IRX",
    "FED": "ZQ=F",
    "SP500": "^GSPC",
    "NASDAQ": "^IXIC",
    "RSP": "RSP",
    "RUT": "^RUT",
    "VIX": "^VIX",
    "DXY": "DX-Y.NYB",
    "WTI": "CL=F",
    "BRENT": "BZ=F",
    "GOLD": "GC=F",
    "BTC": "BTC-USD"
}

@st.cache_data(ttl=3600)
def fetch_macro_data():
    data = {}
    history = {}
    for key, ticker in MACRO_TICKERS.items():
        try:
            # Stahujeme 2 roky dat pro vypocet SMA 200
            tkr = yf.Ticker(ticker, session=session)
            hist = tkr.history(period="2y")
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                
                # Zpracování specifik (FED sazba)
                if key == "FED":
                    data[key] = 100 - current_price
                    data[f"{key}_change"] = (100 - current_price) - (100 - prev_price)
                else:
                    data[key] = current_price
                    data[f"{key}_change"] = current_price - prev_price
                    
                # Výpočet SMA a ořez pro grafy na poslední rok (cca 252 obchodních dnů)
                hist['SMA50'] = hist['Close'].rolling(window=50).mean()
                hist['SMA200'] = hist['Close'].rolling(window=200).mean()
                
                if key == "BTC":
                    history[key] = hist[['Close', 'SMA50', 'SMA200']].tail(365)
                else:
                    history[key] = hist[['Close', 'SMA50', 'SMA200']].tail(252)
        except:
            data[key] = None
            data[f"{key}_change"] = None
    return data, history

with st.spinner(_["loading"]):
    macro_data, macro_history = fetch_macro_data()

if macro_data:
    tab_dash, tab_curve, tab_com = st.tabs([_["tab_dash"], _["tab_curve"], _["tab_com"]])

    with tab_dash:
        def fmt(val, is_pct=False, is_curr=False, is_crypto=False):
            if val is None or pd.isna(val): return "N/A"
            if is_pct: return f"{val:.2f} %"
            if is_curr: return f"${val:,.2f}"
            if is_crypto: return f"${val:,.0f}"
            return f"{val:,.2f}"

        # Řada 1: Dluhopisy a FED
        st.subheader(_["metrics_h1"])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(_["m_3m"], fmt(macro_data.get("3M"), is_pct=True), f"{macro_data.get('3M_change', 0):+.2f} bp" if macro_data.get("3M") else None)
        c2.metric(_["m_10y"], fmt(macro_data.get("10Y"), is_pct=True), f"{macro_data.get('10Y_change', 0):+.2f} bp" if macro_data.get("10Y") else None)
        c3.metric(_["m_30y"], fmt(macro_data.get("30Y"), is_pct=True), f"{macro_data.get('30Y_change', 0):+.2f} bp" if macro_data.get("30Y") else None)
        c4.metric(_["m_fed"], fmt(macro_data.get("FED"), is_pct=True), f"{macro_data.get('FED_change', 0):+.2f} %" if macro_data.get("FED") else None)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Řada 2: Indexy
        st.subheader(_["metrics_h2"])
        i1, i2, i3, i4 = st.columns(4)
        i1.metric(_["m_sp500"], fmt(macro_data.get("SP500")), f"{macro_data.get('SP500_change', 0):+.2f}" if macro_data.get("SP500") else None)
        i2.metric(_["m_nasdaq"], fmt(macro_data.get("NASDAQ")), f"{macro_data.get('NASDAQ_change', 0):+.2f}" if macro_data.get("NASDAQ") else None)
        i3.metric(_["m_rsp"], fmt(macro_data.get("RSP")), f"{macro_data.get('RSP_change', 0):+.2f}" if macro_data.get("RSP") else None)
        i4.metric(_["m_rut"], fmt(macro_data.get("RUT")), f"{macro_data.get('RUT_change', 0):+.2f}" if macro_data.get("RUT") else None)

        st.markdown("<br>", unsafe_allow_html=True)

        # Řada 3: Riziko a Komodity
        st.subheader(_["metrics_h3"])
        r1, r2, r3, r4, r5, r6 = st.columns(6)
        r1.metric(_["m_vix"], fmt(macro_data.get("VIX")), f"{macro_data.get('VIX_change', 0):+.2f}" if macro_data.get("VIX") else None)
        r2.metric(_["m_dxy"], fmt(macro_data.get("DXY")), f"{macro_data.get('DXY_change', 0):+.2f}" if macro_data.get("DXY") else None)
        r3.metric(_["m_btc"], fmt(macro_data.get("BTC"), is_crypto=True), f"{macro_data.get('BTC_change', 0):+.0f}" if macro_data.get("BTC") else None)
        r4.metric(_["m_gold"], fmt(macro_data.get("GOLD"), is_curr=True), f"{macro_data.get('GOLD_change', 0):+.2f}" if macro_data.get("GOLD") else None)
        r5.metric(_["m_wti"], fmt(macro_data.get("WTI"), is_curr=True), f"{macro_data.get('WTI_change', 0):+.2f}" if macro_data.get("WTI") else None)
        r6.metric(_["m_brent"], fmt(macro_data.get("BRENT"), is_curr=True), f"{macro_data.get('BRENT_change', 0):+.2f}" if macro_data.get("BRENT") else None)

        st.markdown("---")
        st.subheader(_["h_eval"])
        
        ec1, ec2 = st.columns(2)
        y10 = macro_data.get("10Y")
        y3m = macro_data.get("3M")
        vix = macro_data.get("VIX")
        dxy = macro_data.get("DXY")
        fed = macro_data.get("FED")

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
                    
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"**{_['eval_fed']}**")
            if fed is not None:
                st.info(f"🏛️ Aktuální naceněná implikovaná sazba FEDu: **{fed:.2f} %**")

    with tab_curve:
        st.subheader(_["chart_yc"])
        if "10Y" in macro_history and "3M" in macro_history:
            # Izolace čistých cen (Close) z tabulky před spojením
            df_10y = macro_history["10Y"][['Close']].rename(columns={"Close": "10Y"})
            df_3m = macro_history["3M"][['Close']].rename(columns={"Close": "3M"})
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

    def draw_technical_chart(title, df, line_color):
        st.subheader(title)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode='lines', name='Cena (Close)', line=dict(color=line_color, width=2)))
        if "SMA50" in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df["SMA50"], mode='lines', name='SMA 50', line=dict(color='#00E676', width=1, dash='dash')))
        if "SMA200" in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df["SMA200"], mode='lines', name='SMA 200', line=dict(color='#E91E63', width=1.5, dash='dashdot')))
        fig.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, t=30, b=0), hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with tab_com:
        if "WTI" in macro_history: draw_technical_chart(_["chart_wti"], macro_history["WTI"], '#EF5350')
        if "BRENT" in macro_history: draw_technical_chart(_["chart_brent"], macro_history["BRENT"], '#BA68C8')
        if "GOLD" in macro_history: draw_technical_chart(_["chart_gold"], macro_history["GOLD"], '#FFD54F')
        if "BTC" in macro_history: draw_technical_chart(_["chart_btc"], macro_history["BTC"], '#FF9800')