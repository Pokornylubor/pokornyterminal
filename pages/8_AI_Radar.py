import streamlit as st
import yfinance as yf
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from openai import OpenAI
import google.generativeai as genai

# --- INITIAL SETUP ---
st.set_page_config(page_title="POKORNY TERMINAL | AI RADAR", layout="wide", initial_sidebar_state="collapsed")

aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)

import menu
menu.vykresli_menu()

current_lang = st.session_state.get("lang", "CZ")

t = {
    "CZ": {
        "title": "AI SENTIMENT & NEWS RADAR",
        "desc": "KVANTITATIVNÍ A FUNDAMENTÁLNÍ ANALÝZA TRŽNÍCH KATALYZÁTORŮ.",
        "tick_db": "DATABÁZE",
        "tick_cust": "VLASTNÍ TICKER",
        "btn_ai": "📊 Analyzovat datový tok",
        "spin_search": "Stahování datového toku...",
        "spin_ai": "AI analyzuje agregovaný datový tok a počítá sentiment...",
        "err_api": "⚠️ AI API klíč nebyl nalezen. Ujistěte se, že je klíč uložen ve Streamlit Secrets.",
        "err_ai": "Chyba AI enginu:",
        "err_news": "Žádné aktuální zprávy nebyly nalezeny."
    }
}
_ = t.get(current_lang, t["CZ"])

# ========================================================
# ABSOLUTNÍ OVERRIDE (IGNORUJEME ZASEKNUTÝ WATCHLIST)
# ========================================================
# Natvrdo nastavujeme Groq a jeho nejstabilnější dostupný model
model_provider = "Groq"
selected_model = "llama3-8b-8192" 
api_key = st.secrets.get("GROQ_API_KEY", "")

st.title(_["title"])
st.caption(_["desc"])
st.info(f"🔧 **Natvrdo vynucený engine:** {model_provider} | **Model:** {selected_model}")
st.markdown("---")

if not api_key:
    st.warning(_["err_api"])
    st.stop()

if "radar_vybrany_ticker" not in st.session_state: st.session_state.radar_vybrany_ticker = None
if "radar_analyza" not in st.session_state: st.session_state.radar_analyza = None
if "radar_zpravy_text" not in st.session_state: st.session_state.radar_zpravy_text = ""
if "radar_zpravy_list" not in st.session_state: st.session_state.radar_zpravy_list = []
if "radar_chat" not in st.session_state: st.session_state.radar_chat = []

tickers = [] # Zjednodušeno pro test
tickers.sort()

c1, c2, c3 = st.columns([1, 1, 2])
dropdown_val = c1.selectbox("DATABÁZE", tickers, index=None, placeholder="Choose an option")
custom_val = c2.text_input("VLASTNÍ TICKER", placeholder="")

vybrany_ticker = custom_val.strip().upper() if custom_val.strip() else dropdown_val

if vybrany_ticker != st.session_state.radar_vybrany_ticker:
    st.session_state.radar_vybrany_ticker = vybrany_ticker
    st.session_state.radar_analyza = None
    st.session_state.radar_chat = []
    st.session_state.radar_zpravy_text = ""
    st.session_state.radar_zpravy_list = []

@st.cache_data(ttl=600)
def fetch_news(ticker):
    news_list = []
    try:
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        for item in root.findall('.//item')[:8]:
            title = item.find('title').text if item.find('title') is not None else "Bez titulku"
            link = item.find('link').text if item.find('link') is not None else "#"
            pubDate = item.find('pubDate').text if item.find('pubDate') is not None else "Neznámý čas"
            if len(pubDate) > 22: pubDate = pubDate[:22]
            news_list.append({"title": title, "link": link, "publisher": "Yahoo Finance (RSS)", "pub_time_str": pubDate})
        if news_list: return news_list
    except: pass

    try:
        t = yf.Ticker(ticker)
        yf_news = t.news
        for n in yf_news[:8]:
            title = n.get("title", "Bez titulku")
            link = n.get("link", "#")
            publisher = n.get("publisher", "Yahoo Finance")
            try:
                ts = n.get("providerPublishTime", 0)
                pubDate = datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M") if ts else "Neznámý čas"
            except:
                pubDate = "Neznámý čas"
            news_list.append({"title": title, "link": link, "publisher": publisher, "pub_time_str": pubDate})
    except: pass
    return news_list

