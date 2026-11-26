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
        "search_ph": "Vyhledat...",
        "noise_exp": "Filtr šumu (blokovaná slova a skryté zprávy)",
        "noise_inp": "Vlastní blokovaná slova (oddělená čárkou):",
        "noise_ph": "např. 401(k), BMW, Moneyist, Buy the Dip",
        "noise_reset": "Obnovit skryté zprávy",
        "session_stats": "Započítáno v sentimentu: **{cnt}** zpráv | Kumulativní S&P 500 Sentiment: **{reg} ({sc:+.4f})**",
        "sent_mgr_exp": "Spravovat zprávy v celkovém sentimentu",
        "sent_include": "Započítat do celkového S&P 500 sentimentu",
        "sent_remove": "Odebrat",
        "sent_excluded_tag": "(vypnuto ze sentimentu)",
        "open_card": "AI Vysvětlení →",
        "open_cached": "Otevřít kartu →",
        "back_feed": "← Zpět na živý přehled zpráv",
        "btn_tr_other": "Strojový překlad → EN",
        "btn_tr_back": "Zpět do CZ",
        "orig_exp": "Zobrazit originál článku",
        "card_sub": "Strojový překlad & AI extrakce",
        "card_src_link": "Otevřít zdrojový článek ↗",
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
        "lib_search_ph": "Vyhledat...",
        "lib_open": "Číst →",
        "lib_del": "Smazat",
        "lib_deleted": "Odstraněno z Archivu.",
        "lib_back": "← Zpět do Archivu",
        "filter_map": {
            "ALL": "Vše",
            "WATCHLIST": "Moje Portfolio & Watchlist",
            "EQUITIES": "Firmy",
            "TRADE": "Obchodní války & Geopolitika",
            "MACRO": "Makro & Centrální banky",
            "COMMODITIES": "Komodity",
            "MARKET": "Trh"
        },
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
        "search_ph": "Search...",
        "noise_exp": "Noise filter (blocked keywords & hidden news)",
        "noise_inp": "Custom blocked keywords (comma-separated):",
        "noise_ph": "e.g. 401(k), BMW, Moneyist, Buy the Dip",
        "noise_reset": "Restore hidden news",
        "session_stats": "Included in sentiment: **{cnt}** news | Cumulative S&P 500 Sentiment: **{reg} ({sc:+.4f})**",
        "sent_mgr_exp": "Manage news in cumulative sentiment",
        "sent_include": "Include in cumulative S&P 500 sentiment",
        "sent_remove": "Remove",
        "sent_excluded_tag": "(excluded from sentiment)",
        "open_card": "AI Explanation →",
        "open_cached": "Open Card →",
        "back_feed": "← Back to live news feed",
        "btn_tr_other": "Machine Translation → CZ",
        "btn_tr_back": "Back to EN",
        "orig_exp": "Show original article",
        "card_sub": "AI Summary & Extraction",
        "card_src_link": "Open source article ↗",
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
        "lib_search_ph": "Search...",
        "lib_open": "Read →",
        "lib_del": "Delete",
        "lib_deleted": "Removed from Archive.",
        "lib_back": "← Back to Archive",
        "filter_map": {
            "ALL": "All",
            "WATCHLIST": "My Portfolio & Watchlist",
            "EQUITIES": "Equities",
            "TRADE": "Trade Wars & Geopolitics",
            "MACRO": "Macro & Central Banks",
            "COMMODITIES": "Commodities",
            "MARKET": "Market"
        },
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
    ("live_analyzed_cache", {}),       # key: f"{item_id}_{lang}"
    ("live_card_lang_override", {}),   # key: item_id -> "CZ" / "EN"
    ("live_excluded_sentiment", set()),
    ("live_chat_history", {}),
    ("live_hidden_ids", set()),
    ("live_custom_block", ""),
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
    ("CNBC Top News", "https://www.cnbc.com/id/100003114/device/rss/rss.html", "MARKET"),
    ("CNBC Finance", "https://www.cnbc.com/id/10000664/device/rss/rss.html", "EQUITIES"),
    ("CNBC Economy", "https://www.cnbc.com/id/20910258/device/rss/rss.html", "MACRO"),
    ("CNBC Earnings", "https://www.cnbc.com/id/15839135/device/rss/rss.html", "EQUITIES"),
    ("MarketWatch", "https://feeds.marketwatch.com/marketwatch/topstories/", "MARKET"),
    ("MarketWatch Bulletins", "https://feeds.marketwatch.com/marketwatch/realtimeheadlines/", "MARKET"),
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex", "MARKET")
]

