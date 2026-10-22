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
        "tab_analysis": "📈 HLOUBKOVÁ ANALÝZA & SROVNÁNÍ",
        "tab_fed": "🏦 FEDWATCH TOOL",
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
        "metrics_h1": "Dluhopisový trh & FED",
        "metrics_h2": "Akciové indexy",
        "metrics_h3": "Riziko, Komodity & Likvidita",
        "m_10y": "10Y Treasury",
        "m_30y": "30Y Treasury",
        "m_3m": "3M T-Bill",
        "m_fed": "Implikovaná sazba FEDu",
        "m_sp500": "S&P 500",
        "m_nasdaq": "NASDAQ",
        "m_rsp": "RSP",
        "m_rut": "Russell 2000",
        "m_vix": "VIX",
        "m_dxy": "DXY",
        "m_wti": "Ropa WTI",
        "m_brent": "Ropa Brent",
        "m_gold": "Zlato",
        "m_btc": "Bitcoin",
        "perf_sel": "Vyberte instrument pro detailní profil:",
        "perf_mat": "Výkonnostní matice",
        "p_1w": "1 Týden",
        "p_1m": "1 Měsíc",
        "p_ytd": "YTD",
        "p_1y": "1 Rok",
        "p_3y": "3 Roky",
        "p_5y": "5 Let",
        "comp_sel": "Srovnání relativní procentuální výkonnosti (vyberte max 5 aktiv):",
        "comp_period": "Časový horizont pro srovnání:",
        "loading": "Načítání a agregace dekády makroekonomických dat...",
        "fed_title": "Pravděpodobnost cílové sazby (CME FedWatch Model)",
        "fed_next": "Nejbližší zasedání FOMC:",
        "fed_days": "Zbývá dní:",
        "fed_y": "Pravděpodobnost (%)",
        "fed_x": "Cílová sazba (v bps)",
        "f_tgt": "CÍLOVÁ SAZBA (BPS)",
        "f_now": "NYNÍ",
        "f_1d": "1 DEN",
        "f_1w": "1 TÝDEN",
        "f_1m": "1 MĚSÍC",
        "chart_yc": "Spread výnosové křivky (10Y minus 3M)",
        "chart_vix": "Historie indexu strachu (VIX)",
        "sys_risk": "Systémová rizika trhu",
        "help_title": "📖 JAK ČÍST TENTO RADAR (NÁPOVĚDA)",
        "help_text": """
**1. Výnosová křivka (Spread 10Y - 3M)**
Základní ukazatel zdraví ekonomiky. Pokud je výnos krátkodobých 3M dluhopisů vyšší než 10Y (spread je záporný), trh je v tzv. inverzi. To historicky předpovídá recesi.

**2. Očekávání sazeb FEDu**
Aplikace analyzuje cenu futures kontraktů na úrokové sazby (ZQ=F). Neukazuje oficiální sazbu, ale to, **co si myslí trh**, že FED udělá.

**3. VIX (Index strachu)**
Měří očekávanou volatilitu. Hodnoty pod 15 znamenají absolutní klid (Risk-On). Hodnoty nad 25 signalizují paniku (Risk-Off).

**4. DXY (Dolarový index)**
Ukazuje sílu USD proti koši světových měn. Silný dolar (nad 105) zdražuje americké zboží a sráží ceny komodit.

**5. S&P 500 vs. RSP (Equal Weight)**
Pokud S&P 500 roste, ale RSP klesá, trh je nezdravý a drží ho nad vodou jen pár technologických gigantů.
        """
    },
    "EN": {
        "title": "🌍 MACROECONOMIC DASHBOARD & RISK",
        "desc": "TRACKING YIELD CURVE, INDICES, VOLATILITY, INFLATION, AND LIQUIDITY.",
        "tab_dash": "🧭 MACRO DASHBOARD",
        "tab_analysis": "📈 DEEP ANALYSIS & COMPARISON",
        "tab_fed": "🏦 FEDWATCH TOOL",
        "h_eval": "Automated Market Environment Evaluation",
        "eval_yc": "Yield Curve Steepness / Inversion",
        "eval_yc_inv": "Curve is INVERTED (10Y < 3M). Historically strong signal of approaching economic recession. Credit market under pressure.",
        "eval_yc_norm": "Curve is NORMAL (10Y > 3M). Healthy economic environment, market pricing in future growth.",
        "eval_vix": "Fear Index (VIX)",
        "eval_vix_low": "Low volatility. Market is calm, potentially complacent (Greed).",
        "eval_vix_mid": "Normal market volatility. Environment without extreme swings.",
        "eval_vix_high": "Elevated nervousness and fear. Investors buying protection.",
        "eval_vix_panic": "Extreme PANIC. Market selling off sharply.",
        "eval_dxy": "US Dollar Strength (DXY)",
        "eval_dxy_high": "Strong dollar. Acts as a headwind for US multinational corporations and pressures commodity prices.",
        "eval_dxy_low": "Weaker dollar. Supports commodity prices and US multinational earnings.",
        "metrics_h1": "Bond Market & FED",
        "metrics_h2": "Equity Indices",
        "metrics_h3": "Risk, Commodities & Liquidity",
        "m_10y": "10Y Treasury",
        "m_30y": "30Y Treasury",
        "m_3m": "3M T-Bill",
        "m_fed": "Implied FED Rate",
        "m_sp500": "S&P 500",
        "m_nasdaq": "NASDAQ",
        "m_rsp": "RSP",
        "m_rut": "Russell 2000",
        "m_vix": "VIX",
        "m_dxy": "DXY",
        "m_wti": "WTI Crude",
        "m_brent": "Brent Crude",
        "m_gold": "Gold",
        "m_btc": "Bitcoin",
        "perf_sel": "Select instrument for detailed profile:",
        "perf_mat": "Performance Matrix",
        "p_1w": "1 Week",
        "p_1m": "1 Month",
        "p_ytd": "YTD",
        "p_1y": "1 Year",
        "p_3y": "3 Years",
        "p_5y": "5 Years",
        "comp_sel": "Relative percentage performance comparison (max 5 assets):",
        "comp_period": "Comparison time horizon:",
        "loading": "Loading and aggregating a decade of macroeconomic data...",
        "fed_title": "Target Rate Probabilities (CME FedWatch Model)",
        "fed_next": "Next FOMC Meeting:",
        "fed_days": "Days remaining:",
        "fed_y": "Probability (%)",
        "fed_x": "Target Rate (in bps)",
        "f_tgt": "TARGET RATE (BPS)",
        "f_now": "NOW",
        "f_1d": "1 DAY",
        "f_1w": "1 WEEK",
        "f_1m": "1 MONTH",
        "chart_yc": "Yield Curve Spread (10Y minus 3M)",
        "chart_vix": "VIX History",
        "sys_risk": "Systemic Market Risks",
        "help_title": "📖 HOW TO READ THIS RADAR (GUIDE)",
        "help_text": """
**1. Yield Curve (10Y - 3M Spread)**
A primary indicator of economic health. If 3M yields exceed 10Y (negative spread), the curve is inverted.

**2. FED Rate Expectations**
The app analyzes FED Funds Futures (ZQ=F). It shows **what the market expects** the FED to do.

**3. VIX (Fear Index)**
Measures expected volatility. Under 15 means calm (Risk-On). Over 25 signals panic (Risk-Off).

**4. DXY (Dollar Index)**
Measures USD strength against a global basket. A strong dollar (>105) hurts US exports and pressures commodities.

**5. S&P 500 vs. RSP (Equal Weight)**
If S&P 500 is rising while RSP is falling, the rally lacks breadth.
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

# CME FOMC Schedule pro 2026/2027
FOMC_DATES = [
    datetime(2026, 10, 28), datetime(2026, 12, 9),
    datetime(2027, 1, 27), datetime(2027, 3, 17),
    datetime(2027, 4, 28), datetime(2027, 6, 9),
    datetime(2027, 7, 28), datetime(2027, 9, 15),
    datetime(2027, 10, 27), datetime(2027, 12, 8)
]

def safe_iloc(df, steps_back):
    if len(df) > steps_back:
        return df['Close'].iloc[-(steps_back+1)]
    return None

def calc_fed_probs(implied_rate):
    lower_bound = (implied_rate // 0.25) * 0.25
    mid_point = lower_bound + 0.125
    
    if implied_rate >= mid_point:
        prob_move = (implied_rate - mid_point) / 0.25
        prob_stay = 1.0 - prob_move
        return {
            "current_target": f"{int(lower_bound*100)}-{int((lower_bound+0.25)*100)}",
            "next_target": f"{int((lower_bound+0.25)*100)}-{int((lower_bound+0.50)*100)}",
            "prob_stay": prob_stay * 100,
            "prob_move": prob_move * 100
        }
    else:
        prob_move = (mid_point - implied_rate) / 0.25
        prob_stay = 1.0 - prob_move
        return {
            "current_target": f"{int(lower_bound*100)}-{int((lower_bound+0.25)*100)}",
            "next_target": f"{int((lower_bound-0.25)*100)}-{int(lower_bound*100)}",
            "prob_stay": prob_stay * 100,
            "prob_move": prob_move * 100
        }

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
                
                if key == "FED":
                    data["FED_hist"] = {
                        "now": current_price,
                        "1d": prev_price,
                        "1w": perf[_["p_1w"]] if perf[_["p_1w"]] else current_price,
                        "1m": perf[_["p_1m"]] if perf[_["p_1m"]] else current_price
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
    tab_dash, tab_analysis, tab_fed = st.tabs([_["tab_dash"], _["tab_analysis"], _["tab_fed"]])

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

    with tab_analysis:
        # 1. HLOUBKOVÝ PROFIL AKTIVA
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
            fig_perf.add_trace(go.Scatter(x=sel_hist.index, y=sel_hist["Close"], mode='lines', name=selected_asset_name, line=dict(color='#2962FF', width=2)))
            
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
            
            fig_perf.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=10, b=0), hovermode='x unified')
            st.plotly_chart(fig_perf, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")
        
        # 2. RELATIVNÍ SROVNÁNÍ VÍCE AKTIV
        st.subheader(_["comp_sel"])
        default_selections = [_["m_sp500"], _["m_nasdaq"], _["m_btc"]]
        valid_defaults = [a for a in default_selections if a in asset_options]
        
        selected_compare = st.multiselect("", list(asset_options.keys()), default=valid_defaults, max_selections=5, label_visibility="collapsed")
        period = st.radio(_["comp_period"], ["1M", "6M", "YTD", "1Y", "3Y", "5Y"], horizontal=True, index=3)
        
        if selected_compare:
            fig_comp = go.Figure()
            period_map = {"1M": 21, "6M": 126, "1Y": 252, "3Y": 252*3, "5Y": 252*5}
            
            for asset_name in selected_compare:
                c_key = asset_options[asset_name]
                df_hist = macro_history[c_key].dropna(subset=['Close']).copy()
                
                if period == "YTD":
                    df_hist = df_hist[df_hist.index.year == datetime.now().year]
                else:
                    days = period_map.get(period, 252)
                    df_hist = df_hist.tail(days)
                    
                if not df_hist.empty:
                    first_val = df_hist['Close'].iloc[0]
                    if first_val != 0:
                        pct_series = ((df_hist['Close'] / first_val) - 1) * 100
                    else:
                        pct_series = df_hist['Close'] * 0
                        
                    fig_comp.add_trace(go.Scatter(x=df_hist.index, y=pct_series, mode='lines', name=asset_name, line=dict(width=2)))
            
            fig_comp.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=10, b=0), hovermode='x unified', yaxis_ticksuffix="%")
            st.plotly_chart(fig_comp, use_container_width=True, config={'displayModeBar': False})

        st.markdown("---")
        
        # 3. SYSTÉMOVÁ RIZIKA
        st.subheader(_["sys_risk"])
        if "10Y" in macro_history and "3M" in macro_history:
            df_10y = macro_history["10Y"][['Close']].rename(columns={"Close": "10Y"})
            df_3m = macro_history["3M"][['Close']].rename(columns={"Close": "3M"})
            df_spread = df_10y.join(df_3m).dropna()
            df_spread["Spread"] = df_spread["10Y"] - df_spread["3M"]
            df_spread = df_spread.tail(252*5)
            
            fig_spread = go.Figure()
            fig_spread.add_trace(go.Scatter(x=df_spread.index, y=df_spread["Spread"], mode='lines', name='10Y - 3M Spread', line=dict(color='#E91E63', width=2)))
            fig_spread.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Hranice inverze (0%)", annotation_position="bottom right")
            fig_spread.update_layout(title=_["chart_yc"], template="plotly_dark", height=300, margin=dict(l=0, r=0, t=40, b=0), hovermode='x unified')
            st.plotly_chart(fig_spread, use_container_width=True, config={'displayModeBar': False})
            
        if "VIX" in macro_history:
            df_vix = macro_history["VIX"].tail(252*5)
            fig_vix = go.Figure()
            fig_vix.add_trace(go.Scatter(x=df_vix.index, y=df_vix["Close"], mode='lines', name='VIX', line=dict(color='#FFA726', width=2)))
            fig_vix.add_hline(y=25, line_dash="dash", line_color="red", annotation_text="Hranice strachu (25)", annotation_position="top right")
            fig_vix.update_layout(title=_["chart_vix"], template="plotly_dark", height=300, margin=dict(l=0, r=0, t=40, b=0), hovermode='x unified')
            st.plotly_chart(fig_vix, use_container_width=True, config={'displayModeBar': False})

    with tab_fed:
        st.subheader(_["fed_title"])
        
        # Info o dalsim zasedani FOMC
        today = datetime.now()
        next_meeting = next((d for d in FOMC_DATES if d >= today), None)
        
        if next_meeting:
            days_left = (next_meeting - today).days
            mtg_str = next_meeting.strftime("%d. %m. %Y")
            
            mc1, mc2 = st.columns(2)
            mc1.info(f"🏛️ **{_['fed_next']}** {mtg_str}")
            mc2.warning(f"⏳ **{_['fed_days']}** {days_left}")
            st.markdown("<br>", unsafe_allow_html=True)
            
        if "FED_hist" in macro_data:
            f_hist = macro_data["FED_hist"]
            
            probs_now = calc_fed_probs(f_hist["now"])
            probs_1d = calc_fed_probs(f_hist["1d"])
            probs_1w = calc_fed_probs(f_hist["1w"])
            probs_1m = calc_fed_probs(f_hist["1m"])

            fig_fed = go.Figure()
            fig_fed.add_trace(go.Bar(
                x=[probs_now["current_target"], probs_now["next_target"]],
                y=[probs_now["prob_stay"], probs_now["prob_move"]],
                text=[f"{probs_now['prob_stay']:.1f}%", f"{probs_now['prob_move']:.1f}%"],
                textposition='outside',
                marker_color='#2980B9'
            ))

            fig_fed.update_layout(
                template="plotly_dark", 
                height=400,
                yaxis=dict(title=_["fed_y"], range=[0, 105], ticksuffix="%"),
                xaxis=dict(title=_["fed_x"]),
                margin=dict(l=0, r=0, t=10, b=0)
            )
            st.plotly_chart(fig_fed, use_container_width=True, config={'displayModeBar': False})

            df_fed_prob = pd.DataFrame({
                _["f_tgt"]: [probs_now["current_target"], probs_now["next_target"]],
                _["f_now"]: [f"{probs_now['prob_stay']:.1f}%", f"{probs_now['prob_move']:.1f}%"],
                _["f_1d"]: [f"{probs_1d['prob_stay']:.1f}%", f"{probs_1d['prob_move']:.1f}%"],
                _["f_1w"]: [f"{probs_1w['prob_stay']:.1f}%", f"{probs_1w['prob_move']:.1f}%"],
                _["f_1m"]: [f"{probs_1m['prob_stay']:.1f}%", f"{probs_1m['prob_move']:.1f}%"]
            })
            st.table(df_fed_prob.set_index(_["f_tgt"]))