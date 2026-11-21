import streamlit as st
import yfinance as yf
import requests
import json
import os
import sys
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo

# --- INITIAL SETUP ---
st.set_page_config(page_title="POKORNY TERMINAL | AI RADAR", layout="wide", initial_sidebar_state="collapsed")

aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)

import menu
menu.vykresli_menu()

# --- FULL-WIDTH EDITORIAL CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

.stApp { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

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
    font-size: 1.75rem;
    font-weight: 700;
    color: #F4F4F5;
    line-height: 1.25;
    letter-spacing: -0.02em;
    margin: 0 0 14px 0;
}
.brief-badge {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.76rem;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 3px;
    letter-spacing: 0.05em;
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
    font-family: 'Inter', sans-serif;
    font-size: 0.98rem;
    line-height: 1.7;
    color: #D4D4D8;
    margin: 0;
}
.brief-lib-row { padding: 14px 0; border-bottom: 1px solid #1F2227; }
.brief-lib-title { font-family: 'Inter', sans-serif; font-size: 1.06rem; font-weight: 600; color: #F4F4F5; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)

current_lang = st.session_state.get("lang", "CZ")

WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")
ARCHIVE_FILE = os.path.join(hlavni_slozka, "ai_radar_archive.json")

# --- DICTIONARY ---
t = {
    "CZ": {
        "title": "AI SENTIMENT & MARKET BRIEF",
        "desc": "SYNTÉZA TRŽNÍCH ZPRÁV, MAKRO REŽIM (RISK-ON / RISK-OFF) A ARCHIV REPORTŮ.",
        "tab_gen": "GENERÁTOR",
        "tab_lib": "ARCHIV REPORTŮ",
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
        "btn_ai": "Vygenerovat report",
        "btn_save": "Uložit do Archivu (GitHub)",
        "saved_ok": "Report uložen do Archivu a synchronizován na GitHub.",
        "already_saved": "Tento report je již uložený v Archivu.",
        "spin_search": "Stahování datového toku...",
        "spin_ai": "AI syntetizuje datový tok...",
        "spin_chat": "AI formuluje odpověď...",
        "err_api": "AI API klíč nebo model nebyl nalezen. Zkontrolujte GROQ_API_KEY v Secrets a Nastavení.",
        "err_ai": "Chyba AI enginu:",
        "err_news": "Žádné aktuální zprávy nebyly nalezeny.",
        "sources": "Zdrojové zprávy použité pro syntézu",
        "what_happened": "CO SE STALO",
        "why_move": "PROČ TO HÝBE TRHEM (FUNDAMENT)",
        "watch_next": "CO SLEDOVAT DÁL",
        "no_title": "Bez titulku",
        "no_time": "Neznámý čas",
        "chat_h": "Dotazy k tomuto reportu",
        "chat_ph": "Zeptejte se na detaily, valuaci nebo historický kontext...",
        "lib_empty": "Archiv je zatím prázdný. Vygenerujte report v záložce Generátor a uložte ho.",
        "lib_filter": "FILTR",
        "lib_all": "Vše",
        "lib_macro_lbl": "MARKET BRIEF",
        "lib_stock_lbl": "AKCIE",
        "lib_saved_h": "ULOŽENÉ REPORTY",
        "lib_search": "HLEDAT V ARCHIVU",
        "lib_search_ph": "Ticker, téma nebo klíčové slovo...",
        "lib_open": "Číst →",
        "lib_del": "Smazat",
        "lib_deleted": "Report byl odstraněn z Archivu.",
        "lib_back": "← Zpět do Archivu",
        "presets": {
            "US Trh & Indexy (S&P 500, Nasdaq)": "S&P 500 Nasdaq stock market today Wall Street",
            "FED, Inflace & Dluhopisy": "Federal Reserve interest rates CPI inflation treasury yields",
            "AI & Polovodiče": "AI semiconductors Nvidia data center chip stocks",
            "Zlato, Ropa & Komodity": "gold price XAUUSD crude oil commodities market",
            "Makro & Měny (USD, EUR)": "global macro economy EURUSD central banks markets"
        }
    },
    "EN": {
        "title": "AI SENTIMENT & MARKET BRIEF",
        "desc": "MARKET NEWS SYNTHESIS, MACRO REGIME (RISK-ON / RISK-OFF) & REPORT ARCHIVE.",
        "tab_gen": "GENERATOR",
        "tab_lib": "REPORT ARCHIVE",
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
        "btn_ai": "Generate Report",
        "btn_save": "Save to Archive (GitHub)",
        "saved_ok": "Report saved to Archive and synced to GitHub.",
        "already_saved": "This report is already saved in the Archive.",
        "spin_search": "Fetching data feed...",
        "spin_ai": "AI is synthesizing data feed...",
        "spin_chat": "AI is generating response...",
        "err_api": "AI API key or model not found. Check GROQ_API_KEY in Secrets and Settings.",
        "err_ai": "AI Engine Error:",
        "err_news": "No current news found.",
        "sources": "Source news used for synthesis",
        "what_happened": "WHAT HAPPENED",
        "why_move": "WHY IT MOVES THE MARKET (FUNDAMENTALS)",
        "watch_next": "WHAT TO WATCH NEXT",
        "no_title": "No Title",
        "no_time": "Unknown Time",
        "chat_h": "Questions about this report",
        "chat_ph": "Ask about details, valuation, or historical context...",
        "lib_empty": "Archive is empty. Generate a report in the Generator tab and save it.",
        "lib_filter": "FILTER",
        "lib_all": "All",
        "lib_macro_lbl": "MARKET BRIEF",
        "lib_stock_lbl": "EQUITY",
        "lib_saved_h": "SAVED REPORTS",
        "lib_search": "SEARCH ARCHIVE",
        "lib_search_ph": "Ticker, topic, or keyword...",
        "lib_open": "Read →",
        "lib_del": "Delete",
        "lib_deleted": "Report removed from Archive.",
        "lib_back": "← Back to Archive",
        "presets": {
            "US Market & Indices (S&P 500, Nasdaq)": "S&P 500 Nasdaq stock market today Wall Street",
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
st.markdown("---")

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
tickers = sorted(list(set(app_data.get("portfolio", []) + app_data.get("watchlist", []))))

api_key = st.secrets.get("GROQ_API_KEY", "")
model_provider = st.session_state.get("ai_provider", saved_settings.get("ai_provider", "Groq"))
selected_model = st.session_state.get("ai_model", saved_settings.get("ai_model", ""))

if not api_key or not selected_model:
    st.warning(_["err_api"])
    st.stop()

# --- SESSION STATE ---
for key, default in [
    ("lab_current_report", None),
    ("lab_chat", []),
    ("lab_saved_id", None),
    ("lib_selected_id", None),
    ("lib_chat", [])
]:
    if key not in st.session_state:
        st.session_state[key] = default

# --- DIRECT HTTP AI CALL ---
def call_llm_api(messages, api_klic, provider, model_name, temperature=0.2, timeout=30):
    url = "https://api.groq.com/openai/v1/chat/completions" if provider == "Groq" else "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_klic}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:250]}")
    return resp.json()["choices"][0]["message"]["content"]

@st.cache_data(ttl=600)
def fetch_news(query_str, is_ticker=True):
    news_list = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    search_q = f"{query_str}+stock+news" if is_ticker else query_str.replace(" ", "+")
    try:
        url = f"https://news.google.com/rss/search?q={search_q}&hl=en-US&gl=US&ceid=US:en"
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            for item in root.findall('.//item')[:10]:
                title = item.find('title').text if item.find('title') is not None else _["no_title"]
                link = item.find('link').text if item.find('link') is not None else "#"
                pubDate = item.find('pubDate').text if item.find('pubDate') is not None else _["no_time"]
                if len(pubDate) > 22:
                    pubDate = pubDate[:22]
                news_list.append({"title": title, "link": link, "publisher": "Google News", "pub_time_str": pubDate})
            if news_list:
                return news_list
    except Exception:
        pass

    if is_ticker:
        try:
            yf_news = yf.Ticker(query_str).news
            if yf_news:
                for n in yf_news[:8]:
                    content = n.get("content", n)
                    title = content.get("title", _["no_title"])
                    link = content.get("canonicalUrl", {}).get("url", n.get("link", "#"))
                    pubDate = content.get("pubDate", _["no_time"])
                    if pubDate and len(pubDate) > 16:
                        pubDate = pubDate[:16].replace("T", " ")
                    if title != _["no_title"]:
                        news_list.append({"title": title, "link": link, "publisher": "Yahoo Finance", "pub_time_str": pubDate})
        except Exception:
            pass

    return news_list

def generuj_ai_report(tema, typ, zpravy_text, api_klic, provider, model_name, lang):
    jazyk_vyzva = "v češtině (Czech)" if lang == "CZ" else "in English"
    kontext_role = "overall equity/macro market brief" if typ == "MARKET BRIEF" else f"specific equity ticker {tema}"

    prompt = f"""You are an elite quantitative hedge fund analyst writing an institutional brief for {kontext_role} ({tema}).
Read the following recent news headlines and synthesize them into one sharp, high-signal market update.
Return STRICTLY valid JSON.
News Data:
{zpravy_text}

JSON Structure:
{{
    "hlavni_nadpis": "One punchy, institutional headline summarizing the key takeaway {jazyk_vyzva}.",
    "rezim": "RISK-ON" or "RISK-OFF" or "NEUTRAL",
    "sentiment_skore": <float between -1.0 (strong Risk-Off) and 1.0 (strong Risk-On)>,
    "co_se_stalo": "Executive summary of key events in 3-5 crisp sentences {jazyk_vyzva}.",
    "proc_to_hybe_trhem": "Fundamental & liquidity impact analysis (rates, margins, DCF, positioning) {jazyk_vyzva}.",
    "na_co_se_zamerit": "2-3 concrete catalysts or levels to watch next as plain text {jazyk_vyzva}."
}}
Output raw JSON only."""
    try:
        vysledek = call_llm_api([{"role": "user", "content": prompt}], api_klic, provider, model_name, temperature=0.1, timeout=30).strip()
        if vysledek.startswith("```"):
            vysledek = vysledek.strip("`").replace("json\n", "", 1).strip()
        return json.loads(vysledek)
    except Exception as e:
        return {"error": str(e)}

def chat_s_ai(otazka, report_obj, historie, api_klic, provider, model_name, lang):
    jazyk_vyzva = "Odpovídej v češtině." if lang == "CZ" else "Answer in English."
    analyza_str = json.dumps({
        "tema": report_obj.get("tema"),
        "hlavni_nadpis": report_obj.get("hlavni_nadpis"),
        "co_se_stalo": report_obj.get("co_se_stalo"),
        "proc_to_hybe_trhem": report_obj.get("proc_to_hybe_trhem"),
        "na_co_se_zamerit": report_obj.get("na_co_se_zamerit")
    }, ensure_ascii=False)
    zdroje_txt = "\n".join([f"- {z['pub_time_str']}: {z['title']}" for z in report_obj.get("zdroje", [])])
    
    messages = [
        {"role": "system", "content": f"Jsi institucionální analytik hedgeového fondu. Odpovídej přímým, analytickým stylem. Report: {analyza_str}. Zdrojové zprávy: {zdroje_txt}. {jazyk_vyzva}"}
    ]
    for msg in historie:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": otazka})
    
    try:
        return call_llm_api(messages, api_klic, provider, model_name, temperature=0.3, timeout=25)
    except Exception as e:
        return f"⚠️ AI Error ({e})."

def vykresli_report_kartu(rep):
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
tab_gen, tab_lib = st.tabs([_["tab_gen"], _["tab_lib"]])

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
                news_data = fetch_news(search_query, is_ticker=(not is_macro))
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
                    odpoved = chat_s_ai(prompt, rep, st.session_state.lab_chat[:-1], api_key, model_provider, selected_model, current_lang)
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
                        odpoved = chat_s_ai(prompt_lib, selected_rep, st.session_state.lib_chat[:-1], api_key, model_provider, selected_model, current_lang)
                        st.markdown(odpoved)
                if not odpoved.startswith("⚠️"):
                    st.session_state.lib_chat.append({"role": "assistant", "content": odpoved})
        else:
            f1, f2 = st.columns([1.2, 2.8])
            filtr_opts = [_["lib_all"], _["lib_macro_lbl"], _["lib_stock_lbl"]]
            typ_filtr = f1.selectbox(_["lib_filter"], filtr_opts)
            hledat = f2.text_input(_["lib_search"], placeholder=_["lib_search_ph"]).strip().lower()

            filtered = []
            for r in archive:
                r_typ = r.get("typ", "")
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
                badge_color = "#22C55E" if (rezim == "RISK-ON" or skore > 0.15) else "#EF4444" if (rezim == "RISK-OFF" or skore < -0.15) else "#A1A1AA"

                c_info, c_btn = st.columns([6, 1])
                with c_info:
                    row_html = (
                        f'<div class="brief-lib-row">'
                        f'<div class="brief-meta" style="margin-bottom:4px;">'
                        f'{item.get("datum", "")}  ·  {item.get("typ", "")}  ·  {item.get("tema", "")}  ·  '
                        f'<span style="color:{badge_color}; font-weight:600;">{rezim} {skore:+.2f}</span>'
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