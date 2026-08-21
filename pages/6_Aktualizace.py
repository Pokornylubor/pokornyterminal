import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import json
import os
import sys

# --- CENTRÁLNÍ PAMĚŤ A MENU ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)
WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")

st.set_page_config(page_title="SEC 13F Radar", page_icon="🏛️", layout="wide")
import menu
menu.vykresli_menu() 

SEC_HEADERS = {"User-Agent": "Lubor Pokorny (pokornyl98@gmail.com)"} 

t = {
    "CZ": {
        "title": "🏛️ SEC EDGAR 13F Radar", "desc": "Živá vládní data z EDGAR.", "exp_feed": "🔥 Live Feed z trhu", "btn_feed": "Stáhnout 40 reportů",
        "spin_feed": "Stahuji...", "sel_fund": "Vyber Fond:", "cik_input": "Zadej CIK:", "name_input": "Název pro uložení:",
        "btn_save": "💾 Uložit do paměti", "succ_save": "✅ Uloženo!", "btn_down": "Stáhnout Data",
        "err_no13f": "Žádný report.", "err_xml": "Nelze přečíst XML.", "succ_down": "✅ Nalezeno."
    },
    "EN": {
        "title": "🏛️ SEC EDGAR 13F Radar", "desc": "Live government data from EDGAR.", "exp_feed": "🔥 Live Market Feed", "btn_feed": "Download 40 reports",
        "spin_feed": "Downloading...", "sel_fund": "Select Fund:", "cik_input": "Enter CIK:", "name_input": "Name to save:",
        "btn_save": "💾 Save", "succ_save": "✅ Saved!", "btn_down": "Download Data",
        "err_no13f": "No report.", "err_xml": "Cannot read XML.", "succ_down": "✅ Found."
    }
}
_ = t.get(st.session_state.lang, t["CZ"])

st.title(_["title"])
st.markdown(_["desc"])

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, "r") as f: return json.load(f)
    return {"saved_ciks": {}}

def save_watchlist(data):
    with open(WATCHLIST_FILE, "w") as f: json.dump(data, f, indent=4)

data = load_watchlist()
if "saved_ciks" not in data: data["saved_ciks"] = {}

SUPERINVESTORS = {"Warren Buffett (Berkshire)": "1067983", "Michael Burry (Scion)": "1649339"}
SUPERINVESTORS.update(data["saved_ciks"])
SUPERINVESTORS["🔍 Jiný fond (CIK)"] = "CUSTOM"

with st.expander(_["exp_feed"]):
    if st.button(_["btn_feed"]):
        with st.spinner(_["spin_feed"]):
            res = requests.get("https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=13F-HR&count=40&output=atom", headers=SEC_HEADERS)
            if res.status_code == 200:
                feed = [{"Datum": e.find('updated').text[:10], "Fond": e.find('title').text.split('-')[0].strip()} for e in BeautifulSoup(res.content, 'xml').find_all('entry')]
                st.dataframe(pd.DataFrame(feed), use_container_width=True)

col1, col2, col3 = st.columns([2, 2, 1])
with col1: vyber = st.selectbox(_["sel_fund"], list(SUPERINVESTORS.keys()))
with col2:
    if SUPERINVESTORS[vyber] == "CUSTOM": cik_input = st.text_input(_["cik_input"], "").strip(); novy_nazev = st.text_input(_["name_input"], "").strip()
    else: cik_input = SUPERINVESTORS[vyber]; novy_nazev = ""
with col3:
    if SUPERINVESTORS[vyber] == "CUSTOM" and cik_input and novy_nazev and st.button(_["btn_save"]):
        data["saved_ciks"][novy_nazev] = cik_input
        save_watchlist(data); st.success(_["succ_save"]); st.rerun()

def parse_13f_xml(cik, acc):
    url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/infotable.xml"
    res = requests.get(url, headers=SEC_HEADERS)
    if res.status_code == 200:
        pos = [{"Akcie": i.find('nameOfIssuer').text, "Hodnota ($)": float(i.find('value').text)*1000} for i in BeautifulSoup(res.content, 'xml').find_all('infoTable') if i.find('nameOfIssuer')]
        return pd.DataFrame(pos).groupby("Akcie").sum().reset_index() if pos else pd.DataFrame()
    return pd.DataFrame()

if st.button(_["btn_down"], type="primary"):
    cik = cik_input.zfill(10)
    with st.spinner("..."):
        res = requests.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=SEC_HEADERS)
        if res.status_code == 200:
            filings = res.json().get("filings", {}).get("recent", {})
            hr_indices = [i for i, f in enumerate(filings.get("form", [])) if "13F-HR" in f]
            if hr_indices:
                df = parse_13f_xml(cik, filings["accessionNumber"][hr_indices[0]].replace("-", ""))
                if not df.empty:
                    df["%"] = (df["Hodnota ($)"] / df["Hodnota ($)"].sum()) * 100
                    st.success(_["succ_down"])
                    st.dataframe(df.sort_values(by="%", ascending=False).style.format({"Hodnota ($)": "${:,.0f}", "%": "{:.2f}%"}), use_container_width=True)
