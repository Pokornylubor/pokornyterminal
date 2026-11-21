import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os
import sys
import random
import requests
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
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

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
        "Accept-Language": "en-US,en;q=0.9"
    }

# --- CLEAN EDITORIAL CSS ---
st.markdown("""
<style>
@import url('[https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap](https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap)');

.stApp { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

.term-sec-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    font-weight: 600;
    color: #71717A;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin: 18px 0 10px 0;
}
.term-memo-box {
    width: 100%;
    padding: 24px 28px;
    background-color: #0D0F12;
    border: 1px solid #1F2227;
    border-radius: 6px;
    margin: 14px 0 22px 0;
}
</style>
""", unsafe_allow_html=True)

current_lang = st.session_state.get("lang", "CZ")

# --- DICTIONARY ---
t = {
    "CZ": {
        "title": "HLOUBKOVÝ ANALYTICKÝ TERMINÁL",
        "desc": "INSTITUCIONÁLNÍ ČASOVÁ OSA VÝKAZŮ, VALUACE, KONSENZUS A ZPRÁVY.",
        "db_select": "DATABÁZE",
        "custom_tick": "VLASTNÍ TICKER",
        "periodicity": "PERIODICITA MATICE:",
        "annual": "Roční (Annual)",
        "quarterly": "Kvartální (Quarterly)",
        "loading": "STAHOVÁNÍ VÝKAZŮ...",
        "err_data": "DATA PRO TENTO TICKER NEJSOU DOSTUPNÁ.",
        "tab_matrix": "FINANČNÍ MATICE & VÝHLED",
        "tab_val": "VALUACE & KPI",
        "tab_ai": "AI ANALYTIK",
        "tab_ana": "ANALYTICI & KONSENZUS",
        "tab_earn": "EARNINGS & HISTORIE",
        "tab_news": "NOVINKY & ČLÁNKY",
        "tab_raw": "STRUKTUROVANÁ ROZVAHA",
        "targets_h": "Wall Street Konsenzus & Cílové Ceny",
        "t_low": "Bear Target",
        "t_mean": "Konsenzus (Mean)",
        "t_high": "Bull Target",
        "t_rec": "Doporučení",
        "t_num": "Počet analytiků",
        "met_val": "VALUACE",
        "met_mul": "MULTIPLIKÁTORY & LIKVIDITA",
        "met_mar": "MARŽE (KASKÁDA)",
        "met_ret": "RENTABILITA",
        "met_ltm": "LTM (TTM) DATA",
        "r_rev": "Tržby (Revenue)",
        "r_rev_growth": " ↳ Meziroční růst tržeb (YoY)",
        "r_gp": "Hrubý zisk (Gross Profit)",
        "r_gm": " ↳ Hrubá marže (Gross Margin)",
        "r_ebit": "Provozní zisk (Operating Income / EBIT)",
        "r_om": " ↳ Provozní marže (Operating Margin)",
        "r_ni": "Čistý zisk (Net Income)",
        "r_nm": " ↳ Čistá marže (Net Margin)",
        "r_eps": "Zisk na akcii (EPS)",
        "r_fcf": "Volné cash flow (Free Cash Flow)",
        "r_fcfm": " ↳ FCF marže",
        "currency_lbl": "Měna výkazů:",
        "convert_usd": "Převést výkazy z {curr} do USD (dle historických kurzů)",
        "matrix_h": "Finanční časová osa",
        "kpi_h": "KPI Dashboard",
        "kpi_pe": "P/E (Trailing)",
        "kpi_fpe": "Forward P/E",
        "kpi_peg": "PEG Ratio",
        "kpi_ps": "Cena / Tržby (P/S)",
        "kpi_pfcf": "Cena / FCF",
        "kpi_evebitda": "EV / EBITDA",
        "kpi_pb": "Cena / Účetní hodnota (P/B)",
        "kpi_de": "Dluh / Vlastní kapitál",
        "kpi_cr": "Běžná likvidita",
        "kpi_qr": "Pohotová likvidita",
        "kpi_gm": "Hrubá marže",
        "kpi_ebitdam": "EBITDA marže",
        "kpi_om": "Provozní marže",
        "kpi_nm": "Čistá marže",
        "kpi_fcfm": "FCF marže",
        "kpi_roe": "ROE",
        "kpi_roic": "ROIC",
        "kpi_roa": "ROA",
        "kpi_roce": "ROCE",
        "kpi_roi": "ROI (Proxy)",
        "kpi_rev": "LTM Tržby",
        "kpi_ebitda": "LTM EBITDA",
        "kpi_ni": "LTM Čistý zisk",
        "kpi_fcf": "LTM FCF",
        "kpi_eps": "LTM EPS",
        "bal_h": "Rozvaha",
        "bal_na": "Rozvaha není k dispozici.",
        "est_q1": "Q+1 (Odhad)",
        "est_q2": "Q+2 (Odhad)",
        "earn_next_h": "Nadcházející kvartální report",
        "earn_hist_h": "Historie překonání odhadů (Beat / Miss)",
        "earn_date_lbl": "Termín",
        "earn_eps_lbl": "Odhad EPS",
        "earn_rev_lbl": "Očekávané tržby",
        "eh_date": "Kvartál",
        "eh_act": "Skutečné EPS",
        "eh_est": "Odhad EPS",
        "eh_diff": "Rozdíl",
        "eh_surp": "Překonání odhadu (%)",
        "eh_na1": "Oficiální datum příštího reportu zatím nebylo stanoveno.",
        "eh_na2": "Termín příštích earnings není momentálně k dispozici.",
        "eh_na3": "Historie kvartálních překonání není k dispozici.",
        "eh_na4": "Historie kvartálních earnings není dostupná.",
        "news_h": "Zpravodajský feed —",
        "news_pub": "Zdroj",
        "news_date": "Vydáno",
        "news_na": "Aktuálně nejsou dostupné žádné zprávy.",
        "ai_btn": "Vygenerovat AI Investiční Memo (z živých výkazů)",
        "ai_spin": "AI analyzuje výkazy, marže a valuaci...",
        "ai_no_key": "Pro AI Analytika nastavte GROQ_API_KEY v Secrets a vyberte model v Nastavení.",
        "ai_chat_h": "KONZULTACE S AI NAD VÝKAZY",
        "ai_chat_ph": "Zeptejte se na DCF, marže, zadlužení, valuaci nebo rizika...",
        "chart_rev_h": "TRŽBY · ČISTÝ ZISK · FREE CASH FLOW",
        "chart_mar_h": "VÝVOJ MARŽÍ (%)"
    },
    "EN": {
        "title": "DEEP INSTITUTIONAL TERMINAL",
        "desc": "INSTITUTIONAL FINANCIAL STATEMENTS TIMELINE, VALUATION, CONSENSUS & NEWS.",
        "db_select": "DATABASE",
        "custom_tick": "CUSTOM TICKER",
        "periodicity": "MATRIX PERIODICITY:",
        "annual": "Annual",
        "quarterly": "Quarterly",
        "loading": "LOADING STATEMENTS...",
        "err_data": "DATA FOR THIS TICKER NOT AVAILABLE.",
        "tab_matrix": "FINANCIAL MATRIX & OUTLOOK",
        "tab_val": "VALUATION & KPIs",
        "tab_ai": "AI ANALYST",
        "tab_ana": "ANALYSTS & CONSENSUS",
        "tab_earn": "EARNINGS & TRACK RECORD",
        "tab_news": "NEWS & ARTICLES",
        "tab_raw": "STRUCTURED BALANCE SHEET",
        "targets_h": "Wall Street Consensus & Price Targets",
        "t_low": "Bear Target",
        "t_mean": "Consensus (Mean)",
        "t_high": "Bull Target",
        "t_rec": "Recommendation",
        "t_num": "Analyst Coverage",
        "met_val": "VALUATION",
        "met_mul": "MULTIPLES & LIQUIDITY",
        "met_mar": "MARGINS (CASCADE)",
        "met_ret": "PROFITABILITY",
        "met_ltm": "LTM (TTM) DATA",
        "r_rev": "Total Revenue",
        "r_rev_growth": " ↳ Revenue Growth (YoY)",
        "r_gp": "Gross Profit",
        "r_gm": " ↳ Gross Margin",
        "r_ebit": "Operating Income (EBIT)",
        "r_om": " ↳ Operating Margin",
        "r_ni": "Net Income",
        "r_nm": " ↳ Net Margin",
        "r_eps": "Diluted EPS",
        "r_fcf": "Free Cash Flow (FCF)",
        "r_fcfm": " ↳ FCF Margin",
        "currency_lbl": "Reporting Currency:",
        "convert_usd": "Convert statements from {curr} to USD (using historical rates)",
        "matrix_h": "Financial Timeline",
        "kpi_h": "KPI Dashboard",
        "kpi_pe": "P/E (Trailing)",
        "kpi_fpe": "Forward P/E",
        "kpi_peg": "PEG Ratio",
        "kpi_ps": "Price / Sales",
        "kpi_pfcf": "Price / FCF",
        "kpi_evebitda": "EV / EBITDA",
        "kpi_pb": "Price / Book",
        "kpi_de": "Debt / Equity",
        "kpi_cr": "Current Ratio",
        "kpi_qr": "Quick Ratio",
        "kpi_gm": "Gross Margin",
        "kpi_ebitdam": "EBITDA Margin",
        "kpi_om": "Operating Margin",
        "kpi_nm": "Net Margin",
        "kpi_fcfm": "FCF Margin",
        "kpi_roe": "ROE",
        "kpi_roic": "ROIC",
        "kpi_roa": "ROA",
        "kpi_roce": "ROCE",
        "kpi_roi": "ROI (Proxy)",
        "kpi_rev": "LTM Revenue",
        "kpi_ebitda": "LTM EBITDA",
        "kpi_ni": "LTM Net Income",
        "kpi_fcf": "LTM FCF",
        "kpi_eps": "LTM EPS",
        "bal_h": "Balance Sheet",
        "bal_na": "Balance sheet is not available.",
        "est_q1": "Q+1 (Est)",
        "est_q2": "Q+2 (Est)",
        "earn_next_h": "Upcoming Earnings Report",
        "earn_hist_h": "Earnings Surprise History (Beat / Miss)",
        "earn_date_lbl": "Date",
        "earn_eps_lbl": "Consensus EPS",
        "earn_rev_lbl": "Consensus Revenue",
        "eh_date": "Quarter",
        "eh_act": "Actual EPS",
        "eh_est": "Estimated EPS",
        "eh_diff": "Difference",
        "eh_surp": "Beat / Miss (%)",
        "eh_na1": "Official next earnings date not set yet.",
        "eh_na2": "Next earnings date is currently unavailable.",
        "eh_na3": "Earnings surprise history is not available.",
        "eh_na4": "Earnings history is currently unavailable.",
        "news_h": "News Feed —",
        "news_pub": "Source",
        "news_date": "Published",
        "news_na": "No news currently available.",
        "ai_btn": "Generate AI Investment Memo (from live statements)",
        "ai_spin": "AI is analyzing statements, margins and valuation...",
        "ai_no_key": "Configure GROQ_API_KEY in Secrets and select a model in Settings to use AI Analyst.",
        "ai_chat_h": "AI FUNDAMENTAL CONSULTATION",
        "ai_chat_ph": "Ask about DCF, margins, leverage, valuation, or risks...",
        "chart_rev_h": "REVENUE · NET INCOME · FREE CASH FLOW",
        "chart_mar_h": "MARGIN TRENDS (%)"
    }
}
_ = t.get(current_lang, t["CZ"])