DEFAULT_NOISE_PATTERNS = (
    "why ", "3 stocks to", "2 stocks to", "motley fool", "investorplace", "prediction:",
    "401(k)", "i'm in my", "should i ", "am i a ", "my son", "my daughter", "my husband",
    "my wife", "inheritance", "is it time to buy", "24/7 wall st", "buyer beware",
    "i hate that", "the moneyist", "retire at", "retirement savings"
)

CZ_DAYS = {0: "po", 1: "út", 2: "st", 3: "čt", 4: "pá", 5: "so", 6: "ne"}
EN_DAYS = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}

def format_timestamp(dt_utc, lang="CZ"):
    dt_prg = dt_utc.astimezone(ZoneInfo("Europe/Prague"))
    if lang == "EN":
        day_abbr = EN_DAYS.get(dt_prg.weekday(), "")
        return f"{day_abbr} {dt_prg.strftime('%Y-%m-%d %H:%M')} CET"
    day_abbr = CZ_DAYS.get(dt_prg.weekday(), "")
    return f"{day_abbr} {dt_prg.day}. {dt_prg.month}. {dt_prg.year} {dt_prg.strftime('%H:%M')} SEČ"

def clean_html_text(raw_html):
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "lxml")
    return re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()

def classify_topic_key(title_lower, default_key):
    if any(k in title_lower for k in ("tariff", "trade war", "sanction", "china", "export control", "ustr", "customs", "geopolit", "iran", "russia", "ukraine", "israel")):
        return "TRADE"
    if any(k in title_lower for k in ("fed ", "federal reserve", "powell", "fomc", "cpi", "inflation", "pce", "payroll", "unemployment", "gdp", "treasury", "yield", "interest rate", "ecb")):
        return "MACRO"
    if any(k in title_lower for k in ("oil", "crude", "wti", "brent", "gold", "xau", "copper", "natural gas", "opec", "commodity")):
        return "COMMODITIES"
    if any(k in title_lower for k in ("earnings", "revenue", "eps", "guidance", "quarter", "q1", "q2", "q3", "q4", "shares", "stock", "ceo", "merger", "buyback", "ai ", "nvidia", "apple", "dell", "amazon", "google", "microsoft", "meta", "tesla")):
        return "EQUITIES"
    return default_key

def parse_single_rss(source_name, url, default_key, matched_ticker=None):
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
            topic_key = classify_topic_key(title.lower(), default_key)

            items_out.append({
                "id": uid,
                "title": title,
                "summary": summary,
                "link": link,
                "source": source_name,
                "topic_key": topic_key,
                "ticker": matched_ticker,
                "pub_utc_iso": dt_parsed.isoformat(),
                "pub_cz": format_timestamp(dt_parsed, "CZ"),
                "pub_en": format_timestamp(dt_parsed, "EN"),
                "_ts": ts_unix
            })
    except Exception:
        pass
    return items_out

@st.cache_data(ttl=300, show_spinner=False)
def fetch_live_wire_feed(user_tickers_tuple):
    tasks = []
    for src_name, url, tkey in WIRE_FEEDS:
        tasks.append((src_name, url, tkey, None))

    for tkr in list(user_tickers_tuple)[:12]:
        q_enc = requests.utils.quote(f"{tkr} stock earnings OR guidance OR news when:2d")
        gn_url = f"https://news.google.com/rss/search?q={q_enc}&hl=en-US&gl=US&ceid=US:en"
        tasks.append((f"Watchlist ({tkr})", gn_url, "EQUITIES", tkr))

    raw_all = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(parse_single_rss, s, u, tg, tk) for (s, u, tg, tk) in tasks]
        for fut in as_completed(futures):
            raw_all.extend(fut.result())

    raw_all.sort(key=lambda x: x["_ts"], reverse=True)

    deduped = []
    for cand in raw_all:
        c_low = cand["title"].lower()
        if any(noise in c_low for noise in DEFAULT_NOISE_PATTERNS):
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
        suffix = "za 30 min" if lang == "CZ" else "in 30 min"
        if spy_chg is not None:
            parts.append(f"S&P 500 (SPY): {spy_chg:+.2f} % {suffix}")
        if tkr_chg is not None:
            parts.append(f"{primary_ticker}: {tkr_chg:+.2f} % {suffix}")

        if parts:
            return " | ".join(parts) + "."
        return "Zpráva vyšla mimo aktivní obchodní hodiny US burzy (víkend / noční pauza)." if lang == "CZ" else "Published outside active US market hours (weekend / overnight)."
    except Exception:
        return pending_msg

