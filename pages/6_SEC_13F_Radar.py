import streamlit as st
import pandas as pd
import requests
import cloudscraper
from bs4 import BeautifulSoup
import json
import os
import sys
import base64
import time
import re

# --- CENTRÁLNÍ PAMĚŤ A MENU ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)
WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")

st.set_page_config(page_title="SEC 13F Radar", page_icon="🏛️", layout="wide")
import menu
menu.vykresli_menu() 

# Přesný formát, který SEC vyžaduje, aby tě neblokovali
SEC_HEADERS = {
    "User-Agent": "PokornyTerminal pokornyl98@gmail.com",
    "Accept-Encoding": "gzip, deflate"
} 

# Tímto nasadíme na aplikaci masku skutečného prohlížeče
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

t = {
    "CZ": {
        "title": "🏛️ SEC EDGAR 13F Radar", "desc": "Živá vládní data z EDGAR (Chytrý extraktor).", "exp_feed": "🔥 Live Feed z trhu", "btn_feed": "Stáhnout 40 reportů",
        "spin_feed": "Stahuji...", "sel_fund": "Vyber Fond:", "cik_input": "Zadej CIK:", "name_input": "Název pro uložení:",
        "btn_save": "💾 Uložit na Cloud", "succ_save": "✅ Uloženo!", "btn_down": "Stáhnout Data",
        "err_no13f": "❌ Žádný report nebyl nalezen.", "err_xml": "❌ Nelze přečíst data z reportu.", "succ_down": "✅ Nalezeno."
    },
    "EN": {
        "title": "🏛️ SEC EDGAR 13F Radar", "desc": "Live government data from EDGAR (Smart Extractor).", "exp_feed": "🔥 Live Market Feed", "btn_feed": "Download 40 reports",
        "spin_feed": "Downloading...", "sel_fund": "Select Fund:", "cik_input": "Enter CIK:", "name_input": "Name to save:",
        "btn_save": "💾 Save to Cloud", "succ_save": "✅ Saved!", "btn_down": "Download Data",
        "err_no13f": "❌ No report found.", "err_xml": "❌ Cannot read data.", "succ_down": "✅ Found."
    }
}
_ = t.get(st.session_state.lang, t["CZ"])

st.title(_["title"])
st.markdown(_["desc"])

def save_data(data):
    with open(WATCHLIST_FILE, "w") as f: json.dump(data, f, indent=4)
    try:
        if "GITHUB_TOKEN" in st.secrets:
            token, owner, repo = st.secrets["GITHUB_TOKEN"], st.secrets["GITHUB_OWNER"], st.secrets["GITHUB_REPO"]
            url, headers = f"https://api.github.com/repos/{owner}/{repo}/contents/watchlist.json", {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
            sha = requests.get(url, headers=headers).json().get("sha")
            payload = {"message": "Cloud sync SEC 13F CIK", "content": base64.b64encode(json.dumps(data, indent=4).encode("utf-8")).decode("utf-8"), "branch": "main"}
            if sha: payload["sha"] = sha
            requests.put(url, headers=headers, json=payload)
    except Exception: pass

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, "r") as f: return json.load(f)
    return {"saved_ciks": {}}

data = load_watchlist()
if "saved_ciks" not in data: data["saved_ciks"] = {}

SUPERINVESTORS = {
    "Warren Buffett (Berkshire Hathaway)": "1067983",
    "Michael Burry (Scion Asset Management)": "1649339",
    "Stanley Druckenmiller (Duquesne)": "1502579",
    "Chris Hohn (TCI Fund Management)": "1642871",
    "Bill Ackman (Pershing Square)": "1336528",
    "Ray Dalio (Bridgewater Associates)": "1350694",
    "David Tepper (Appaloosa)": "1009207",
    "Seth Klarman (Baupost Group)": "1061768",
    "Jim Simons (Renaissance Technologies)": "1037389",
    "Carl Icahn (Icahn Capital)": "921669"
}
SUPERINVESTORS.update(data["saved_ciks"])
SUPERINVESTORS["🔍 Jiný fond (Zadat CIK manuálně)"] = "CUSTOM"

with st.expander(_["exp_feed"]):
    if st.button(_["btn_feed"]):
        with st.spinner(_["spin_feed"]):
            res = scraper.get("https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=13F-HR&count=40&output=atom", headers=SEC_HEADERS)
            if res.status_code == 200:
                feed = [{"Datum": e.find('updated').text[:10], "Fond": e.find('title').text.split('-')[0].strip()} for e in BeautifulSoup(res.content, 'xml').find_all('entry')]
                st.dataframe(pd.DataFrame(feed), use_container_width=True)
            else:
                st.error("❌ SEC tě dočasně zablokoval na 10 minut za rychlé klikání. Zkus to později.")