st.title(_["title"])
st.caption(_["desc"])
st.markdown("---")

def load_data():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return {"portfolio": data, "watchlist": [], "settings": {}}
                return data
        except Exception as e:
            st.error(f"Kritická chyba při čtení watchlist.json: {e}")
            st.stop()
    st.error(f"Soubor watchlist.json nebyl nalezen na cestě: {WATCHLIST_FILE}")
    st.stop()

data = load_data()
all_tickers = list(dict.fromkeys(data.get("portfolio", []) + data.get("watchlist", [])))
saved_settings = data.get("settings", {})

api_key = str(st.secrets.get("GROQ_API_KEY", "")).strip()
model_provider = st.session_state.get("ai_provider", saved_settings.get("ai_provider", "Groq"))
selected_model = st.session_state.get("ai_model", saved_settings.get("ai_model", ""))

if "term_ai_ticker" not in st.session_state: st.session_state.term_ai_ticker = None
if "term_ai_memo" not in st.session_state: st.session_state.term_ai_memo = None
if "term_ai_chat" not in st.session_state: st.session_state.term_ai_chat = []

col_sel1, col_sel2, col_sel3 = st.columns([2.5, 1.5, 3])
ph_text = "Vyhledat..." if current_lang == "CZ" else "Search..."
ph_db = "Vybrat..." if current_lang == "CZ" else "Select..."

