import streamlit as st
import requests
import os
import sys

# --- CENTRÁLNÍ PAMĚŤ A MENU ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)

# Import našeho lokálního motoru pro SEC
try:
    import sec_updater
except Exception:
    pass

st.set_page_config(page_title="Aktualizace Dat", page_icon="🎛️", layout="centered")
import menu
menu.vykresli_menu()

t = {
    "CZ": {
        "title": "🎛️ Dálkové ovládání cloudu & SEC", 
        "desc": "Manuálně spusť masivní stahování dat (13F Dataroma, 40 000 4F Insiderů a přímé vládní spojení SEC).",
        "btn": "🚀 Odeslat povel k aktualizaci (13F + 40k 4F + SEC EDGAR)", 
        "spin": "Stahuji aktuální SEC data (to může trvat minutu) a odesílám signál cloudu...", 
        "succ": "✅ SEC data stažena lokálně a povel cloudu odeslán na GitHub!",
        "err_gh": "❌ Chyba GitHubu: ", 
        "err_ex": "❌ Chyba Secrets: "
    },
    "EN": {
        "title": "🎛️ Cloud & SEC Remote Control", 
        "desc": "Manually trigger massive data download (13F Dataroma, 40,000 4F Insiders, and direct SEC Radar).",
        "btn": "🚀 Send Update Command (13F + 40k 4F + SEC EDGAR)", 
        "spin": "Downloading SEC data (may take a minute) and sending signal to cloud...", 
        "succ": "✅ SEC data downloaded locally and command sent to GitHub!",
        "err_gh": "❌ GitHub error: ", 
        "err_ex": "❌ Secrets error: "
    }
}
_ = t.get(st.session_state.lang, t["CZ"])

st.title(_["title"])
st.markdown(_["desc"])

if st.button(_["btn"], use_container_width=True):
    with st.spinner(_["spin"]):
        
        # 1. KROK: Spustíme náš nový motor na pozadí, který potichu stáhne čerstvá data přímo od vlády
        try:
            sec_updater.update_sec_funds()
        except Exception as e:
            st.warning(f"⚠️ SEC motor narazil na problém: {e}")

        # 2. KROK: Odeslání původního povelu na GitHub (pro Dataromu a Insidery)
        try:
            token, owner, repo = st.secrets["GITHUB_TOKEN"], st.secrets["GITHUB_OWNER"], st.secrets["GITHUB_REPO"]
            url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/aktualizace.yml/dispatches"
            res = requests.post(url, headers={"Accept": "application/vnd.github.v3+json", "Authorization": f"token {token}"}, json={"ref": "main"})
            
            if res.status_code == 204: 
                st.success(_["succ"])
                st.balloons()
            else: 
                st.error(_["err_gh"] + res.text)
        except Exception as e:
            st.error(_["err_ex"] + str(e))
