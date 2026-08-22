import streamlit as st
import pandas as pd
import json
import os
import sys

# --- INITIAL SETUP ---
st.set_page_config(page_title="POKORNY TERMINAL | SEC 13F", layout="wide", initial_sidebar_state="collapsed")

# --- DIRECTORY MANAGEMENT ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)
WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")
SEC_DATA_DIR = os.path.join(hlavni_slozka, "sec_data")

try:
    import sec_updater
except: pass

import menu
menu.vykresli_menu() 

# --- DICTIONARY ---
t = {
    "CZ": {
        "title": "SEC 13F RADAR (SUPERINVESTOŘI)",
        "desc": "BLESKOVÉ NAČÍTÁNÍ HISTORICKÝCH DAT PORTFOLIÍ PŘÍMO ZE SEC EDGAR.",
        "exp": "SYSTÉMOVÁ KONFIGURACE: OBLÍBENÍ",
        "fav": "OBLÍBENÍ SUPERINVESTOŘI:",
        "save_cloud": "ULOŽIT ZMĚNY",
        "show_all": "ZOBRAZIT VŠECHNY Z DATABÁZE",
        "sel_inv": "VÝBĚR SUPERINVESTORA",
        "manual_opt": "VLASTNÍ FOND (ZADAT CIK MANUÁLNĚ)",
        "cik_lbl": "CIK KÓD:",
        "name_lbl": "NÁZEV FONDU:",
        "save_new": "ULOŽIT NOVÝ FOND",
        "succ_save": "SYSTÉM AKTUALIZOVÁN.",
        "btn_upd": "VYNUTIT AKTUALIZACI (SEC)",
        "spin_upd": "STAHOVÁNÍ ČERSTVÝCH DAT PŘÍMO ZE SEC...",
        "warn_nodata": "DATA PRO TOHOTO INVESTORA NEJSOU STAŽENA. KLIKNĚTE NA 'VYNUTIT AKTUALIZACI' NEBO SPUSŤTE FÁZI 2 V CENTRU AKTUALIZACÍ."
    },
    "EN": {
        "title": "SEC 13F RADAR (SUPERINVESTORS)",
        "desc": "LIGHTNING FAST HISTORICAL PORTFOLIO DATA FROM SEC EDGAR.",
        "exp": "SYSTEM CONFIG: FAVORITES",
        "fav": "FAVORITE SUPERINVESTORS:",
        "save_cloud": "COMMIT CHANGES",
        "show_all": "SHOW ALL FROM DATABASE",
        "sel_inv": "SELECT SUPERINVESTOR",
        "manual_opt": "CUSTOM FUND (MANUAL CIK ENTRY)",
        "cik_lbl": "CIK CODE:",
        "name_lbl": "FUND NAME:",
        "save_new": "COMMIT NEW FUND",
        "succ_save": "SYSTEM UPDATED.",
        "btn_upd": "FORCE UPDATE (SEC)",
        "spin_upd": "DOWNLOADING FRESH DATA FROM SEC...",
        "warn_nodata": "DATA FOR THIS INVESTOR NOT DOWNLOADED YET. CLICK 'FORCE UPDATE' OR RUN PHASE 2 IN THE UPDATE CENTER."
    }
}
_ = t.get(st.session_state.get("lang", "CZ"), t["CZ"])

st.title(_["title"])
st.caption(_["desc"])

def save_data(data):
    with open(WATCHLIST_FILE, "w") as f: json.dump(data, f, indent=4)

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r") as f: return json.load(f)
        except: pass
    return {"saved_ciks": {}, "sec_favorites": []}

data = load_watchlist()
if "saved_ciks" not in data: data["saved_ciks"] = {}
if "sec_favorites" not in data: data["sec_favorites"] = []

