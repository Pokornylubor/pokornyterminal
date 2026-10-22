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
        "tab_analysis": "📈 ANALÝZA & GRAFY",
        "h_eval": "Automatické vyhodnocení tržního prostředí",
        "eval_yc": "Zploštění / Inverze výnosové křivky",
        "eval_yc_inv": "Křivka je v INVERZI (10Y < 3M). Historicky silný signál blížící se recese.",
        "eval_yc_norm": "Křivka je NORMÁLNÍ (10Y > 3M). Zdravé ekonomické prostředí.",
        "eval_vix": "Index strachu (VIX)",
        "eval_vix_low": "Nízká volatilita. Na trhu vládne klid (Greed).",
        "eval_vix_mid": "Normální tržní volatilita.",
        "eval_vix_high": "Zvýšená nervozita a strach. Trh se zajišťuje.",
        "eval_vix_panic": "Extrémní PANIKA. Prudké výprodeje.",
        "eval_dxy": "Síla amerického dolaru (DXY)",
        "eval_dxy_high": "Silný dolar. Protivítr pro nadnárodní zisky a komodity.",
        "eval_dxy_low": "Slabší dolar. Podporuje ceny komodit a zámořské zisky.",
        "eval_fed": "Tržní očekávání úrokových sazeb (FED Funds Futures)",
        "fed_now": "Aktuálně naceňovaná sazba:",
        "fed_1w": "Očekávání před týdnem:",
        "fed_1m": "Očekávání před měsícem:",
        "metrics_h1": "Dluhopisový trh & FED",
        "metrics_h2": "Akciové indexy",
        "metrics_h3": "Riziko, Komodity & Likvidita",
        "m_10y": "10Y Treasury Yield",
        "m_30y": "30Y Treasury Yield",
        "m_3m": "3M T-Bill",
        "m_fed": "Implikovaná sazba FEDu",
        "m_sp500": "S&P 500",
        "m_nasdaq": "NASDAQ",
        "m_rsp": "S&P 500 (Equal Weight)",
        "m_rut": "Russell 2000",
        "m_vix": "VIX (Volatilita)",
        "m_dxy": "DXY (Dolar Index)",
        "m_wti": "Ropa WTI",
        "m_brent": "Ropa Brent",
        "m_gold": "Zlato",
        "m_btc": "Bitcoin (Risk-On proxy)",
        "perf_sel": "Vyberte instrument pro detailní analýzu:",
        "perf_mat": "Výkonnostní matice",
        "p_1w": "1 Týden",
        "p_1m": "1 Měsíc",
        "p_ytd": "YTD",
        "p_1y": "1 Rok",
        "p_3y": "3 Roky",
        "p_5y": "5 Let",
        "loading": "Načítání makroekonomických dat...",
        "help_title": "📖 JAK ČÍST TENTO RADAR (NÁPOVĚDA)",
        "help_text": """
**1. Výnosová křivka (Spread 10Y - 3M)**
Základní ukazatel zdraví ekonomiky. Pokud je výnos krátkodobých 3M dluhopisů vyšší než 10Y (spread je záporný), trh je v tzv. inverzi. To historicky předpovídá recesi, protože investoři očekávají, že centrální banka bude muset v budoucnu prudce snižovat sazby kvůli ekonomickým problémům.

**2. Očekávání sazeb FEDu**
Aplikace analyzuje cenu futures kontraktů na úrokové sazby (ZQ=F). Neukazuje oficiální sazbu, ale to, **co si myslí trh**, že FED udělá. Pokud aktuální sazba klesá oproti stavu před měsícem, trh začíná naceňovat snižování sazeb (Dovish pivot).

**3. VIX (Index strachu)**
Měří očekávanou volatilitu opcí na S&P 500. Hodnoty pod 15 znamenají absolutní klid (Risk-On). Hodnoty nad 25 signalizují paniku a krev na trzích – to jsou historicky nejlepší momenty pro dlouhodobé nákupy (Risk-Off).

**4. DXY (Dolarový index)**
Ukazuje sílu USD proti koši světových měn. Silný dolar (nad 105) zdražuje americké zboží ve světě a sráží ceny komodit. Slabý dolar pomáhá akciím a zlatu.

**5. S&P 500 vs. RSP (Equal Weight)**
Klasický S&P 500 je tažen několika giganty (Apple, Microsoft, Nvidia). Index RSP dává každé z 500 firem stejnou váhu (0.2 %). Pokud S&P 500 roste, ale RSP klesá, trh je nezdravý a drží ho nad vodou jen pár technologických firem.
        """
    },
    "EN": {
        "title": "🌍 MACROECONOMIC DASHBOARD & RISK",
        "desc": "TRACKING YIELD CURVE, INDICES, VOLATILITY, INFLATION, AND LIQUIDITY.",
        "tab_dash": "🧭 MACRO DASHBOARD",
        "tab_analysis": "📈 ANALYSIS & CHARTS",
        "h_eval": "Automated Market Environment Evaluation",
        "eval_yc": "Yield Curve Steepness / Inversion",
        "eval_yc_inv": "Curve is INVERTED (10Y < 3M). Historically strong signal of approaching recession.",
        "eval_yc_norm": "Curve is NORMAL (10Y > 3M). Healthy economic environment.",
        "eval_vix": "Fear Index (VIX)",
        "eval_vix_low": "Low volatility. Market is calm (Greed).",
        "eval_vix_mid": "Normal market volatility.",
        "eval_vix_high": "Elevated nervousness and fear. Market is hedging.",
        "eval_vix_panic": "Extreme PANIC. Sharp sell-offs.",
        "eval_dxy": "US Dollar Strength (DXY)",
        "eval_dxy_high": "Strong dollar. Headwind for multinationals and commodities.",
        "eval_dxy_low": "Weaker dollar. Supports commodities and overseas earnings.",
        "eval_fed": "Market FED Rate Expectations (FED Funds Futures)",
        "fed_now": "Currently implied rate:",
        "fed_1w": "Expectations 1 week ago:",
        "fed_1m": "Expectations 1 month ago:",
        "metrics_h1": "Bond Market & FED",
        "metrics_h2": "Equity Indices",
        "metrics_h3": "Risk, Commodities & Liquidity",
        "m_10y": "10Y Treasury Yield",
        "m_30y": "30Y Treasury Yield",
        "m_3m": "3M T-Bill",
        "m_fed": "Implied FED Rate",
        "m_sp500": "S&P 500",
        "m_nasdaq": "NASDAQ",
        "m_rsp": "S&P 500 (Equal Weight)",
        "m_rut": "Russell 2000",
        "m_vix": "VIX (Volatility)",
        "m_dxy": "DXY (US Dollar Index)",
        "m_wti": "WTI Crude Oil",
        "m_brent": "Brent Crude Oil",
        "m_gold": "Gold",
        "m_btc": "Bitcoin (Risk-On proxy)",
        "perf_sel": "Select instrument for detailed analysis:",
        "perf_mat": "Performance Matrix",
        "p_1w": "1 Week",
        "p_1m": "1 Month",
        "p_ytd": "YTD",
        "p_1y": "1 Year",
        "p_3y": "3 Years",
        "p_5y": "5 Years",
        "loading": "Loading macroeconomic data...",
        "help_title": "📖 HOW TO READ THIS RADAR (GUIDE)",
        "help_text": """
**1. Yield Curve (10Y - 3M Spread)**
A primary indicator of economic health. If 3M yields exceed 10Y (negative spread), the curve is inverted. Historically, this predicts recession as markets expect the central bank to slash rates.

**2. FED Rate Expectations**
The app analyzes FED Funds Futures (ZQ=F). It shows **what the market expects** the FED to do. If the implied rate is falling compared to a month ago, the market is pricing in rate cuts (Dovish pivot).

**3. VIX (Fear Index)**
Measures expected volatility on S&P 500 options. Under 15 means calm (Risk-On). Over 25 signals panic and hedging—often the best times for long-term accumulation (Risk-Off).

**4. DXY (Dollar Index)**
Measures USD strength against a global basket. A strong dollar (>105) hurts US exports and pressures commodities. A weak dollar supports global equities.

**5. S&P 500 vs. RSP (Equal Weight)**
The standard S&P 500 is heavily skewed by mega-caps. RSP gives every company an equal 0.2% weight. If S&P 500 is rising while RSP is falling, the rally lacks breadth.
        """
    }
}
_ = t.get(st.session_state.get("lang", "CZ"), t["CZ"])