col1, col2, col3 = st.columns([2, 2, 1])
with col1: vyber = st.selectbox(_["sel_fund"], list(SUPERINVESTORS.keys()))
with col2:
    if SUPERINVESTORS[vyber] == "CUSTOM": cik_input, novy_nazev = st.text_input(_["cik_input"], "").strip(), st.text_input(_["name_input"], "").strip()
    else: cik_input, novy_nazev = SUPERINVESTORS[vyber], ""
with col3:
    if SUPERINVESTORS[vyber] == "CUSTOM" and cik_input and novy_nazev and st.button(_["btn_save"]):
        data["saved_ciks"][novy_nazev] = cik_input
        save_data(data); st.success(_["succ_save"]); st.rerun()

if st.button(_["btn_down"], type="primary"):
    cik = cik_input.zfill(10)
    with st.spinner("Pátrám v hlubinách SEC EDGAR (Bypass režim)..."):
        time.sleep(1) # Extra pauza proti zablokování
        
        url_json = f"https://data.sec.gov/submissions/CIK{cik}.json"
        res = scraper.get(url_json, headers=SEC_HEADERS)
        
        # Detekce blokace od vlády
        if res.status_code == 403 or res.status_code == 429:
            st.error("🚨 OCHRANA SEC: Americká vláda zablokovala tvou IP adresu na 10 minut za rychlé klikání. Běž si uvařit kávu a zkus to za chvíli!")
            st.stop()
            
        if res.status_code == 200:
            filings = res.json().get("filings", {}).get("recent", {})
            hr_indices = [i for i, f in enumerate(filings.get("form", [])) if "13F" in str(f).upper() and "NT" not in str(f).upper()]
            
            if hr_indices:
                acc_no_hyphens = filings['accessionNumber'][hr_indices[0]]
                acc_no_clean = acc_no_hyphens.replace('-', '')
                
                # CHYTRÝ KROK: Místo hádání jména XML se podíváme přímo do indexu složky na serveru!
                idx_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no_clean}/index.json"
                idx_res = scraper.get(idx_url, headers=SEC_HEADERS)
                
                xml_filename = None
                if idx_res.status_code == 200:
                    files = idx_res.json().get("directory", {}).get("item", [])
                    for file in files:
                        name = file.get("name", "").lower()
                        # Hledáme soubor, který má příponu .xml a je to tabulka
                        if name.endswith(".xml") and ("table" in name or "info" in name or "13f" in name):
                            xml_filename = file.get("name")
                            if "table" in name: break # Ideální přesná shoda
                
                if not xml_filename: xml_filename = "infotable.xml" # Nouzová záloha
                
                xml_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no_clean}/{xml_filename}"
                xml_res = scraper.get(xml_url, headers=SEC_HEADERS)
                
                if xml_res.status_code == 200:
                    content = xml_res.text
                    
                    # REGEX: Nezničítejný textový rentgen, který vyseká akcie i z toho největšího chaosu
                    blocks = re.findall(r'(?is)<[^>]*?infoTable[^>]*>(.*?)</[^>]*?infoTable>', content)
                    
                    pos = []
                    for block in blocks:
                        issuer_match = re.search(r'(?is)<[^>]*?nameOfIssuer[^>]*>(.*?)</[^>]*?nameOfIssuer>', block)
                        value_match = re.search(r'(?is)<[^>]*?value[^>]*>(.*?)</[^>]*?value>', block)
                        
                        if issuer_match and value_match:
                            try:
                                issuer = issuer_match.group(1).strip()
                                val = float(value_match.group(1).strip().replace(',', '')) * 1000
                                pos.append({"Akcie": issuer, "Hodnota ($)": val})
                            except:
                                pass
                    
                    if pos:
                        df = pd.DataFrame(pos).groupby("Akcie").sum().reset_index()
                        df["%"] = (df["Hodnota ($)"] / df["Hodnota ($)"].sum()) * 100
                        st.success(f"✅ Staženo ze souboru: {xml_filename}")
                        st.dataframe(df.sort_values(by="%", ascending=False).style.format({"Hodnota ($)": "${:,.0f}", "%": "{:.2f}%"}), use_container_width=True)
                    else:
                        st.error("❌ Nalezený XML soubor je pravděpodobně prázdný, nebo fond požádal o utajení pozic.")
                else:
                    st.error("❌ Nepodařilo se stáhnout tabulku s pozicemi.")
            else:
                st.error("❌ Tento fond za poslední období nepodal žádný 13F formulář (nebo používá jiné CIK).")
        else:
            st.error("❌ API americké vlády neodpovídá.")
