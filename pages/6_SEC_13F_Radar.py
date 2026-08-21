import streamlit as st
import pandas as pd
import requests
import cloudscraper
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

# Přesný formát, který SEC vyžaduje (jinak dává okamžitý ban)
SEC_HEADERS = {
    "User-Agent": "PokornyTerminal pokornyl98@gmail.com",
    "Accept-Encoding": "gzip, deflate"
} 
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

t = {
    "CZ": {
        "title": "🏛️ SEC EDGAR 13F Radar", "desc": "Živá vládní data z EDGAR (Anti-Ban verze).", "exp_feed": "🔥 Live Feed z trhu", "btn_feed": "Stáhnout 40 reportů",
        "spin_feed": "Stahuji...", "sel_fund": "Vyber Fond:", "cik_input": "Zadej CIK:", "name_input": "Název pro uložení:",
        "btn_save": "💾 Uložit na Cloud", "succ_save": "✅ Uloženo!", "btn_down": "Stáhnout Data",
        "err_no13f": "❌ Žádný report nebyl nalezen (fond asi ještě nepodal 13F).", "err_xml": "❌ Nelze přečíst data z reportu.", "succ_down": "✅ Nalezeno."
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

# Opravené CIK kódy aktuálních fondů
SUPERINVESTORS = {
    "Warren Buffett (Berkshire Hathaway)": "1067983",
    "Michael Burry (Scion Asset Management)": "1649339",
    "Stanley Druckenmiller (Duquesne Family Office)": "1536411",
    "Chris Hohn (TCI Fund Management)": "1647251",
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
                feed = [{"Datum": e.split('<updated>')[1][:10], "Fond": e.split('<title>')[1].split('-')[0].strip()} for e in res.text.split('<entry>')[1:]]
                st.dataframe(pd.DataFrame(feed), use_container_width=True)

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
    with st.spinner("Pátrám v hlubinách SEC EDGAR..."):
        time.sleep(0.5) 
        res = scraper.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=SEC_HEADERS)
        
        if res.status_code in [403, 429]:
            st.error("🚨 OCHRANA SEC: Tvoje IP je dočasně zablokovaná za rychlé klikání. Připoj PC na minutu přes Hotspot z mobilu, nebo chvíli počkej.")
            st.stop()
            
        if res.status_code == 200:
            filings = res.json().get("filings", {}).get("recent", {})
            hr_indices = [i for i, f in enumerate(filings.get("form", [])) if "13F" in str(f).upper() and "NT" not in str(f).upper()]
            
            if hr_indices:
                acc_no_hyphens = filings['accessionNumber'][hr_indices[0]]
                acc_no_clean = acc_no_hyphens.replace('-', '')
                
                txt_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no_clean}/{acc_no_hyphens}.txt"
                txt_res = scraper.get(txt_url, headers=SEC_HEADERS)
                
                if txt_res.status_code == 200:
                    # Nezničítejný Regex Rentgen
                    blocks = re.findall(r'(?is)<[^>]*?infoTable[^>]*>(.*?)</[^>]*?infoTable>', txt_res.text)
                    pos = []
                    for block in blocks:
                        issuer = re.search(r'(?is)<[^>]*?nameOfIssuer[^>]*>(.*?)</[^>]*?nameOfIssuer>', block)
                        val = re.search(r'(?is)<[^>]*?value[^>]*>(.*?)</[^>]*?value>', block)
                        if issuer and val:
                            try:
                                pos.append({"Akcie": issuer.group(1).strip(), "Hodnota ($)": float(val.group(1).strip().replace(',', '')) * 1000})
                            except: pass
                    
                    if pos:
                        df = pd.DataFrame(pos).groupby("Akcie").sum().reset_index()
                        df["%"] = (df["Hodnota ($)"] / df["Hodnota ($)"].sum()) * 100
                        st.success(_["succ_down"])
                        st.dataframe(df.sort_values(by="%", ascending=False).style.format({"Hodnota ($)": "${:,.0f}", "%": "{:.2f}%"}), use_container_width=True)
                    else: st.error(_["err_xml"])
                else: st.error("❌ Master soubor nelze stáhnout.")
            else: st.error(_["err_no13f"])
        else: st.error("❌ Nelze se připojit na SEC API.")
