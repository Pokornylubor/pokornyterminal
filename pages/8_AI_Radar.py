import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import json
import os
import sys
import re
import hashlib
import random
import subprocess
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# --- INITIAL SETUP ---
st.set_page_config(page_title="POKORNY TERMINAL | AI RADAR", layout="wide", initial_sidebar_state="collapsed")

aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)

import menu
menu.vykresli_menu()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
]

def get_headers(is_html=False):
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" if is_html else "application/rss+xml, application/xml, text/xml, */*",
        "Accept-Language": "en-US,en;q=0.9"
    }

# --- EDITORIAL DARK CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

.stApp { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

.news-card {
    width: 100%;
    margin: 10px 0 18px 0;
    padding: 24px 28px;
    background-color: #0D0F12;
    border: 1px solid #1F2227;
    border-radius: 8px;
}
.news-time {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #71717A;
    margin-bottom: 8px;
}
.news-title {
    font-family: 'Inter', sans-serif;
    font-size: 1.55rem;
    font-weight: 700;
    color: #F4F4F5;
    line-height: 1.28;
    letter-spacing: -0.015em;
    margin: 0 0 8px 0;
}
.news-sub {
    font-size: 0.78rem;
    color: #71717A;
    margin-bottom: 14px;
}
.news-body {
    font-size: 0.96rem;
    line-height: 1.68;
    color: #D4D4D8;
    margin: 0 0 16px 0;
}
.news-pill-row {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 8px;
}
.news-cat-pill {
    font-family: 'Inter', sans-serif;
    font-size: 0.76rem;
    font-weight: 600;
    color: #E4E4E7;
    background-color: #181B20;
    border: 1px solid #272A30;
    padding: 3px 10px;
    border-radius: 5px;
}
.news-score-pill {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 5px;
}
.news-caption {
    font-size: 0.80rem;
    color: #71717A;
    margin-bottom: 16px;
}
.news-ai-box {
    background-color: #12151A;
    border: 1px solid #22262E;
    border-radius: 6px;
    padding: 18px 22px;
    margin-top: 10px;
}
.news-ai-hdr {
    font-size: 0.92rem;
    font-weight: 700;
    color: #F4F4F5;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.news-ai-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    font-weight: 600;
    color: #60A5FA;
    background: rgba(59,130,246,0.14);
    padding: 2px 7px;
    border-radius: 4px;
}
.news-sec-lbl {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    font-weight: 600;
    color: #71717A;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 12px 0 4px 0;
}
.news-sec-txt {
    font-size: 0.93rem;
    line-height: 1.62;
    color: #E4E4E7;
    margin: 0;
}
.news-feed-row {
    padding: 12px 14px;
    border-bottom: 1px solid #1F2227;
}
.news-feed-title {
    font-size: 1.01rem;
    font-weight: 600;
    color: #F4F4F5;
    margin-top: 3px;
}
.brief-article {
    width: 100%;
    margin: 12px 0 24px 0;
    padding: 28px 32px;
    background-color: #0D0F12;
    border: 1px solid #1F2227;
    border-radius: 6px;
}
.brief-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #71717A;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 10px;
}
.brief-headline {
    font-family: 'Inter', sans-serif;
    font-size: 1.70rem;
    font-weight: 700;
    color: #F4F4F5;
    line-height: 1.25;
    margin: 0 0 14px 0;
}
.brief-badge {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.76rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 3px;
    margin-bottom: 18px;
}
.brief-divider { border: none; border-top: 1px solid #1F2227; margin: 18px 0; }
.brief-sec-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    font-weight: 600;
    color: #71717A;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    margin: 20px 0 8px 0;
}
.brief-body {
    font-size: 0.98rem;
    line-height: 1.7;
    color: #D4D4D8;
    margin: 0;
}
.brief-lib-row { padding: 14px 0; border-bottom: 1px solid #1F2227; }
.brief-lib-title { font-size: 1.06rem; font-weight: 600; color: #F4F4F5; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

current_lang = st.session_state.get("lang", "CZ")

WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")
ARCHIVE_FILE = os.path.join(hlavni_slozka, "ai_radar_archive.json")

# --- DICTIONARY ---
t = {
    "CZ": {
        "title": "AI ZPRÁVY & SENTIMENT",
        "desc": "ŽIVÝ MONITOR TRŽNÍCH ZPRÁV, S&P 500 RISK-ON / RISK-OFF SKÓRE, 30MIN MINUTOVÁ REAKCE TRHU A SYNTÉZY.",
        "tab_live": "ŽIVÝ RADAR",
        "tab_gen": "MARKET BRIEF (SOUHRN)",
        "tab_lib": "ARCHIV REPORTŮ",
        "refresh_btn": "Obnovit zprávy",
        "filter_lbl": "FILTR ZPRÁV",
        "search_lbl": "HLEDAT VE ZPRÁVÁCH",
        "search_ph": "Ticker, firma, Fed, cla, ropa...",
        "open_card": "AI Vysvětlení →",
        "back_feed": "← Zpět na živý přehled zpráv",
        "orig_exp": "Zobrazit originál článku",
        "score_desc": "Změřený dopad na S&P 500 sentiment. Kladné hodnoty podporují Risk-On, záporné Risk-Off.",
        "ai_expl_hdr": "AI vysvětlení",
        "what_happened": "CO SE STALO",
        "why_sp500": "PROČ TO HÝBE TRHEM S&P 500",
        "why_move": "PROČ TO HÝBE TRHEM (FUNDAMENT)",
        "how_reacted": "JAK TRH REAGOVAL",
        "react_pending": "Doplní se 30 minut po zprávě z minutových cen.",
        "watch_next": "CO SLEDOVAT DÁL",
        "ask_news_h": "Vaše otázky k této zprávě",
        "ask_news_sub": "Zeptejte se, proč pohnula trhem, jak reagovaly ceny nebo co k tématu zaznělo v posledních dnech.",
        "ask_news_ph": "Zeptat se AI na tuto zprávu...",
        "save_card": "Uložit zprávu do Archivu (GitHub)",
        "mode_lbl": "REŽIM ANALÝZY",
        "mode_macro": "MARKET BRIEF (Trh & Makro)",
        "mode_stock": "AKCIE (Ticker)",
        "macro_preset": "TRŽNÍ OKRUH",
        "macro_custom": "VLASTNÍ TÉMA",
        "macro_ph": "Zadejte vlastní téma...",
        "tick_db": "DATABÁZE",
        "tick_cust": "VLASTNÍ TICKER",
        "tick_ph": "Vyhledat...",
        "db_ph": "Vybrat...",
        "btn_ai": "Vygenerovat souhrnný report",
        "btn_save": "Uložit do Archivu (GitHub)",
        "saved_ok": "Uloženo do Archivu a synchronizováno na GitHub.",
        "already_saved": "Již uloženo v Archivu.",
        "spin_search": "Stahování zpráv z CNBC, MarketWatch, Yahoo Finance a Watchlistu...",
        "spin_ai": "AI analyzuje zprávu, počítá S&P 500 skóre a měří minutovou reakci trhu...",
        "spin_chat": "AI formuluje odpověď...",
        "err_api": "AI API klíč nebo model nebyl nalezen. Zkontrolujte GROQ_API_KEY v Secrets a Nastavení.",
        "err_ai": "Chyba AI enginu:",
        "err_news": "Žádné aktuální zprávy nebyly nalezeny.",
        "sources": "Zdrojové zprávy použité pro syntézu",
        "no_title": "Bez titulku",
        "no_time": "Neznámý čas",
        "chat_h": "Dotazy k tomuto reportu",
        "chat_ph": "Zeptejte se na detaily...",
        "lib_empty": "Archiv je zatím prázdný.",
        "lib_filter": "FILTR",
        "lib_all": "Vše",
        "lib_macro_lbl": "MARKET BRIEF",
        "lib_stock_lbl": "AKCIE",
        "lib_card_lbl": "ZPRÁVA (AI)",
        "lib_saved_h": "ULOŽENÉ ZPRÁVY A REPORTY",
        "lib_search": "HLEDAT V ARCHIVU",
        "lib_search_ph": "Ticker, téma nebo klíčové slovo...",
        "lib_open": "Číst →",
        "lib_del": "Smazat",
        "lib_deleted": "Odstraněno z Archivu.",
        "lib_back": "← Zpět do Archivu",
        "presets": {
            "US Trh & Indexy (S&P 500, Nasdaq)": "S&P 500 Nasdaq stock market Wall Street",
            "FED, Inflace & Dluhopisy": "Federal Reserve interest rates CPI inflation treasury yields",
            "AI & Polovodiče": "AI semiconductors Nvidia data center chip stocks",
            "Zlato, Ropa & Komodity": "gold price XAUUSD crude oil commodities market",
            "Makro & Měny (USD, EUR)": "global macro economy EURUSD central banks markets"
        }
    },
    "EN": {
        "title": "AI NEWS & SENTIMENT",
        "desc": "REAL-TIME MARKET NEWS MONITOR, S&P 500 RISK-ON / RISK-OFF SCORE & 30-MIN MARKET REACTION.",
        "tab_live": "LIVE RADAR",
        "tab_gen": "MARKET BRIEF (SYNTHESIS)",
        "tab_lib": "REPORT ARCHIVE",
        "refresh_btn": "Refresh News",
        "filter_lbl": "NEWS FILTER",
        "search_lbl": "SEARCH NEWS",
        "search_ph": "Ticker, company, Fed, tariffs, oil...",
        "open_card": "AI Explanation →",
        "back_feed": "← Back to live news feed",
        "orig_exp": "Show original article",
        "score_desc": "Measured impact on S&P 500 sentiment. Positive values support Risk-On, negative Risk-Off.",
        "ai_expl_hdr": "AI Explanation",
        "what_happened": "WHAT HAPPENED",
        "why_sp500": "WHY IT MOVES THE S&P 500",
        "why_move": "WHY IT MOVES THE MARKET (FUNDAMENTALS)",
        "how_reacted": "HOW THE MARKET REACTED",
        "react_pending": "Populates 30 minutes after the news from 1-minute prices.",
        "watch_next": "WHAT TO WATCH NEXT",
        "ask_news_h": "Your questions about this news",
        "ask_news_sub": "Ask why it moved the market, how prices reacted, or recent context.",
        "ask_news_ph": "Ask AI about this news...",
        "save_card": "Save news card to Archive (GitHub)",
        "mode_lbl": "ANALYSIS MODE",
        "mode_macro": "MARKET BRIEF (Macro & Market)",
        "mode_stock": "EQUITY (Ticker)",
        "macro_preset": "MARKET FOCUS",
        "macro_custom": "CUSTOM TOPIC",
        "macro_ph": "Enter custom topic...",
        "tick_db": "DATABASE",
        "tick_cust": "CUSTOM TICKER",
        "tick_ph": "Search...",
        "db_ph": "Select...",
        "btn_ai": "Generate Synthesis Report",
        "btn_save": "Save to Archive (GitHub)",
        "saved_ok": "Saved to Archive and synced to GitHub.",
        "already_saved": "Already saved in Archive.",
        "spin_search": "Fetching news from CNBC, MarketWatch, Yahoo Finance & Watchlist...",
        "spin_ai": "AI is analyzing article, scoring S&P 500 impact & checking 1m prices...",
        "spin_chat": "AI is formulating response...",
        "err_api": "AI API key or model not found. Check GROQ_API_KEY in Secrets and Settings.",
        "err_ai": "AI Engine Error:",
        "err_news": "No current news found.",
        "sources": "Source news used for synthesis",
        "no_title": "No Title",
        "no_time": "Unknown Time",
        "chat_h": "Questions about this report",
        "chat_ph": "Ask for details...",
        "lib_empty": "Archive is empty.",
        "lib_filter": "FILTER",
        "lib_all": "All",
        "lib_macro_lbl": "MARKET BRIEF",
        "lib_stock_lbl": "EQUITY",
        "lib_card_lbl": "AI NEWS CARD",
        "lib_saved_h": "SAVED NEWS & REPORTS",
        "lib_search": "SEARCH ARCHIVE",
        "lib_search_ph": "Ticker, topic, or keyword...",
        "lib_open": "Read →",
        "lib_del": "Delete",
        "lib_deleted": "Removed from Archive.",
        "lib_back": "← Back to Archive",
        "presets": {
            "US Market & Indices (S&P 500, Nasdaq)": "S&P 500 Nasdaq stock market Wall Street",
            "FED, Inflation & Bonds": "Federal Reserve interest rates CPI inflation treasury yields",
            "AI & Semiconductors": "AI semiconductors Nvidia data center chip stocks",
            "Gold, Oil & Commodities": "gold price XAUUSD crude oil commodities market",
            "Macro & FX (USD, EUR)": "global macro economy EURUSD central banks markets"
        }
    }
}
_ = t.get(current_lang, t["CZ"])
MACRO_PRESETS = _["presets"]

st.title(_["title"])
st.caption(_["desc"])

# --- DATA HELPERS ---
def load_app_data():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"portfolio": [], "watchlist": [], "settings": {}}

def load_archive():
    if os.path.exists(ARCHIVE_FILE):
        try:
            with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []

def save_archive(archive_list, commit_msg="AI Radar: Aktualizace archivu"):
    with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(archive_list, f, indent=4, ensure_ascii=False)
    try:
        if "GITHUB_TOKEN" in st.secrets:
            token = st.secrets["GITHUB_TOKEN"]
            owner = st.secrets["GITHUB_OWNER"]
            repo = st.secrets["GITHUB_REPO"]
            remote_url = f"https://{owner}:{token}@github.com/{owner}/{repo}.git"
            subprocess.run(["git", "config", "--global", "user.email", "bot@pokornyterminal.cz"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "config", "--global", "user.name", "Terminal Bot"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "pull", "--rebase", remote_url, "main"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "add", ARCHIVE_FILE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "commit", "-m", commit_msg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "push", remote_url, "HEAD:main"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

app_data = load_app_data()
saved_settings = app_data.get("settings", {})
portfolio_tickers = app_data.get("portfolio", [])
watchlist_tickers = app_data.get("watchlist", [])
tickers = sorted(list(set(portfolio_tickers + watchlist_tickers)))

api_key = str(st.secrets.get("GROQ_API_KEY", "")).strip()
model_provider = st.session_state.get("ai_provider", saved_settings.get("ai_provider", "Groq"))
selected_model = st.session_state.get("ai_model", saved_settings.get("ai_model", ""))

if not api_key or not selected_model:
    st.warning(_["err_api"])
    st.stop()

# --- SESSION STATE ---
for key, default in [
    ("live_selected_item", None),
    ("live_analyzed_cache", {}),
    ("live_chat_history", {}),
    ("lab_current_report", None),
    ("lab_chat", []),
    ("lab_saved_id", None),
    ("lib_selected_id", None),
    ("lib_chat", [])
]:
    if key not in st.session_state:
        st.session_state[key] = default

# --- GROQ / OPENAI DYNAMIC API ---
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

def call_llm_api(messages, api_klic, provider, model_name, temperature=0.15, timeout=30, max_tokens=1400):
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
            last_err = f"HTTP {e.code}: {err_body}"
            if e.code in (400, 404, 413, 429) and mdl != models_to_try[-1]:
                continue
            raise RuntimeError(last_err)
    raise RuntimeError(last_err)

# --- MULTI-SOURCE REAL-TIME NEWS ENGINE ---
WIRE_FEEDS = [
    ("CNBC Top News", "https://www.cnbc.com/id/100003114/device/rss/rss.html", "Trh"),
    ("CNBC Finance", "https://www.cnbc.com/id/10000664/device/rss/rss.html", "Firmy"),
    ("CNBC Economy", "https://www.cnbc.com/id/20910258/device/rss/rss.html", "Makro"),
    ("CNBC Earnings", "https://www.cnbc.com/id/15839135/device/rss/rss.html", "Firmy"),
    ("MarketWatch", "https://feeds.marketwatch.com/marketwatch/topstories/", "Trh"),
    ("MarketWatch Bulletins", "https://feeds.marketwatch.com/marketwatch/realtimeheadlines/", "Trh"),
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex", "Trh")
]

CZ_DAYS = {0: "po", 1: "út", 2: "st", 3: "čt", 4: "pá", 5: "so", 6: "ne"}

def format_cz_timestamp(dt_utc):
    dt_prg = dt_utc.astimezone(ZoneInfo("Europe/Prague"))
    day_abbr = CZ_DAYS.get(dt_prg.weekday(), "")
    return f"{day_abbr} {dt_prg.day}. {dt_prg.month}. {dt_prg.year} {dt_prg.strftime('%H:%M')} SEČ"

def clean_html_text(raw_html):
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "lxml")
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()

def classify_topic_hint(title_lower, default_tag):
    if any(k in title_lower for k in ("tariff", "trade war", "sanction", "china", "export control", "ustr", "customs", "geopolit", "iran", "russia", "ukraine", "israel")):
        return "Obchodní války & Geopolitika"
    if any(k in title_lower for k in ("fed ", "federal reserve", "powell", "fomc", "cpi", "inflation", "pce", "payroll", "unemployment", "gdp", "treasury", "yield", "interest rate", "ecb")):
        return "Makro & Centrální banky"
    if any(k in title_lower for k in ("oil", "crude", "wti", "brent", "gold", "xau", "copper", "natural gas", "opec", "commodity")):
        return "Komodity"
    if any(k in title_lower for k in ("earnings", "revenue", "eps", "guidance", "quarter", "q1", "q2", "q3", "q4", "shares", "stock", "ceo", "merger", "buyback", "ai ", "nvidia", "apple", "dell", "amazon", "google", "microsoft", "meta", "tesla")):
        return "Firmy"
    return default_tag

def parse_single_rss(source_name, url, default_tag, matched_ticker=None):
    items_out = []
    try:
        resp = requests.get(url, headers=get_headers(is_html=False), timeout=7)
        if resp.status_code != 200:
            return []
        root = ET.fromstring(resp.content)
        for item in root.findall(".//item")[:14]:
            title = (item.find("title").text or "").strip() if item.find("title") is not None else ""
            if not title:
                continue
            link = (item.find("link").text or "#").strip() if item.find("link") is not None else "#"
            desc_raw = (item.find("description").text or "") if item.find("description") is not None else ""
            summary = clean_html_text(desc_raw)
            pub_raw = (item.find("pubDate").text or "").strip() if item.find("pubDate") is not None else ""
            try:
                dt_parsed = pd.to_datetime(pub_raw, utc=True).to_pydatetime()
            except Exception:
                dt_parsed = datetime.now(ZoneInfo("UTC"))

            ts_unix = dt_parsed.timestamp()
            uid = hashlib.md5(f"{title[:70]}_{int(ts_unix // 3600)}".encode("utf-8")).hexdigest()[:12]
            topic_tag = classify_topic_hint(title.lower(), default_tag)

            items_out.append({
                "id": uid,
                "title": title,
                "summary": summary,
                "link": link,
                "source": source_name,
                "topic_tag": topic_tag,
                "ticker": matched_ticker,
                "pub_utc_iso": dt_parsed.isoformat(),
                "pub_cz": format_cz_timestamp(dt_parsed),
                "_ts": ts_unix
            })
    except Exception:
        pass
    return items_out

@st.cache_data(ttl=300, show_spinner=False)
def fetch_live_wire_feed(user_tickers_tuple):
    tasks = []
    for src_name, url, tag in WIRE_FEEDS:
        tasks.append((src_name, url, tag, None))

    for tkr in list(user_tickers_tuple)[:12]:
        q_enc = requests.utils.quote(f"{tkr} stock earnings OR guidance OR news when:2d")
        gn_url = f"https://news.google.com/rss/search?q={q_enc}&hl=en-US&gl=US&ceid=US:en"
        tasks.append((f"Watchlist ({tkr})", gn_url, "Firmy", tkr))

    raw_all = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(parse_single_rss, s, u, tg, tk) for (s, u, tg, tk) in tasks]
        for fut in as_completed(futures):
            raw_all.extend(fut.result())

    raw_all.sort(key=lambda x: x["_ts"], reverse=True)

    deduped = []
    for cand in raw_all:
        c_low = cand["title"].lower()
        if any(noise in c_low for noise in ("why ", "3 stocks to", "2 stocks to", "motley fool", "investorplace", "prediction:")):
            continue
        is_dup = False
        for ex_item in deduped:
            sim = SequenceMatcher(None, c_low[:75], ex_item["title"].lower()[:75]).ratio()
            if sim > 0.72:
                is_dup = True
                if "news.google.com" in ex_item["link"] and "news.google.com" not in cand["link"]:
                    ex_item["link"] = cand["link"]
                    ex_item["source"] = cand["source"]
                    if len(cand["summary"]) > len(ex_item["summary"]):
                        ex_item["summary"] = cand["summary"]
                if cand["ticker"] and not ex_item["ticker"]:
                    ex_item["ticker"] = cand["ticker"]
                break
        if not is_dup:
            deduped.append(cand)

    return deduped[:65]

@st.cache_data(ttl=1800, show_spinner=False)
def scrape_article_body(url, fallback_summary):
    if not url or url == "#" or "news.google.com" in url:
        return fallback_summary
    try:
        resp = requests.get(url, headers=get_headers(is_html=True), timeout=7)
        if resp.status_code != 200:
            return fallback_summary
        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        clean_paras = [p for p in paragraphs if len(p) > 45 and "cookie" not in p.lower() and "subscribe" not in p.lower()]
        full_txt = " ".join(clean_paras)
        if len(full_txt) > 220:
            return full_txt[:3800]
    except Exception:
        pass
    return fallback_summary

# --- 1-MINUTE MARKET REACTION ENGINE (T0 vs T0 + 30 MIN) ---
@st.cache_data(ttl=300, show_spinner=False)
def get_30min_market_reaction(pub_utc_iso, primary_ticker=None, lang="CZ"):
    pending_msg = t.get(lang, t["CZ"])["react_pending"]
    try:
        pub_utc = datetime.fromisoformat(pub_utc_iso)
        now_utc = datetime.now(ZoneInfo("UTC"))
        elapsed_min = (now_utc - pub_utc).total_seconds() / 60.0

        if elapsed_min < 30:
            return pending_msg

        ny_tz = ZoneInfo("America/New_York")
        t0_ny = pub_utc.astimezone(ny_tz)
        t30_ny = t0_ny + timedelta(minutes=30)

        def calc_ticker_move(sym):
            df_1m = yf.download(sym, period="5d", interval="1m", prepost=True, progress=False)
            if df_1m is None or df_1m.empty:
                return None
            if isinstance(df_1m.columns, pd.MultiIndex):
                df_1m.columns = df_1m.columns.get_level_values(0)
            idx = df_1m.index
            if idx.tz is None:
                idx = idx.tz_localize("UTC").tz_convert(ny_tz)
            else:
                idx = idx.tz_convert(ny_tz)
            df_1m.index = idx

            after_t0 = df_1m[df_1m.index >= t0_ny]
            after_t30 = df_1m[df_1m.index >= t30_ny]
            if after_t0.empty or after_t30.empty:
                return None
            if (after_t0.index[0] - t0_ny).total_seconds() > 900:
                return None
            p0 = float(after_t0["Open"].iloc[0])
            p30 = float(after_t30["Close"].iloc[0])
            if p0 <= 0:
                return None
            return ((p30 / p0) - 1.0) * 100.0

        spy_chg = calc_ticker_move("SPY")
        tkr_chg = calc_ticker_move(primary_ticker) if (primary_ticker and primary_ticker != "SPY") else None

        parts = []
        if spy_chg is not None:
            parts.append(f"S&P 500 (SPY): {spy_chg:+.2f} % za 30 min")
        if tkr_chg is not None:
            parts.append(f"{primary_ticker}: {tkr_chg:+.2f} % za 30 min")

        if parts:
            return " | ".join(parts) + "."
        return "Zpráva vyšla mimo aktivní obchodní hodiny US burzy (víkend / noční pauza)." if lang == "CZ" else "Published outside active US market hours."
    except Exception:
        return pending_msg

# --- AI NEWS CARD ANALYZER ---
def analyze_single_news(item, full_text, api_klic, provider, model_name, lang):
    lang_instr = "Piš 100% čistou, spisovnou češtinou bez anglických frází." if lang == "CZ" else "Write in clean, institutional English."
    prompt = f"""Jsi hlavní kvantitativní a makroekonomický analytik.
Analyzuj níže uvedenou zprávu a vyhodnoť její reálný dopad na index S&P 500 (Risk-On vs. Risk-Off).
{lang_instr}

PRAVIDLA PRO SKÓRE (`sentiment_score`):
- Rozsah je od -1.0000 do +1.0000 (uveď přesně na 4 desetinná místa).
- Jednotlivá firma (výsledky, zakázky, výhled): obvykle -0.1000 až +0.1000 (např. +0.0450).
- Sektorová / velká megacap zpráva: -0.2500 až +0.2500.
- Makro / Fed / Inflace / Cla / Obchodní války / Geopolitika: -0.8000 až +0.8000 (např. nové plošné tarify = -0.4400).

PŘÍSNÁ PRAVIDLA PRO TEXT:
- V `preklad_shrnuti` přelož a věcně shrň celý článek s přesnými čísly (tržby, EPS, backlog, marže, sazby, cla).
- V `co_se_stalo` shrň fakta ve 3–4 hutných větách.
- V `proc_to_hybe_trhem` vysvětli konkrétní dopad na S&P 500, ziskové marže, AI cyklus nebo úrokové sazby.
- Vrať VÝHRADNĚ platný JSON bez jakéhokoli dalšího textu.

Originální titulek: {item['title']}
Zdroj: {item['source']}
Text článku:
{full_text or item['summary']}

Struktura JSON:
{{
    "titulek_cz": "Přesný český překlad titulku",
    "preklad_shrnuti": "Podrobný český překlad a shrnutí zprávy se všemi tvrdými čísly",
    "kategorie": "Firmy" nebo "Obchodní války" nebo "Makro" nebo "Centrální banky" nebo "Komodity" nebo "Geopolitika",
    "sentiment_score": 0.0450,
    "hlavni_ticker": "DELL" nebo "",
    "co_se_stalo": "3–4 věcné věty co přesně se stalo",
    "proc_to_hybe_trhem": "2–3 věty proč a jakým mechanismem to hýbe indexem S&P 500"
}}"""
    try:
        raw_out = call_llm_api([{"role": "user", "content": prompt}], api_klic, provider, model_name, temperature=0.1, timeout=30, max_tokens=1200).strip()
        if raw_out.startswith("```"):
            raw_out = raw_out.strip("`").replace("json\n", "", 1).strip()
        return json.loads(raw_out)
    except Exception as e:
        return {"error": str(e)}

def render_news_card(card_obj):
    score = float(card_obj.get("sentiment_score", 0.0))
    if score > 0.005:
        sc_bg, sc_fg = "rgba(34,197,94,0.16)", "#22C55E"
    elif score < -0.005:
        sc_bg, sc_fg = "rgba(239,68,68,0.16)", "#EF4444"
    else:
        sc_bg, sc_fg = "rgba(161,161,170,0.16)", "#A1A1AA"

    cat_lbl = card_obj.get("kategorie", "Trh")
    tkr_lbl = card_obj.get("hlavni_ticker", "")
    cat_full = f"{cat_lbl} · {tkr_lbl}" if tkr_lbl else cat_lbl

    html = (
        f'<div class="news-card">'
        f'<div class="news-time">{card_obj.get("pub_cz", "")}  ·  {card_obj.get("source", "")}</div>'
        f'<div class="news-title">{card_obj.get("titulek_cz", card_obj.get("title", ""))}</div>'
        f'<div class="news-sub">Strojový překlad & AI extrakce  ·  <a href="{card_obj.get("link", "#")}" target="_blank" style="color:#60A5FA; text-decoration:none;">Otevřít zdrojový článek ↗</a></div>'
        f'<p class="news-body">{card_obj.get("preklad_shrnuti", "")}</p>'
        f'<div class="news-pill-row">'
        f'<span class="news-cat-pill">{cat_full}</span>'
        f'<span class="news-score-pill" style="background:{sc_bg}; color:{sc_fg};">{score:+.4f}</span>'
        f'</div>'
        f'<div class="news-caption">{_["score_desc"]}</div>'
        f'<div class="news-ai-box">'
        f'<div class="news-ai-hdr">✦ {_["ai_expl_hdr"]} <span class="news-ai-tag">AI</span></div>'
        f'<div class="news-sec-lbl">{_["what_happened"]}</div>'
        f'<p class="news-sec-txt">{card_obj.get("co_se_stalo", "")}</p>'
        f'<div class="news-sec-lbl">{_["why_sp500"]}</div>'
        f'<p class="news-sec-txt">{card_obj.get("proc_to_hybe_trhem", "")}</p>'
        f'<div class="news-sec-lbl">{_["how_reacted"]}</div>'
        f'<p class="news-sec-txt" style="color:#A1A1AA;">{card_obj.get("reakce_trhu", _["react_pending"])}</p>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)

    with st.expander(_["orig_exp"], expanded=False):
        st.markdown(f"**{card_obj.get('title', '')}**")
        st.write(card_obj.get("full_text") or card_obj.get("summary") or "")

# --- MARKET BRIEF GENERATOR ---
@st.cache_data(ttl=900, show_spinner=False)
def fetch_brief_news(query_str, is_ticker=True):
    news_list = []
    base_q = f"{query_str} stock news" if is_ticker else query_str
    for window in (["when:3d", "when:7d"] if not is_ticker else ["when:7d", "when:14d"]):
        try:
            q_encoded = requests.utils.quote(f"{base_q} {window}")
            url = f"[https://news.google.com/rss/search?q=](https://news.google.com/rss/search?q=){q_encoded}&hl=en-US&gl=US&ceid=US:en"
            response = requests.get(url, headers=get_headers(), timeout=8)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                temp = []
                for item in root.findall('.//item')[:15]:
                    title = item.find('title').text if item.find('title') is not None else _["no_title"]
                    link = item.find('link').text if item.find('link') is not None else "#"
                    pub_raw = item.find('pubDate').text if item.find('pubDate') is not None else ""
                    try:
                        dt_parsed = pd.to_datetime(pub_raw, utc=True)
                        pub_str = dt_parsed.tz_convert("Europe/Prague").strftime("%d. %m. %Y %H:%M")
                        ts = dt_parsed.timestamp()
                    except Exception:
                        pub_str = pub_raw[:22] if len(pub_raw) > 22 else (pub_raw or _["no_time"])
                        ts = 0.0
                    temp.append({"title": title, "link": link, "publisher": "Google News", "pub_time_str": pub_str, "_ts": ts})
                temp.sort(key=lambda x: x["_ts"], reverse=True)
                for row in temp[:10]:
                    row.pop("_ts", None)
                    news_list.append(row)
                if news_list:
                    return news_list
        except Exception:
            pass
    return news_list

def generuj_ai_report(tema, typ, zpravy_text, api_klic, provider, model_name, lang):
    lang_rules = (
        "Piš 100% čistou, přirozenou a gramaticky správnou češtinou bez anglicismů."
        if lang == "CZ" else "Write 100% pure, natural institutional English focused on recent market developments."
    )
    kontext_role = "souhrnný makro a tržní přehled" if typ == "MARKET BRIEF" else f"analýzu akcie {tema}"
    prompt = f"""Jsi analytik akciového trhu a makra připravující přehled pro {kontext_role} ({tema}).
{lang_rules}
Syntetizuj níže uvedené nejnovější zprávy do jasného, věcného reportu. Vrať VÝHRADNĚ platný JSON.
Zprávy:
{zpravy_text}

Struktura JSON:
{{
    "hlavni_nadpis": "Výstižný, věcný titulek shrnující hlavní dění.",
    "rezim": "RISK-ON" nebo "RISK-OFF" nebo "NEUTRAL",
    "sentiment_skore": <desetinné číslo od -1.0 do 1.0>,
    "co_se_stalo": "Shrnutí hlavních událostí v 4–6 věcných větách s konkrétními čísly.",
    "proc_to_hybe_trhem": "Dopad na trhy, sazby, marže, valuace a likviditu.",
    "na_co_se_zamerit": "2–3 konkrétní faktory nebo úrovně ke sledování jako prostý text."
}}"""
    try:
        vysledek = call_llm_api([{"role": "user", "content": prompt}], api_klic, provider, model_name, temperature=0.1, timeout=30, max_tokens=1400).strip()
        if vysledek.startswith("```"):
            vysledek = vysledek.strip("`").replace("json\n", "", 1).strip()
        return json.loads(vysledek)
    except Exception as e:
        return {"error": str(e)}

def chat_s_ai(otazka, context_str, historie, api_klic, provider, model_name, lang):
    jazyk_vyzva = "Odpovídej čistou, přirozenou češtinou bez anglicismů." if lang == "CZ" else "Answer in clean, institutional English."
    messages = [{"role": "system", "content": f"Jsi seniorní tržní analytik. Odpovídej věcně a s konkrétními čísly. Kontext zprávy/reportu: {context_str}. {jazyk_vyzva}"}]
    for msg in historie[-6:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": otazka})
    try:
        return call_llm_api(messages, api_klic, provider, model_name, temperature=0.25, timeout=25, max_tokens=900)
    except Exception as e:
        return f"⚠️ AI Error ({e})."

def vykresli_report_kartu(rep):
    if rep.get("typ") in ("ZPRÁVA (AI)", "AI NEWS CARD", "MOODIX KARTA"):
        render_news_card(rep)
        return

    skore = float(rep.get("sentiment_skore", 0.0))
    rezim = rep.get("rezim", "NEUTRAL").upper()
    if rezim == "RISK-ON" or skore > 0.15:
        badge_bg, badge_fg = "rgba(34,197,94,0.14)", "#22C55E"
    elif rezim == "RISK-OFF" or skore < -0.15:
        badge_bg, badge_fg = "rgba(239,68,68,0.14)", "#EF4444"
    else:
        badge_bg, badge_fg = "rgba(161,161,170,0.14)", "#A1A1AA"

    watch_val = rep.get("na_co_se_zamerit", "")
    if isinstance(watch_val, list):
        watch_val = " ".join([str(x) for x in watch_val])
    watch_html = f'<div class="brief-sec-label">{_["watch_next"]}</div><p class="brief-body">{watch_val}</p>' if watch_val else ""

    html_card = (
        f'<div class="brief-article">'
        f'<div class="brief-meta">{rep.get("datum", "")}  ·  {rep.get("typ", "")}  ·  {rep.get("tema", "")}</div>'
        f'<h1 class="brief-headline">{rep.get("hlavni_nadpis", "")}</h1>'
        f'<span class="brief-badge" style="background-color:{badge_bg}; color:{badge_fg};">{rezim}   {skore:+.2f}</span>'
        f'<hr class="brief-divider" />'
        f'<div class="brief-sec-label">{_["what_happened"]}</div>'
        f'<p class="brief-body">{rep.get("co_se_stalo", "")}</p>'
        f'<div class="brief-sec-label">{_["why_move"]}</div>'
        f'<p class="brief-body">{rep.get("proc_to_hybe_trhem", "")}</p>'
        f'{watch_html}'
        f'</div>'
    )
    st.markdown(html_card, unsafe_allow_html=True)

    if rep.get("zdroje"):
        with st.expander(_["sources"]):
            for article in rep["zdroje"]:
                st.markdown(f"- `{article.get('pub_time_str', '')}` · [{article.get('title', '')}]({article.get('link', '#')})")

# --- MAIN TABS ---
tab_live, tab_gen, tab_lib = st.tabs([_["tab_live"], _["tab_gen"], _["tab_lib"]])

with tab_live:
    if st.session_state.live_selected_item:
        raw_item = st.session_state.live_selected_item
        item_id = raw_item["id"]

        if st.button(_["back_feed"]):
            st.session_state.live_selected_item = None
            st.rerun()

        if item_id not in st.session_state.live_analyzed_cache:
            with st.spinner(_["spin_ai"]):
                full_body = scrape_article_body(raw_item["link"], raw_item["summary"])
                ai_res = analyze_single_news(raw_item, full_body, api_key, model_provider, selected_model, current_lang)
                if "error" not in ai_res:
                    det_tkr = (ai_res.get("hlavni_ticker") or raw_item.get("ticker") or "").strip().upper()
                    react_txt = get_30min_market_reaction(raw_item["pub_utc_iso"], det_tkr, current_lang)
                    now_dt = datetime.now(ZoneInfo("Europe/Prague"))
                    card_data = {
                        "id": f"{now_dt.strftime('%Y%m%d_%H%M%S')}_NEWS_{item_id}",
                        "raw_id": item_id,
                        "datum": raw_item["pub_cz"],
                        "pub_cz": raw_item["pub_cz"],
                        "pub_utc_iso": raw_item["pub_utc_iso"],
                        "typ": "ZPRÁVA (AI)",
                        "tema": det_tkr if det_tkr else ai_res.get("kategorie", "Trh"),
                        "source": raw_item["source"],
                        "link": raw_item["link"],
                        "title": raw_item["title"],
                        "summary": raw_item["summary"],
                        "full_text": full_body,
                        "hlavni_nadpis": ai_res.get("titulek_cz", raw_item["title"]),
                        "titulek_cz": ai_res.get("titulek_cz", raw_item["title"]),
                        "preklad_shrnuti": ai_res.get("preklad_shrnuti", raw_item["summary"]),
                        "kategorie": ai_res.get("kategorie", raw_item["topic_tag"]),
                        "hlavni_ticker": det_tkr,
                        "sentiment_score": float(ai_res.get("sentiment_score", 0.0)),
                        "sentiment_skore": float(ai_res.get("sentiment_score", 0.0)),
                        "rezim": "RISK-ON" if float(ai_res.get("sentiment_score", 0.0)) > 0.005 else ("RISK-OFF" if float(ai_res.get("sentiment_score", 0.0)) < -0.005 else "NEUTRAL"),
                        "co_se_stalo": ai_res.get("co_se_stalo", ""),
                        "proc_to_hybe_trhem": ai_res.get("proc_to_hybe_trhem", ""),
                        "reakce_trhu": react_txt
                    }
                    st.session_state.live_analyzed_cache[item_id] = card_data
                else:
                    st.error(f"{_['err_ai']} {ai_res['error']}")

        if item_id in st.session_state.live_analyzed_cache:
            card_obj = st.session_state.live_analyzed_cache[item_id]
            if card_obj.get("reakce_trhu") == _["react_pending"]:
                card_obj["reakce_trhu"] = get_30min_market_reaction(card_obj["pub_utc_iso"], card_obj.get("hlavni_ticker"), current_lang)
                st.session_state.live_analyzed_cache[item_id] = card_obj

            render_news_card(card_obj)

            if st.button(_["save_card"], key=f"save_news_{item_id}"):
                arch = load_archive()
                if not any(x.get("raw_id") == item_id for x in arch):
                    arch.insert(0, card_obj)
                    save_archive(arch, commit_msg=f"AI Radar: Uložena zpráva ({card_obj['tema']})")
                st.success(_["saved_ok"])

            st.markdown("---")
            st.markdown(f"**{_['ask_news_h']}**")
            st.caption(_["ask_news_sub"])

            chat_list = st.session_state.live_chat_history.setdefault(item_id, [])
            for m in chat_list:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])

            if q_news := st.chat_input(_["ask_news_ph"], key=f"chat_news_{item_id}"):
                chat_list.append({"role": "user", "content": q_news})
                with st.chat_message("user"):
                    st.markdown(q_news)
                with st.chat_message("assistant"):
                    with st.spinner(_["spin_chat"]):
                        ctx = json.dumps({
                            "titulek": card_obj["titulek_cz"],
                            "clanek": card_obj["full_text"][:2500],
                            "skore_sp500": card_obj["sentiment_score"],
                            "co_se_stalo": card_obj["co_se_stalo"],
                            "proc_to_hybe": card_obj["proc_to_hybe_trhem"],
                            "reakce_trhu": card_obj["reakce_trhu"],
                            "moje_portfolio": portfolio_tickers
                        }, ensure_ascii=False)
                        ans = chat_s_ai(q_news, ctx, chat_list[:-1], api_key, model_provider, selected_model, current_lang)
                        st.markdown(ans)
                if not ans.startswith("⚠️"):
                    chat_list.append({"role": "assistant", "content": ans})
                    st.rerun()
    else:
        c_top1, c_top2, c_top3 = st.columns([1.4, 2.2, 0.9])
        filter_opts = ["Vše", "Moje Portfolio & Watchlist", "Firmy", "Obchodní války & Geopolitika", "Makro & Centrální banky", "Komodity"]
        sel_filter = c_top1.selectbox(_["filter_lbl"], filter_opts, label_visibility="collapsed")
        q_filter = c_top2.text_input(_["search_lbl"], placeholder=_["search_ph"], label_visibility="collapsed").strip().lower()
        if c_top3.button(_["refresh_btn"], use_container_width=True):
            fetch_live_wire_feed.clear()
            st.rerun()

        with st.spinner(_["spin_search"]):
            wire_items = fetch_live_wire_feed(tuple(tickers))

        if st.session_state.live_analyzed_cache:
            tot_sc = sum(float(c.get("sentiment_score", 0.0)) for c in st.session_state.live_analyzed_cache.values())
            cnt_sc = len(st.session_state.live_analyzed_cache)
            reg_lbl = "RISK-ON" if tot_sc > 0.02 else ("RISK-OFF" if tot_sc < -0.02 else "NEUTRAL")
            st.info(f"Analyzováno v této relaci: **{cnt_sc}** zpráv | Kumulativní S&P 500 Sentiment: **{reg_lbl} ({tot_sc:+.4f})**")

        filtered_wire = []
        for it in wire_items:
            if sel_filter == "Moje Portfolio & Watchlist" and not it.get("ticker"):
                continue
            elif sel_filter not in ("Vše", "Moje Portfolio & Watchlist") and it.get("topic_tag") != sel_filter:
                continue
            if q_filter:
                hay = f"{it['title']} {it['summary']} {it.get('ticker') or ''} {it['source']}".lower()
                if q_filter not in hay:
                    continue
            filtered_wire.append(it)

        if not filtered_wire:
            st.info(_["err_news"])
        else:
            for it in filtered_wire:
                cached_c = st.session_state.live_analyzed_cache.get(it["id"])
                disp_title = cached_c["titulek_cz"] if cached_c else it["title"]
                tkr_badge = f" · `{it['ticker']}`" if it.get("ticker") else ""
                if cached_c:
                    sc = float(cached_c["sentiment_score"])
                    sc_col = "#22C55E" if sc > 0.005 else ("#EF4444" if sc < -0.005 else "#A1A1AA")
                    sc_html = f' · <span style="color:{sc_col}; font-weight:600;">{cached_c["kategorie"]} {sc:+.4f}</span>'
                else:
                    sc_html = f' · <span style="color:#A1A1AA;">{it["topic_tag"]}</span>'

                r1, r2 = st.columns([5.5, 1.2])
                with r1:
                    st.markdown(
                        f'<div class="news-feed-row">'
                        f'<div class="news-time" style="margin-bottom:2px;">{it["pub_cz"]}  ·  {it["source"]}{tkr_badge}{sc_html}</div>'
                        f'<div class="news-feed-title">{disp_title}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                with r2:
                    st.markdown('<div style="padding-top:14px;"></div>', unsafe_allow_html=True)
                    btn_txt = "Otevřít kartu →" if cached_c else _["open_card"]
                    if st.button(btn_txt, key=f"open_wire_{it['id']}", use_container_width=True):
                        st.session_state.live_selected_item = it
                        st.rerun()

with tab_gen:
    mode = st.radio(_["mode_lbl"], [_["mode_macro"], _["mode_stock"]], horizontal=True)
    is_macro = (mode == _["mode_macro"])

    target_label = None
    search_query = None

    if is_macro:
        c1, c2 = st.columns([1.2, 1.8])
        preset_name = c1.selectbox(_["macro_preset"], list(MACRO_PRESETS.keys()))
        custom_topic = c2.text_input(_["macro_custom"], placeholder=_["macro_ph"])
        if custom_topic.strip():
            target_label = custom_topic.strip()
            search_query = custom_topic.strip()
        else:
            target_label = preset_name
            search_query = MACRO_PRESETS[preset_name]
    else:
        c1, c2 = st.columns([1.2, 1.2])
        custom_val = c1.text_input(_["tick_cust"], placeholder=_["tick_ph"])
        dropdown_val = c2.selectbox(_["tick_db"], tickers, index=None, placeholder=_["db_ph"])
        vybrany_ticker = custom_val.strip().upper() if custom_val.strip() else dropdown_val
        target_label = vybrany_ticker
        search_query = vybrany_ticker

    if target_label:
        if st.button(_["btn_ai"], use_container_width=True, type="primary"):
            with st.spinner(_["spin_search"]):
                news_data = fetch_brief_news(search_query, is_ticker=(not is_macro))
            if not news_data:
                st.warning(_["err_news"])
            else:
                agregovany_text = "\n".join([f"- {n['pub_time_str']}: {n['title']}" for n in news_data])
                typ_str = "MARKET BRIEF" if is_macro else "AKCIE"
                with st.spinner(_["spin_ai"]):
                    analyza = generuj_ai_report(target_label, typ_str, agregovany_text, api_key, model_provider, selected_model, current_lang)
                    if "error" not in analyza:
                        now_dt = datetime.now(ZoneInfo("Europe/Prague"))
                        rep_id = f"{now_dt.strftime('%Y%m%d_%H%M%S')}_{'MACRO' if is_macro else target_label}"
                        st.session_state.lab_current_report = {
                            "id": rep_id,
                            "datum": now_dt.strftime("%d. %m. %Y %H:%M"),
                            "typ": typ_str,
                            "tema": target_label,
                            "hlavni_nadpis": analyza.get("hlavni_nadpis", ""),
                            "rezim": analyza.get("rezim", "NEUTRAL"),
                            "sentiment_skore": float(analyza.get("sentiment_skore", 0.0)),
                            "co_se_stalo": analyza.get("co_se_stalo", ""),
                            "proc_to_hybe_trhem": analyza.get("proc_to_hybe_trhem", ""),
                            "na_co_se_zamerit": analyza.get("na_co_se_zamerit", ""),
                            "zdroje": news_data
                        }
                        st.session_state.lab_chat = []
                        st.session_state.lab_saved_id = None
                    else:
                        st.error(f"{_['err_ai']} {analyza['error']}")

    if st.session_state.lab_current_report:
        rep = st.session_state.lab_current_report
        vykresli_report_kartu(rep)

        if st.session_state.lab_saved_id == rep["id"]:
            st.info(_["already_saved"])
        else:
            if st.button(_["btn_save"]):
                archive = load_archive()
                archive.insert(0, rep)
                save_archive(archive, commit_msg=f"AI Radar: Uložen report {rep['tema']}")
                st.session_state.lab_saved_id = rep["id"]
                st.success(_["saved_ok"])

        st.markdown(f'<div class="brief-sec-label">{_["chat_h"]}</div>', unsafe_allow_html=True)
        for msg in st.session_state.lab_chat:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input(_["chat_ph"], key="gen_chat_input"):
            st.session_state.lab_chat.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner(_["spin_chat"]):
                    odpoved = chat_s_ai(prompt, json.dumps(rep, ensure_ascii=False, default=str), st.session_state.lab_chat[:-1], api_key, model_provider, selected_model, current_lang)
                    st.markdown(odpoved)
            if not odpoved.startswith("⚠️"):
                st.session_state.lab_chat.append({"role": "assistant", "content": odpoved})

with tab_lib:
    archive = load_archive()

    if not archive:
        st.info(_["lib_empty"])
    else:
        selected_rep = next((r for r in archive if r.get("id") == st.session_state.lib_selected_id), None)

        if selected_rep:
            col_back, col_del = st.columns([5, 1])
            if col_back.button(_["lib_back"]):
                st.session_state.lib_selected_id = None
                st.session_state.lib_chat = []
                st.rerun()
            if col_del.button(_["lib_del"], use_container_width=True):
                new_archive = [r for r in archive if r.get("id") != selected_rep["id"]]
                save_archive(new_archive, commit_msg=f"AI Radar: Smazán report {selected_rep.get('tema')}")
                st.session_state.lib_selected_id = None
                st.session_state.lib_chat = []
                st.success(_["lib_deleted"])
                st.rerun()

            vykresli_report_kartu(selected_rep)

            st.markdown(f'<div class="brief-sec-label">{_["chat_h"]}</div>', unsafe_allow_html=True)
            for msg in st.session_state.lib_chat:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            if prompt_lib := st.chat_input(_["chat_ph"], key="lib_chat_input"):
                st.session_state.lib_chat.append({"role": "user", "content": prompt_lib})
                with st.chat_message("user"):
                    st.markdown(prompt_lib)
                with st.chat_message("assistant"):
                    with st.spinner(_["spin_chat"]):
                        odpoved = chat_s_ai(prompt_lib, json.dumps(selected_rep, ensure_ascii=False, default=str), st.session_state.lib_chat[:-1], api_key, model_provider, selected_model, current_lang)
                        st.markdown(odpoved)
                if not odpoved.startswith("⚠️"):
                    st.session_state.lib_chat.append({"role": "assistant", "content": odpoved})
        else:
            f1, f2 = st.columns([1.2, 2.8])
            filtr_opts = [_["lib_all"], _["lib_card_lbl"], _["lib_macro_lbl"], _["lib_stock_lbl"]]
            typ_filtr = f1.selectbox(_["lib_filter"], filtr_opts)
            hledat = f2.text_input(_["lib_search"], placeholder=_["lib_search_ph"]).strip().lower()

            filtered = []
            for r in archive:
                r_typ = r.get("typ", "")
                if typ_filtr == _["lib_card_lbl"] and r_typ not in ("ZPRÁVA (AI)", "AI NEWS CARD", "MOODIX KARTA"):
                    continue
                if typ_filtr == _["lib_macro_lbl"] and r_typ != "MARKET BRIEF":
                    continue
                if typ_filtr == _["lib_stock_lbl"] and r_typ not in ("AKCIE", "EQUITY"):
                    continue
                if hledat:
                    haystack = f"{r.get('tema', '')} {r.get('hlavni_nadpis', '')} {r.get('co_se_stalo', '')}".lower()
                    if hledat not in haystack:
                        continue
                filtered.append(r)

            st.markdown(f'<div class="brief-sec-label">{_["lib_saved_h"]} · {len(filtered)}</div>', unsafe_allow_html=True)
            for item in filtered:
                skore = float(item.get("sentiment_skore", 0.0))
                rezim = item.get("rezim", "NEUTRAL").upper()
                badge_color = "#22C55E" if (rezim == "RISK-ON" or skore > 0.005) else "#EF4444" if (rezim == "RISK-OFF" or skore < -0.005) else "#A1A1AA"

                c_info, c_btn = st.columns([6, 1])
                with c_info:
                    row_html = (
                        f'<div class="brief-lib-row">'
                        f'<div class="brief-meta" style="margin-bottom:4px;">'
                        f'{item.get("datum", "")}  ·  {item.get("typ", "")}  ·  {item.get("tema", "")}  ·  '
                        f'<span style="color:{badge_color}; font-weight:600;">{rezim} {skore:+.4f}</span>'
                        f'</div>'
                        f'<div class="brief-lib-title">{item.get("hlavni_nadpis", "")}</div>'
                        f'</div>'
                    )
                    st.markdown(row_html, unsafe_allow_html=True)
                with c_btn:
                    st.markdown('<div style="padding-top:18px;"></div>', unsafe_allow_html=True)
                    if st.button(_["lib_open"], key=f"open_{item.get('id')}", use_container_width=True):
                        st.session_state.lib_selected_id = item.get("id")
                        st.session_state.lib_chat = []
                        st.rerun()