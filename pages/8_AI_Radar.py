import streamlit as st
import yfinance as yf
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from openai import OpenAI

# --- INITIAL SETUP ---
st.set_page_config(page_title="POKORNY TERMINAL | AI RADAR", layout="wide", initial_sidebar_state="collapsed")

aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)

import menu
menu.vykresli_menu()

current_lang = st.session_state.get("lang", "CZ")

# --- DICTIONARY ---
t = {
    "CZ": {
        "title": "AI SENTIMENT & NEWS RADAR",
        "desc": "KVANTITATIVNÍ A FUNDAMENTÁLNÍ ANALÝZA TRŽNÍCH KATALYZÁTORŮ.",
        "tick_h": "Vyhledávání katalyzátorů",
        "tick_dd": "Vyberte ticker...",
        "tick_cust_opt": "✏️ Napsat vlastní ticker...",
        "tick_cust_ph": "Napište ticker (např. TSLA) a stiskněte Enter...",
        "btn_ai": "🧠 Generovat celkovou AI syntézu",
        "spin_search": "Stahování datového toku...",
        "spin_ai": "AI analyzuje agregovaný datový tok a počítá sentiment...",
        "err_api": "⚠️ AI není nakonfigurována. Přejděte do sekce '⚙️ Nastavení' a vložte platný API klíč.",
        "err_ai": "Chyba AI enginu:",
        "err_news": "Žádné aktuální zprávy nebyly nalezeny.",
        "sources": "🗄️ Zdrojové zprávy použité pro syntézu",
        "ai_expl": "🤖 AI VYSVĚTLENÍ",
        "what_happened": "CO SE STALO",
        "fund_imp": "FUNDAMENTÁLNÍ DOPAD",
        "sent_desc": "Změřený dopad na tržní sentiment. Kladné hodnoty podporují Risk-On, záporné Risk-Off.",
        "sent": "Sentiment",
        "no_title": "Bez titulku",
        "no_time": "Neznámý čas"
    },
    "EN": {
        "title": "AI SENTIMENT & NEWS RADAR",
        "desc": "QUANTITATIVE AND FUNDAMENTAL ANALYSIS OF MARKET CATALYSTS.",
        "tick_h": "Catalyst Search",
        "tick_dd": "Select ticker...",
        "tick_cust_opt": "✏️ Enter custom ticker...",
        "tick_cust_ph": "Type ticker (e.g. TSLA) and press Enter...",
        "btn_ai": "🧠 Generate Aggregated AI Synthesis",
        "spin_search": "Downloading data feed...",
        "spin_ai": "AI is analyzing aggregated data feed and calculating sentiment...",
        "err_api": "⚠️ AI is not configured. Go to '⚙️ Settings' and provide a valid API key.",
        "err_ai": "AI Engine Error:",
        "err_news": "No current news found.",
        "sources": "🗄️ Source news used for synthesis",
        "ai_expl": "🤖 AI EXPLANATION",
        "what_happened": "WHAT HAPPENED",
        "fund_imp": "FUNDAMENTAL IMPACT",
        "sent_desc": "Measured impact on market sentiment. Positive values support Risk-On, negative Risk-Off.",
        "sent": "Sentiment",
        "no_title": "No Title",
        "no_time": "Unknown Time"
    }
}
_ = t.get(current_lang, t["CZ"])

WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")

def load_tickers():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return list(set(data.get("portfolio", []) + data.get("watchlist", [])))
        except: pass
    return ["AAPL", "MSFT", "NVDA"]

# --- NAČTENÍ KONFIGURACE Z GLOBÁLNÍ PAMĚTI ---
api_key = st.session_state.get("ai_api_key", "")
model_provider = st.session_state.get("ai_provider", "Groq")
selected_model = st.session_state.get("ai_model", "")

st.title(_["title"])
st.caption(_["desc"])
st.markdown("---")

if not api_key or not selected_model:
    st.warning(_["err_api"])
    st.stop()

# --- ČISTÝ VÝBĚR TICKERU ---
tickers = load_tickers()
tickers.sort()

# Sestavení možností (Watchlist + volba pro vlastní zadání)
options = tickers + [_["tick_cust_opt"]]

st.markdown(f"#### {_['tick_h']}")
c1, c2 = st.columns([1, 3])

with c1:
    selected_dropdown = st.selectbox("Výběr", options, index=None, placeholder=_["tick_dd"], label_visibility="collapsed")
    
    vybrany_ticker = None
    if selected_dropdown == _["tick_cust_opt"]:
        vybrany_ticker = st.text_input("Custom Ticker", placeholder=_["tick_cust_ph"], label_visibility="collapsed")
        if vybrany_ticker:
            vybrany_ticker = vybrany_ticker.strip().upper()
    elif selected_dropdown:
        vybrany_ticker = selected_dropdown

