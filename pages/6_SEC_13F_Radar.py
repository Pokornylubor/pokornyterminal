import streamlit as st
import pandas as pd
import json
import os
import sys
import subprocess

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
        "exp_db": "⚙️ SPRÁVA DATABÁZE (PŘIDAT / UPRAVIT / SMAZAT)",
        "fav": "OBLÍBENÍ SUPERINVESTOŘI:",
        "save_cloud": "ULOŽIT ZMĚNY",
        "show_all": "ZOBRAZIT VŠECHNY Z DATABÁZE",
        "sel_inv": "VÝBĚR SUPERINVESTORA",
        "cik_lbl": "CIK KÓD:",
        "name_lbl": "NÁZEV FONDU:",
        "save_new": "ULOŽIT NOVÝ FOND",
        "edit_btn": "ULOŽIT ÚPRAVY",
        "succ_save": "SYSTÉM AKTUALIZOVÁN A ULOŽEN NA GITHUB.",
        "succ_edit": "FOND BYL ÚSPĚŠNĚ UPRAVEN A ULOŽEN.",
        "btn_upd": "VYNUTIT AKTUALIZACI (SEC)",
        "spin_upd": "STAHOVÁNÍ ČERSTVÝCH DAT PŘÍMO ZE SEC...",
        "warn_nodata": "DATA PRO TOHOTO INVESTORA NEJSOU STAŽENA. KLIKNĚTE NA 'VYNUTIT AKTUALIZACI' NEBO SPUSŤTE FÁZI 3 V CENTRU AKTUALIZACÍ."
    },
    "EN": {
        "title": "SEC 13F RADAR (SUPERINVESTORS)",
        "desc": "LIGHTNING FAST HISTORICAL PORTFOLIO DATA FROM SEC EDGAR.",
        "exp": "SYSTEM CONFIG: FAVORITES",
        "exp_db": "⚙️ DATABASE MANAGEMENT (ADD / EDIT / DELETE)",
        "fav": "FAVORITE SUPERINVESTORS:",
        "save_cloud": "COMMIT CHANGES",
        "show_all": "SHOW ALL FROM DATABASE",
        "sel_inv": "SELECT SUPERINVESTOR",
        "cik_lbl": "CIK CODE:",
        "name_lbl": "FUND NAME:",
        "save_new": "COMMIT NEW FUND",
        "edit_btn": "SAVE EDITS",
        "succ_save": "SYSTEM UPDATED AND COMMITTED TO GITHUB.",
        "succ_edit": "FUND SUCCESSFULLY EDITED AND SAVED.",
        "btn_upd": "FORCE UPDATE (SEC)",
        "spin_upd": "DOWNLOADING FRESH DATA FROM SEC...",
        "warn_nodata": "DATA FOR THIS INVESTOR NOT DOWNLOADED YET. CLICK 'FORCE UPDATE' OR RUN PHASE 2 IN THE UPDATE CENTER."
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
            subprocess.run(["git", "commit", "-m", "Automatická úprava watchlistu z mobilu"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "push", remote_url, "HEAD:main"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass 

def save_data(data):
    with open(WATCHLIST_FILE, "w", encoding="utf-8") as f: 
        json.dump(data, f, indent=4)
    commit_watchlist_to_github() 

def load_watchlist():
    data = {"saved_ciks": {}, "sec_favorites": []}
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f: 
                loaded_data = json.load(f)
                if "saved_ciks" in loaded_data: data["saved_ciks"] = loaded_data["saved_ciks"]
                if "sec_favorites" in loaded_data: data["sec_favorites"] = loaded_data["sec_favorites"]
        except: pass
    return data

data = load_watchlist()
ALL_FUNDS = data["saved_ciks"]
fund_names = sorted(list(ALL_FUNDS.keys()))
vychozi_vyber = [f for f in data["sec_favorites"] if f in fund_names]

# --- SEKCE NASTAVENÍ (HORNÍ LIŠTY) ---
col_exp1, col_exp2 = st.columns(2)

with col_exp1:
    with st.expander(_["exp"], expanded=False):
        vybrani = st.multiselect(_["fav"], options=fund_names, default=vychozi_vyber)
        if st.button(_["save_cloud"], use_container_width=True):
            data["sec_favorites"] = vybrani
            save_data(data)
            st.rerun()

with col_exp2:
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
                                data["sec_favorites"] = [novy_nazev if f == fond_k_uprave else f for f in data["sec_favorites"]]
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
                    if fond_k_odstraneni in data["sec_favorites"]:
                        data["sec_favorites"].remove(fond_k_odstraneni)
                    save_data(data)
                    st.success(f"✅ Fond '{fond_k_odstraneni}' byl odstraněn.")
                    st.rerun()

st.markdown("---")

# --- HLAVNÍ SEKCE ZOBRAZENÍ PORTFOLIA ---
c1, c2 = st.columns([1, 4])
with c1:
    st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)
    zobrazit_vse = st.checkbox(_["show_all"], value=False if vychozi_vyber else True)
    
nabidka = fund_names if (not vychozi_vyber or zobrazit_vse) else vychozi_vyber

if not nabidka:
    st.info("Databáze je prázdná nebo nemáš žádné oblíbené. Přidej fond v sekci 'SPRÁVA DATABÁZE'.")
else:
    with c2:
        vyber = st.selectbox(_["sel_inv"], nabidka)

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
                        subprocess.run(["git", "commit", "-m", f"Okamžité stažení portfolia (CIK: {cik}) z mobilu"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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