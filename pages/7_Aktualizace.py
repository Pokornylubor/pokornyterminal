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
        
        "p1_title": "FÁZE 1: CLOUDOVÝ ENGINE (INSIDERS - FORM 4)",
        "p1_desc": "Využívá servery GitHubu. Stáhne historii pouze pro Insider transakce.",
        "p1_btn": "SPUSTIT INSIDERS NA CLOUDU",
        
        "p2_title": "FÁZE 2: CLOUDOVÝ ENGINE (SUPERINVESTOŘI - DATAROMA)",
        "p2_desc": "Využívá servery GitHubu. Stáhne nejnovější 13F reporty od Superinvestorů.",
        "p2_btn": "SPUSTIT SUPERINVESTORY NA CLOUDU",
        
        "cloud_spin": "ODESÍLÁM SIGNÁL NA CLOUD...",
        "cloud_ok": "SIGNÁL PŘIJAT. CLOUD NA POZADÍ STAHUJE DATA (PROCES POTRVÁ PÁR MINUT).",
        "cloud_err1": "CLOUD ZAMÍTL PŘÍSTUP. KÓD:",
        "cloud_err2": "CHYBA SPOJENÍ S CLOUDEM:",
        
        "p3_title": "FÁZE 3: LOKÁLNÍ ENGINE (SEC EDGAR)",
        "p3_desc": "Využívá výkon tohoto PC k očištění SEC dat a automaticky je odešle na GitHub.",
        "p3_btn": "SPUSTIT LOKÁLNÍ STAHOVÁNÍ SEC",
        "p3_stat": "STAHOVÁNÍ DATA SEC A SYNCHRONIZACE CLOUDU...",
        "p3_step1": "⏳ Stahuji SEC data z EDGAR...",
        "p3_step1ok": "✅ Lokální stahování dokončeno.",
        "p3_step2": "🔄 Slaďuji lokální systém s repozitářem...",
        "p3_step3": "⬆️ Připravuji odeslání...",
        "p3_step4": "☁️ Nahrávám nová data na GitHub...",
        "p3_done": "VŠECHNY PROCESY ÚSPĚŠNĚ DOKONČENY.",
        "p3_same": "DATA SE NEZMĚNILA (REPOZITÁŘ JE AKTUÁLNÍ).",
        "p3_nofile": "SYS ERR: SOUBOR SEC_UPDATER.PY NENALEZEN.",
        "p3_err": "CHYBA PŘI ZPRACOVÁNÍ. DETAIL:"
    },
    "EN": {
        "title": "DATA UPDATE CENTER",
        "desc": "SYSTEM MANAGEMENT AND MANUAL TRIGGERING OF UPDATE ENGINES.",
        
        "p1_title": "PHASE 1: CLOUD ENGINE (INSIDERS - FORM 4)",
        "p1_desc": "Uses GitHub servers. Downloads Insider history.",
        "p1_btn": "TRIGGER INSIDERS CLOUD DOWNLOAD",
        
        "p2_title": "PHASE 2: CLOUD ENGINE (SUPERINVESTORS - DATAROMA)",
        "p2_desc": "Uses GitHub servers. Downloads latest 13F reports.",
        "p2_btn": "TRIGGER SUPERINVESTORS CLOUD DOWNLOAD",
        
        "cloud_spin": "SENDING SIGNAL TO CLOUD...",
        "cloud_ok": "SIGNAL ACCEPTED. CLOUD IS DOWNLOADING DATA IN BACKGROUND (TAKES A FEW MINS).",
        "cloud_err1": "CLOUD DENIED ACCESS. CODE:",
        "cloud_err2": "CLOUD CONNECTION ERROR:",
        
        "p3_title": "PHASE 3: LOCAL ENGINE (SEC EDGAR)",
        "p3_desc": "Uses this PC to clean SEC data and automatically pushes it to GitHub.",
        "p3_btn": "TRIGGER LOCAL SEC DOWNLOAD",
        "p3_stat": "DOWNLOADING SEC DATA & SYNCING CLOUD...",
        "p3_step1": "⏳ Downloading SEC data from EDGAR...",
        "p3_step1ok": "✅ Local download complete.",
        "p3_step2": "🔄 Syncing local system with repository...",
        "p3_step3": "⬆️ Preparing to commit...",
        "p3_step4": "☁️ Pushing new data to GitHub...",
        "p3_done": "ALL PROCESSES SUCCESSFULLY COMPLETED.",
        "p3_same": "NO DATA CHANGES (REPOSITORY IS UP TO DATE).",
        "p3_nofile": "SYS ERR: FILE SEC_UPDATER.PY NOT FOUND.",
        "p3_err": "PROCESSING ERROR. DETAIL:"
    }
}
_ = t.get(st.session_state.get("lang", "CZ"), t["CZ"])