PREDEFINED_FUNDS = {
    "Warren Buffett (Berkshire Hathaway)": "1067983",
    "Michael Burry (Scion Asset Management)": "1649339",
    "Stanley Druckenmiller (Duquesne Family Office)": "1536411",
    "Chris Hohn (TCI Fund Management)": "1647251",
    "Bill Ackman (Pershing Square)": "0002026053",
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

with st.expander(_["exp"], expanded=False):
    vybrani = st.multiselect(_["fav"], options=fund_names, default=vychozi_vyber)
    if st.button(_["save_cloud"], use_container_width=True):
        data["sec_favorites"] = vybrani
        save_data(data)
        st.rerun()

st.markdown("---")

c1, c2 = st.columns([1, 4])
with c1:
    st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
    zobrazit_vse = st.checkbox(_["show_all"], value=False if vychozi_vyber else True)
    
nabidka = fund_names if (not vychozi_vyber or zobrazit_vse) else vychozi_vyber
nabidka.append(_["manual_opt"])

with c2:
    vyber = st.selectbox(_["sel_inv"], nabidka)

if vyber == _["manual_opt"]:
    m1, m2, m3 = st.columns([2, 2, 1])
    with m1: cik_input = st.text_input(_["cik_lbl"], "").strip()
    with m2: novy_nazev = st.text_input(_["name_lbl"], "").strip()
    with m3:
        st.markdown("<br>", unsafe_allow_html=True)
        if cik_input and novy_nazev and st.button(_["save_new"], use_container_width=True):
            data["saved_ciks"][novy_nazev] = cik_input
            save_data(data)
            st.success(_["succ_save"])
            st.rerun()
else:
    cik = str(ALL_FUNDS[vyber]).zfill(10)
    csv_path = os.path.join(SEC_DATA_DIR, f"{cik}.csv")
    meta_path = os.path.join(SEC_DATA_DIR, f"{cik}_meta.json")
    
    st.markdown("<br>", unsafe_allow_html=True)
    c_upd = st.columns([4, 1])[1]
    with c_upd:
        if st.button(_["btn_upd"], use_container_width=True):
            with st.spinner(_["spin_upd"]):
                sec_updater.update_sec_funds(target_cik=cik)
            st.rerun()
            
    if os.path.exists(csv_path) and os.path.exists(meta_path):
        with open(meta_path, "r") as f: meta = json.load(f)
        
        # Překlad hlavičky na EN/CZ
        rep_str = "Reported:" if st.session_state.get("lang") == "EN" else "Zobrazen report:"
        asof_str = "As of" if st.session_state.get("lang") == "EN" else "Ke dni"
        last_str = "Last updated:" if st.session_state.get("lang") == "EN" else "Naposledy staženo:"
        
        st.info(f"**{vyber.split('(')[0].strip()}** | {rep_str} **{meta['kvartal']}** ({asof_str} {meta['report_date']}) | *{last_str} {meta['last_updated']}*")
        
        df = pd.read_csv(csv_path)
        df[" "] = "" 
        
        def style_df(row):
            styles = [''] * len(row)
            act_val = str(row['RecentActivity'])
            if "Buy" in act_val or "Add" in act_val or "New" in act_val: styles[2] = 'color: #26A69A; font-weight: bold;'
            elif "Reduce" in act_val or "Sell" in act_val: styles[2] = 'color: #EF5350; font-weight: bold;'
            
            if pd.notnull(row['+/-Reported Price']):
                try:
                    val = float(row['+/-Reported Price'])
                    if val > 0: styles[8] = 'color: #26A69A;' 
                    elif val < 0: styles[8] = 'color: #EF5350;'
                except: pass
            return styles
            
        styled_df = df.style.apply(style_df, axis=1).format({
            "% of Portfolio": "{:.2f}%",
            "Shares": "{:,.0f}",
            "ReportedPrice*": "${:,.2f}",
            "Value": "${:,.0f}",
            "Current Price": lambda x: f"${x:,.2f}" if pd.notnull(x) else "",
            "+/-Reported Price": lambda x: f"{x:+.2f}%" if pd.notnull(x) else "",
            "52Week Low": lambda x: f"${x:,.2f}" if pd.notnull(x) else "",
            "52Week High": lambda x: f"${x:,.2f}" if pd.notnull(x) else ""
        })
        
        st.dataframe(styled_df, use_container_width=True, hide_index=True, height=650)
    else:
        st.warning(_["warn_nodata"])