# --- AI NEWS CARD ANALYZER ---
def analyze_single_news(item, full_text, api_klic, provider, model_name, lang):
    if lang == "CZ":
        lang_instr = "Piš 100% čistou, spisovnou češtinou bez anglických frází."
        cat_opts = '"Firmy" nebo "Obchodní války" nebo "Makro" nebo "Centrální banky" nebo "Komodity" nebo "Geopolitika"'
    else:
        lang_instr = "Write 100% pure, concise, institutional English. Do NOT use Czech words."
        cat_opts = '"Equities" or "Trade Wars" or "Macro" or "Central Banks" or "Commodities" or "Geopolitics"'

    prompt = f"""You are a senior quantitative & macro market analyst.
Analyze the news article below and evaluate its real impact on the S&P 500 index (Risk-On vs. Risk-Off).
{lang_instr}

SCORING RULES (`sentiment_score`):
- Range from -1.0000 to +1.0000 (4 decimal places).
- Single company (earnings, orders, guidance): typically -0.1000 to +0.1000 (e.g. +0.0450).
- Sector / megacap news: -0.2500 to +0.2500.
- Macro / Fed / Inflation / Tariffs / Trade Wars / Geopolitics: -0.8000 to +0.8000 (e.g. broad tariffs = -0.4400).

STRICT RULES:
- Return ONLY valid JSON with no extra text.
- `titulek`: Headline in target language.
- `preklad_shrnuti`: Concise summary of the article in target language with all hard numbers.
- `co_se_stalo`: 3-4 factual sentences on what happened in target language.
- `proc_to_hybe_trhem`: 2-3 sentences on why and how it moves the S&P 500 in target language.

Original headline: {item['title']}
Source: {item['source']}
Article text:
{full_text or item['summary']}

JSON structure:
{{
    "titulek": "...",
    "preklad_shrnuti": "...",
    "kategorie": {cat_opts},
    "sentiment_score": 0.0450,
    "hlavni_ticker": "DELL" or "",
    "co_se_stalo": "...",
    "proc_to_hybe_trhem": "..."
}}"""
    try:
        raw_out = call_llm_api([{"role": "user", "content": prompt}], api_klic, provider, model_name, temperature=0.1, timeout=30, max_tokens=1200).strip()
        if raw_out.startswith("```"):
            raw_out = raw_out.strip("`").replace("json\n", "", 1).strip()
        return json.loads(raw_out)
    except Exception as e:
        return {"error": str(e)}

