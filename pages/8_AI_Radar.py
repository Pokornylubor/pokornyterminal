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
        "tick_db": "DATABÁZE",
        "tick_cust": "VLASTNÍ TICKER",
        "btn_ai": "📊 Analyzovat datový tok",
        "spin_search": "Stahování datového toku...",
        "spin_ai": "AI analyzuje agregovaný datový tok a počítá sentiment...",
        "err_api": "⚠️ AI API klíč nebyl nalezen. Ujistěte se, že je GROQ_API_KEY uložen ve Streamlit Secrets.",
        "err_ai": "Chyba AI enginu:",
        "err_news": "⚠️ Žádné validní zprávy nebyly nalezeny. AI analýza byla zrušena, aby se zamezilo chybám.",
        "sources": "🗄️ Zdrojové zprávy použité pro syntézu",
        "what_happened": "CO SE STALO",
        "why_move": "PROČ TO HÝBE TRHEM (FUNDAMENT)",
        "sent_desc": "Změřený dopad na tržní sentiment. Kladné hodnoty podporují Risk-On, záporné Risk-Off.",
        "no_title": "Bez titulku",
        "no_time": "Neznámý čas",
        "hist_h": "📜 Správa uložených analýz (Historie)",
        "hist_empty": "Zatím nebyly uloženy žádné analýzy."
    },
    "EN": {
        "title": "AI SENTIMENT & NEWS RADAR",
        "desc": "QUANTITATIVE AND FUNDAMENTAL ANALYSIS OF MARKET CATALYSTS.",
        "tick_db": "DATABASE",
        "tick_cust": "CUSTOM TICKER",
        "btn_ai": "📊 Analyze Data Feed",
        "spin_search": "Downloading data feed...",
        "spin_ai": "AI is analyzing aggregated data feed and calculating sentiment...",
        "err_api": "⚠️ AI API key not found. Ensure GROQ_API_KEY is saved in Streamlit Secrets.",
        "err_ai": "AI Engine Error:",
        "err_news": "⚠️ No valid news found. AI analysis aborted to prevent errors.",
        "sources": "🗄️ Source news used for synthesis",
        "what_happened": "WHAT HAPPENED",
        "why_move": "WHY IT MOVES THE MARKET (FUNDAMENTALS)",
        "sent_desc": "Measured impact on market sentiment. Positive values support Risk-On, negative Risk-Off.",
        "no_title": "No Title",
        "no_time": "Unknown Time",
        "hist_h": "📜 Manage Saved Analyses (History)",
        "hist_empty": "No analyses have been saved yet."
    }
}
_ = t.get(current_lang, t["CZ"])

WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")
HISTORY_FILE = os.path.join(hlavni_slozka, "radar_history.json")

def load_app_data():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {"portfolio": [], "watchlist": [], "settings": {}}

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return []

def save_all_history(history_list):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history_list, f, indent=4, ensure_ascii=False)
    except: pass

def add_to_history(ticker, analyza):
    history = load_history()
    zaznam = {
        "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "ticker": ticker.upper(),
        "analyza": analyza
    }
    history.insert(0, zaznam)
    save_all_history(history)

app_data = load_app_data()
saved_settings = app_data.get("settings", {})

def load_tickers():
    return list(set(app_data.get("portfolio", []) + app_data.get("watchlist", [])))

api_key = st.secrets.get("GROQ_API_KEY", "")
model_provider = st.session_state.get("ai_provider", saved_settings.get("ai_provider", "Groq"))
selected_model = st.session_state.get("ai_model", saved_settings.get("ai_model", ""))

st.title(_["title"])
st.caption(_["desc"])
st.markdown("---")

if not api_key or not selected_model:
    st.warning(_["err_api"])
    st.stop()

if "radar_vybrany_ticker" not in st.session_state: st.session_state.radar_vybrany_ticker = None
if "radar_analyza" not in st.session_state: st.session_state.radar_analyza = None
if "radar_zpravy_list" not in st.session_state: st.session_state.radar_zpravy_list = []

tickers = load_tickers()
tickers.sort()

c1, c2, c3 = st.columns([1, 1, 2])
dropdown_val = c1.selectbox(_["tick_db"], tickers, index=None, placeholder="Choose an option")
custom_val = c2.text_input(_["tick_cust"], placeholder="")

vybrany_ticker = custom_val.strip().upper() if custom_val.strip() else dropdown_val

if vybrany_ticker != st.session_state.radar_vybrany_ticker:
    st.session_state.radar_vybrany_ticker = vybrany_ticker
    st.session_state.radar_analyza = None
    st.session_state.radar_zpravy_list = []

@st.cache_data(ttl=600)
def fetch_news(ticker):
    news_list = []
    try:
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}®ion=US&lang=en-US"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        for item in root.findall('.//item'):
            title = item.find('title').text if item.find('title') is not None else _["no_title"]
            # Tvrdý filtr: zpráva musí mít aspoň 15 znaků a nesmí to být generic balast
            if not title or len(title.strip()) < 15 or "Bez titulku" in title or "No Title" in title: 
                continue
            
            link = item.find('link').text if item.find('link') is not None else "#"
            pubDate = item.find('pubDate').text if item.find('pubDate') is not None else _["no_time"]
            if len(pubDate) > 22: pubDate = pubDate[:22]
            news_list.append({"title": title, "link": link, "publisher": "Yahoo Finance (RSS)", "pub_time_str": pubDate})
            if len(news_list) >= 8: break
    except: pass

    try:
        t = yf.Ticker(ticker)
        yf_news = t.news
        if isinstance(yf_news, list):
            for n in yf_news:
                title = n.get("title", _["no_title"])
                if not title or len(title.strip()) < 15 or "Bez titulku" in title or "No Title" in title:
                    continue
                
                link = n.get("link", "#")
                publisher = n.get("publisher", "Yahoo Finance")
                try:
                    ts = n.get("providerPublishTime", 0)
                    pubDate = datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M") if ts else _["no_time"]
                except:
                    pubDate = _["no_time"]
                news_list.append({"title": title, "link": link, "publisher": publisher, "pub_time_str": pubDate})
                if len(news_list) >= 8: break
    except: pass
    return news_list[:8]

