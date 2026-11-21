import streamlit as st
import pandas as pd
import yfinance as yf
import os
import sys
import calendar
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta

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
        "title": "MAKROEKONOMICKÝ PANEL & RIZIKA",
        "desc": "SLEDOVÁNÍ VÝNOSOVÉ KŘIVKY, INDEXŮ, VOLATILITY, INFLACE A LIKVIDITY.",
        "tab_dash": "MAKRO DASHBOARD",
        "tab_analysis": "ANALÝZA & SROVNÁNÍ",
        "tab_fed": "FEDWATCH TOOL",
        "h_eval": "Vyhodnocení tržního prostředí",
        "eval_yc": "Výnosová křivka",
        "eval_yc_inv": "INVERZE (10Y < 3M). Úvěrový trh pod tlakem. Historický signál recese.",
        "eval_yc_norm": "NORMÁLNÍ (10Y > 3M). Trh oceňuje budoucí růst.",
        "eval_fng": "Market Sentiment (Fear & Greed)",
        "eval_dxy": "Síla USD (DXY)",
        "eval_dxy_high": "Silný dolar. Protivítr pro nadnárodní zisky a komodity.",
        "eval_dxy_low": "Slabší dolar. Podporuje ceny komodit a zámořské zisky.",
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
        "perf_header": "DETAILNÍ PROFIL AKTIVA",
        "perf_sel": "Vyberte instrument:",
        "perf_mat": "Výkonnostní matice",
        "p_1w": "1 Týden",
        "p_1m": "1 Měsíc",
        "p_ytd": "YTD",
        "p_1y": "1 Rok",
        "p_3y": "3 Roky",
        "p_5y": "5 Let",
        "comp_header": "RELATIVNÍ SROVNÁNÍ",
        "comp_sel": "Vyberte aktiva k porovnání:",
        "comp_period": "Časový horizont:",
        "loading": "Načítání makroekonomických dat...",
        "fed_title": "Pravděpodobnost cílové sazby (CME FedWatch Model)",
        "fed_sel_mtg": "Zasedání FOMC:",
        "fed_current_bracket": "Aktuální pásmo sazeb FEDu:",
        "fed_next": "Zasedání FOMC:",
        "fed_days": "Zbývá dní:",
        "fed_y": "Pravděpodobnost (%)",
        "fed_x": "Cílová sazba (v bps)",
        "f_tgt": "CÍLOVÁ SAZBA (BPS)",
        "f_now": "NYNÍ",
        "f_1d": "1 DEN",
        "f_1w": "1 TÝDEN",
        "f_1m": "1 MĚSÍC",
        "fed_curr_lbl": "Aktuální cílové pásmo je",
        "fed_curr_tbl": " (Aktuální)",
        "fed_err": "Nepodařilo se stáhnout měsíční Fed Funds futures kontrakty z CBOT.",
        "chart_yc": "Spread výnosové křivky (10Y minus 3M)",
        "chart_vix": "Index strachu (VIX)",
        "sys_risk": "Systémová rizika",
        "help_title": "NÁPOVĚDA",
        "help_text": """
**1. Výnosová křivka (Spread 10Y - 3M)**
Základní ukazatel zdraví ekonomiky. Výnos krátkodobých dluhopisů vyšší než 10Y znamená inverzi.

**2. Očekávání sazeb FEDu (CME Metodika)**
Pravděpodobnosti vypočítané přímo z měsíčních 30-Day Fed Funds futures kontraktů na CBOT (`ZQ*.CBT`) s váženým průměrem dnů před a po zasedání FOMC.

**3. Fear & Greed Index**
Agregovaný sentiment trhu. <25: Extreme Fear (příležitost k akumulaci). >75: Extreme Greed (zvýšené riziko korekce).

**4. DXY (Dolarový index)**
Síla USD. Silný dolar (>105) sráží komodity.

**5. S&P 500 vs. RSP (Equal Weight)**
Pokud S&P roste a RSP klesá, trh je tažen úzkou skupinou firem.
        """
    },
    "EN": {
        "title": "MACROECONOMIC DASHBOARD & RISK",
        "desc": "TRACKING YIELD CURVE, INDICES, VOLATILITY, INFLATION, AND LIQUIDITY.",
        "tab_dash": "MACRO DASHBOARD",
        "tab_analysis": "DEEP ANALYSIS & COMPARISON",
        "tab_fed": "FEDWATCH TOOL",
        "h_eval": "Market Environment Evaluation",
        "eval_yc": "Yield Curve",
        "eval_yc_inv": "INVERTED (10Y < 3M). Credit market under pressure. Recession signal.",
        "eval_yc_norm": "NORMAL (10Y > 3M). Market pricing in future growth.",
        "eval_fng": "Market Sentiment (Fear & Greed)",
        "eval_dxy": "USD Strength (DXY)",
        "eval_dxy_high": "Strong dollar. Headwind for multinationals and commodities.",
        "eval_dxy_low": "Weaker dollar. Supports commodities and overseas earnings.",
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
        "perf_header": "ASSET PROFILE",
        "perf_sel": "Select instrument:",
        "perf_mat": "Performance Matrix",
        "p_1w": "1 Week",
        "p_1m": "1 Month",
        "p_ytd": "YTD",
        "p_1y": "1 Year",
        "p_3y": "3 Years",
        "p_5y": "5 Years",
        "comp_header": "RELATIVE COMPARISON",
        "comp_sel": "Select assets to compare:",
        "comp_period": "Time horizon:",
        "loading": "Loading macroeconomic data...",
        "fed_title": "Target Rate Probabilities (CME FedWatch Model)",
        "fed_sel_mtg": "FOMC Meeting:",
        "fed_current_bracket": "Current FED Target Bracket:",
        "fed_next": "FOMC Meeting:",
        "fed_days": "Days remaining:",
        "fed_y": "Probability (%)",
        "fed_x": "Target Rate (in bps)",
        "f_tgt": "TARGET RATE (BPS)",
        "f_now": "NOW",
        "f_1d": "1 DAY",
        "f_1w": "1 WEEK",
        "f_1m": "1 MONTH",
        "fed_curr_lbl": "Current target range is",
        "fed_curr_tbl": " (Current)",
        "fed_err": "Could not load monthly CBOT Fed Funds futures contracts.",
        "chart_yc": "Yield Curve Spread (10Y minus 3M)",
        "chart_vix": "VIX History",
        "sys_risk": "Systemic Risks",
        "help_title": "GUIDE",
        "help_text": """
**1. Yield Curve (10Y - 3M Spread)**
Primary economic health indicator. 3M > 10Y implies inversion.

**2. FED Rate Expectations (CME Methodology)**
Implied probabilities calculated from monthly CBOT 30-Day Fed Funds futures (`ZQ*.CBT`) using day-count weighting before and after the FOMC meeting.

**3. Fear & Greed Index**
Aggregated market sentiment. <25: Extreme Fear. >75: Extreme Greed.

**4. DXY (Dollar Index)**
USD strength. Strong dollar (>105) pressures commodities.

**5. S&P 500 vs. RSP (Equal Weight)**
Divergence signals narrow market breadth.
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

RATES = ["10Y", "30Y", "3M", "FED"]

FOMC_DATES = [
    datetime(2026, 10, 28), datetime(2026, 12, 9),
    datetime(2027, 1, 27), datetime(2027, 3, 17),
    datetime(2027, 4, 28), datetime(2027, 6, 9),
    datetime(2027, 7, 28), datetime(2027, 9, 15),
    datetime(2027, 10, 27), datetime(2027, 12, 8)
]

FUTURES_MONTH_CODES = {
    1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M",
    7: "N", 8: "Q", 9: "U", 10: "V", 11: "X", 12: "Z"
}

def zq_ticker_for(year, month):
    return f"ZQ{FUTURES_MONTH_CODES[month]}{str(year)[-2:]}.CBT"

def safe_iloc(df, steps_back):
    if len(df) > steps_back:
        return float(df['Close'].iloc[-(steps_back+1)])
    return None

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_cme_fedwatch_data():
    """
    Přesná replika CME FedWatch:
    1. Určí aktuální cílové pásmo z aktuálního měsíčního ZQ kontraktu (kde v měsíci bez FOMC leží EFFR na středu pásma).
    2. Pro vybrané FOMC zasedání stáhne příslušný měsíční ZQ kontrakt (a předchozí měsíc).
    3. Spočítá vážený průměr dnů v měsíci před rozhodnutím FOMC a po něm (změna platí den po zasedání).
    """
    today = datetime.now()
    future_meetings = [d for d in FOMC_DATES if d.date() >= today.date()]
    if not future_meetings:
        return None

    # Stáhneme futures pro aktuální měsíc a pro následujících 6 zasedání
    months_needed = {(today.year, today.month)}
    for m_dt in future_meetings[:6]:
        months_needed.add((m_dt.year, m_dt.month))
        prev_m_dt = m_dt.replace(day=1) - timedelta(days=1)
        months_needed.add((prev_m_dt.year, prev_m_dt.month))

    zq_hist = {}
    for (y, m) in sorted(months_needed):
        sym = zq_ticker_for(y, m)
        try:
            h = yf.Ticker(sym, session=session).history(period="3mo")
            if not h.empty:
                zq_hist[(y, m)] = 100.0 - h['Close']
        except Exception:
            pass

    if not zq_hist:
        return None

    # Určení aktuálního cílového pásma Fedu (zaokrouhleno na nejbližší 0.25 % pásmo kolem EFFR)
    curr_series = zq_hist.get((today.year, today.month))
    if curr_series is None or curr_series.empty:
        first_key = sorted(zq_hist.keys())[0]
        curr_series = zq_hist[first_key]
    effr_now = float(curr_series.iloc[-1])

    # Pásmo má šířku 0.25 %, střed je lower + 0.125 -> lower = round((effr - 0.125) / 0.25) * 0.25
    curr_lower = round((effr_now - 0.125) / 0.25) * 0.25
    curr_mid = curr_lower + 0.125

    def get_rate_at_offset(series, offset):
        if series is None or series.empty:
            return None
        if offset == 0:
            return float(series.iloc[-1])
        if len(series) > offset:
            return float(series.iloc[-(offset + 1)])
        return float(series.iloc[0])

    meetings_output = []
    running_mids = {0: curr_mid, 1: curr_mid, 5: curr_mid, 21: curr_mid}

    for mtg in future_meetings[:6]:
        s_mtg = zq_hist.get((mtg.year, mtg.month))
        if s_mtg is None or s_mtg.empty:
            continue

        days_in_month = calendar.monthrange(mtg.year, mtg.month)[1]
        # Zasedání končí v den mtg.day; nová sazba vstupuje v platnost následující den
        days_before = mtg.day
        days_after = days_in_month - days_before

        # Zjistíme, zda v témže měsíci nebylo dřívější zasedání (zpravidla není, FOMC zasedá 8x ročně)
        prev_m_dt = mtg.replace(day=1) - timedelta(days=1)
        s_prev = zq_hist.get((prev_m_dt.year, prev_m_dt.month))

        snap_probs = {}
        for off in (0, 1, 5, 21):
            r_month = get_rate_at_offset(s_mtg, off)
            if r_month is None:
                continue

            # Počáteční sazba před tímto zasedáním
            if (mtg.year, mtg.month) == (today.year, today.month) and off == 0:
                r_start = curr_mid
            elif s_prev is not None and not s_prev.empty:
                r_prev_val = get_rate_at_offset(s_prev, off)
                # Zaokrouhlíme předchozí měsíc na nejbližší 25bps střed pásma (pokud v předchozím měsíci nebylo FOMC, rovná se přesně středu)
                r_start = round((r_prev_val - 0.125) / 0.25) * 0.25 + 0.125
            else:
                r_start = running_mids[off]

            # CME rovnice: r_month = (days_before * r_start + days_after * r_end) / days_in_month
            if days_after > 0:
                r_end = (r_month * days_in_month - days_before * r_start) / days_after
            else:
                r_end = r_month

            running_mids[off] = r_end

            # Převod r_end na pravděpodobnosti sousedních 25 bps pásem (CME Binomický strom)
            end_lower = (r_end // 0.25) * 0.25
            end_mid_low = end_lower + 0.125
            if r_end >= end_mid_low:
                b1_low = end_lower
                b2_low = end_lower + 0.25
                p2 = (r_end - end_mid_low) / 0.25
                p1 = 1.0 - p2
            else:
                b1_low = end_lower - 0.25
                b2_low = end_lower
                p2 = (r_end - (b1_low + 0.125)) / 0.25
                p1 = 1.0 - p2

            p1 = max(0.0, min(1.0, p1)) * 100.0
            p2 = max(0.0, min(1.0, p2)) * 100.0

            lbl1 = f"{int(round(b1_low*100))}-{int(round((b1_low+0.25)*100))}"
            lbl2 = f"{int(round(b2_low*100))}-{int(round((b2_low+0.25)*100))}"
            snap_probs[off] = {lbl1: p1, lbl2: p2}

        meetings_output.append({
            "date": mtg,
            "date_str": mtg.strftime("%d. %m. %Y"),
            "curr_bracket": f"{int(round(curr_lower*100))}-{int(round((curr_lower+0.25)*100))}",
            "curr_lower": curr_lower,
            "probs": snap_probs
        })

    return meetings_output

@st.cache_data(ttl=3600)
def fetch_fng():
    try:
        r = requests.get('https://production.dataviz.cnn.io/index/fearandgreed/graphdata', headers=session.headers, timeout=5)
        data = r.json()
        return data['fear_and_greed']['score'], data['fear_and_greed']['rating']
    except:
        return None, None

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
                pct_chg = ((current_price / prev_price) - 1) * 100 if prev_price and key not in RATES else None
                
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
                
                calculated_perf = {}
                for p_key, p_val in perf.items():
                    if p_val is not None:
                        if key in RATES:
                            calculated_perf[p_key] = f"{(current_price - p_val) * 100:+.0f} bps"
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
    fng_score, fng_rating = fetch_fng()
    fedwatch_meetings = fetch_cme_fedwatch_data()

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
            elif key in RATES: val_str = f"{val:.2f} %"
            else: val_str = f"{val:,.2f}"
            
            sign = "-" if abs_chg < 0 else "+"
            val_abs = abs(abs_chg)
            
            if key in RATES:
                delta_str = f"{sign}{val_abs * 100:.1f} bps"
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
        
        st.subheader(_["metrics_h2"])
        i1, i2, i3, i4 = st.columns(4)
        render_metric(i1, "SP500")
        render_metric(i2, "NASDAQ")
        render_metric(i3, "RSP")
        render_metric(i4, "RUT")

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
        
        ec1, ec2, ec3 = st.columns(3)
        y10 = macro_data.get("10Y", {}).get("price")
        y3m = macro_data.get("3M", {}).get("price")
        dxy = macro_data.get("DXY", {}).get("price")

        with ec1:
            st.markdown(f"**{_['eval_yc']}:**")
            if y10 is not None and y3m is not None:
                spread = y10 - y3m
                if spread < 0:
                    st.error(f"{_['eval_yc_inv']} (Spread: {spread:.2f} %)")
                else:
                    st.success(f"{_['eval_yc_norm']} (Spread: +{spread:.2f} %)")

        with ec2:
            if fng_score is not None:
                if fng_score < 25: 
                    state_text = "Extrémní strach" if st.session_state.lang == "CZ" else "Extreme Fear"
                    color = "#EF5350"
                elif fng_score < 45: 
                    state_text = "Strach" if st.session_state.lang == "CZ" else "Fear"
                    color = "#FFA726"
                elif fng_score <= 55: 
                    state_text = "Neutrální" if st.session_state.lang == "CZ" else "Neutral"
                    color = "#9E9E9E"
                elif fng_score <= 75: 
                    state_text = "Chamtivost" if st.session_state.lang == "CZ" else "Greed"
                    color = "#66BB6A"
                else: 
                    state_text = "Extrémní chamtivost" if st.session_state.lang == "CZ" else "Extreme Greed"
                    color = "#2E7D32"
                
                st.markdown(f"**{_['eval_fng']}:** <span style='color:{color}; font-weight:bold;'>{state_text}</span>", unsafe_allow_html=True)
                
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=fng_score,
                    gauge={
                        'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
                        'bar': {'color': "white", 'thickness': 0.15},
                        'steps': [
                            {'range': [0, 25], 'color': "#EF5350"},
                            {'range': [25, 45], 'color': "#FFA726"},
                            {'range': [45, 55], 'color': "#9E9E9E"},
                            {'range': [55, 75], 'color': "#66BB6A"},
                            {'range': [75, 100], 'color': "#2E7D32"}
                        ]
                    }
                ))
                fig_gauge.update_layout(template="plotly_dark", height=160, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})
            else:
                st.markdown(f"**{_['eval_fng']}:**")
                st.info("Data nedostupná.")

        with ec3:
            st.markdown(f"**{_['eval_dxy']}:**")
            if dxy is not None:
                if dxy > 105:
                    st.warning(f"{_['eval_dxy_high']} (DXY: {dxy:.2f})")
                else:
                    st.success(f"{_['eval_dxy_low']} (DXY: {dxy:.2f})")

    with tab_analysis:
        asset_options = {name: key for key, (ticker, name) in MACRO_TICKERS.items() if key in macro_data}
        
        st.markdown(f"#### {_['perf_header']}")
        col_sel, col_chk = st.columns([3, 2])
        selected_asset_name = col_sel.selectbox("", list(asset_options.keys()), index=None, placeholder=_["perf_sel"], label_visibility="collapsed")
        
        s_col1, s_col2 = col_chk.columns(2)
        show_sma50 = s_col1.checkbox("Zobrazit SMA 50", value=True)
        show_sma200 = s_col2.checkbox("Zobrazit SMA 200", value=True)
        
        if selected_asset_name:
            sel_key = asset_options[selected_asset_name]
            sel_hist = macro_history[sel_key].dropna(subset=['Close'])
            sel_perf = macro_data[sel_key]["performance"]
            
            st.markdown(f"### {_['perf_mat']} — {selected_asset_name}")
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
        
        st.markdown(f"#### {_['comp_header']}")
        selected_compare = st.multiselect("", list(asset_options.keys()), default=[], max_selections=5, placeholder=_["comp_sel"], label_visibility="collapsed")
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
        
        st.subheader(_["sys_risk"])
        if "10Y" in macro_history and "3M" in macro_history:
            df_10y = macro_history["10Y"][['Close']].rename(columns={"Close": "10Y"})
            df_3m = macro_history["3M"][['Close']].rename(columns={"Close": "3M"})
            df_spread = df_10y.join(df_3m).dropna()
            df_spread["Spread"] = df_spread["10Y"] - df_spread["3M"]
            df_spread = df_spread.tail(252*5)
            
            fig_spread = go.Figure()
            fig_spread.add_trace(go.Scatter(x=df_spread.index, y=df_spread["Spread"], mode='lines', name='10Y - 3M Spread', line=dict(color='#E91E63', width=2)))
            fig_spread.add_hline(y=0, line_dash="dash", line_color="red")
            fig_spread.update_layout(title=_["chart_yc"], template="plotly_dark", height=300, margin=dict(l=0, r=0, t=40, b=0), hovermode='x unified')
            st.plotly_chart(fig_spread, use_container_width=True, config={'displayModeBar': False})
            
        if "VIX" in macro_history:
            df_vix = macro_history["VIX"].tail(252*5)
            fig_vix = go.Figure()
            fig_vix.add_trace(go.Scatter(x=df_vix.index, y=df_vix["Close"], mode='lines', name='VIX', line=dict(color='#FFA726', width=2)))
            fig_vix.add_hline(y=25, line_dash="dash", line_color="red")
            fig_vix.update_layout(title=_["chart_vix"], template="plotly_dark", height=300, margin=dict(l=0, r=0, t=40, b=0), hovermode='x unified')
            st.plotly_chart(fig_vix, use_container_width=True, config={'displayModeBar': False})

    with tab_fed:
        st.subheader(_["fed_title"])
        
        if fedwatch_meetings:
            mtg_labels = [m["date_str"] for m in fedwatch_meetings]
            sel_mtg_str = st.radio(_["fed_sel_mtg"], mtg_labels, horizontal=True)
            sel_mtg = next(m for m in fedwatch_meetings if m["date_str"] == sel_mtg_str)

            today = datetime.now()
            days_left = max(0, (sel_mtg["date"].date() - today.date()).days)

            mc1, mc2 = st.columns(2)
            mc1.info(f"**{_['fed_next']}** {sel_mtg['date_str']}")
            mc2.warning(f"**{_['fed_days']}** {days_left}")

            curr_b = sel_mtg["curr_bracket"]
            st.markdown(f"<div style='text-align: center; margin-top: 20px; margin-bottom: 5px; font-size: 16px; color: #ECEFF1;'>{_['fed_curr_lbl']} <b>{curr_b} bps</b></div>", unsafe_allow_html=True)

            probs_map = sel_mtg["probs"]
            all_brackets = sorted(
                {b for snap in probs_map.values() for b in snap.keys()},
                key=lambda x: int(x.split("-")[0])
            )

            now_snap = probs_map.get(0, {})
            x_vals = all_brackets
            y_vals = [now_snap.get(b, 0.0) for b in x_vals]

            fig_fed = go.Figure()
            fig_fed.add_trace(go.Bar(
                x=x_vals,
                y=y_vals,
                text=[f"{v:.1f}%" for v in y_vals],
                textposition='outside',
                marker_color=['#22C55E' if b == curr_b else '#2980B9' for b in x_vals]
            ))

            fig_fed.update_layout(
                template="plotly_dark",
                height=360,
                yaxis=dict(title=_["fed_y"], range=[0, 110], ticksuffix="%"),
                xaxis=dict(title=_["fed_x"], type="category"),
                margin=dict(l=0, r=0, t=10, b=0)
            )
            st.plotly_chart(fig_fed, use_container_width=True, config={'displayModeBar': False})

            rows_tbl = []
            for b in all_brackets:
                lbl_b = f"{b}{_['fed_curr_tbl']}" if b == curr_b else b
                rows_tbl.append({
                    _["f_tgt"]: lbl_b,
                    _["f_now"]: f"{probs_map.get(0, {}).get(b, 0.0):.1f}%",
                    _["f_1d"]: f"{probs_map.get(1, {}).get(b, 0.0):.1f}%",
                    _["f_1w"]: f"{probs_map.get(5, {}).get(b, 0.0):.1f}%",
                    _["f_1m"]: f"{probs_map.get(21, {}).get(b, 0.0):.1f}%"
                })

            df_fed_prob = pd.DataFrame(rows_tbl).set_index(_["f_tgt"])
            st.table(df_fed_prob)
        else:
            st.warning(_["fed_err"])