st.title(_["title"])
st.caption(_["desc"])
st.markdown("---")

# ==========================================
# POMOCNÁ FUNKCE PRO CLOUD
# ==========================================
def spust_cloud_workflow(workflow_soubor):
    try:
        token = st.secrets["GITHUB_TOKEN"]
        owner = st.secrets["GITHUB_OWNER"]
        repo = st.secrets["GITHUB_REPO"]
        
        url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_soubor}/dispatches"
        res = requests.post(
            url, 
            headers={"Accept": "application/vnd.github.v3+json", "Authorization": f"token {token}"}, 
            json={"ref": "main"}
        )
        
        if res.status_code == 204: 
            st.success(_["cloud_ok"])
        else: 
            st.error(f"{_['cloud_err1']} {res.status_code}. {res.text}")
            
    except Exception as e:
        st.error(f"{_['cloud_err2']} {e}")

# ==========================================
# FÁZE 1: CLOUD - INSIDERS
# ==========================================
st.markdown(f"### {_['p1_title']}")
st.markdown(_["p1_desc"])

if st.button(_["p1_btn"], use_container_width=True):
    with st.spinner(_["cloud_spin"]):
        spust_cloud_workflow("insiders_denne.yml")

st.markdown("---")

# ==========================================
# FÁZE 2: CLOUD - SUPERINVESTOŘI
# ==========================================
st.markdown(f"### {_['p2_title']}")
st.markdown(_["p2_desc"])

if st.button(_["p2_btn"], use_container_width=True):
    with st.spinner(_["cloud_spin"]):
        spust_cloud_workflow("superinvestori_kvartal.yml")

st.markdown("---")

# ==========================================
# FÁZE 3: LOKÁL - SEC Data + Odesílač
# ==========================================
st.markdown(f"### {_['p3_title']}")
st.markdown(_["p3_desc"])

if st.button(_["p3_btn"], use_container_width=True):
    with st.status(_["p3_stat"], expanded=True) as status:
        try:
            aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
            hlavni_slozka = os.path.dirname(aktualni_slozka)
            cesta_sec = os.path.join(hlavni_slozka, "sec_updater.py")
            
            if os.path.exists(cesta_sec):
                st.write(_["p3_step1"])
                subprocess.run([sys.executable, cesta_sec], cwd=hlavni_slozka, check=True)
                st.write(_["p3_step1ok"])
                
                st.write(_["p3_step2"])
                subprocess.run(["git", "pull", "origin", "main", "--no-edit"], cwd=hlavni_slozka)
                
                st.write(_["p3_step3"])
                subprocess.run(["git", "add", "."], cwd=hlavni_slozka, check=True)
                
                commit = subprocess.run(["git", "commit", "-m", "SYS: Aktualizace SEC dat (Lokál)"], cwd=hlavni_slozka, capture_output=True)
                
                if commit.returncode == 0:
                    st.write(_["p3_step4"])
                    subprocess.run(["git", "push"], cwd=hlavni_slozka, check=True)
                    status.update(label=_["p3_done"], state="complete", expanded=False)
                else:
                    status.update(label=_["p3_same"], state="complete", expanded=False)
                    
            else:
                status.update(label=_["p3_nofile"], state="error")
                
        except Exception as e:
            status.update(label=_["p3_err"], state="error")
            st.error(f"{e}")