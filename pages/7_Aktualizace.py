import streamlit as st
import requests
import subprocess
import os
import sys

# --- INITIAL SETUP ---
st.set_page_config(page_title="POKORNY TERMINAL | SYSTEM UPDATE", layout="wide", initial_sidebar_state="collapsed")

import menu
menu.vykresli_menu()

# --- DICTIONARY ---
t = {
    "CZ": {
        "title": "CENTRUM AKTUALIZACE DAT",
        "desc": "SPRÁVA SYSTÉMU A RUČNÍ SPOUŠTĚNÍ AKTUALIZAČNÍCH MOTORŮ.",
        "p1_title": "FÁZE 1: CLOUDOVÝ ENGINE (DATAROMA A FORM 4)",
        "p1_desc": "Využívá servery GitHubu. Stáhne historii Insiderů a 13F Superinvestory.",
        "p1_btn": "SPUSTIT CLOUDOVÉ STAHOVÁNÍ",
        "p1_spin": "ODESÍLÁM SIGNÁL NA CLOUD...",
        "p1_ok": "SIGNÁL PŘIJAT. CLOUD NA POZADÍ STAHUJE DATA (PROCES POTRVÁ PÁR MINUT).",
        "p1_err1": "CLOUD ZAMÍTL PŘÍSTUP. KÓD:",
        "p1_err2": "CHYBA SPOJENÍ S CLOUDEM:",
        "p2_title": "FÁZE 2: LOKÁLNÍ ENGINE (SEC EDGAR)",
        "p2_desc": "Využívá výkon tohoto PC k očištění SEC dat a automaticky je odešle na GitHub.",
        "p2_btn": "SPUSTIT LOKÁLNÍ STAHOVÁNÍ SEC",
        "p2_stat": "STAHOVÁNÍ DATA SEC A SYNCHRONIZACE CLOUDU...",
        "p2_step1": "⏳ Stahuji SEC data z EDGAR...",
        "p2_step1ok": "✅ Lokální stahování dokončeno.",
        "p2_step2": "🔄 Slaďuji lokální systém s repozitářem...",
        "p2_step3": "⬆️ Připravuji odeslání...",
        "p2_step4": "☁️ Nahrávám nová data na GitHub...",
        "p2_done": "VŠECHNY PROCESY ÚSPĚŠNĚ DOKONČENY.",
        "p2_same": "DATA SE NEZMĚNILA (REPOZITÁŘ JE AKTUÁLNÍ).",
        "p2_nofile": "SYS ERR: SOUBOR SEC_UPDATER.PY NENALEZEN.",
        "p2_err": "CHYBA PŘI ZPRACOVÁNÍ. DETAIL:"
    },
    "EN": {
        "title": "DATA UPDATE CENTER",
        "desc": "SYSTEM MANAGEMENT AND MANUAL TRIGGERING OF UPDATE ENGINES.",
        "p1_title": "PHASE 1: CLOUD ENGINE (DATAROMA & FORM 4)",
        "p1_desc": "Uses GitHub servers to download Insider history and 13F Superinvestors.",
        "p1_btn": "TRIGGER CLOUD DOWNLOAD",
        "p1_spin": "SENDING SIGNAL TO CLOUD...",
        "p1_ok": "SIGNAL ACCEPTED. CLOUD IS DOWNLOADING DATA IN BACKGROUND (TAKES A FEW MINS).",
        "p1_err1": "CLOUD DENIED ACCESS. CODE:",
        "p1_err2": "CLOUD CONNECTION ERROR:",
        "p2_title": "PHASE 2: LOCAL ENGINE (SEC EDGAR)",
        "p2_desc": "Uses this PC to clean SEC data and automatically pushes it to GitHub.",
        "p2_btn": "TRIGGER LOCAL SEC DOWNLOAD",
        "p2_stat": "DOWNLOADING SEC DATA & SYNCING CLOUD...",
        "p2_step1": "⏳ Downloading SEC data from EDGAR...",
        "p2_step1ok": "✅ Local download complete.",
        "p2_step2": "🔄 Syncing local system with repository...",
        "p2_step3": "⬆️ Preparing to commit...",
        "p2_step4": "☁️ Pushing new data to GitHub...",
        "p2_done": "ALL PROCESSES SUCCESSFULLY COMPLETED.",
        "p2_same": "NO DATA CHANGES (REPOSITORY IS UP TO DATE).",
        "p2_nofile": "SYS ERR: FILE SEC_UPDATER.PY NOT FOUND.",
        "p2_err": "PROCESSING ERROR. DETAIL:"
    }
}
_ = t.get(st.session_state.get("lang", "CZ"), t["CZ"])

st.title(_["title"])
st.caption(_["desc"])
st.markdown("---")

# ==========================================
# CLOUD: Dataroma a 4F Insideři
# ==========================================
st.markdown(f"### {_['p1_title']}")
st.markdown(_["p1_desc"])

if st.button(_["p1_btn"], use_container_width=True):
    with st.spinner(_["p1_spin"]):
        try:
            token = st.secrets["GITHUB_TOKEN"]
            owner = st.secrets["GITHUB_OWNER"]
            repo = st.secrets["GITHUB_REPO"]
            
            url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/aktualizace.yml/dispatches"
            res = requests.post(
                url, 
                headers={"Accept": "application/vnd.github.v3+json", "Authorization": f"token {token}"}, 
                json={"ref": "main"}
            )
            
            if res.status_code == 204: 
                st.success(_["p1_ok"])
            else: 
                st.error(f"{_['p1_err1']} {res.status_code}. {res.text}")
                
        except Exception as e:
            st.error(f"{_['p1_err2']} {e}")

st.markdown("---")

# ==========================================
# LOKÁL: SEC Data + Automatický odesílač
# ==========================================
st.markdown(f"### {_['p2_title']}")
st.markdown(_["p2_desc"])

if st.button(_["p2_btn"], use_container_width=True):
    with st.status(_["p2_stat"], expanded=True) as status:
        try:
            aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
            hlavni_slozka = os.path.dirname(aktualni_slozka)
            cesta_sec = os.path.join(hlavni_slozka, "sec_updater.py")
            
            if os.path.exists(cesta_sec):
                st.write(_["p2_step1"])
                subprocess.run([sys.executable, cesta_sec], cwd=hlavni_slozka, check=True)
                st.write(_["p2_step1ok"])
                
                st.write(_["p2_step2"])
                subprocess.run(["git", "pull", "origin", "main", "--no-edit"], cwd=hlavni_slozka)
                
                st.write(_["p2_step3"])
                subprocess.run(["git", "add", "."], cwd=hlavni_slozka, check=True)
                
                commit = subprocess.run(["git", "commit", "-m", "SYS: Aktualizace SEC dat (Lokál)"], cwd=hlavni_slozka, capture_output=True)
                
                if commit.returncode == 0:
                    st.write(_["p2_step4"])
                    subprocess.run(["git", "push"], cwd=hlavni_slozka, check=True)
                    status.update(label=_["p2_done"], state="complete", expanded=False)
                else:
                    status.update(label=_["p2_same"], state="complete", expanded=False)
                    
            else:
                status.update(label=_["p2_nofile"], state="error")
                
        except Exception as e:
            status.update(label=_["p2_err"], state="error")
            st.error(f"{e}")
