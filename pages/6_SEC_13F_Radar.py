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

# SEC vyžaduje striktní hlavičku (Jinak dává ban)
SEC_HEADERS = {
    "User-Agent": "PokornyTerminal pokornyl98@gmail.com",
    "Accept-Encoding": "gzip, deflate"
} 
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

t = {
    "CZ": {
        "title": "🏛️ SEC EDGAR 13F Radar", "desc": "Živá vládní data z EDGAR (Nejnovější kvartál).", "exp_feed": "🔥 Live Feed z trhu", "btn_feed": "Stáhnout 40 reportů",
        "spin_feed": "Stahuji...", "sel_fund": "Vyber Fond:", "cik_input": "Zadej CIK:", "name_input": "Název pro uložení:",
        "btn_save": "💾 Uložit nový fond na Cloud", "succ_save": "✅ Uloženo!", "btn_down": "Stáhnout Data",
        "err_no13f": "❌ Žádný report nebyl nalezen.", "err_xml": "❌ Nelze přečíst data z reportu.", 
        "succ_down": "✅ Nalezeno!", "exp_fav": "⭐ Nastavit oblíbené", "fav_lbl": "Moji oblíbenci:", 
        "save_fav": "💾 Uložit oblíbené na Cloud", "show_all": "Zobrazit všechny"
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
            payload = {"message": "Cloud sync SEC 13F Radar", "content": base64.b64encode(json.dumps(data, indent=4).encode("utf-8")).decode("utf-8"), "branch": "main"}
            if sha: payload["sha"] = sha
            requests.put(url, headers=headers, json=payload)
    except Exception: pass

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r") as f: return json.load(f)
        except: pass
    return {"saved_ciks": {}, "sec_favorites": []}

data = load_watchlist()
if "saved_ciks" not in data: data["saved_ciks"] = {}
if "sec_favorites" not in data: data["sec_favorites"] = []

# --- DATABÁZE FONDŮ ---
PREDEFINED_FUNDS = {
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

# Spojíme předpřipravené a tvoje vlastní
ALL_FUNDS = PREDEFINED_FUNDS.copy()
ALL_FUNDS.update(data["saved_ciks"])
fund_names = sorted(list(ALL_FUNDS.keys()))

# --- UI: OBLÍBENÍ (Stejné jako Dataroma) ---
vychozi_vyber = [f for f in data["sec_favorites"] if f in fund_names]

with st.expander(_["exp_fav"], expanded=False):
    vybrani = st.multiselect(_["fav_lbl"], options=fund_names, default=vychozi_vyber)
    if st.button(_["save_fav"], use_container_width=True):
        data["sec_favorites"] = vybrani
        save_data(data)
        st.rerun()

st.markdown("---")

# --- UI: VÝBĚR FONDU ---
zobrazit_vse = st.checkbox(_["show_all"], value=False)
nabidka = fund_names if (not vychozi_vyber or zobrazit_vse) else vychozi_vyber
nabidka.append("🔍 Jiný fond (Zadat CIK manuálně)")

vyber = st.selectbox(_["sel_fund"], nabidka)

if vyber == "🔍 Jiný fond (Zadat CIK manuálně)":
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1: cik_input = st.text_input(_["cik_input"], "").strip()
    with c2: novy_nazev = st.text_input(_["name_input"], "").strip()
    with c3:
        st.markdown("<br>", unsafe_allow_html=True)
        if cik_input and novy_nazev and st.button(_["btn_save"], use_container_width=True):
            data["saved_ciks"][novy_nazev] = cik_input
            save_data(data)
            st.success(_["succ_save"])
            st.rerun()
else:
    cik_input = ALL_FUNDS[vyber]

# --- STAHOVÁNÍ DAT ---
if st.button(_["btn_down"], type="primary"):
    cik = cik_input.zfill(10)
    with st.spinner("Pátrám po nejnovějším kvartálu..."):
        time.sleep(0.5)
        res = scraper.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=SEC_HEADERS)
        
        if res.status_code in [403, 429]:
            st.error("🚨 OCHRANA SEC: Tvoje IP je dočasně zablokovaná za rychlé klikání. Zkus to přes hotspot nebo počkej.")
            st.stop()
            
        if res.status_code == 200:
            recent = res.json().get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            acc_nums = recent.get("accessionNumber", [])
            report_dates = recent.get("reportDate", [])
            
            # Najdeme všechny 13F reporty a přidáme k nim datum reportu
            valid_filings = []
            for i in range(len(forms)):
                f_type = str(forms[i]).upper()
                if "13F" in f_type and "NT" not in f_type:
                    valid_filings.append({
                        "acc_num": acc_nums[i],
                        "report_date": report_dates[i] if i < len(report_dates) else "0000-00-00"
                    })
            
            if valid_filings:
                # SEŘAZENÍ: Vždy chronologicky podle data reportu (Nejnovější nahoře)
                valid_filings.sort(key=lambda x: x["report_date"], reverse=True)
                latest_filing = valid_filings[0]
                
                acc_no_hyphens = latest_filing["acc_num"]
                acc_no_clean = acc_no_hyphens.replace('-', '')
                
                txt_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no_clean}/{acc_no_hyphens}.txt"
                txt_res = scraper.get(txt_url, headers=SEC_HEADERS)
                
                if txt_res.status_code == 200:
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
                        
                        # Zobrazí jasný důkaz o tom, k jakému datu report skutečně je!
                        st.success(f"{_['succ_down']} Report ke dni: **{latest_filing['report_date']}**")
                        st.dataframe(df.sort_values(by="%", ascending=False).style.format({"Hodnota ($)": "${:,.0f}", "%": "{:.2f}%"}), use_container_width=True)
                    else: st.error(_["err_xml"])
                else: st.error("❌ Master soubor nelze stáhnout.")
            else: st.error(_["err_no13f"])
        else: st.error("❌ Nelze se připojit na SEC API.")