def analyzuj_agregovane_zpravy(ticker, zpravy_text, api_klic, provider, model_name, lang):
    if provider == "Groq":
        client = OpenAI(api_key=api_klic, base_url="https://api.groq.com/openai/v1", max_retries=3)
    else:
        client = OpenAI(api_key=api_klic, max_retries=3)

    jazyk_vyzva = "v češtině (Czech)" if lang == "CZ" else "in English"
    prompt = f"""
    You are an elite quantitative hedge fund analyst. Read the following recent news headlines for ticker {ticker}.
    Synthesize them into one unified, professional market update. Return the output STRICTLY as valid JSON.
    News Data: {zpravy_text}
    
    JSON Structure:
    {{
        "hlavni_nadpis": "One overarching headline summarizing the current situation for {ticker} {jazyk_vyzva}.",
        "co_se_stalo": "Executive summary combining the key points from the news in 3-5 sentences {jazyk_vyzva}.",
        "proc_to_hybe_trhem": "Fundamental impact analysis (business model, DCF, liquidity, reasons for price action) {jazyk_vyzva}.",
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
    if st.button(_["btn_ai"], use_container_width=True):
        with st.spinner(_["spin_search"]):
            news_data = fetch_news(vybrany_ticker)
            
        if not news_data:
            st.warning(_["err_news"])
        else:
            agregovany_text = "\n".join([f"- {n['pub_time_str']}: {n['title']}" for n in news_data])
            with st.spinner(_["spin_ai"]):
                analyza = analyzuj_agregovane_zpravy(vybrany_ticker, agregovany_text, api_key, model_provider, selected_model, current_lang)
                if "error" not in analyza:
                    st.session_state.radar_analyza = analyza
                    st.session_state.radar_zpravy_list = news_data
                    # Okamžité uložení reportu
                    add_to_history(vybrany_ticker, analyza)
                else:
                    st.error(f"{_['err_ai']} {analyza['error']}")

    if st.session_state.radar_analyza:
        a = st.session_state.radar_analyza
        skore = float(a.get('sentiment_skore', 0))
        
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f"### 🔹 {a.get('hlavni_nadpis', 'Analýza trhu')}")
            barva = "green" if skore > 0 else "red" if skore < 0 else "grey"
            st.markdown(f"`{vybrany_ticker}`   <span style='color:{barva}; font-weight:bold; background-color:rgba(255,255,255,0.1); padding: 2px 6px; border-radius:4px;'>{skore:+.4f}</span>", unsafe_allow_html=True)
            st.caption(_["sent_desc"])
            st.markdown("---")
            
            # OPRAVA MEZER: Nyní používáme čisté HTML, což donutí Streamlit zahodit jeho obří mezery
            zprava_html = f"""
            <div style='line-height: 1.5; font-size: 15px;'>
                <p style='margin-bottom: 4px;'><strong>{_['what_happened']}</strong></p>
                <p style='margin-top: 0; margin-bottom: 16px;'>{a.get('co_se_stalo', '')}</p>
                <p style='margin-bottom: 4px;'><strong>{_['why_move']}</strong></p>
                <p style='margin-top: 0; margin-bottom: 0;'>{a.get('proc_to_hybe_trhem', '')}</p>
            </div>
            """
            st.markdown(zprava_html, unsafe_allow_html=True)
            
        with st.expander(_["sources"]):
            for article in st.session_state.radar_zpravy_list:
                st.markdown(f"- **{article['pub_time_str']}** | [{article['title']}]({article['link']})")

# --- MANAŽER HISTORIE (UPRAVIT / SMAZAT) ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(f"### {_['hist_h']}")

history_data = load_history()

if not history_data:
    st.info(_["hist_empty"])
else:
    for i, item in enumerate(history_data):
        a = item.get("analyza", {})
        sk = float(a.get("sentiment_skore", 0))
        ikona = "🟢" if sk > 0 else "🔴" if sk < 0 else "⚪"
        
        with st.expander(f"{item.get('timestamp')} | {item.get('ticker')} {ikona}"):
            # Editovatelná pole pro úpravu reportu
            new_title = st.text_input("Nadpis reportu:", value=a.get('hlavni_nadpis', ''), key=f"title_{i}")
            new_co = st.text_area("Co se stalo:", value=a.get('co_se_stalo', ''), key=f"co_{i}", height=120)
            new_proc = st.text_area("Proč to hýbe trhem:", value=a.get('proc_to_hybe_trhem', ''), key=f"proc_{i}", height=120)
            
            c1, c2, c3 = st.columns([1, 1, 3])
            
            # Tlačítko pro ULOŽENÍ změn
            if c1.button("💾 Uložit úpravy", key=f"save_{i}", use_container_width=True):
                history_data[i]["analyza"]["hlavni_nadpis"] = new_title
                history_data[i]["analyza"]["co_se_stalo"] = new_co
                history_data[i]["analyza"]["proc_to_hybe_trhem"] = new_proc
                save_all_history(history_data)
                st.rerun()
                
            # Tlačítko pro SMAZÁNÍ
            if c2.button("🗑️ Smazat report", key=f"del_{i}", use_container_width=True):
                history_data.pop(i)
                save_all_history(history_data)
                st.rerun()