def get_or_create_card(raw_item, target_lang):
    cache_key = f"{raw_item['id']}_{target_lang}"
    if cache_key in st.session_state.live_analyzed_cache:
        card_obj = st.session_state.live_analyzed_cache[cache_key]
        pending_txt = t.get(target_lang, t["CZ"])["react_pending"]
        if card_obj.get("reakce_trhu") == pending_txt:
            card_obj["reakce_trhu"] = get_30min_market_reaction(card_obj["pub_utc_iso"], card_obj.get("hlavni_ticker"), target_lang)
            st.session_state.live_analyzed_cache[cache_key] = card_obj
        return card_obj, None

    full_body = scrape_article_body(raw_item["link"], raw_item["summary"])
    ai_res = analyze_single_news(raw_item, full_body, api_key, model_provider, selected_model, target_lang)
    if "error" in ai_res:
        return None, ai_res["error"]

    det_tkr = (ai_res.get("hlavni_ticker") or raw_item.get("ticker") or "").strip().upper()
    react_txt = get_30min_market_reaction(raw_item["pub_utc_iso"], det_tkr, target_lang)
    now_dt = datetime.now(ZoneInfo("Europe/Prague"))
    t_loc = t.get(target_lang, t["CZ"])
    pub_disp = raw_item.get("pub_en" if target_lang == "EN" else "pub_cz", raw_item.get("pub_cz", ""))
    score_val = float(ai_res.get("sentiment_score", 0.0))

    card_data = {
        "id": f"{now_dt.strftime('%Y%m%d_%H%M%S')}_NEWS_{raw_item['id']}_{target_lang}",
        "raw_id": raw_item["id"],
        "lang": target_lang,
        "datum": pub_disp,
        "pub_disp": pub_disp,
        "pub_utc_iso": raw_item["pub_utc_iso"],
        "typ": t_loc["lib_card_lbl"],
        "tema": det_tkr if det_tkr else ai_res.get("kategorie", t_loc["filter_map"]["MARKET"]),
        "source": raw_item["source"],
        "link": raw_item["link"],
        "title": raw_item["title"],
        "summary": raw_item["summary"],
        "full_text": full_body,
        "hlavni_nadpis": ai_res.get("titulek", raw_item["title"]),
        "titulek_cz": ai_res.get("titulek", raw_item["title"]),
        "preklad_shrnuti": ai_res.get("preklad_shrnuti", raw_item["summary"]),
        "kategorie": ai_res.get("kategorie", t_loc["filter_map"].get(raw_item["topic_key"], t_loc["filter_map"]["MARKET"])),
        "hlavni_ticker": det_tkr,
        "sentiment_score": score_val,
        "sentiment_skore": score_val,
        "rezim": "RISK-ON" if score_val > 0.005 else ("RISK-OFF" if score_val < -0.005 else "NEUTRAL"),
        "co_se_stalo": ai_res.get("co_se_stalo", ""),
        "proc_to_hybe_trhem": ai_res.get("proc_to_hybe_trhem", ""),
        "reakce_trhu": react_txt
    }
    st.session_state.live_analyzed_cache[cache_key] = card_data
    return card_data, None