def analyzuj_agregovane_zpravy(ticker, zpravy_text, api_klic, provider, model_name, lang):
    jazyk_vyzva = "v češtině (Czech)"
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
        client = OpenAI(api_key=api_klic, base_url="https://api.groq.com/openai/v1", max_retries=3)
        response = client.chat.completions.create(model=model_name, messages=[{"role": "user", "content": prompt}], temperature=0.1, max_tokens=800, timeout=20.0)
        vysledek = response.choices[0].message.content
        if vysledek.startswith("```json"): vysledek = vysledek.strip("`").replace("json\n", "")
        elif vysledek.startswith("```"): vysledek = vysledek.strip("`")
        return json.loads(vysledek)
    except Exception as e:
        return {"error": f"Groq API chyba: {str(e)}"}

def chat_s_ai(otazka, kontext_zprav, analyza_json, historie, api_klic, provider, model_name, lang):
    jazyk_vyzva = "Odpovídej v češtině."
    analyza_str = json.dumps(analyza_json, ensure_ascii=False)
    system_msg = f"Jsi institucionální analytik hedgeového fondu. Odpovídej uživateli na dotazy ohledně této tržní události. Buď přímý, analytický a přesný. Zde je tvá původní syntéza: {analyza_str}. Zdrojové zprávy: {kontext_zprav}. {jazyk_vyzva}"
    
    try:
        client = OpenAI(api_key=api_klic, base_url="https://api.groq.com/openai/v1", max_retries=3)
        messages = [{"role": "system", "content": system_msg}]
        for msg in historie: messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": otazka})
        response = client.chat.completions.create(model=model_name, messages=messages, temperature=0.3, max_tokens=800, timeout=15.0)
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ Došlo k výpadku spojení s Groq ({e})."

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
                    st.session_state.radar_zpravy_text = agregovany_text
                    st.session_state.radar_zpravy_list = news_data
                    st.session_state.radar_chat = []
                else:
                    st.error(f"{_['err_ai']} {analyza['error']}")

    if st.session_state.radar_analyza:
        a = st.session_state.radar_analyza
        skore = float(a.get('sentiment_skore', 0))
        
        st.markdown("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown(f"### 🔹 {a.get('hlavni_nadpis', 'Analýza trhu')}")
            barva = "green" if skore > 0 else "red" if skore < 0 else "grey"
            st.markdown(f"`{vybrany_ticker}` &nbsp; <span style='color:{barva}; font-weight:bold; background-color:rgba(255,255,255,0.1); padding: 2px 6px; border-radius:4px;'>{skore:+.4f}</span>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("**CO SE STALO**")
            st.write(a.get("co_se_stalo", ""))
            st.markdown("**PROČ TO HÝBE TRHEM**")
            st.write(a.get("proc_to_hybe_trhem", ""))
            
        with st.expander("🗄️ Zdrojové zprávy"):
            for article in st.session_state.radar_zpravy_list:
                st.markdown(f"- **{article['pub_time_str']}** | [{article['title']}]({article['link']})")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 💬 Vaše otázky k této zprávě")
        
        for msg in st.session_state.radar_chat:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
                
        if prompt := st.chat_input("Zeptejte se..."):
            st.session_state.radar_chat.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
                
            with st.chat_message("assistant"):
                with st.spinner("AI formuluje odpověď..."):
                    odpoved = chat_s_ai(prompt, st.session_state.radar_zpravy_text, st.session_state.radar_analyza, st.session_state.radar_chat[:-1], api_key, model_provider, selected_model, current_lang)
                    st.markdown(odpoved)
            if not odpoved.startswith("⚠️"):
                st.session_state.radar_chat.append({"role": "assistant", "content": odpoved})