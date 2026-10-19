import streamlit as st
import pandas as pd
import json
import os
import sys
import subprocess

# --- INITIAL SETUP ---
st.set_page_config(page_title="POKORNY TERMINAL | 13F REPORTY", layout="wide", initial_sidebar_state="collapsed")

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
        "title": "SEC 13F REPORTY",
        "desc": "BLESKOVÉ NAČÍTÁNÍ HISTORICKÝCH DAT PORTFOLIÍ PŘÍMO ZE SEC EDGAR.",
        "exp_db": "⚙️ SPRÁVA DATABÁZE (PŘIDAT / UPRAVIT / SMAZAT)",
        "sel_inv": "VÝBĚR 13F REPORTU (FONDU):",
        "cik_lbl": "CIK KÓD:",
        "name_lbl": "NÁZEV FONDU:",
        "save_new": "ULOŽIT NOVÝ FOND",
        "edit_btn": "ULOŽIT ÚPRAVY",
        "succ_save": "SYSTÉM AKTUALIZOVÁN A ULOŽEN NA GITHUB.",
        "succ_edit": "FOND BYL ÚSPĚŠNĚ UPRAVEN A ULOŽEN.",
        "btn_upd": "VYNUTIT AKTUALIZACI (SEC)",
        "spin_upd": "STAHOVÁNÍ ČERSTVÝCH DAT PŘÍMO ZE SEC...",
        "warn_nodata": "DATA PRO TENTO REPORT NEJSOU STAŽENA. KLIKNĚTE NA 'VYNUTIT AKTUALIZACI'."
    },
    "EN": {
        "title": "SEC 13F REPORTS",
        "desc": "LIGHTNING FAST HISTORICAL PORTFOLIO DATA FROM SEC EDGAR.",
        "exp_db": "⚙️ DATABASE MANAGEMENT (ADD / EDIT / DELETE)",
        "sel_inv": "SELECT 13F REPORT (FUND):",
        "cik_lbl": "CIK CODE:",
        "name_lbl": "FUND NAME:",
        "save_new": "COMMIT NEW FUND",
        "edit_btn": "SAVE EDITS",
        "succ_save": "SYSTEM UPDATED AND COMMITTED TO GITHUB.",
        "succ_edit": "FUND SUCCESSFULLY EDITED AND SAVED.",
        "btn_upd": "FORCE UPDATE (SEC)",
        "spin_upd": "DOWNLOADING FRESH DATA FROM SEC...",
        "warn_nodata": "DATA FOR THIS REPORT NOT DOWNLOADED YET. CLICK 'FORCE UPDATE'."
    }
}
_ = t.get(st.session_state.get("lang", "CZ"), t["CZ"])

st.title(_["title"])
st.caption(_["desc"])