def render_news_card(card_obj):
    card_lang = card_obj.get("lang", current_lang)
    t_loc = t.get(card_lang, t["CZ"])

    score = float(card_obj.get("sentiment_score", 0.0))
    if score > 0.005:
        sc_bg, sc_fg = "rgba(34,197,94,0.16)", "#22C55E"
    elif score < -0.005:
        sc_bg, sc_fg = "rgba(239,68,68,0.16)", "#EF4444"
    else:
        sc_bg, sc_fg = "rgba(161,161,170,0.16)", "#A1A1AA"

    cat_lbl = card_obj.get("kategorie", t_loc["filter_map"]["MARKET"])
    tkr_lbl = card_obj.get("hlavni_ticker", "")
    cat_full = f"{cat_lbl} · {tkr_lbl}" if tkr_lbl else cat_lbl
    pub_show = card_obj.get("pub_disp", card_obj.get("pub_cz", card_obj.get("datum", "")))

    html = (
        f'<div class="news-card">'
        f'<div class="news-time">{pub_show}  ·  {card_obj.get("source", "")}</div>'
        f'<div class="news-title">{card_obj.get("hlavni_nadpis", card_obj.get("titulek_cz", card_obj.get("title", "")))}</div>'
        f'<div class="news-sub">{t_loc["card_sub"]}  ·  <a href="{card_obj.get("link", "#")}" target="_blank" style="color:#60A5FA; text-decoration:none;">{t_loc["card_src_link"]}</a></div>'
        f'<p class="news-body">{card_obj.get("preklad_shrnuti", "")}</p>'
        f'<div class="news-pill-row">'
        f'<span class="news-cat-pill">{cat_full}</span>'
        f'<span class="news-score-pill" style="background:{sc_bg}; color:{sc_fg};">{score:+.4f}</span>'
        f'</div>'
        f'<div class="news-caption">{t_loc["score_desc"]}</div>'
        f'<div class="news-ai-box">'
        f'<div class="news-ai-hdr">✦ {t_loc["ai_expl_hdr"]} <span class="news-ai-tag">AI</span></div>'
        f'<div class="news-sec-lbl">{t_loc["what_happened"]}</div>'
        f'<p class="news-sec-txt">{card_obj.get("co_se_stalo", "")}</p>'
        f'<div class="news-sec-lbl">{t_loc["why_sp500"]}</div>'
        f'<p class="news-sec-txt">{card_obj.get("proc_to_hybe_trhem", "")}</p>'
        f'<div class="news-sec-lbl">{t_loc["how_reacted"]}</div>'
        f'<p class="news-sec-txt" style="color:#A1A1AA;">{card_obj.get("reakce_trhu", t_loc["react_pending"])}</p>'
        f'</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)

    with st.expander(t_loc["orig_exp"], expanded=False):
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
        other_lang = "EN" if current_lang == "CZ" else "CZ"
        active_card_lang = st.session_state.live_card_lang_override.get(item_id, current_lang)

        cb1, cb2 = st.columns([4, 1.5])
        with cb1:
            if st.button(_["back_feed"]):
                st.session_state.live_selected_item = None
                st.rerun()
        with cb2:
            tr_btn_lbl = _["btn_tr_back"] if active_card_lang != current_lang else _["btn_tr_other"]
            if st.button(tr_btn_lbl, use_container_width=True, key=f"tr_toggle_{item_id}"):
                st.session_state.live_card_lang_override[item_id] = current_lang if active_card_lang != current_lang else other_lang
                st.rerun()

        with st.spinner(_["spin_ai"]):
            card_obj, err_msg = get_or_create_card(raw_item, active_card_lang)

        if err_msg:
            st.error(f"{_['err_ai']} {err_msg}")
        elif card_obj:
            render_news_card(card_obj)

            cs1, cs2 = st.columns([2.5, 2.5])
            with cs1:
                is_included = item_id not in st.session_state.live_excluded_sentiment
                new_inc = st.checkbox(_["sent_include"], value=is_included, key=f"inc_sent_{item_id}")
                if new_inc and item_id in st.session_state.live_excluded_sentiment:
                    st.session_state.live_excluded_sentiment.remove(item_id)
                    st.rerun()
                elif not new_inc and item_id not in st.session_state.live_excluded_sentiment:
                    st.session_state.live_excluded_sentiment.add(item_id)
                    st.rerun()
            with cs2:
                if st.button(_["save_card"], key=f"save_news_{item_id}", use_container_width=True):
                    arch = load_archive()
                    if not any(x.get("raw_id") == item_id and x.get("lang") == active_card_lang for x in arch):
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
                            "titulek": card_obj["hlavni_nadpis"],
                            "clanek": card_obj["full_text"][:2500],
                            "skore_sp500": card_obj["sentiment_score"],
                            "co_se_stalo": card_obj["co_se_stalo"],
                            "proc_to_hybe": card_obj["proc_to_hybe_trhem"],
                            "reakce_trhu": card_obj["reakce_trhu"],
                            "moje_portfolio": portfolio_tickers
                        }, ensure_ascii=False)
                        ans = chat_s_ai(q_news, ctx, chat_list[:-1], api_key, model_provider, selected_model, active_card_lang)
                        st.markdown(ans)
                if not ans.startswith("⚠️"):
                    chat_list.append({"role": "assistant", "content": ans})
                    st.rerun()
    else:
        fmap = _["filter_map"]
        filter_keys = ["ALL", "WATCHLIST", "EQUITIES", "TRADE", "MACRO", "COMMODITIES"]

        c_top1, c_top2, c_top3 = st.columns([1.4, 2.2, 0.9])
        sel_filter_key = c_top1.selectbox(
            _["filter_lbl"],
            filter_keys,
            format_func=lambda k: fmap[k],
            label_visibility="collapsed"
        )
        q_filter = c_top2.text_input(_["search_lbl"], placeholder=_["search_ph"], label_visibility="collapsed").strip().lower()
        if c_top3.button(_["refresh_btn"], use_container_width=True):
            fetch_live_wire_feed.clear()
            st.rerun()

        with st.expander(_["noise_exp"], expanded=False):
            cn1, cn2 = st.columns([4, 1.2])
            st.session_state.live_custom_block = cn1.text_input(
                _["noise_inp"],
                value=st.session_state.live_custom_block,
                placeholder=_["noise_ph"]
            )
            if st.session_state.live_hidden_ids:
                with cn2:
                    st.markdown('<div style="padding-top:28px;"></div>', unsafe_allow_html=True)
                    if st.button(_["noise_reset"], use_container_width=True):
                        st.session_state.live_hidden_ids = set()
                        st.rerun()

        with st.spinner(_["spin_search"]):
            wire_items = fetch_live_wire_feed(tuple(tickers))

        # Unikátní analyzované zprávy (preferujeme aktuální jazyk, jinak jiný uložený)
        unique_analyzed = {}
        for k_cache, c_val in st.session_state.live_analyzed_cache.items():
            rid = c_val.get("raw_id")
            if not rid:
                continue
            if rid not in unique_analyzed or c_val.get("lang") == current_lang:
                unique_analyzed[rid] = c_val

        if unique_analyzed:
            included_cards = [c for rid, c in unique_analyzed.items() if rid not in st.session_state.live_excluded_sentiment]
            tot_sc = sum(float(c.get("sentiment_score", 0.0)) for c in included_cards)
            cnt_sc = len(included_cards)
            reg_lbl = "RISK-ON" if tot_sc > 0.02 else ("RISK-OFF" if tot_sc < -0.02 else "NEUTRAL")
            st.info(_["session_stats"].format(cnt=cnt_sc, reg=reg_lbl, sc=tot_sc))

            with st.expander(_["sent_mgr_exp"], expanded=False):
                for rid, c_obj in unique_analyzed.items():
                    is_in = rid not in st.session_state.live_excluded_sentiment
                    m1, m2 = st.columns([5.2, 1.2])
                    sc_v = float(c_obj.get("sentiment_score", 0.0))
                    tag_ex = "" if is_in else f" *{_['sent_excluded_tag']}*"
                    m1.markdown(f"`{sc_v:+.4f}` · **{c_obj.get('hlavni_nadpis', c_obj.get('title', ''))}**{tag_ex}")
                    tog_lbl = _["sent_remove"] if is_in else "+ Zahrnout" if current_lang == "CZ" else "+ Include"
                    if m2.button(tog_lbl, key=f"mgr_sent_{rid}", use_container_width=True):
                        if is_in:
                            st.session_state.live_excluded_sentiment.add(rid)
                        else:
                            st.session_state.live_excluded_sentiment.remove(rid)
                        st.rerun()

        custom_blocks = [w.strip().lower() for w in st.session_state.live_custom_block.split(",") if w.strip()]

        filtered_wire = []
        for it in wire_items:
            if it["id"] in st.session_state.live_hidden_ids:
                continue
            if custom_blocks and any(b in it["title"].lower() for b in custom_blocks):
                continue
            if sel_filter_key == "WATCHLIST" and not it.get("ticker"):
                continue
            elif sel_filter_key not in ("ALL", "WATCHLIST") and it.get("topic_key") != sel_filter_key:
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
                cached_c = st.session_state.live_analyzed_cache.get(f"{it['id']}_{current_lang}") or unique_analyzed.get(it["id"])
                disp_title = cached_c["hlavni_nadpis"] if (cached_c and cached_c.get("lang") == current_lang) else it["title"]
                pub_show = it["pub_en"] if current_lang == "EN" else it["pub_cz"]
                tkr_badge = f" · `{it['ticker']}`" if it.get("ticker") else ""
                if cached_c:
                    sc = float(cached_c["sentiment_score"])
                    sc_col = "#22C55E" if sc > 0.005 else ("#EF4444" if sc < -0.005 else "#A1A1AA")
                    ex_note = f' <span style="color:#71717A;">{_["sent_excluded_tag"]}</span>' if it["id"] in st.session_state.live_excluded_sentiment else ""
                    sc_html = f' · <span style="color:{sc_col}; font-weight:600;">{cached_c["kategorie"]} {sc:+.4f}</span>{ex_note}'
                else:
                    topic_lbl = fmap.get(it.get("topic_key", "MARKET"), fmap["MARKET"])
                    sc_html = f' · <span style="color:#A1A1AA;">{topic_lbl}</span>'

                r1, r2, r3 = st.columns([5.2, 1.2, 0.35])
                with r1:
                    st.markdown(
                        f'<div class="news-feed-row">'
                        f'<div class="news-time" style="margin-bottom:2px;">{pub_show}  ·  {it["source"]}{tkr_badge}{sc_html}</div>'
                        f'<div class="news-feed-title">{disp_title}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                with r2:
                    st.markdown('<div style="padding-top:14px;"></div>', unsafe_allow_html=True)
                    btn_txt = _["open_cached"] if cached_c else _["open_card"]
                    if st.button(btn_txt, key=f"open_wire_{it['id']}", use_container_width=True):
                        st.session_state.live_selected_item = it
                        st.rerun()
                with r3:
                    st.markdown('<div style="padding-top:14px;"></div>', unsafe_allow_html=True)
                    if st.button("✕", key=f"hide_wire_{it['id']}", use_container_width=True):
                        st.session_state.live_hidden_ids.add(it["id"])
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