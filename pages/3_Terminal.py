import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os
import sys
import random
import subprocess
import requests
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo
import plotly.graph_objects as go

# --- INITIAL SETUP ---
st.set_page_config(page_title="POKORNY TERMINAL | VALUATION", layout="wide", initial_sidebar_state="collapsed")

# --- DIRECTORY MANAGEMENT ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)
WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")
MEMOS_FILE = os.path.join(hlavni_slozka, "terminal_memos.json")

import menu
menu.vykresli_menu()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
]

SEC_HEADERS = {"User-Agent": "PokornyTerminal/1.0 (pokornyl98@gmail.com)"}

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
        "Accept-Language": "en-US,en;q=0.9"
    }

# --- INSTITUTIONAL DARK CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

.stApp { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

.term-topbar {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 12px;
    padding: 14px 20px;
    background-color: #0D0F12;
    border: 1px solid #1F2227;
    border-radius: 6px;
    margin: 12px 0 18px 0;
}
.term-co-name { font-size: 1.45rem; font-weight: 700; color: #F4F4F5; letter-spacing: -0.02em; }
.term-co-tick { font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; color: #71717A; margin-left: 10px; }
.term-arch-pill {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    color: #22C55E;
    background: rgba(34,197,94,0.12);
    border: 1px solid rgba(34,197,94,0.28);
    padding: 2px 8px;
    border-radius: 99px;
    margin-left: 12px;
}
.term-co-stats { font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #71717A; }
.term-co-stats b { color: #F4F4F5; font-weight: 600; }

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
    margin: 14px 0 18px 0;
}
.term-memo-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #71717A;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid #1F2227;
}

/* STRUCTURED STATEMENTS TABLE */
.kf-wrap {
    width: 100%;
    overflow-x: auto;
    border: 1px solid #1F2227;
    border-radius: 6px;
    background-color: #0B0D10;
    margin-top: 8px;
}
.kf-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    color: #E4E4E7;
}
.kf-table th {
    text-align: right;
    padding: 10px 14px;
    font-weight: 600;
    font-size: 0.76rem;
    color: #A1A1AA;
    border-bottom: 1px solid #1F2227;
    background-color: #0D0F12;
    white-space: nowrap;
}
.kf-table th:first-child { text-align: left; min-width: 230px; }
.kf-table td {
    text-align: right;
    padding: 8px 14px;
    border-bottom: 1px solid #16181D;
    white-space: nowrap;
}
.kf-table td:first-child {
    text-align: left;
    font-family: 'Inter', sans-serif;
    font-size: 0.84rem;
}
.kf-table tr:hover td { background-color: rgba(255,255,255,0.025); }
.kf-row-main td:first-child { color: #F4F4F5; font-weight: 600; }
.kf-row-main td { color: #F4F4F5; font-weight: 500; }
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
        "periodicity": "PERIODICITA:",
        "annual": "Roční (Annual)",
        "quarterly": "Kvartální (Quarterly)",
        "loading": "STAHOVÁNÍ VÝKAZŮ...",
        "err_data": "DATA PRO TENTO TICKER NEJSOU DOSTUPNÁ.",
        "tab_ov": "OVERVIEW",
        "tab_val": "VALUATION",
        "tab_inc": "INCOME STATEMENT",
        "tab_bs": "BALANCE SHEET",
        "tab_cf": "CASH FLOW",
        "tab_ai": "AI ANALYTIK",
        "tab_ana": "ANALYTICI & EARNINGS",
        "tab_news": "NOVINKY",
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
        "r_mcap": "Market Cap",
        "r_cash": "Cash & ST Investments",
        "r_debt": "Total Debt",
        "r_ev": "Enterprise Value",
        "r_rev": "Tržby (Revenue)",
        "r_rev_growth": "Růst tržeb (YoY)",
        "r_gp": "Hrubý zisk (Gross Profit)",
        "r_gm": "Hrubá marže",
        "r_ebit": "Provozní zisk (EBIT)",
        "r_om": "EBIT marže",
        "r_ebitda": "EBITDA",
        "r_ni": "Čistý zisk (Net Income)",
        "r_nm": "Čistá marže",
        "r_eps": "Zisk na akcii (EPS)",
        "r_ocf": "Provozní cash flow (OCF)",
        "r_capex": "Kapitálové výdaje (CapEx)",
        "r_fcf": "Volné cash flow (FCF)",
        "r_fcfm": "FCF marže",
        "unit_lbl": "JEDNOTKY:",
        "unit_b": "Mld. (B)",
        "unit_m": "Mil. (M)",
        "currency_lbl": "Měna výkazů:",
        "convert_usd": "Převést výkazy z {curr} do USD (dle historických kurzů)",
        "matrix_h": "KEY FIGURES",
        "arch_cnt": "mem v archivu",
        "kpi_h": "KPI Dashboard & Valuace",
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
        "stmt_na": "Výkaz není pro tento ticker dostupný.",
        "est_q1": "Q+1E",
        "est_q2": "Q+2E",
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
        "ai_save": "Uložit do terminal_memos.json (GitHub)",
        "ai_saved_ok": "Investiční Memo uloženo do terminal_memos.json a synchronizováno na GitHub.",
        "ai_already_saved": "Toto Investiční Memo je již uložené.",
        "ai_saved_list": "ULOŽENÁ INVESTIČNÍ MEMA",
        "ai_load_btn": "Načíst",
        "ai_del_btn": "Smazat",
        "ai_spin": "AI analyzuje výkazy, marže a valuaci...",
        "ai_no_key": "Pro AI Analytika nastavte GROQ_API_KEY v Secrets a vyberte model v Nastavení.",
        "ai_chat_h": "KONZULTACE S AI NAD VÝKAZY",
        "ai_chat_ph": "Vyhledat..."
    },
    "EN": {
        "title": "DEEP INSTITUTIONAL TERMINAL",
        "desc": "INSTITUTIONAL FINANCIAL STATEMENTS TIMELINE, VALUATION, CONSENSUS & NEWS.",
        "db_select": "DATABASE",
        "custom_tick": "CUSTOM TICKER",
        "periodicity": "PERIODICITY:",
        "annual": "Annual",
        "quarterly": "Quarterly",
        "loading": "LOADING STATEMENTS...",
        "err_data": "DATA FOR THIS TICKER NOT AVAILABLE.",
        "tab_ov": "OVERVIEW",
        "tab_val": "VALUATION",
        "tab_inc": "INCOME STATEMENT",
        "tab_bs": "BALANCE SHEET",
        "tab_cf": "CASH FLOW",
        "tab_ai": "AI ANALYST",
        "tab_ana": "ANALYSTS & EARNINGS",
        "tab_news": "NEWS",
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
        "r_mcap": "Market Cap",
        "r_cash": "Cash & ST Investments",
        "r_debt": "Total Debt",
        "r_ev": "Enterprise Value",
        "r_rev": "Revenue",
        "r_rev_growth": "Revenue growth",
        "r_gp": "Gross profit",
        "r_gm": "Gross margin",
        "r_ebit": "EBIT",
        "r_om": "EBIT margin",
        "r_ebitda": "EBITDA",
        "r_ni": "Net income",
        "r_nm": "Net margin",
        "r_eps": "EPS (diluted)",
        "r_ocf": "Operating cash flow",
        "r_capex": "Capital expenditure",
        "r_fcf": "Free cash flow",
        "r_fcfm": "FCF margin",
        "unit_lbl": "UNITS:",
        "unit_b": "Bn (B)",
        "unit_m": "Mn (M)",
        "currency_lbl": "Reporting Currency:",
        "convert_usd": "Convert statements from {curr} to USD (using historical rates)",
        "matrix_h": "KEY FIGURES",
        "arch_cnt": "saved memos",
        "kpi_h": "KPI Dashboard & Valuation",
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
        "stmt_na": "Statement not available for this ticker.",
        "est_q1": "Q+1E",
        "est_q2": "Q+2E",
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
        "ai_save": "Save to terminal_memos.json (GitHub)",
        "ai_saved_ok": "Investment Memo saved to terminal_memos.json and synced to GitHub.",
        "ai_already_saved": "This Investment Memo is already saved.",
        "ai_saved_list": "SAVED INVESTMENT MEMOS",
        "ai_load_btn": "Load",
        "ai_del_btn": "Delete",
        "ai_spin": "AI is analyzing statements, margins and valuation...",
        "ai_no_key": "Configure GROQ_API_KEY in Secrets and select a model in Settings to use AI Analyst.",
        "ai_chat_h": "AI FUNDAMENTAL CONSULTATION",
        "ai_chat_ph": "Search..."
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

def load_memos():
    if os.path.exists(MEMOS_FILE):
        try:
            with open(MEMOS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []

def save_memos(memos_list, commit_msg="Terminal: Aktualizace terminal_memos.json"):
    with open(MEMOS_FILE, "w", encoding="utf-8") as f:
        json.dump(memos_list, f, indent=4, ensure_ascii=False)
    try:
        if "GITHUB_TOKEN" in st.secrets:
            token = st.secrets["GITHUB_TOKEN"]
            owner = st.secrets["GITHUB_OWNER"]
            repo = st.secrets["GITHUB_REPO"]
            remote_url = f"https://{owner}:{token}@github.com/{owner}/{repo}.git"
            subprocess.run(["git", "config", "--global", "user.email", "bot@pokornyterminal.cz"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "config", "--global", "user.name", "Terminal Bot"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "pull", "--rebase", remote_url, "main"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "add", MEMOS_FILE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "commit", "-m", commit_msg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "push", remote_url, "HEAD:main"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

data = load_data()
all_tickers = list(dict.fromkeys(data.get("portfolio", []) + data.get("watchlist", [])))
saved_settings = data.get("settings", {})

api_key = str(st.secrets.get("GROQ_API_KEY", "")).strip()
model_provider = st.session_state.get("ai_provider", saved_settings.get("ai_provider", "Groq"))
selected_model = st.session_state.get("ai_model", saved_settings.get("ai_model", ""))

if "term_ai_ticker" not in st.session_state: st.session_state.term_ai_ticker = None
if "term_ai_memo_obj" not in st.session_state: st.session_state.term_ai_memo_obj = None
if "term_ai_saved_id" not in st.session_state: st.session_state.term_ai_saved_id = None
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
    st.session_state.term_ai_memo_obj = None
    st.session_state.term_ai_saved_id = None
    st.session_state.term_ai_chat = []

@st.cache_data(ttl=3600, show_spinner=False)
def get_groq_available_models(api_klic):
    try:
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {api_klic}", "User-Agent": random.choice(USER_AGENTS)}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            items = json.loads(resp.read().decode("utf-8")).get("data", [])
            skip = ("whisper", "tts", "guard", "prompt-guard", "orpheus")
            return [m["id"] for m in items if m.get("id") and not any(s in m["id"].lower() for s in skip)]
    except Exception:
        return []

def call_llm_api(messages, api_klic, provider, model_name, temperature=0.2, timeout=30, max_tokens=850):
    url = "https://api.groq.com/openai/v1/chat/completions" if provider == "Groq" else "https://api.openai.com/v1/chat/completions"
    models_to_try = [model_name]
    if provider == "Groq":
        for m in get_groq_available_models(api_klic):
            if m not in models_to_try:
                models_to_try.append(m)

    last_err = ""
    for mdl in models_to_try:
        payload = json.dumps({
            "model": mdl,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload,
            headers={"Authorization": f"Bearer {api_klic}", "Content-Type": "application/json", "User-Agent": random.choice(USER_AGENTS)},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            err_txt = e.read().decode("utf-8", errors="ignore")[:250]
            last_err = f"HTTP {e.code}: {err_txt}"
            if e.code in (400, 404, 429) and mdl != models_to_try[-1]:
                continue
            raise RuntimeError(last_err)
    raise RuntimeError(last_err)

def fmt_cell(val, unit_mode="B", is_pct=False, is_eps=False):
    if val is None or pd.isna(val): return "—"
    try: val = float(val)
    except Exception: return str(val)
    if is_pct: return f"{val * 100:.1f}%"
    if is_eps: return f"{val:,.2f}"
    if unit_mode == "M": return f"{val / 1e6:,.0f} M"
    return f"{val / 1e9:,.2f} B"

def render_statement_html(df, unit_mode="B", rate_fn=None):
    if df is None or df.empty:
        return None
    cols_sorted = sorted(df.columns)
    th_cells = ['<th>Položka / Line Item</th>'] + [f'<th>{c.strftime("%Y-%m-%d")}</th>' for c in cols_sorted]
    rows_html = []
    for idx_name in df.index:
        tds = [f'<td>{idx_name}</td>']
        for c in cols_sorted:
            v = df.loc[idx_name, c]
            r = rate_fn(c) if rate_fn else 1.0
            is_eps_row = "eps" in str(idx_name).lower()
            v_conv = (float(v) * r) if pd.notna(v) else None
            tds.append(f'<td>{fmt_cell(v_conv, unit_mode=unit_mode, is_eps=is_eps_row)}</td>')
        rows_html.append(f'<tr class="kf-row-main">{"".join(tds)}</tr>')
    return f'<div class="kf-wrap"><table class="kf-table"><thead><tr>{"".join(th_cells)}</tr></thead><tbody>{"".join(rows_html)}</tbody></table></div>'

# --- SEC EDGAR 10-YEAR BACKFILL ---
@st.cache_data(ttl=86400, show_spinner=False)
def get_sec_cik_map():
    try:
        r = requests.get("https://www.sec.gov/files/company_tickers.json", headers=SEC_HEADERS, timeout=6)
        if r.status_code == 200:
            raw = r.json()
            return {v["ticker"].upper(): str(v["cik_str"]).zfill(10) for v in raw.values()}
    except Exception:
        pass
    return {}

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_sec_annual_history(ticker):
    cik_map = get_sec_cik_map()
    cik = cik_map.get(ticker.upper())
    if not cik:
        return {}
    try:
        r = requests.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json", headers=SEC_HEADERS, timeout=8)
        if r.status_code != 200:
            return {}
        us_gaap = r.json().get("facts", {}).get("us-gaap", {})
    except Exception:
        return {}

    tag_groups = {
        "rev": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"],
        "gp": ["GrossProfit"],
        "ebit": ["OperatingIncomeLoss"],
        "ni": ["NetIncomeLoss"],
        "eps": ["EarningsPerShareDiluted"],
        "ocf": ["NetCashProvidedByUsedInOperatingActivities"],
        "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
        "cash": ["CashAndCashEquivalentsAtCarryingValue"],
        "debt": ["LongTermDebtNoncurrent", "LongTermDebt"]
    }

    hist = {}
    for key, tags in tag_groups.items():
        unit_pref = "USD/shares" if key == "eps" else "USD"
        for tag in tags:
            units = us_gaap.get(tag, {}).get("units", {})
            entries = units.get(unit_pref)
            if not entries:
                continue
            for e in entries:
                if e.get("form") == "10-K" and e.get("fp") == "FY" and e.get("fy") and e.get("val") is not None:
                    fy = int(e["fy"])
                    if 2016 <= fy <= 2025:
                        lbl = f"FY{fy}"
                        if lbl not in hist:
                            hist[lbl] = {}
                        if key not in hist[lbl]:
                            hist[lbl][key] = float(e["val"])
            if any(key in v for v in hist.values()):
                break
    return hist

@st.cache_data(ttl=900, show_spinner=False)
def load_ticker_bundle(ticker):
    tkr = yf.Ticker(ticker)
    bundle = {
        "info": {}, "fast": {}, "hist_price": 0.0,
        "fin_a": pd.DataFrame(), "fin_q": pd.DataFrame(),
        "cf_a": pd.DataFrame(), "cf_q": pd.DataFrame(),
        "bs_a": pd.DataFrame(), "bs_q": pd.DataFrame(),
        "rev_est": None, "eps_est": None,
        "cal": None, "eh": None, "edates": None
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
    try: bundle["bs_a"] = tkr.balance_sheet
    except Exception: pass
    try: bundle["bs_q"] = tkr.quarterly_balance_sheet
    except Exception: pass
    try: bundle["rev_est"] = tkr.revenue_estimate
    except Exception: pass
    try: bundle["eps_est"] = tkr.earnings_estimate
    except Exception: pass
    try: bundle["cal"] = tkr.calendar
    except Exception: pass
    try: bundle["eh"] = tkr.earnings_history
    except Exception: pass
    try: bundle["edates"] = tkr.earnings_dates
    except Exception: pass
    return bundle

@st.cache_data(ttl=3600, show_spinner=False)
def load_fx_history(currency_code):
    try: return yf.Ticker(f"{currency_code}USD=X").history(period="10y")
    except Exception: return pd.DataFrame()

@st.cache_data(ttl=900, show_spinner=False)
def fetch_ticker_news(ticker):
    articles = []
    try:
        rss_url = f"https://news.google.com/rss/search?q={ticker}+stock+news&hl=en-US&gl=US&ceid=US:en"
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
            if articles: return articles
    except Exception: pass

    try:
        yf_rss = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}®ion=US&lang=en-US"
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
            if articles: return articles
    except Exception: pass

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
    except Exception: pass
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
        bs_period = bundle["bs_q"] if is_quarterly else bundle["bs_a"]
        balance_sheet = bundle["bs_a"]

        if financials is None or financials.empty:
            st.error(_["err_data"])
            st.stop()

        short_name = info.get("shortName", final_tick)
        currency_code = info.get("financialCurrency") or info.get("currency") or fast.get("currency") or "USD"
        trading_currency = info.get("currency") or fast.get("currency") or "USD"

        all_memos = load_memos()
        memo_count = sum(1 for r in all_memos if str(r.get("tema", "")).upper() == final_tick)
        arch_badge = f'<span class="term-arch-pill">{memo_count} {_["arch_cnt"]}</span>' if memo_count > 0 else ""

        mcap_str = f"{market_cap/1e9:,.2f}B {trading_currency}" if (market_cap and market_cap >= 1e9) else (f"{market_cap/1e6:,.1f}M {trading_currency}" if market_cap else "N/A")
        st.markdown(
            f'<div class="term-topbar">'
            f'<div><span class="term-co-name">{short_name}</span><span class="term-co-tick">{final_tick}</span>{arch_badge}</div>'
            f'<div class="term-co-stats">last close <b>{curr_price:,.2f} {trading_currency}</b>   ·   mkt cap <b>{mcap_str}</b></div>'
            f'</div>',
            unsafe_allow_html=True
        )

        # --- FX & UNITS CONTROLS ---
        c_u1, c_u2 = st.columns([3, 1.4])
        convert_to_usd = False
        display_currency = currency_code
        fx_hist = pd.DataFrame()
        latest_fx = 1.0

        if currency_code != "USD":
            convert_to_usd = c_u1.toggle(f"💱 {_['convert_usd'].replace('{curr}', currency_code)}", value=False)
            if convert_to_usd:
                display_currency = "USD"
                fx_hist = load_fx_history(currency_code)
                if not fx_hist.empty: latest_fx = float(fx_hist['Close'].iloc[-1])

        unit_choice = c_u2.radio(_["unit_lbl"], [_["unit_b"], _["unit_m"]], horizontal=True)
        unit_mode = "B" if unit_choice == _["unit_b"] else "M"
        unit_div = 1e9 if unit_mode == "B" else 1e6
        unit_suffix = "B" if unit_mode == "B" else "M"

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
            df_sorted = df.reindex(sorted(df.columns, reverse=True), axis=1)
            for key in keys:
                if key in df_sorted.index:
                    vals = pd.to_numeric(df_sorted.loc[key], errors='coerce').dropna().iloc[:4]
                    if len(vals) == 4:
                        return float(vals.sum())
            return None

        def get_first_val(df, keys, col=None):
            if df is None or df.empty: return None
            for k in keys:
                if k in df.index:
                    v = df.loc[k, col] if (col is not None and col in df.columns) else df.loc[k].iloc[0]
                    if pd.notna(v): return float(v)
            return None

        total_rev_ltm = info.get("totalRevenue") or get_ltm_from_quarterly(q_fin_for_kpi, ['Total Revenue'])
        gm_info = info.get("grossMargins")
        gross_profit_ltm = (total_rev_ltm * gm_info) if (total_rev_ltm and gm_info) else get_ltm_from_quarterly(q_fin_for_kpi, ['Gross Profit'])
        om_info = info.get("operatingMargins")
        op_inc_ltm = (total_rev_ltm * om_info) if (total_rev_ltm and om_info) else get_ltm_from_quarterly(q_fin_for_kpi, ['Operating Income', 'EBIT'])
        net_income_ltm = info.get("netIncomeToCommon") or info.get("netIncome") or get_ltm_from_quarterly(q_fin_for_kpi, ['Net Income', 'Net Income Common Stockholders'])
        ebitda_ltm = info.get("ebitda") or get_ltm_from_quarterly(q_fin_for_kpi, ['Normalized EBITDA', 'EBITDA'])
        ocf_ltm = info.get("operatingCashflow") or get_ltm_from_quarterly(q_cf_for_kpi, ['Operating Cash Flow'])
        capex_ltm = get_ltm_from_quarterly(q_cf_for_kpi, ['Capital Expenditure'])

        fcf = info.get("freeCashflow") or get_ltm_from_quarterly(q_cf_for_kpi, ['Free Cash Flow'])
        if fcf is None and ocf_ltm is not None and capex_ltm is not None:
            fcf = ocf_ltm - abs(capex_ltm)

        eps_ltm = info.get("trailingEps") or get_ltm_from_quarterly(q_fin_for_kpi, ['Diluted EPS', 'Basic EPS'])

        latest_bs = bundle["bs_q"] if (bundle["bs_q"] is not None and not bundle["bs_q"].empty) else balance_sheet
        latest_cash = get_first_val(latest_bs, ['Cash Cash Equivalents And Short Term Investments', 'Cash And Cash Equivalents'])
        latest_debt = get_first_val(latest_bs, ['Total Debt'])
        latest_ev = (market_cap + (latest_debt or 0) - (latest_cash or 0)) if market_cap else info.get("enterpriseValue")

        calc_debt_eq, roic, roce, roi = None, None, None, None
        total_debt, stockholders_eq, total_assets, current_assets, current_liab, inventory = 0, 0, 0, 0, 0, 0
        if balance_sheet is not None and not balance_sheet.empty:
            try:
                total_debt = get_first_val(balance_sheet, ['Total Debt']) or 0
                stockholders_eq = get_first_val(balance_sheet, ['Stockholders Equity']) or 0
                total_assets = get_first_val(balance_sheet, ['Total Assets']) or 0
                current_assets = get_first_val(balance_sheet, ['Current Assets']) or 0
                current_liab = get_first_val(balance_sheet, ['Current Liabilities', 'Total Current Liabilities']) or 0
                inventory = get_first_val(balance_sheet, ['Inventory']) or 0
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
        ev_ebitda = info.get("enterpriseToEbitda") or ((latest_ev / ebitda_ltm) if (latest_ev and ebitda_ltm and ebitda_ltm > 0) else None)
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
            ebit_0 = get_first_val(financials, ['EBIT', 'Operating Income'])
            if ebit_0: roce = ebit_0 / capital_employed
        if net_income_ltm and total_assets > 0: roi = net_income_ltm / total_assets

        # --- BUILD STRUCTURED MATRIX (SEC 10Y BACKFILL + YFINANCE + LTM + ESTIMATES) ---
        matrix_dict = {}
        est_col_labels = []
        last_hist_year = 2024

        yf_years = set()
        if not financials.empty:
            hist_cols = sorted(financials.columns)
            last_hist_year = hist_cols[-1].year
            yf_years = {f"FY{c.year}" for c in hist_cols}

        if not is_quarterly and display_currency == "USD":
            sec_hist = fetch_sec_annual_history(final_tick)
            for fy_lbl in sorted(sec_hist.keys()):
                if fy_lbl not in yf_years:
                    s = sec_hist[fy_lbl]
                    s_ocf = s.get("ocf")
                    s_capex = s.get("capex")
                    s_fcf = (s_ocf - abs(s_capex)) if (s_ocf is not None and s_capex is not None) else None
                    matrix_dict[fy_lbl] = {
                        _["r_mcap"]: None,
                        _["r_cash"]: s.get("cash"),
                        _["r_debt"]: s.get("debt"),
                        _["r_ev"]: None,
                        _["r_rev"]: s.get("rev"),
                        _["r_gp"]: s.get("gp"),
                        _["r_ebit"]: s.get("ebit"),
                        _["r_ebitda"]: None,
                        _["r_ni"]: s.get("ni"),
                        _["r_eps"]: s.get("eps"),
                        _["r_ocf"]: s_ocf,
                        _["r_capex"]: abs(s_capex) if s_capex is not None else None,
                        _["r_fcf"]: s_fcf
                    }

        if not financials.empty:
            for col in sorted(financials.columns):
                rate = get_rate(col)
                col_label = f"{col.year}-Q{col.quarter}" if is_quarterly else f"FY{col.year}"
                c_cash = get_first_val(bs_period, ['Cash Cash Equivalents And Short Term Investments', 'Cash And Cash Equivalents'], col)
                c_debt = get_first_val(bs_period, ['Total Debt'], col)
                c_rev = get_first_val(financials, ['Total Revenue'], col)
                c_gp = get_first_val(financials, ['Gross Profit'], col)
                c_ebit = get_first_val(financials, ['Operating Income', 'EBIT'], col)
                c_ebitda = get_first_val(financials, ['Normalized EBITDA', 'EBITDA'], col)
                c_ni = get_first_val(financials, ['Net Income Common Stockholders', 'Net Income'], col)
                c_eps = get_first_val(financials, ['Diluted EPS', 'Basic EPS'], col)
                c_ocf = get_first_val(cashflow, ['Operating Cash Flow'], col)
                c_capex = get_first_val(cashflow, ['Capital Expenditure'], col)
                c_fcf = get_first_val(cashflow, ['Free Cash Flow'], col)
                if c_fcf is None and c_ocf is not None and c_capex is not None:
                    c_fcf = c_ocf - abs(c_capex)

                matrix_dict[col_label] = {
                    _["r_mcap"]: None,
                    _["r_cash"]: c_cash * rate if c_cash is not None else None,
                    _["r_debt"]: c_debt * rate if c_debt is not None else None,
                    _["r_ev"]: None,
                    _["r_rev"]: c_rev * rate if c_rev is not None else None,
                    _["r_gp"]: c_gp * rate if c_gp is not None else None,
                    _["r_ebit"]: c_ebit * rate if c_ebit is not None else None,
                    _["r_ebitda"]: c_ebitda * rate if c_ebitda is not None else None,
                    _["r_ni"]: c_ni * rate if c_ni is not None else None,
                    _["r_eps"]: c_eps * rate if c_eps is not None else None,
                    _["r_ocf"]: c_ocf * rate if c_ocf is not None else None,
                    _["r_capex"]: abs(c_capex) * rate if c_capex is not None else None,
                    _["r_fcf"]: c_fcf * rate if c_fcf is not None else None
                }

        if not is_quarterly:
            rate = latest_fx if convert_to_usd else 1.0
            matrix_dict["LTM"] = {
                _["r_mcap"]: market_cap * rate if market_cap else None,
                _["r_cash"]: latest_cash * rate if latest_cash is not None else None,
                _["r_debt"]: latest_debt * rate if latest_debt is not None else None,
                _["r_ev"]: latest_ev * rate if latest_ev else None,
                _["r_rev"]: total_rev_ltm * rate if total_rev_ltm is not None else None,
                _["r_gp"]: gross_profit_ltm * rate if gross_profit_ltm is not None else None,
                _["r_ebit"]: op_inc_ltm * rate if op_inc_ltm is not None else None,
                _["r_ebitda"]: ebitda_ltm * rate if ebitda_ltm is not None else None,
                _["r_ni"]: net_income_ltm * rate if net_income_ltm is not None else None,
                _["r_eps"]: eps_ltm * rate if eps_ltm is not None else None,
                _["r_ocf"]: ocf_ltm * rate if ocf_ltm is not None else None,
                _["r_capex"]: abs(capex_ltm) * rate if capex_ltm is not None else None,
                _["r_fcf"]: fcf * rate if fcf is not None else None
            }

        try:
            rev_est = bundle["rev_est"]
            eps_est = bundle["eps_est"]
            est_keys = [("0q", _["est_q1"]), ("+1q", _["est_q2"])] if is_quarterly else [("0y", f"FY{last_hist_year + 1}E"), ("+1y", f"FY{last_hist_year + 2}E")]
            for k, label in est_keys:
                est_col_labels.append(label)
                rate = latest_fx if convert_to_usd else 1.0
                e_val = eps_est.loc[k, "avg"] if (eps_est is not None and not eps_est.empty and k in eps_est.index and "avg" in eps_est.columns) else None
                r_val = rev_est.loc[k, "avg"] if (rev_est is not None and not rev_est.empty and k in rev_est.index and "avg" in rev_est.columns) else None
                matrix_dict[label] = {
                    _["r_mcap"]: None, _["r_cash"]: None, _["r_debt"]: None, _["r_ev"]: None,
                    _["r_rev"]: (float(r_val) * rate) if pd.notna(r_val) else None,
                    _["r_gp"]: None, _["r_ebit"]: None, _["r_ebitda"]: None,
                    _["r_ni"]: (float(e_val) * rate * shares_out) if (pd.notna(e_val) and shares_out) else None,
                    _["r_eps"]: (float(e_val) * rate) if pd.notna(e_val) else None,
                    _["r_ocf"]: None, _["r_capex"]: None, _["r_fcf"]: None
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

        # --- MAIN TABS ---
        tab_ov, tab_val, tab_inc, tab_bs, tab_cf, tab_ai, tab_ana, tab_news = st.tabs([
            _["tab_ov"], _["tab_val"], _["tab_inc"], _["tab_bs"], _["tab_cf"], _["tab_ai"], _["tab_ana"], _["tab_news"]
        ])

        with tab_ov:
            chart_box = st.container()

            row_defs = [
                (_["r_mcap"], "val"),
                (_["r_cash"], "val"),
                (_["r_debt"], "val"),
                (_["r_ev"], "val"),
                (_["r_rev"], "val"),
                (_["r_rev_growth"], "pct"),
                (_["r_gp"], "val"),
                (_["r_gm"], "pct"),
                (_["r_ebit"], "val"),
                (_["r_om"], "pct"),
                (_["r_ebitda"], "val"),
                (_["r_ni"], "val"),
                (_["r_nm"], "pct"),
                (_["r_eps"], "eps"),
                (_["r_ocf"], "val"),
                (_["r_capex"], "val"),
                (_["r_fcf"], "val"),
                (_["r_fcfm"], "pct"),
            ]

            valid_rows = [(k, kind) for k, kind in row_defs if k in df_matrix.index]
            row_names = [k for k, _ in valid_rows]
            row_kinds = {k: kind for k, kind in valid_rows}

            cols = list(df_matrix.columns)
            disp_data = {}
            for c in cols:
                disp_data[c] = [
                    fmt_cell(
                        df_matrix.loc[k, c],
                        unit_mode=unit_mode,
                        is_pct=(row_kinds[k] == "pct"),
                        is_eps=(row_kinds[k] == "eps")
                    )
                    for k in row_names
                ]

            df_kf = pd.DataFrame(disp_data, index=row_names)
            df_kf.index.name = f'{_["matrix_h"]} ({display_currency} {unit_suffix})'

            def style_kf(df_in):
                styles = pd.DataFrame("", index=df_in.index, columns=df_in.columns)
                if "LTM" in styles.columns:
                    styles["LTM"] = "background-color: rgba(34, 197, 94, 0.10); color: #22C55E; font-weight: 600;"
                for ec in est_col_labels:
                    if ec in styles.columns:
                        styles[ec] = "color: #9CA3AF; font-style: italic;"
                return styles

            st.caption("☑️ Klikněte na čtvereček vlevo u libovolné metriky pro její vykreslení do grafu." if current_lang == "CZ" else "☑️ Click the checkbox next to any metric to plot it on the chart.")

            kf_event = st.dataframe(
                df_kf.style.apply(style_kf, axis=None),
                use_container_width=True,
                height=min(665, 38 + len(row_names) * 35),
                on_select="rerun",
                selection_mode="multi-row",
                key=f"kf_sel_{final_tick}_{period_type}_{unit_mode}"
            )

            selected_idx = kf_event.selection.rows if (kf_event and kf_event.selection) else []
            sel_metrics = [row_names[i] for i in selected_idx if i < len(row_names)]

            palette = ["#22C55E", "#3B82F6", "#F97316", "#A855F7", "#14B8A6", "#EAB308", "#EC4899", "#06B6D4"]

            with chart_box:
                if sel_metrics:
                    c_chips, c_type = st.columns([5, 1.2])
                    chips_html = "".join([
                        f'<span style="display:inline-flex;align-items:center;gap:6px;background:#14171C;border:1px solid #262930;border-radius:4px;padding:3px 9px;margin:0 6px 6px 0;font-family:\'JetBrains Mono\',monospace;font-size:0.76rem;color:#E4E4E7;">'
                        f'<span style="width:8px;height:8px;border-radius:2px;background:{palette[i % len(palette)]};display:inline-block;"></span>{m}</span>'
                        for i, m in enumerate(sel_metrics)
                    ])
                    c_chips.markdown(chips_html, unsafe_allow_html=True)
                    chart_type = c_type.radio(
                        "Typ grafu",
                        ["Sloupce", "Linie"] if current_lang == "CZ" else ["Bar", "Line"],
                        horizontal=True,
                        label_visibility="collapsed",
                        key=f"ctype_{final_tick}"
                    )
                    is_line = chart_type in ("Linie", "Line")

                    all_pct = all(row_kinds[m] == "pct" for m in sel_metrics)
                    all_eps = all(row_kinds[m] == "eps" for m in sel_metrics)

                    fig = go.Figure()
                    for i, m in enumerate(sel_metrics):
                        color_hex = palette[i % len(palette)]
                        raw_vals = pd.to_numeric(df_matrix.loc[m, cols], errors='coerce')
                        kind = row_kinds[m]

                        if kind == "pct":
                            y_vals = raw_vals * 100
                            hover_tpl = f"%{{x}}: %{{y:.1f}}%<extra>{m}</extra>"
                        elif kind == "eps":
                            y_vals = raw_vals
                            hover_tpl = f"%{{x}}: %{{y:,.2f}} {display_currency}<extra>{m}</extra>"
                        else:
                            y_vals = raw_vals / unit_div
                            fmt_h = ",.2f" if unit_mode == "B" else ",.0f"
                            hover_tpl = f"%{{x}}: %{{y:{fmt_h}}} {unit_suffix} {display_currency}<extra>{m}</extra>"

                        if is_line:
                            fig.add_trace(go.Scatter(
                                x=cols, y=y_vals, name=m, mode="lines+markers",
                                line=dict(color=color_hex, width=2.5),
                                marker=dict(size=6, color=color_hex),
                                hovertemplate=hover_tpl
                            ))
                        else:
                            est_fill = "rgba(255,255,255,0.06)"
                            bar_colors = [est_fill if c in est_col_labels else color_hex for c in cols]
                            line_colors = [color_hex if c in est_col_labels else "rgba(0,0,0,0)" for c in cols]
                            line_widths = [1.8 if c in est_col_labels else 0 for c in cols]
                            fig.add_trace(go.Bar(
                                x=cols, y=y_vals, name=m,
                                marker=dict(color=bar_colors, line=dict(color=line_colors, width=line_widths)),
                                hovertemplate=hover_tpl
                            ))

                    y_suffix = "%" if all_pct else (f" {display_currency}" if all_eps else f" {unit_suffix}")
                    fig.update_layout(
                        template="plotly_dark",
                        barmode="group",
                        bargap=0.28,
                        bargroupgap=0.08,
                        height=300,
                        paper_bgcolor="#0D0F12",
                        plot_bgcolor="#0D0F12",
                        margin=dict(l=10, r=10, t=12, b=10),
                        showlegend=False,
                        xaxis=dict(showgrid=False, tickfont=dict(family="JetBrains Mono", size=11, color="#A1A1AA")),
                        yaxis=dict(showgrid=True, gridcolor="#1F2227", ticksuffix=y_suffix, tickfont=dict(family="JetBrains Mono", size=11, color="#71717A"))
                    )
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        with tab_val:
            st.markdown(f'<div class="term-sec-label">{short_name} ({final_tick}) · {_["kpi_h"]}</div>', unsafe_allow_html=True)
            vkpi1, vkpi2, vkpi3, vkpi4, vkpi5 = st.columns(5)

            def fmt_kpi(val, is_pct=False, is_curr=False, curr_label="USD"):
                if val is None or pd.isna(val): return "N/A"
                if is_pct: return f"{val*100:.2f} %"
                if is_curr:
                    if abs(val) >= 1e9: return f"{val/1e9:.2f} B {curr_label}"
                    if abs(val) >= 1e6: return f"{val/1e6:.2f} M {curr_label}"
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

        with tab_inc:
            st.markdown(f'<div class="term-sec-label">INCOME STATEMENT · {final_tick} ({display_currency} {unit_suffix})</div>', unsafe_allow_html=True)
            inc_html = render_statement_html(financials, unit_mode=unit_mode, rate_fn=get_rate)
            if inc_html: st.markdown(inc_html, unsafe_allow_html=True)
            else: st.info(_["stmt_na"])

        with tab_bs:
            st.markdown(f'<div class="term-sec-label">BALANCE SHEET · {final_tick} ({display_currency} {unit_suffix})</div>', unsafe_allow_html=True)
            bs_html = render_statement_html(bs_period, unit_mode=unit_mode, rate_fn=get_rate)
            if bs_html: st.markdown(bs_html, unsafe_allow_html=True)
            else: st.info(_["stmt_na"])

        with tab_cf:
            st.markdown(f'<div class="term-sec-label">CASH FLOW STATEMENT · {final_tick} ({display_currency} {unit_suffix})</div>', unsafe_allow_html=True)
            cf_html = render_statement_html(cashflow, unit_mode=unit_mode, rate_fn=get_rate)
            if cf_html: st.markdown(cf_html, unsafe_allow_html=True)
            else: st.info(_["stmt_na"])

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
                    "Financial_Matrix": df_matrix.dropna(how="all").to_dict()
                }
                kpi_json_str = json.dumps(kpi_summary, ensure_ascii=False, default=str)

                if st.button(_["ai_btn"], type="primary", use_container_width=True):
                    now_dt = datetime.now(ZoneInfo("Europe/Prague"))
                    datum_str = now_dt.strftime("%d. %m. %Y %H:%M")
                    lang_instr = "v čisté češtině bez anglických frází" if current_lang == "CZ" else "in clean institutional English"
                    memo_prompt = f"""Jsi Senior Equity Analyst & Portfolio Manager. Dnešní datum a čas je {datum_str}.
Na základě PŘESNĚ TĚCHTO finančních dat vypracuj stručné institucionální investiční memo {lang_instr} (nepiš žádné úvodní řádky s datem ani zástupné symboly v hranatých závorkách, začni rovnou bodem 1):
1. **KVALITA BYZNYSU & MARŽE** (trend tržeb, provozní páka, FCF konverze, ROIC)
2. **VALUACE & MARGIN OF SAFETY** (zhodnocení P/E, Forward P/E, EV/EBITDA, P/FCF vůči růstu)
3. **ROZVAHA & RIZIKA** (zadlužení, likvidita, hlavní hrozby)
4. **VERDIKT ANALYTIKA** (jasný postoj + klíčové číslo k sledování)

Používej výhradně tato data:
{kpi_json_str}"""
                    with st.spinner(_["ai_spin"]):
                        try:
                            memo_txt = call_llm_api([{"role": "user", "content": memo_prompt}], api_key, model_provider, selected_model, temperature=0.2, timeout=35, max_tokens=1100)
                            rep_id = f"{now_dt.strftime('%Y%m%d_%H%M%S')}_MEMO_{final_tick}"
                            st.session_state.term_ai_memo_obj = {
                                "id": rep_id,
                                "datum": datum_str,
                                "typ": "INVESTIČNÍ MEMO",
                                "tema": final_tick,
                                "hlavni_nadpis": f"Investiční memo: {short_name} ({final_tick}) · {curr_price:,.2f} {trading_currency}",
                                "obsah": memo_txt,
                                "chat": []
                            }
                            st.session_state.term_ai_saved_id = None
                            st.session_state.term_ai_chat = []
                        except Exception as e:
                            st.error(f"AI Error: {e}")

                if st.session_state.term_ai_memo_obj:
                    m_obj = st.session_state.term_ai_memo_obj
                    st.markdown(
                        f'<div class="term-memo-box">'
                        f'<div class="term-memo-meta">{m_obj.get("datum", "")}  ·  INVESTIČNÍ MEMO  ·  {short_name} ({final_tick})</div>',
                        unsafe_allow_html=True
                    )
                    st.markdown(m_obj.get("obsah", m_obj.get("co_se_stalo", "")))
                    st.markdown('</div>', unsafe_allow_html=True)

                    saved_chat_len = len(m_obj.get("chat", []))
                    curr_chat_len = len(st.session_state.term_ai_chat)
                    has_unsaved_chat = (st.session_state.term_ai_saved_id == m_obj["id"] and curr_chat_len != saved_chat_len)

                    if st.session_state.term_ai_saved_id == m_obj["id"] and not has_unsaved_chat:
                        st.info(_["ai_already_saved"])
                    else:
                        btn_lbl = (
                            f"💾 Aktualizovat Memo + Chat ({curr_chat_len} zpráv) na GitHub"
                            if has_unsaved_chat else
                            f"💾 {_['ai_save']}"
                        )
                        if st.button(btn_lbl):
                            memos = load_memos()
                            m_obj["chat"] = list(st.session_state.term_ai_chat)
                            existing_idx = next((idx for idx, x in enumerate(memos) if x.get("id") == m_obj["id"]), None)
                            if existing_idx is not None:
                                memos[existing_idx] = m_obj
                            else:
                                memos.insert(0, m_obj)
                            save_memos(memos, commit_msg=f"Terminal: Uloženo Memo + Chat {final_tick}")
                            st.session_state.term_ai_memo_obj = m_obj
                            st.session_state.term_ai_saved_id = m_obj["id"]
                            st.success(_["ai_saved_ok"])

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
                            lang_reply = "Odpovídej čistou češtinou, stručně a k věci." if current_lang == "CZ" else "Answer in clean, concise English."
                            compact_kpi = {
                                "company": f"{short_name} ({final_tick})",
                                "price": f"{curr_price} {trading_currency}",
                                "PE": pe, "Forward_PE": fwd_pe, "PEG": peg, "EV_EBITDA": ev_ebitda, "P_FCF": p_fcf,
                                "Gross_Margin": gross_margin, "Operating_Margin": op_margin, "Net_Margin": profit_margin,
                                "ROE": roe, "ROIC": roic, "Debt_to_Equity": calc_debt_eq, "Current_Ratio": current_ratio,
                                "LTM_Revenue": total_rev_ltm, "LTM_Net_Income": net_income_ltm, "LTM_FCF": fcf
                            }
                            msgs = [{"role": "system", "content": f"Jsi Senior Equity Analyst. Data: {json.dumps(compact_kpi, default=str)}. {lang_reply}"}]
                            for m in st.session_state.term_ai_chat[-6:-1]:
                                msgs.append({"role": m["role"], "content": m["content"]})
                            msgs.append({"role": "user", "content": q_term})
                            try: ans = call_llm_api(msgs, api_key, model_provider, selected_model, temperature=0.25, timeout=25, max_tokens=650)
                            except Exception as e: ans = f"⚠️ AI Error ({e})."
                            st.markdown(ans)
                    if not ans.startswith("⚠️"):
                        st.session_state.term_ai_chat.append({"role": "assistant", "content": ans})
                        st.rerun()

                saved_memos = [r for r in all_memos if str(r.get("tema", "")).upper() == final_tick]
                if saved_memos:
                    st.markdown("---")
                    st.markdown(f'<div class="term-sec-label">{_["ai_saved_list"]} ({final_tick}) · {len(saved_memos)}</div>', unsafe_allow_html=True)
                    for sm in saved_memos:
                        chat_cnt = len(sm.get("chat", []))
                        chat_tag = f" · 💬 {chat_cnt}" if chat_cnt > 0 else ""
                        c_m1, c_m2, c_m3 = st.columns([5, 1, 1])
                        c_m1.markdown(f"`{sm.get('datum', '')}` · **{sm.get('hlavni_nadpis', final_tick)}**{chat_tag}")
                        if c_m2.button(_["ai_load_btn"], key=f"load_m_{sm.get('id')}", use_container_width=True):
                            st.session_state.term_ai_memo_obj = sm
                            st.session_state.term_ai_saved_id = sm.get("id")
                            st.session_state.term_ai_chat = list(sm.get("chat", []))
                            st.rerun()
                        if c_m3.button(_["ai_del_btn"], key=f"del_m_{sm.get('id')}", use_container_width=True):
                            new_m = [r for r in all_memos if r.get("id") != sm.get("id")]
                            save_memos(new_m, commit_msg=f"Terminal: Smazáno Memo {final_tick}")
                            if st.session_state.term_ai_memo_obj and st.session_state.term_ai_memo_obj.get("id") == sm.get("id"):
                                st.session_state.term_ai_memo_obj = None
                                st.session_state.term_ai_chat = []
                            st.rerun()

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

            st.markdown("---")
            st.subheader(_["earn_next_h"])
            try:
                today_d = datetime.now(ZoneInfo("Europe/Prague")).date()
                next_date = None
                cal = bundle["cal"]
                if isinstance(cal, dict) and 'Earnings Date' in cal:
                    for d_cand in cal['Earnings Date']:
                        d_val = d_cand.date() if hasattr(d_cand, "date") else d_cand
                        if d_val >= today_d:
                            next_date = d_val
                            break

                if not next_date and bundle["edates"] is not None and not bundle["edates"].empty:
                    future_dates = sorted([idx.date() for idx in bundle["edates"].index if idx.date() >= today_d])
                    if future_dates:
                        next_date = future_dates[0]

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

                    keep_cols = [c for c in ["epsActual", "epsEstimate", "epsDifference", "surprisePercent"] if c in df_eh.columns]
                    df_eh = df_eh[keep_cols].rename(columns={
                        "epsActual": _["eh_act"],
                        "epsEstimate": _["eh_est"],
                        "epsDifference": _["eh_diff"],
                        "surprisePercent": _["eh_surp"]
                    })
                    for col_eps in [_["eh_act"], _["eh_est"]]:
                        if col_eps in df_eh.columns:
                            df_eh[col_eps] = df_eh[col_eps].apply(lambda x: f"{float(x):.2f}" if pd.notna(x) else "-")
                    if _["eh_diff"] in df_eh.columns:
                        df_eh[_["eh_diff"]] = df_eh[_["eh_diff"]].apply(lambda x: f"{float(x):+.2f}" if pd.notna(x) else "-")
                    if _["eh_surp"] in df_eh.columns:
                        df_eh[_["eh_surp"]] = df_eh[_["eh_surp"]].apply(lambda x: f"{float(x)*100:+.2f} %" if pd.notna(x) else "-")
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