st.title(_["title"])
st.caption(_["desc"])

with st.expander(_["help_title"]):
    st.markdown(_["help_text"])

st.markdown("---")

MACRO_TICKERS = {
    "10Y": ("^TNX", _["m_10y"]),
    "30Y": ("^TYX", _["m_30y"]),
    "3M": ("^IRX", _["m_3m"]),
    "FED": ("ZQ=F", _["m_fed"]),
    "SP500": ("^GSPC", _["m_sp500"]),
    "NASDAQ": ("^IXIC", _["m_nasdaq"]),
    "RSP": ("RSP", _["m_rsp"]),
    "RUT": ("^RUT", _["m_rut"]),
    "VIX": ("^VIX", _["m_vix"]),
    "DXY": ("DX-Y.NYB", _["m_dxy"]),
    "WTI": ("CL=F", _["m_wti"]),
    "BRENT": ("BZ=F", _["m_brent"]),
    "GOLD": ("GC=F", _["m_gold"]),
    "BTC": ("BTC-USD", _["m_btc"])
}

RATES_AND_VOL = ["10Y", "30Y", "3M", "FED", "VIX"]

def safe_iloc(df, steps_back):
    if len(df) > steps_back:
        return df['Close'].iloc[-(steps_back+1)]
    return None

@st.cache_data(ttl=3600)
def fetch_macro_data():
    data = {}
    history = {}
    
    current_year = datetime.now().year
    
    for key, (ticker, name) in MACRO_TICKERS.items():
        try:
            tkr = yf.Ticker(ticker, session=session)
            hist = tkr.history(period="6y")
            if not hist.empty:
                current_price = float(hist['Close'].iloc[-1])
                prev_price = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_price
                
                if key == "FED":
                    hist['Close'] = 100 - hist['Close']
                    current_price = 100 - current_price
                    prev_price = 100 - prev_price
                
                abs_chg = current_price - prev_price
                pct_chg = ((current_price / prev_price) - 1) * 100 if prev_price and key not in RATES_AND_VOL else None
                
                data[key] = {
                    "price": current_price,
                    "abs_chg": abs_chg,
                    "pct_chg": pct_chg
                }
                
                perf = {}
                perf[_["p_1w"]] = safe_iloc(hist, 5)
                perf[_["p_1m"]] = safe_iloc(hist, 21)
                
                ytd_df = hist[hist.index.year == current_year]
                perf[_["p_ytd"]] = ytd_df['Close'].iloc[0] if not ytd_df.empty else None
                
                perf[_["p_1y"]] = safe_iloc(hist, 252)
                perf[_["p_3y"]] = safe_iloc(hist, 252*3)
                perf[_["p_5y"]] = safe_iloc(hist, 252*5)
                
                # Dodatecna historie pro modul sazeb FEDu
                if key == "FED":
                    data["FED_hist"] = {
                        "1w": perf[_["p_1w"]],
                        "1m": perf[_["p_1m"]]
                    }
                
                calculated_perf = {}
                for p_key, p_val in perf.items():
                    if p_val is not None:
                        if key in RATES_AND_VOL:
                            calculated_perf[p_key] = f"{(current_price - p_val) * 100:+.0f} bps" if key != "VIX" else f"{current_price - p_val:+.2f} pts"
                        else:
                            calculated_perf[p_key] = f"{((current_price / p_val) - 1) * 100:+.2f} %"
                    else:
                        calculated_perf[p_key] = "-"
                        
                data[key]["performance"] = calculated_perf

                hist['SMA50'] = hist['Close'].rolling(window=50).mean()
                hist['SMA200'] = hist['Close'].rolling(window=200).mean()
                history[key] = hist[['Close', 'SMA50', 'SMA200']]
        except:
            pass
    return data, history