custom_tick = col_sel1.text_input(f"🔍 {_['custom_tick']}", placeholder=ph_text)
sel_tick = col_sel2.selectbox(f"📂 {_['db_select']}", all_tickers, index=None, placeholder=ph_db)
period_type = col_sel3.radio(_["periodicity"], [_["annual"], _["quarterly"]], horizontal=True)

final_tick = custom_tick.upper().strip() if custom_tick.strip() else sel_tick

if final_tick != st.session_state.term_ai_ticker:
    st.session_state.term_ai_ticker = final_tick
    st.session_state.term_ai_memo = None
    st.session_state.term_ai_chat = []

# --- NATIVE URLLIB AI CALL ---
def call_llm_api(messages, api_klic, provider, model_name, temperature=0.2, timeout=30):
    url = "[https://api.groq.com/openai/v1/chat/completions](https://api.groq.com/openai/v1/chat/completions)" if provider == "Groq" else "[https://api.openai.com/v1/chat/completions](https://api.openai.com/v1/chat/completions)"
    payload = json.dumps({
        "model": model_name,
        "messages": messages,
        "temperature": temperature
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_klic}",
            "Content-Type": "application/json",
            "User-Agent": random.choice(USER_AGENTS)
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")[:250]
        raise RuntimeError(f"HTTP {e.code}: {err_body}")

def format_val(val, currency_code, is_pct=False, is_eps=False, force_currency=False):
    if val is None or pd.isna(val) or val == "-": return "-"
    try: val = float(val)
    except Exception: return str(val)
    if is_pct: return f"{val * 100:+.1f} %"
    if is_eps: return f"{val:.2f} {currency_code}"
    if abs(val) >= 1e9: return f"{val / 1e9:,.2f} B" + (f" {currency_code}" if force_currency else "")
    if abs(val) >= 1e6: return f"{val / 1e6:,.2f} M" + (f" {currency_code}" if force_currency else "")
    return f"{val:,.2f}" + (f" {currency_code}" if force_currency else "")

# --- CACHED YFINANCE BUNDLE (zabraňuje blokaci při přepínání záložek a chatu) ---
@st.cache_data(ttl=900, show_spinner=False)
def load_ticker_bundle(ticker):
    tkr = yf.Ticker(ticker)
    bundle = {
        "info": {}, "fast": {}, "hist_price": 0.0,
        "fin_a": pd.DataFrame(), "fin_q": pd.DataFrame(),
        "cf_a": pd.DataFrame(), "cf_q": pd.DataFrame(),
        "bs": pd.DataFrame(), "rev_est": None, "eps_est": None,
        "cal": None, "eh": None
    }
    try: bundle["info"] = tkr.info or {}
    except Exception: pass
    try: bundle["fast"] = dict(tkr.fast_info)
    except Exception: pass
    try:
        h = tkr.history(period="5d")
        if not h.empty: bundle["hist_price"] = float(h["Close"].iloc[-1])
    except Exception: pass
    try: bundle["fin_a"] = tkr.financials
    except Exception: pass
    try: bundle["fin_q"] = tkr.quarterly_financials
    except Exception: pass
    try: bundle["cf_a"] = tkr.cashflow
    except Exception: pass
    try: bundle["cf_q"] = tkr.quarterly_cashflow
    except Exception: pass
    try: bundle["bs"] = tkr.balance_sheet
    except Exception: pass
    try: bundle["rev_est"] = tkr.revenue_estimate
    except Exception: pass
    try: bundle["eps_est"] = tkr.earnings_estimate
    except Exception: pass
    try: bundle["cal"] = tkr.calendar
    except Exception: pass
    try: bundle["eh"] = tkr.earnings_history
    except Exception: pass
    return bundle

@st.cache_data(ttl=3600, show_spinner=False)
def load_fx_history(currency_code):
    try:
        return yf.Ticker(f"{currency_code}USD=X").history(period="10y")
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=900, show_spinner=False)
def fetch_ticker_news(ticker):
    articles = []
    # 1. Google News RSS
    try:
        rss_url = f"[https://news.google.com/rss/search?q=](https://news.google.com/rss/search?q=){ticker}+stock+news&hl=en-US&gl=US&ceid=US:en"
        rss_resp = requests.get(rss_url, headers=get_headers(), timeout=8)
        if rss_resp.status_code == 200:
            root = ET.fromstring(rss_resp.content)
            for item in root.findall('.//item')[:12]:
                title = item.find('title').text if item.find('title') is not None else "N/A"
                link = item.find('link').text if item.find('link') is not None else "#"
                pubDate = item.find('pubDate').text if item.find('pubDate') is not None else "N/A"
                source_el = item.find('source')
                publisher = source_el.text if source_el is not None and source_el.text else "Google News"
                try: dt_str = pd.to_datetime(pubDate).strftime("%d. %m. %Y %H:%M")
                except Exception: dt_str = pubDate[:22] if len(pubDate) > 22 else pubDate
                articles.append({"title": title, "link": link, "date": dt_str, "publisher": publisher})
            if articles:
                return articles
    except Exception:
        pass

    # 2. Yahoo Finance RSS fallback
    try:
        yf_rss = f"[https://feeds.finance.yahoo.com/rss/2.0/headline?s=](https://feeds.finance.yahoo.com/rss/2.0/headline?s=){ticker}®ion=US&lang=en-US"
        r2 = requests.get(yf_rss, headers=get_headers(), timeout=8)
        if r2.status_code == 200:
            root = ET.fromstring(r2.content)
            for item in root.findall('.//item')[:12]:
                title = item.find('title').text if item.find('title') is not None else "N/A"
                link = item.find('link').text if item.find('link') is not None else "#"
                pubDate = item.find('pubDate').text if item.find('pubDate') is not None else "N/A"
                try: dt_str = pd.to_datetime(pubDate).strftime("%d. %m. %Y %H:%M")
                except Exception: dt_str = pubDate[:22] if len(pubDate) > 22 else pubDate
                articles.append({"title": title, "link": link, "date": dt_str, "publisher": "Yahoo Finance"})
            if articles:
                return articles
    except Exception:
        pass

    # 3. yfinance.news fallback
    try:
        yf_news = yf.Ticker(ticker).news
        if yf_news:
            for n in yf_news[:10]:
                content = n.get("content", n)
                title = content.get("title")
                link = content.get("canonicalUrl", {}).get("url", n.get("link", "#"))
                pubDate = content.get("pubDate", "N/A")
                if title:
                    dt_str = pubDate[:16].replace("T", " ") if isinstance(pubDate, str) and len(pubDate) > 16 else str(pubDate)
                    articles.append({"title": title, "link": link, "date": dt_str, "publisher": "Yahoo Finance"})
    except Exception:
        pass

    return articles

