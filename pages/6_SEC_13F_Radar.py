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

SEC_HEADERS = {
    "User-Agent": "PokornyTerminal pokornyl98@gmail.com",
    "Accept-Encoding": "gzip, deflate"
} 
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

t = {
    "CZ": {
        "title": "🏛️ SEC EDGAR 13F Radar", "desc": "Živá vládní data z EDGAR (Klon Dataromy).", "exp_feed": "🔥 Live Feed z trhu",
        "btn_feed": "Stáhnout 40 reportů", "spin_feed": "Stahuji...", "sel_fund": "Vyber Fond:", "cik_input": "Zadej CIK:", 
        "name_input": "Název pro uložení:", "btn_save": "💾 Uložit nový fond na Cloud", "succ_save": "✅ Uloženo!", 
        "btn_down": "Stáhnout Data", "err_no13f": "❌ Žádný report nebyl nalezen.", "err_xml": "❌ Nelze přečíst data z reportu.", 
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

def preved_na_kvartal(datum_str):
    if not datum_str or len(datum_str) < 10: return "Neznámý kvartál"
    rok = datum_str[:4]
    mesic = datum_str[5:7]
    if mesic in ['01', '02', '03']: return f"Q1 {rok}"
    if mesic in ['04', '05', '06']: return f"Q2 {rok}"
    if mesic in ['07', '08', '09']: return f"Q3 {rok}"
    if mesic in ['10', '11', '12']: return f"Q4 {rok}"
    return datum_str

PREDEFINED_FUNDS = {
    "Warren Buffett (Berkshire Hathaway)": "1067983",
    "Michael Burry (Scion Asset Management)": "1649339",
    "Stanley Druckenmiller (Duquesne Family Office)": "1536411",
    "Chris Hohn (TCI Fund Management)": "1647251",
    "Bill Ackman (Pershing Square)": "0002026053",  # ZDE JE TVÉ NOVÉ CIK
    "Ray Dalio (Bridgewater Associates)": "1350694",
    "David Tepper (Appaloosa)": "1009207",
    "Seth Klarman (Baupost Group)": "1061768",
    "Jim Simons (Renaissance Technologies)": "1037389",
    "Carl Icahn (Icahn Capital)": "921669"
}

ALL_FUNDS = PREDEFINED_FUNDS.copy()
ALL_FUNDS.update(data["saved_ciks"])
fund_names = sorted(list(ALL_FUNDS.keys()))

vychozi_vyber = [f for f in data["sec_favorites"] if f in fund_names]

with st.expander(_["exp_fav"], expanded=False):
    vybrani = st.multiselect(_["fav_lbl"], options=fund_names, default=vychozi_vyber)
    if st.button(_["save_fav"], use_container_width=True):
        data["sec_favorites"] = vybrani
        save_data(data)
        st.rerun()

st.markdown("---")
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

def get_13f_df(cik, acc_no_hyphens):
    acc_no_clean = acc_no_hyphens.replace('-', '')
    txt_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no_clean}/{acc_no_hyphens}.txt"
    txt_res = scraper.get(txt_url, headers=SEC_HEADERS)
    if txt_res.status_code == 200:
        blocks = re.findall(r'(?is)<[^>]*?infoTable[^>]*>(.*?)</[^>]*?infoTable>', txt_res.text)
        pos = []
        for block in blocks:
            issuer = re.search(r'(?is)<[^>]*?nameOfIssuer[^>]*>(.*?)</[^>]*?nameOfIssuer>', block)
            val = re.search(r'(?is)<[^>]*?value[^>]*>(.*?)</[^>]*?value>', block)
            shares = re.search(r'(?is)<[^>]*?sshPrnamt[^>]*>(.*?)</[^>]*?sshPrnamt>', block)
            if issuer and val and shares:
                try:
                    pos.append({
                        "Stock": issuer.group(1).strip().upper(), 
                        "Value": float(val.group(1).strip().replace(',', '')) * 1000,
                        "Shares": float(shares.group(1).strip().replace(',', ''))
                    })
                except: pass
        if pos:
            return pd.DataFrame(pos).groupby("Stock").sum().reset_index()
    return None

if st.button(_["btn_down"], type="primary"):
    cik = cik_input.zfill(10)
    with st.spinner("Pátrám v hlubinách a transformuji do Dataroma Designu..."):
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
            filing_dates = recent.get("filingDate", [])
            
            valid_filings = []
            for i in range(len(forms)):
                f_type = str(forms[i]).upper()
                if "13F" in f_type and "NT" not in f_type:
                    r_date = report_dates[i] if (i < len(report_dates) and report_dates[i]) else (filing_dates[i] if i < len(filing_dates) else "1900-01-01")
                    valid_filings.append({"acc_num": acc_nums[i], "report_date": r_date, "filing_date": filing_dates[i]})
            
            if valid_filings:
                valid_filings.sort(key=lambda x: x["filing_date"], reverse=True)
                unique_quarters = {}
                for f in valid_filings:
                    if f["report_date"] not in unique_quarters:
                        unique_quarters[f["report_date"]] = f
                
                sorted_quarters = sorted(list(unique_quarters.values()), key=lambda x: x["report_date"], reverse=True)
                
                latest_filing = sorted_quarters[0]
                df_latest = get_13f_df(cik, latest_filing["acc_num"])
                
                if df_latest is not None and not df_latest.empty:
                    df_latest["% of Portfolio"] = (df_latest["Value"] / df_latest["Value"].sum()) * 100
                    df_latest["ReportedPrice*"] = df_latest.apply(lambda r: (r["Value"] / r["Shares"]) if r["Shares"] > 0 else 0, axis=1)
                    df_latest["RecentActivity"] = ""
                    
                    if len(sorted_quarters) > 1:
                        prev_filing = sorted_quarters[1]
                        df_prev = get_13f_df(cik, prev_filing["acc_num"])
                        
                        if df_prev is not None and not df_prev.empty:
                            df_merged = pd.merge(df_latest, df_prev[["Stock", "Shares"]], on="Stock", how="left", suffixes=("", "_prev"))
                            
                            def calc_activity(row):
                                if pd.isna(row["Shares_prev"]) or row["Shares_prev"] == 0:
                                    return "Buy 100%"
                                diff = row["Shares"] - row["Shares_prev"]
                                if diff == 0: return ""
                                
                                pct_change = (diff / row["Shares_prev"]) * 100
                                if pct_change > 0: return f"Add {pct_change:,.2f}%"
                                else: return f"Reduce {abs(pct_change):,.2f}%"
                                
                            df_latest["RecentActivity"] = df_merged.apply(calc_activity, axis=1)
                    
                    df_latest["Current Price"] = "N/A"
                    df_latest["+/-Reported Price"] = "N/A"
                    
                    final_cols = ["Stock", "% of Portfolio", "RecentActivity", "Shares", "ReportedPrice*", "Value", "Current Price", "+/-Reported Price"]
                    df_final = df_latest[final_cols].sort_values(by="% of Portfolio", ascending=False)
                    
                    def style_activity(val):
                        v = str(val)
                        if "Buy" in v or "Add" in v: return 'color: #00ff00;'
                        if "Reduce" in v: return 'color: #ff4b4b;'
                        return 'color: gray;'
                        
                    styled_df = df_final.style.format({
                        "% of Portfolio": "{:.2f}%",
                        "Shares": "{:,.0f}",
                        "ReportedPrice*": "${:,.2f}",
                        "Value": "${:,.0f}"
                    }).map(style_activity, subset=["RecentActivity"])
                    
                    kvartal = preved_na_kvartal(latest_filing['report_date'])
                    st.success(f"✅ Stažen report pro: **{vyber.split('(')[0].strip()}** | {kvartal} (Reportováno ke dni {latest_filing['report_date']})")
                    st.dataframe(styled_df, use_container_width=True)
                else: st.error(_["err_xml"])
            else: st.error(_["err_no13f"])
        else: st.error("❌ Nelze se připojit na SEC API.")