def commit_watchlist_to_github():
    try:
        if "GITHUB_TOKEN" in st.secrets:
            token = st.secrets["GITHUB_TOKEN"]
            owner = st.secrets["GITHUB_OWNER"]
            repo = st.secrets["GITHUB_REPO"]
            remote_url = f"https://{owner}:{token}@github.com/{owner}/{repo}.git"
            
            subprocess.run(["git", "config", "--global", "user.email", "bot@pokornyterminal.cz"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "config", "--global", "user.name", "Terminal Bot"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "add", WATCHLIST_FILE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "commit", "-m", "Automatická úprava 13F watchlistu z mobilu"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "push", remote_url, "HEAD:main"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass 

def save_data(data):
    with open(WATCHLIST_FILE, "w", encoding="utf-8") as f: 
        json.dump(data, f, indent=4)
    commit_watchlist_to_github() 

def load_watchlist():
    data = {"saved_ciks": {}}
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f: 
                loaded_data = json.load(f)
                if "saved_ciks" in loaded_data: 
                    data["saved_ciks"] = loaded_data["saved_ciks"]
        except: pass
    return data

data = load_watchlist()
ALL_FUNDS = data["saved_ciks"]
fund_names = sorted(list(ALL_FUNDS.keys()))

# --- SEKCE SPRÁVY DATABÁZE ---
with st.expander(_["exp_db"], expanded=False):
    akce = st.radio("Zvolte operaci:", ["➕ Přidat", "✏️ Upravit", "🗑️ Smazat"], horizontal=True, label_visibility="collapsed")
    st.markdown("---")
    
    if akce == "➕ Přidat":
        cik_input = st.text_input(_["cik_lbl"], "").strip()
        novy_nazev = st.text_input(_["name_lbl"], "").strip()
        if cik_input and novy_nazev and st.button(_["save_new"], use_container_width=True):
            data["saved_ciks"][novy_nazev] = cik_input
            save_data(data)
            st.success(_["succ_save"])
            st.rerun()
            
    elif akce == "✏️ Upravit":
        if not fund_names:
            st.info("Databáze je prázdná.")
        else:
            fond_k_uprave = st.selectbox("Vyber fond k úpravě:", options=fund_names)
            if fond_k_uprave:
                aktualni_cik = str(ALL_FUNDS[fond_k_uprave])
                novy_cik = st.text_input(_["cik_lbl"], aktualni_cik).strip()
                novy_nazev = st.text_input(_["name_lbl"], fond_k_uprave).strip()
                if st.button(_["edit_btn"], use_container_width=True):
                    if novy_nazev and novy_cik:
                        if novy_nazev != fond_k_uprave:
                            del data["saved_ciks"][fond_k_uprave]
                        data["saved_ciks"][novy_nazev] = novy_cik
                        save_data(data)
                        st.success(_["succ_edit"])
                        st.rerun()
                    else:
                        st.warning("Název i CIK musí být vyplněny.")
                        
    elif akce == "🗑️ Smazat":
        if not fund_names:
            st.info("Databáze je prázdná.")
        else:
            fond_k_odstraneni = st.selectbox("Vyber fond k odstranění:", options=fund_names)
            if st.button("❌ TRVALE SMAZAT FOND", use_container_width=True):
                del data["saved_ciks"][fond_k_odstraneni]
                save_data(data)
                st.success(f"✅ Fond '{fond_k_odstraneni}' byl odstraněn.")
                st.rerun()

st.markdown("---")

# --- HLAVNÍ SEKCE ZOBRAZENÍ 13F PORTFOLIA ---
if not fund_names:
    st.info("Databáze je prázdná. Přidejte fond v sekci 'SPRÁVA DATABÁZE'.")
else:
    # Nový oddělený vyhledávač
    c_search, c_select = st.columns([1, 2])
    with c_search:
        hledani = st.text_input("🔍 Vyhledat report (napište název):", "")
    
    # Filtrace fondů podle vyhledávání
    nalezene_fondy = [f for f in fund_names if hledani.lower() in f.lower()]
    
    with c_select:
        if not nalezene_fondy:
            st.warning("Žádný report neodpovídá hledání.")
            vyber = None
        else:
            vyber = st.selectbox(_["sel_inv"], nalezene_fondy)

    if vyber:
        cik = str(ALL_FUNDS[vyber]).zfill(10)
        csv_path = os.path.join(SEC_DATA_DIR, f"{cik}.csv")
        meta_path = os.path.join(SEC_DATA_DIR, f"{cik}_meta.json")
        
        st.markdown("<br>", unsafe_allow_html=True)
        c_upd = st.columns([4, 1])[1]
        with c_upd:
            if st.button(_["btn_upd"], use_container_width=True):
                with st.spinner(_["spin_upd"]):
                    sec_updater.update_sec_funds(target_cik=cik)
                    try:
                        if "GITHUB_TOKEN" in st.secrets:
                            token = st.secrets["GITHUB_TOKEN"]
                            owner = st.secrets["GITHUB_OWNER"]
                            repo = st.secrets["GITHUB_REPO"]
                            remote_url = f"https://{owner}:{token}@github.com/{owner}/{repo}.git"
                            
                            subprocess.run(["git", "config", "--global", "user.email", "bot@pokornyterminal.cz"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            subprocess.run(["git", "config", "--global", "user.name", "Terminal Bot"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            subprocess.run(["git", "add", "sec_data/"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            subprocess.run(["git", "commit", "-m", f"Okamžité stažení 13F reportu (CIK: {cik}) z mobilu"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            subprocess.run(["git", "push", remote_url, "HEAD:main"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    except Exception: pass
                st.rerun()
                
        if os.path.exists(csv_path) and os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f: meta = json.load(f)
            
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