if final_tick:
    with st.spinner(f"{_['loading']} {final_tick}..."):
        bundle = load_ticker_bundle(final_tick)
        info = bundle["info"]
        fast = bundle["fast"]

        curr_price = info.get("currentPrice") or info.get("regularMarketPrice") or fast.get("lastPrice") or fast.get("regularMarketPreviousClose") or bundle["hist_price"] or 0.0
        market_cap = info.get("marketCap") or fast.get("marketCap")
        shares_out = info.get("sharesOutstanding") or fast.get("shares")
        if not market_cap and curr_price and shares_out:
            market_cap = curr_price * shares_out

        is_quarterly = (period_type == _["quarterly"])
        financials = bundle["fin_q"] if is_quarterly else bundle["fin_a"]
        cashflow = bundle["cf_q"] if is_quarterly else bundle["cf_a"]
        balance_sheet = bundle["bs"]

        if financials is None or financials.empty:
            st.error(_["err_data"])
            st.stop()

        short_name = info.get("shortName", final_tick)
        currency_code = info.get("financialCurrency") or info.get("currency") or fast.get("currency") or "USD"
        trading_currency = info.get("currency") or fast.get("currency") or "USD"

        # --- FX TRANSLATION ---
        convert_to_usd = False
        display_currency = currency_code
        fx_hist = pd.DataFrame()
        latest_fx = 1.0

        if currency_code != "USD":
            convert_to_usd = st.toggle(f"💱 {_['convert_usd'].replace('{curr}', currency_code)}", value=False)
            if convert_to_usd:
                display_currency = "USD"
                fx_hist = load_fx_history(currency_code)
                if not fx_hist.empty:
                    latest_fx = float(fx_hist['Close'].iloc[-1])

        def get_rate(d):
            if not convert_to_usd: return 1.0
            if fx_hist.empty: return latest_fx
            try:
                dt = pd.to_datetime(d)
                if dt.tzinfo is None and fx_hist.index.tz is not None: dt = dt.tz_localize('UTC')
                elif dt.tzinfo is not None and fx_hist.index.tz is None: dt = dt.tz_localize(None)
                idx = fx_hist.index.get_indexer([dt], method='nearest')[0]
                return float(fx_hist['Close'].iloc[idx])
            except Exception:
                return latest_fx

        q_fin_for_kpi = bundle["fin_q"]
        q_cf_for_kpi = bundle["cf_q"]

        def get_ltm_from_quarterly(df, keys):
            if df is None or df.empty: return None
            for key in keys:
                if key in df.index:
                    vals = df.loc[key].iloc[:4]
                    if len(vals) == 4 and not vals.isna().all(): return float(vals.sum())
            return None

        total_rev_ltm = get_ltm_from_quarterly(q_fin_for_kpi, ['Total Revenue']) or info.get("totalRevenue")
        gross_profit_ltm = get_ltm_from_quarterly(q_fin_for_kpi, ['Gross Profit'])
        op_inc_ltm = get_ltm_from_quarterly(q_fin_for_kpi, ['Operating Income', 'EBIT'])
        net_income_ltm = get_ltm_from_quarterly(q_fin_for_kpi, ['Net Income', 'Net Income Common Stockholders']) or info.get("netIncomeToCommon", info.get("netIncome"))
        ebitda_ltm = get_ltm_from_quarterly(q_fin_for_kpi, ['Normalized EBITDA', 'EBITDA']) or info.get("ebitda")

        fcf = get_ltm_from_quarterly(q_cf_for_kpi, ['Free Cash Flow'])
        if fcf is None:
            ocf = get_ltm_from_quarterly(q_cf_for_kpi, ['Operating Cash Flow'])
            capex = get_ltm_from_quarterly(q_cf_for_kpi, ['Capital Expenditure'])
            if ocf and capex is not None: fcf = ocf - abs(capex)
            else: fcf = info.get("freeCashflow")

        eps_ltm = info.get("trailingEps") or get_ltm_from_quarterly(q_fin_for_kpi, ['Diluted EPS', 'Basic EPS'])

        calc_debt_eq, roic, roce, roi = None, None, None, None
        total_debt, stockholders_eq, total_assets, current_assets, current_liab, inventory = 0, 0, 0, 0, 0, 0
        if balance_sheet is not None and not balance_sheet.empty:
            try:
                total_debt = float(balance_sheet.loc['Total Debt'].iloc[0]) if 'Total Debt' in balance_sheet.index else 0
                stockholders_eq = float(balance_sheet.loc['Stockholders Equity'].iloc[0]) if 'Stockholders Equity' in balance_sheet.index else 0
                total_assets = float(balance_sheet.loc['Total Assets'].iloc[0]) if 'Total Assets' in balance_sheet.index else 0
                current_assets = float(balance_sheet.loc['Current Assets'].iloc[0]) if 'Current Assets' in balance_sheet.index else 0
                current_liab = float(balance_sheet.loc['Current Liabilities'].iloc[0]) if 'Current Liabilities' in balance_sheet.index else (float(balance_sheet.loc['Total Current Liabilities'].iloc[0]) if 'Total Current Liabilities' in balance_sheet.index else 0)
                inventory = float(balance_sheet.loc['Inventory'].iloc[0]) if 'Inventory' in balance_sheet.index else 0
                invested_capital = total_debt + stockholders_eq
                capital_employed = total_assets - current_liab
                if stockholders_eq > 0: calc_debt_eq = total_debt / stockholders_eq
            except Exception:
                invested_capital, capital_employed = 0, 0
        else:
            invested_capital, capital_employed = 0, 0

        pe = info.get("trailingPE") or ((curr_price / eps_ltm) if (curr_price and eps_ltm and eps_ltm > 0) else None)
        fwd_pe = info.get("forwardPE")
        peg = info.get("pegRatio")
        ps = info.get("priceToSalesTrailing12Months") or ((market_cap / total_rev_ltm) if (market_cap and total_rev_ltm and total_rev_ltm > 0) else None)
        pb = info.get("priceToBook") or ((market_cap / stockholders_eq) if (market_cap and stockholders_eq and stockholders_eq > 0) else None)
        ev_ebitda = info.get("enterpriseToEbitda")
        p_fcf = (market_cap / fcf) if (market_cap and fcf and fcf > 0) else None

        current_ratio = info.get("currentRatio") or ((current_assets / current_liab) if (current_assets and current_liab > 0) else None)
        quick_ratio = info.get("quickRatio") or (((current_assets - inventory) / current_liab) if (current_assets and current_liab > 0) else None)

        roe = info.get("returnOnEquity") or ((net_income_ltm / stockholders_eq) if (net_income_ltm and stockholders_eq > 0) else None)
        roa = info.get("returnOnAssets") or ((net_income_ltm / total_assets) if (net_income_ltm and total_assets > 0) else None)
        gross_margin = info.get("grossMargins") or ((gross_profit_ltm / total_rev_ltm) if (gross_profit_ltm and total_rev_ltm and total_rev_ltm > 0) else None)
        op_margin = info.get("operatingMargins") or ((op_inc_ltm / total_rev_ltm) if (op_inc_ltm and total_rev_ltm and total_rev_ltm > 0) else None)
        profit_margin = info.get("profitMargins") or ((net_income_ltm / total_rev_ltm) if (net_income_ltm and total_rev_ltm and total_rev_ltm > 0) else None)
        ebitda_margin = (ebitda_ltm / total_rev_ltm) if (ebitda_ltm and total_rev_ltm and total_rev_ltm > 0) else None
        fcf_margin = (fcf / total_rev_ltm) if (fcf and total_rev_ltm and total_rev_ltm > 0) else None

        if net_income_ltm and invested_capital > 0: roic = net_income_ltm / invested_capital
        if not financials.empty and capital_employed > 0:
            try:
                ebit = financials.loc['EBIT'].iloc[0] if 'EBIT' in financials.index else (financials.loc['Operating Income'].iloc[0] if 'Operating Income' in financials.index else 0)
                if ebit: roce = float(ebit) / capital_employed
            except Exception:
                pass
        if net_income_ltm and total_assets > 0: roi = net_income_ltm / total_assets

        # Build matrix
        matrix_dict = {}
        last_hist_year = 2024
        if not financials.empty:
            hist_cols = sorted(financials.columns)
            last_hist_year = hist_cols[-1].year
            for col in hist_cols:
                rate = get_rate(col)
                col_label = f"{col.year}-Q{col.quarter}" if is_quarterly else str(col.year)
                matrix_dict[col_label] = {}
                rev = financials.loc["Total Revenue", col] if "Total Revenue" in financials.index else None
                matrix_dict[col_label][_["r_rev"]] = (rev * rate) if pd.notna(rev) else None
                gp = financials.loc["Gross Profit", col] if "Gross Profit" in financials.index else None
                matrix_dict[col_label][_["r_gp"]] = (gp * rate) if pd.notna(gp) else None
                ebit = financials.loc["Operating Income", col] if "Operating Income" in financials.index else (financials.loc["EBIT", col] if "EBIT" in financials.index else None)
                matrix_dict[col_label][_["r_ebit"]] = (ebit * rate) if pd.notna(ebit) else None
                ni = financials.loc["Net Income Common Stockholders", col] if "Net Income Common Stockholders" in financials.index else (financials.loc["Net Income", col] if "Net Income" in financials.index else None)
                matrix_dict[col_label][_["r_ni"]] = (ni * rate) if pd.notna(ni) else None
                eps = financials.loc["Diluted EPS", col] if "Diluted EPS" in financials.index else (financials.loc["Basic EPS", col] if "Basic EPS" in financials.index else None)
                matrix_dict[col_label][_["r_eps"]] = (eps * rate) if pd.notna(eps) else None
                fcf_val = None
                if not cashflow.empty and col in cashflow.columns:
                    if "Free Cash Flow" in cashflow.index: fcf_val = cashflow.loc["Free Cash Flow", col]
                    elif "Operating Cash Flow" in cashflow.index and "Capital Expenditure" in cashflow.index:
                        fcf_val = cashflow.loc["Operating Cash Flow", col] - abs(cashflow.loc["Capital Expenditure", col])
                matrix_dict[col_label][_["r_fcf"]] = (fcf_val * rate) if pd.notna(fcf_val) else None

        if not is_quarterly:
            rate = latest_fx if convert_to_usd else 1.0
            matrix_dict["LTM"] = {
                _["r_rev"]: (total_rev_ltm * rate) if pd.notna(total_rev_ltm) else None,
                _["r_gp"]: (gross_profit_ltm * rate) if gross_profit_ltm is not None else None,
                _["r_ebit"]: (op_inc_ltm * rate) if op_inc_ltm is not None else None,
                _["r_ni"]: (net_income_ltm * rate) if pd.notna(net_income_ltm) else None,
                _["r_eps"]: (eps_ltm * rate) if pd.notna(eps_ltm) else None,
                _["r_fcf"]: (fcf * rate) if pd.notna(fcf) else None
            }

        try:
            rev_est = bundle["rev_est"]
            eps_est = bundle["eps_est"]
            est_keys = [("0q", _["est_q1"]), ("+1q", _["est_q2"])] if is_quarterly else [("0y", f"{last_hist_year + 1}E"), ("+1y", f"{last_hist_year + 2}E")]
            for k, label in est_keys:
                rate = latest_fx if convert_to_usd else 1.0
                e_val = eps_est.loc[k, "avg"] if (eps_est is not None and not eps_est.empty and k in eps_est.index and "avg" in eps_est.columns) else None
                r_val = rev_est.loc[k, "avg"] if (rev_est is not None and not rev_est.empty and k in rev_est.index and "avg" in rev_est.columns) else None
                matrix_dict[label] = {
                    _["r_eps"]: (e_val * rate) if pd.notna(e_val) else None,
                    _["r_rev"]: (r_val * rate) if pd.notna(r_val) else None,
                    _["r_gp"]: None, _["r_ebit"]: None,
                    _["r_ni"]: (e_val * rate * shares_out) if (pd.notna(e_val) and shares_out) else None,
                    _["r_fcf"]: None
                }
        except Exception:
            pass

        df_matrix = pd.DataFrame(matrix_dict)
        if _["r_rev"] in df_matrix.index:
            rev_series = pd.to_numeric(df_matrix.loc[_["r_rev"]], errors='coerce')
            clean_series = rev_series.drop("LTM", errors="ignore")
            growth_series = clean_series.pct_change()
            if "LTM" in df_matrix.columns: growth_series["LTM"] = None
            df_matrix.loc[_["r_rev_growth"]] = growth_series
            for m_lbl, p_lbl in [(_["r_gm"], _["r_gp"]), (_["r_om"], _["r_ebit"]), (_["r_nm"], _["r_ni"]), (_["r_fcfm"], _["r_fcf"])]:
                if p_lbl in df_matrix.index:
                    df_matrix.loc[m_lbl] = pd.to_numeric(df_matrix.loc[p_lbl], errors='coerce') / rev_series

        ordered_rows = [_["r_rev"], _["r_rev_growth"], _["r_gp"], _["r_gm"], _["r_ebit"], _["r_om"], _["r_ni"], _["r_nm"], _["r_eps"], _["r_fcf"], _["r_fcfm"]]
        df_matrix = df_matrix.reindex([r for r in ordered_rows if r in df_matrix.index])

        df_display = df_matrix.copy().astype(object)
        pct_rows = [_["r_rev_growth"], _["r_gm"], _["r_om"], _["r_nm"], _["r_fcfm"]]
        for r in df_display.index:
            is_pct = (r in pct_rows)
            is_eps = (r == _["r_eps"])
            df_display.loc[r] = df_display.loc[r].apply(lambda x: format_val(x, display_currency, is_pct=is_pct, is_eps=is_eps, force_currency=(not is_pct and not is_eps)))

        st.markdown("---")
        tab_matrix, tab_val, tab_ai, tab_ana, tab_earn, tab_news, tab_raw = st.tabs([
            _["tab_matrix"], _["tab_val"], _["tab_ai"], _["tab_ana"], _["tab_earn"], _["tab_news"], _["tab_raw"]
        ])

        with tab_matrix:
            st.markdown(f'<div class="term-sec-label">{_["matrix_h"]} · {_["currency_lbl"]} {display_currency}</div>', unsafe_allow_html=True)
            st.table(df_display)

            chart_cols = [c for c in df_matrix.columns if c != "LTM"]
            if chart_cols and _["r_rev"] in df_matrix.index:
                ch1, ch2 = st.columns(2)
                with ch1:
                    st.markdown(f'<div class="term-sec-label">{_["chart_rev_h"]} ({display_currency})</div>', unsafe_allow_html=True)
                    fig1 = go.Figure()
                    for row_lbl, color_hex in [(_["r_rev"], "#3B82F6"), (_["r_ni"], "#22C55E"), (_["r_fcf"], "#F97316")]:
                        if row_lbl in df_matrix.index:
                            vals = pd.to_numeric(df_matrix.loc[row_lbl, chart_cols], errors='coerce')
                            fig1.add_trace(go.Bar(x=chart_cols, y=vals, name=row_lbl, marker_color=color_hex))
                    fig1.update_layout(
                        template="plotly_dark", barmode="group", height=340,
                        paper_bgcolor="#0D0F12", plot_bgcolor="#0D0F12",
                        margin=dict(l=10, r=10, t=20, b=10),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
                    )
                    st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})

                with ch2:
                    st.markdown(f'<div class="term-sec-label">{_["chart_mar_h"]}</div>', unsafe_allow_html=True)
                    fig2 = go.Figure()
                    for row_lbl, color_hex in [(_["r_gm"], "#22C55E"), (_["r_om"], "#3B82F6"), (_["r_nm"], "#F97316"), (_["r_fcfm"], "#A855F7")]:
                        if row_lbl in df_matrix.index:
                            vals = pd.to_numeric(df_matrix.loc[row_lbl, chart_cols], errors='coerce') * 100
                            fig2.add_trace(go.Scatter(x=chart_cols, y=vals, mode="lines+markers", name=row_lbl.replace(" ↳ ", ""), line=dict(color=color_hex, width=2.5)))
                    fig2.update_layout(
                        template="plotly_dark", height=340,
                        paper_bgcolor="#0D0F12", plot_bgcolor="#0D0F12",
                        margin=dict(l=10, r=10, t=20, b=10),
                        yaxis_ticksuffix="%",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
                    )
                    st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

        with tab_val:
            st.markdown(f'<div class="term-sec-label">{short_name} ({final_tick}) · {_["kpi_h"]}</div>', unsafe_allow_html=True)
            vkpi1, vkpi2, vkpi3, vkpi4, vkpi5 = st.columns(5)

            def fmt_kpi(val, is_pct=False, is_curr=False, curr_label="USD"):
                if val is None or pd.isna(val): return "N/A"
                if is_pct: return f"{val*100:.2f} %"
                if is_curr:
                    if abs(val) >= 1e9: return f"{val/1e9:.2f}B {curr_label}"
                    if abs(val) >= 1e6: return f"{val/1e6:.2f}M {curr_label}"
                    return f"{val:,.2f} {curr_label}"
                return f"{val:.2f}"

            vkpi1.markdown(f"**{_['met_val']}**")
            vkpi1.metric(_["kpi_pe"], fmt_kpi(pe))
            vkpi1.metric(_["kpi_fpe"], fmt_kpi(fwd_pe))
            vkpi1.metric(_["kpi_peg"], fmt_kpi(peg))
            vkpi1.metric(_["kpi_ps"], fmt_kpi(ps))
            vkpi1.metric(_["kpi_pfcf"], fmt_kpi(p_fcf))

            vkpi2.markdown(f"**{_['met_mul']}**")
            vkpi2.metric(_["kpi_evebitda"], fmt_kpi(ev_ebitda))
            vkpi2.metric(_["kpi_pb"], fmt_kpi(pb))
            vkpi2.metric(_["kpi_de"], fmt_kpi(calc_debt_eq))
            vkpi2.metric(_["kpi_cr"], fmt_kpi(current_ratio))
            vkpi2.metric(_["kpi_qr"], fmt_kpi(quick_ratio))

            vkpi3.markdown(f"**{_['met_mar']}**")
            vkpi3.metric(_["kpi_gm"], fmt_kpi(gross_margin, True))
            vkpi3.metric(_["kpi_ebitdam"], fmt_kpi(ebitda_margin, True))
            vkpi3.metric(_["kpi_om"], fmt_kpi(op_margin, True))
            vkpi3.metric(_["kpi_nm"], fmt_kpi(profit_margin, True))
            vkpi3.metric(_["kpi_fcfm"], fmt_kpi(fcf_margin, True))

            vkpi4.markdown(f"**{_['met_ret']}**")
            vkpi4.metric(_["kpi_roe"], fmt_kpi(roe, True))
            vkpi4.metric(_["kpi_roic"], fmt_kpi(roic, True))
            vkpi4.metric(_["kpi_roa"], fmt_kpi(roa, True))
            vkpi4.metric(_["kpi_roce"], fmt_kpi(roce, True))
            vkpi4.metric(_["kpi_roi"], fmt_kpi(roi, True))

            vkpi5.markdown(f"**{_['met_ltm']}**")
            fx_m = latest_fx if convert_to_usd else 1.0
            vkpi5.metric(_["kpi_rev"], fmt_kpi(total_rev_ltm * fx_m if total_rev_ltm else None, is_curr=True, curr_label=display_currency))
            vkpi5.metric(_["kpi_ebitda"], fmt_kpi(ebitda_ltm * fx_m if ebitda_ltm else None, is_curr=True, curr_label=display_currency))
            vkpi5.metric(_["kpi_ni"], fmt_kpi(net_income_ltm * fx_m if net_income_ltm else None, is_curr=True, curr_label=display_currency))
            vkpi5.metric(_["kpi_fcf"], fmt_kpi(fcf * fx_m if fcf else None, is_curr=True, curr_label=display_currency))
            vkpi5.metric(_["kpi_eps"], fmt_kpi(eps_ltm, is_curr=True, curr_label=trading_currency))

        with tab_ai:
            if not api_key or not selected_model:
                st.warning(_["ai_no_key"])
            else:
                kpi_summary = {
                    "company": f"{short_name} ({final_tick})",
                    "price": f"{curr_price} {trading_currency}",
                    "market_cap": market_cap,
                    "PE": pe, "Forward_PE": fwd_pe, "PEG": peg, "EV_EBITDA": ev_ebitda, "P_FCF": p_fcf,
                    "Gross_Margin": gross_margin, "Operating_Margin": op_margin, "Net_Margin": profit_margin, "FCF_Margin": fcf_margin,
                    "ROE": roe, "ROIC": roic, "Debt_to_Equity": calc_debt_eq, "Current_Ratio": current_ratio,
                    "Financial_Matrix": df_display.to_dict()
                }
                kpi_json_str = json.dumps(kpi_summary, ensure_ascii=False, default=str)

                if st.button(_["ai_btn"], type="primary", use_container_width=True):
                    lang_instr = "v čisté češtině bez anglických frází" if current_lang == "CZ" else "in clean institutional English"
                    memo_prompt = f"""Jsi Senior Equity Analyst & Portfolio Manager. Na základě PŘESNĚ TĚCHTO finančních dat vypracuj stručné institucionální investiční memo {lang_instr}:
1. **KVALITA BYZNYSU & MARŽE** (trend tržeb, provozní páka, FCF konverze, ROIC)
2. **VALUACE & MARGIN OF SAFETY** (zhodnocení P/E, Forward P/E, EV/EBITDA, P/FCF vůči růstu)
3. **ROZVAHA & RIZIKA** (zadlužení, likvidita, hlavní hrozby)
4. **VERDIKT ANALYTIKA** (jasný postoj + klíčové číslo k sledování)

Používej výhradně tato data:
{kpi_json_str}"""
                    with st.spinner(_["ai_spin"]):
                        try:
                            st.session_state.term_ai_memo = call_llm_api([{"role": "user", "content": memo_prompt}], api_key, model_provider, selected_model, temperature=0.2, timeout=35)
                        except Exception as e:
                            st.error(f"AI Error: {e}")

                if st.session_state.term_ai_memo:
                    st.markdown('<div class="term-memo-box">', unsafe_allow_html=True)
                    st.markdown(st.session_state.term_ai_memo)
                    st.markdown('</div>', unsafe_allow_html=True)

                st.markdown(f'<div class="term-sec-label">{_["ai_chat_h"]}</div>', unsafe_allow_html=True)
                for msg in st.session_state.term_ai_chat:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

                if q_term := st.chat_input(_["ai_chat_ph"], key="term_ai_chat_input"):
                    st.session_state.term_ai_chat.append({"role": "user", "content": q_term})
                    with st.chat_message("user"):
                        st.markdown(q_term)
                    with st.chat_message("assistant"):
                        with st.spinner(_["ai_spin"]):
                            lang_reply = "Odpovídej čistou češtinou." if current_lang == "CZ" else "Answer in clean English."
                            msgs = [{"role": "system", "content": f"Jsi Senior Equity Analyst. Máš přesná finanční data firmy {short_name} ({final_tick}): {kpi_json_str}. Odpovídej konkrétně a opírej se o čísla. {lang_reply}"}]
                            for m in st.session_state.term_ai_chat[:-1]:
                                msgs.append({"role": m["role"], "content": m["content"]})
                            msgs.append({"role": "user", "content": q_term})
                            try: ans = call_llm_api(msgs, api_key, model_provider, selected_model, temperature=0.25, timeout=25)
                            except Exception as e: ans = f"⚠️ AI Error ({e})."
                            st.markdown(ans)
                    if not ans.startswith("⚠️"):
                        st.session_state.term_ai_chat.append({"role": "assistant", "content": ans})

        with tab_ana:
            st.subheader(_["targets_h"])
            target_low = info.get("targetLowPrice", curr_price)
            target_mean = info.get("targetMeanPrice", curr_price)
            target_high = info.get("targetHighPrice", curr_price)
            rec_mean = info.get("recommendationKey", "N/A").upper()
            num_analysts = info.get("numberOfAnalystOpinions", "N/A")

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric(_["t_low"], f"{target_low:.2f} {trading_currency}" if target_low else "N/A", f"{(target_low - curr_price) / curr_price * 100:+.1f}%" if (curr_price and target_low) else "N/A")
            c2.metric(_["t_mean"], f"{target_mean:.2f} {trading_currency}" if target_mean else "N/A", f"{(target_mean - curr_price) / curr_price * 100:+.1f}%" if (curr_price and target_mean) else "N/A")
            c3.metric(_["t_high"], f"{target_high:.2f} {trading_currency}" if target_high else "N/A", f"{(target_high - curr_price) / curr_price * 100:+.1f}%" if (curr_price and target_high) else "N/A")
            c4.metric(_["t_rec"], rec_mean)
            c5.metric(_["t_num"], num_analysts)

        with tab_earn:
            st.subheader(_["earn_next_h"])
            try:
                cal = bundle["cal"]
                next_date = cal['Earnings Date'][0] if (isinstance(cal, dict) and 'Earnings Date' in cal and len(cal['Earnings Date']) > 0) else None
                if next_date:
                    eps_est_val, rev_est_val = None, None
                    try:
                        eps_est_val = bundle["eps_est"].loc["0q", "avg"]
                        rev_est_val = bundle["rev_est"].loc["0q", "avg"]
                    except Exception:
                        pass
                    ec1, ec2, ec3 = st.columns(3)
                    ec1.metric(_["earn_date_lbl"], next_date.strftime("%d. %m. %Y"))
                    ec2.metric(_["earn_eps_lbl"], f"${eps_est_val:.2f}" if pd.notna(eps_est_val) else "N/A")
                    rev_str = f"${rev_est_val/1e9:.2f} B" if (pd.notna(rev_est_val) and rev_est_val >= 1e9) else (f"${rev_est_val/1e6:.2f} M" if (pd.notna(rev_est_val) and rev_est_val >= 1e6) else "N/A")
                    ec3.metric(_["earn_rev_lbl"], rev_str)
                else:
                    st.info(_["eh_na1"])
            except Exception:
                st.info(_["eh_na2"])

            st.markdown("---")
            st.subheader(_["earn_hist_h"])
            try:
                eh = bundle["eh"]
                if eh is not None and not eh.empty:
                    df_eh = eh.copy()
                    if isinstance(df_eh.index, pd.DatetimeIndex):
                        df_eh.index = df_eh.index.strftime("%Y-%m-%d")
                        df_eh.index.name = _["eh_date"]
                    elif "quarter" in df_eh.columns:
                        df_eh["quarter"] = pd.to_datetime(df_eh["quarter"]).dt.strftime("%Y-%m-%d")
                    df_eh = df_eh.rename(columns={"epsActual": _["eh_act"], "epsEstimate": _["eh_est"], "epsDifference": _["eh_diff"], "surprisePercent": _["eh_surp"]})
                    if _["eh_diff"] in df_eh.columns: df_eh[_["eh_diff"]] = df_eh[_["eh_diff"]].apply(lambda x: f"{x:+.2f}" if pd.notna(x) else "-")
                    if _["eh_surp"] in df_eh.columns: df_eh[_["eh_surp"]] = df_eh[_["eh_surp"]].apply(lambda x: f"{x*100:+.2f} %" if pd.notna(x) else "-")
                    st.table(df_eh)
                else:
                    st.info(_["eh_na3"])
            except Exception:
                st.info(_["eh_na4"])

        with tab_news:
            st.subheader(f"{_['news_h']} {short_name} ({final_tick})")
            news_articles = fetch_ticker_news(final_tick)
            if news_articles:
                for art in news_articles:
                    st.markdown(f"### [{art['title']}]({art['link']})")
                    st.caption(f"🕒 {_['news_date']}: **{art['date']}** | 🏢 {_['news_pub']}: **{art['publisher']}**")
                    st.markdown("---")
            else:
                st.info(_["news_na"])

        with tab_raw:
            st.subheader(f"{_['bal_h']} — {final_tick}")
            if not balance_sheet.empty:
                bs_display = balance_sheet.copy()
                for col in bs_display.columns:
                    rate = get_rate(col)
                    bs_display[col] = bs_display[col] * rate if pd.notna(bs_display[col]).any() else bs_display[col]
                bs_display.columns = [c.strftime("%Y-%m-%d") for c in bs_display.columns]
                for col in bs_display.columns:
                    bs_display[col] = bs_display[col].apply(lambda x: format_val(x, display_currency, force_currency=True))
                st.table(bs_display)
            else:
                st.info(_["bal_na"])