with st.spinner(_["loading"]):
    macro_data, macro_history = fetch_macro_data()

if macro_data:
    tab_dash, tab_analysis = st.tabs([_["tab_dash"], _["tab_analysis"]])

    with tab_dash:
        def render_metric(col, key, is_curr=False, is_crypto=False):
            if key not in macro_data:
                col.metric(MACRO_TICKERS[key][1], "N/A")
                return
            
            d = macro_data[key]
            val = d["price"]
            abs_chg = d["abs_chg"]
            pct_chg = d["pct_chg"]
            
            if is_curr: val_str = f"${val:,.2f}"
            elif is_crypto: val_str = f"${val:,.0f}"
            elif key in RATES_AND_VOL and key != "VIX": val_str = f"{val:.2f} %"
            else: val_str = f"{val:,.2f}"
            
            # Bezpecne zformatovani delty s fixaci minusu jako prvniho znaku (pro Streamlit barvy)
            sign = "-" if abs_chg < 0 else "+"
            val_abs = abs(abs_chg)
            
            if key in RATES_AND_VOL:
                delta_str = f"{sign}{val_abs * 100:.1f} bps" if key != "VIX" else f"{sign}{val_abs:.2f} pts"
            else:
                if is_curr or is_crypto:
                    delta_str = f"{sign}${val_abs:,.2f} ({pct_chg:+.2f}%)" if pct_chg else f"{sign}${val_abs:,.2f}"
                else:
                    delta_str = f"{sign}{val_abs:,.2f} ({pct_chg:+.2f}%)" if pct_chg else f"{sign}{val_abs:,.2f}"
                    
            col.metric(MACRO_TICKERS[key][1], val_str, delta_str)

        st.subheader(_["metrics_h1"])
        c1, c2, c3, c4 = st.columns(4)
        render_metric(c1, "3M")
        render_metric(c2, "10Y")
        render_metric(c3, "30Y")
        render_metric(c4, "FED")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.subheader(_["metrics_h2"])
        i1, i2, i3, i4 = st.columns(4)
        render_metric(i1, "SP500")
        render_metric(i2, "NASDAQ")
        render_metric(i3, "RSP")
        render_metric(i4, "RUT")

        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader(_["metrics_h3"])
        r1, r2, r3, r4, r5, r6 = st.columns(6)
        render_metric(r1, "VIX")
        render_metric(r2, "DXY")
        render_metric(r3, "BTC", is_crypto=True)
        render_metric(r4, "GOLD", is_curr=True)
        render_metric(r5, "WTI", is_curr=True)
        render_metric(r6, "BRENT", is_curr=True)

        st.markdown("---")
        st.subheader(_["h_eval"])
        
        ec1, ec2 = st.columns(2)
        y10 = macro_data.get("10Y", {}).get("price")
        y3m = macro_data.get("3M", {}).get("price")
        vix = macro_data.get("VIX", {}).get("price")
        dxy = macro_data.get("DXY", {}).get("price")
        fed = macro_data.get("FED", {}).get("price")

        with ec1:
            st.markdown(f"**{_['eval_yc']}**")
            if y10 is not None and y3m is not None:
                spread = y10 - y3m
                if spread < 0:
                    st.error(f"⚠️ {_['eval_yc_inv']} (Spread: {spread:.2f} %)")
                else:
                    st.success(f"✅ {_['eval_yc_norm']} (Spread: +{spread:.2f} %)")

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
                f_hist = macro_data.get("FED_hist", {})
                st.info(f"""
                🏦 **{_['fed_now']} {fed:.2f} %**
                - {_['fed_1w']} {f_hist.get('1w', 'N/A'):.2f} %
                - {_['fed_1m']} {f_hist.get('1m', 'N/A'):.2f} %
                """)

    with tab_analysis:
        st.subheader(_["perf_sel"])
        asset_options = {name: key for key, (ticker, name) in MACRO_TICKERS.items() if key in macro_data}
        
        col_sel, col_s1, col_s2 = st.columns([2, 1, 1])
        selected_asset_name = col_sel.selectbox("", list(asset_options.keys()), label_visibility="collapsed")
        show_sma50 = col_s1.checkbox("Zobrazit SMA 50", value=True)
        show_sma200 = col_s2.checkbox("Zobrazit SMA 200", value=True)
        
        if selected_asset_name:
            sel_key = asset_options[selected_asset_name]
            sel_hist = macro_history[sel_key].dropna(subset=['Close'])
            sel_perf = macro_data[sel_key]["performance"]
            
            df_perf = pd.DataFrame([sel_perf])
            st.table(df_perf)
            
            fig_perf = go.Figure()
            fig_perf.add_trace(go.Scatter(x=sel_hist.index, y=sel_hist["Close"], mode='lines', name='Cena (Close)', line=dict(color='#2962FF', width=2)))
            
            if show_sma50 and "SMA50" in sel_hist.columns:
                fig_perf.add_trace(go.Scatter(x=sel_hist.index, y=sel_hist["SMA50"], mode='lines', name='SMA 50', line=dict(color='#00E676', width=1, dash='dash')))
            if show_sma200 and "SMA200" in sel_hist.columns:
                fig_perf.add_trace(go.Scatter(x=sel_hist.index, y=sel_hist["SMA200"], mode='lines', name='SMA 200', line=dict(color='#E91E63', width=1.5, dash='dashdot')))
            
            if sel_key == "FED":
                fig_perf.update_yaxes(autorange="reversed")
            
            fig_perf.update_xaxes(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1M", step="month", stepmode="backward"),
                        dict(count=6, label="6M", step="month", stepmode="backward"),
                        dict(count=1, label="YTD", step="year", stepmode="todate"),
                        dict(count=1, label="1Y", step="year", stepmode="backward"),
                        dict(count=5, label="5Y", step="year", stepmode="backward"),
                        dict(step="all", label="MAX")
                    ]),
                    bgcolor="#1E1E1E", activecolor="#4CAF50", font=dict(color="white")
                )
            )
            
            fig_perf.update_layout(template="plotly_dark", height=500, margin=dict(l=0, r=0, t=30, b=0), hovermode='x unified')
            st.plotly_chart(fig_perf, use_container_width=True, config={'displayModeBar': False})