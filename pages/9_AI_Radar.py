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
        "api_lbl": "🔑 API Klíč (Groq / OpenAI):",
        "prov_lbl": "Poskytovatel infrastruktury:",
        "mod_lbl": "Jazykový model (LLM):",
        "api_help": "Pro analýzu zpráv vložte API klíč. Doporučujeme Groq pro bleskové a bezplatné zpracování.",
        "tick_lbl": "Zvolte ticker pro analýzu:",
        "news_h": "Poslední katalyzátory a zprávy:",
        "btn_ai": "🧠 Generovat AI Syntézu",
        "spin_search": "Vyhledávám tržní katalyzátory...",
        "spin_ai": "AI provádí kvantitativní a fundamentální syntézu...",
        "err_api": "Nejprve vložte API klíč v horní části modulu.",
        "err_ai": "Chyba AI enginu:",
        "err_news": "Žádné aktuální zprávy nebyly nalezeny. Zdrojová data momentálně neodpovídají.",
        "orig": "Zdrojový dokument:",
        "exec_sum": "EXECUTIVE SUMMARY",
        "fund_imp": "FUNDAMENTÁLNÍ DOPAD (DCF & CASH-FLOW)",
        "sent": "Sentiment",
        "risk_on": "Risk-On",
        "risk_off": "-Risk-Off",
        "neutral": "Neutrální",
        "no_title": "Bez titulku",
        "no_time": "Neznámý čas"
    },
    "EN": {
        "title": "AI SENTIMENT & NEWS RADAR",
        "desc": "QUANTITATIVE AND FUNDAMENTAL ANALYSIS OF MARKET CATALYSTS.",
        "api_lbl": "🔑 API Key (Groq / OpenAI):",
        "prov_lbl": "Infrastructure Provider:",
        "mod_lbl": "Language Model (LLM):",
        "api_help": "Insert an API key for news analysis. We recommend Groq for lightning-fast, free processing.",
        "tick_lbl": "Select ticker for analysis:",
        "news_h": "Latest Catalysts and News:",
        "btn_ai": "🧠 Generate AI Synthesis",
        "spin_search": "Searching for market catalysts...",
        "spin_ai": "AI is performing quantitative and fundamental synthesis...",
        "err_api": "Please insert your API key at the top of the module first.",
        "err_ai": "AI Engine Error:",
        "err_news": "No current news found. Source data is currently unresponsive.",
        "orig": "Source document:",
        "exec_sum": "EXECUTIVE SUMMARY",
        "fund_imp": "FUNDAMENTAL IMPACT (DCF & CASH-FLOW)",
        "sent": "Sentiment",
        "risk_on": "Risk-On",
        "risk_off": "-Risk-Off",
        "neutral": "Neutral",
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

st.title(_["title"])
st.caption(_["desc"])
st.markdown("---")

# --- API KEY MANAGEMENT ---
with st.expander("⚙️ Konfigurace AI Enginu", expanded=True):
    col_api, col_provider, col_model = st.columns([2, 1, 1])
    api_key = col_api.text_input(_["api_lbl"], type="password", placeholder="gsk_... / sk-...")
    model_provider = col_provider.selectbox(_["prov_lbl"], ["Groq", "OpenAI"])
    
    if model_provider == "Groq":
        # Odstraněn nedostupný 70B model, výchozí je nyní 8B-instant a Mixtral
        groq_options = [
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
            "Vlastní model (napsat manuálně)"
        ]
        selected_option = col_model.selectbox(_["mod_lbl"], groq_options, index=0)
        if selected_option == "Vlastní model (napsat manuálně)":
            selected_model = col_model.text_input("Zadejte přesný název Groq modelu:", value="llama-3.1-8b-instant")
        else:
            selected_model = selected_option
    else:
        selected_model = col_model.selectbox(_["mod_lbl"], ["gpt-4o-mini", "gpt-4o"], index=0)

if not api_key:
    st.info(_["api_help"])

# --- UI PRO VÝBĚR TICKERU ---
tickers = load_tickers()
tickers.sort()

c1, c2 = st.columns([1, 3])
vybrany_ticker = c1.selectbox(_["tick_lbl"], tickers)

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
            
            if len(pubDate) > 22:
                pubDate = pubDate[:22]
                
            news_list.append({
                "title": title,
                "link": link,
                "publisher": "Yahoo Finance (RSS)",
                "pub_time_str": pubDate
            })
        if news_list:
            return news_list
    except Exception:
        pass

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
                
            news_list.append({
                "title": title,
                "link": link,
                "publisher": publisher,
                "pub_time_str": pubDate
            })
    except:
        pass
        
    return news_list

def analyzuj_text(titulek, api_klic, provider, model_name, lang):
    if provider == "Groq":
        client = OpenAI(api_key=api_klic, base_url="https://api.groq.com/openai/v1")
    else:
        client = OpenAI(api_key=api_klic)

    jazyk_vyzva = "v češtině (Czech)" if lang == "CZ" else "in English"
    
    prompt = f"""
    You are an elite quantitative hedge fund analyst. Analyze the following corporate news and return the output STRICTLY as valid JSON.
    News headline/text: {titulek}
    
    JSON Structure:
    {{
        "co_se_stalo": "Brief executive summary of the news in 2-3 sentences {jazyk_vyzva}.",
        "dopad_fundament": "How this impacts the business model, cash-flow, or DCF valuation {jazyk_vyzva}.",
        "sentiment_skore": <float between -1.0 (strong Risk-Off) and 1.0 (strong Risk-On)>
    }}
    Do not output anything other than raw JSON.
    """
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        vysledek = response.choices[0].message.content
        if vysledek.startswith("```json"):
            vysledek = vysledek.strip("`").replace("json\n", "")
        return json.loads(vysledek)
    except Exception as e:
        return {"error": str(e)}

if vybrany_ticker:
    st.markdown(f"### {_['news_h']} **{vybrany_ticker}**")
    
    with st.spinner(_["spin_search"]):
        news_data = fetch_news(vybrany_ticker)
    
    if not news_data:
        st.warning(_["err_news"])
    else:
        for idx, article in enumerate(news_data):
            title = article.get("title", _["no_title"])
            publisher = article.get("publisher", "N/A")
            link = article.get("link", "#")
            pub_time = article.get("pub_time_str", _["no_time"])
            
            with st.expander(f"📰 {pub_time} | {publisher}: {title}"):
                st.markdown(f"**{_['orig']}** [{title}]({link})")
                
                if st.button(_["btn_ai"], key=f"btn_{idx}"):
                    if not api_key:
                        st.error(_["err_api"])
                    else:
                        with st.spinner(_["spin_ai"]):
                            analyza = analyzuj_text(title, api_key, model_provider, selected_model, current_lang)
                            
                            if "error" in analyza:
                                st.error(f"{_['err_ai']} {analyza['error']}")
                            else:
                                st.markdown("---")
                                col_skore, col_text = st.columns([1, 4])
                                skore = float(analyza.get('sentiment_skore', 0))
                                
                                with col_skore:
                                    if skore > 0.2:
                                        st.metric(_["sent"], f"{skore:+.2f}", _["risk_on"])
                                    elif skore < -0.2:
                                        st.metric(_["sent"], f"{skore:+.2f}", _["risk_off"])
                                    else:
                                        st.metric(_["sent"], f"{skore:+.2f}", _["neutral"], delta_color="off")
                                
                                with col_text:
                                    st.markdown(f"#### {_['exec_sum']}")
                                    st.info(analyza.get("co_se_stalo", ""))
                                    
                                    st.markdown(f"#### {_['fund_imp']}")
                                    if skore > 0:
                                        st.success(analyza.get("dopad_fundament", ""))
                                    elif skore < 0:
                                        st.error(analyza.get("dopad_fundament", ""))
                                    else:
                                        st.warning(analyza.get("dopad_fundament", ""))