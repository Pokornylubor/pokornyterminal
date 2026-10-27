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

WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")

def load_tickers():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return list(set(data.get("portfolio", []) + data.get("watchlist", [])))
        except: pass
    return ["AAPL", "MSFT", "NVDA"]

st.title("🧠 AI ZPRAVODAJSKÝ & SENTIMENT RADAR")
st.caption("AUTOMATICKÁ FUNDAMENTÁLNÍ ANALÝZA ZPRÁV A MĚŘENÍ TRŽNÍHO SENTIMENTU.")
st.markdown("---")

# --- API KEY MANAGEMENT ---
col_api, col_provider, col_model = st.columns([2, 1, 1])
api_key = col_api.text_input("🔑 Groq / OpenAI API Klíč:", type="password", placeholder="gsk_... nebo sk-...", help="Získejte zdarma na console.groq.com")
model_provider = col_provider.selectbox("Poskytovatel:", ["Groq (Zdarma)", "OpenAI (Placené)"])

# Dynamický výběr modelu podle poskytovatele
if "Groq" in model_provider:
    selected_model = col_model.selectbox("Model:", [
        "llama-3.1-70b-versatile", 
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ], index=0)
else:
    selected_model = col_model.selectbox("Model:", ["gpt-4o-mini", "gpt-4o"], index=0)

if not api_key:
    st.info("Pro analýzu zpráv vložte API klíč. Doporučujeme [Groq](https://console.groq.com/keys) pro bleskové a bezplatné zpracování.")

# --- UI PRO VÝBĚR TICKERU ---
tickers = load_tickers()
tickers.sort()

c1, c2 = st.columns([1, 3])
vybrany_ticker = c1.selectbox("Zvolte ticker pro analýzu:", tickers)

@st.cache_data(ttl=600)
def fetch_news(ticker):
    news_list = []
    
    # 1. Primární metoda: Přímý přístup na Yahoo Finance RSS
    try:
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()
        
        root = ET.fromstring(xml_data)
        for item in root.findall('.//item')[:8]:
            title = item.find('title').text if item.find('title') is not None else "Bez titulku"
            link = item.find('link').text if item.find('link') is not None else "#"
            pubDate = item.find('pubDate').text if item.find('pubDate') is not None else "Neznámý čas"
            
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

    # 2. Záložní metoda: Standardní yfinance
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
                
            news_list.append({
                "title": title,
                "link": link,
                "publisher": publisher,
                "pub_time_str": pubDate
            })
    except:
        pass
        
    return news_list

def analyzuj_text(titulek, api_klic, provider, model_name):
    if "Groq" in provider:
        client = OpenAI(api_key=api_klic, base_url="https://api.groq.com/openai/v1")
    else:
        client = OpenAI(api_key=api_klic)

    prompt = f"""
    Jsi špičkový analytik hedgeového fondu. Analyzuj následující novinku o společnosti a vrať výsledek STRIKTNĚ jako validní JSON.
    Text zprávy: {titulek}
    
    Struktura JSONu:
    {{
        "co_se_stalo": "Stručné vysvětlení podstaty zprávy ve 2-3 větách česky.",
        "dopad_fundament": "Jak to ovlivní byznys model, cash-flow nebo DCF valuaci (česky).",
        "sentiment_skore": <číslo od -1.0 (silný propad/Risk-Off) do 1.0 (silný růst/Risk-On)>
    }}
    Neodpovídej nic jiného než čistý JSON formát.
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
    st.markdown(f"### Poslední katalyzátory a zprávy: **{vybrany_ticker}**")
    
    with st.spinner(f"Hledám katalyzátory pro {vybrany_ticker}..."):
        news_data = fetch_news(vybrany_ticker)
    
    if not news_data:
        st.warning("Žádné aktuální zprávy nebyly nalezeny. API Yahoo Finance momentálně neodpovídá.")
    else:
        for idx, article in enumerate(news_data):
            title = article.get("title", "Bez titulku")
            publisher = article.get("publisher", "Neznámý zdroj")
            link = article.get("link", "#")
            pub_time = article.get("pub_time_str", "Neznámý čas")
            
            with st.expander(f"📰 {pub_time} | {publisher}: {title}"):
                st.markdown(f"**Originál:** [{title}]({link})")
                
                if st.button(f"🧠 Analyzovat AI (Moodix Styl)", key=f"btn_{idx}"):
                    if not api_key:
                        st.error("Nejprve nahoře vložte API klíč.")
                    else:
                        with st.spinner("AI provádí kvantitativní a fundamentální syntézu..."):
                            analyza = analyzuj_text(title, api_key, model_provider, selected_model)
                            
                            if "error" in analyza:
                                st.error(f"Chyba AI: {analyza['error']}")
                            else:
                                st.markdown("---")
                                col_skore, col_text = st.columns([1, 4])
                                skore = float(analyza.get('sentiment_skore', 0))
                                
                                with col_skore:
                                    if skore > 0.2:
                                        st.metric("Sentiment", f"{skore:+.2f}", "Risk-On")
                                    elif skore < -0.2:
                                        st.metric("Sentiment", f"{skore:+.2f}", "-Risk-Off")
                                    else:
                                        st.metric("Sentiment", f"{skore:+.2f}", "Neutrální", delta_color="off")
                                
                                with col_text:
                                    st.markdown("#### CO SE STALO")
                                    st.info(analyza.get("co_se_stalo", ""))
                                    
                                    st.markdown("#### FUNDAMENTÁLNÍ DOPAD (DCF)")
                                    if skore > 0:
                                        st.success(analyza.get("dopad_fundament", ""))
                                    elif skore < 0:
                                        st.error(analyza.get("dopad_fundament", ""))
                                    else:
                                        st.warning(analyza.get("dopad_fundament", ""))