@st.cache_data(ttl=600)
def fetch_news(ticker):
    news_list = []
    try:
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        for item in root.findall('.//item')[:8]:
            title = item.find('title').text if item.find('title') is not None else _["no_title"]
            link = item.find('link').text if item.find('link') is not None else "#"
            pubDate = item.find('pubDate').text if item.find('pubDate') is not None else _["no_time"]
            if len(pubDate) > 22: pubDate = pubDate[:22]
            news_list.append({"title": title, "link": link, "publisher": "Yahoo Finance (RSS)", "pub_time_str": pubDate})
        if news_list: return news_list
    except: pass

    try:
        t = yf.Ticker(ticker)
        yf_news = t.news
        for n in yf_news[:8]:
            title = n.get("title", _["no_title"])
            link = n.get("link", "#")
            publisher = n.get("publisher", "Yahoo Finance")
            try:
                ts = n.get("providerPublishTime", 0)
                pubDate = datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M") if ts else _["no_time"]
            except:
                pubDate = _["no_time"]
            news_list.append({"title": title, "link": link, "publisher": publisher, "pub_time_str": pubDate})
    except: pass
    return news_list

def analyzuj_agregovane_zpravy(ticker, zpravy_text, api_klic, provider, model_name, lang):
    if provider == "Groq":
        client = OpenAI(api_key=api_klic, base_url="https://api.groq.com/openai/v1")
    else:
        client = OpenAI(api_key=api_klic)

    jazyk_vyzva = "v češtině (Czech)" if lang == "CZ" else "in English"
    
    prompt = f"""
    You are an elite quantitative hedge fund analyst. Read the following recent news headlines for ticker {ticker}.
    Synthesize them into one unified, professional market update. Return the output STRICTLY as valid JSON.
    News Data: {zpravy_text}
    
    JSON Structure:
    {{
        "hlavni_nadpis": "One overarching headline summarizing the current situation for {ticker} {jazyk_vyzva}.",
        "co_se_stalo": "Executive summary combining the key points from the news in 3-5 sentences {jazyk_vyzva}.",
        "dopad_fundament": "Fundamental impact analysis (business model, DCF, liquidity) {jazyk_vyzva}.",
        "sentiment_skore": <float between -1.0 (strong Risk-Off) and 1.0 (strong Risk-On)>
    }}
    Do not output anything other than raw JSON.
    """
    try:
        response = client.chat.completions.create(model=model_name, messages=[{"role": "user", "content": prompt}], temperature=0.1)
        vysledek = response.choices[0].message.content
        if vysledek.startswith("```json"): vysledek = vysledek.strip("`").replace("json\n", "")
        return json.loads(vysledek)
    except Exception as e:
        return {"error": str(e)}

if vybrany_ticker:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.spinner(_["spin_search"]):
        news_data = fetch_news(vybrany_ticker)
    
    if not news_data:
        st.warning(_["err_news"])
    else:
        if st.button(_["btn_ai"], use_container_width=True, type="primary"):
            agregovany_text = "\n".join([f"- {n['pub_time_str']}: {n['title']}" for n in news_data])
            with st.spinner(_["spin_ai"]):
                analyza = analyzuj_agregovane_zpravy(vybrany_ticker, agregovany_text, api_key, model_provider, selected_model, current_lang)
                if "error" in analyza:
                    st.error(f"{_['err_ai']} {analyza['error']}")
                else:
                    st.markdown("<br>", unsafe_allow_html=True)
                    with st.container(border=True):
                        st.markdown(f"### 🔹 {analyza.get('hlavni_nadpis', 'Analýza trhu')}")
                        skore = float(analyza.get('sentiment_skore', 0))
                        col_val, col_desc = st.columns([1, 4])
                        with col_val: st.metric(_["sent"], f"{skore:+.4f}")
                        with col_desc: st.caption(_["sent_desc"])
                        st.markdown("---")
                        st.markdown(f"#### {_['ai_expl']}")
                        st.markdown(f"**{_['what_happened']}**")
                        st.write(analyza.get("co_se_stalo", ""))
                        st.markdown(f"**{_['fund_imp']}**")
                        st.write(analyza.get("dopad_fundament", ""))
        
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander(_["sources"]):
            for article in news_data:
                st.markdown(f"- **{article['pub_time_str']}** | [{article['title']}]({article['link']})")