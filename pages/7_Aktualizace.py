import streamlit as st
import requests
import os
import sys

# --- CENTRÁLNÍ PAMĚŤ A MENU ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)

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
        "btn": "🚀 Odeslat povel na Cloud a aktualizovat SEC", 
        "spin_cloud": "Odesílám signál na GitHub...", 
        "spin_sec": "Cloud běží! Nyní stahuji SEC data lokálně (Nechte okno chvíli otevřené)...",
        "succ": "✅ Vše hotovo! Cloud stahuje Insidery a SEC data máš aktuální v PC.",
        "err_gh": "❌ Chyba GitHubu: ", 
        "err_ex": "❌ Chyba Secrets: "
    }
}
_ = t.get(st.session_state.lang, t["CZ"])

st.title(_["title"])
st.markdown(_["desc"])

if st.button(_["btn"], use_container_width=True):
    
    # 1. KROK: Odeslání povelu na GitHub (Bleskové, cloud běží nezávisle)
    with st.spinner(_["spin_cloud"]):
        cloud_success = False
        try:
            token, owner, repo = st.secrets["GITHUB_TOKEN"], st.secrets["GITHUB_OWNER"], st.secrets["GITHUB_REPO"]
            url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/aktualizace.yml/dispatches"
            res = requests.post(url, headers={"Accept": "application/vnd.github.v3+json", "Authorization": f"token {token}"}, json={"ref": "main"})
            
            if res.status_code == 204: 
                cloud_success = True
            else: 
                st.error(_["err_gh"] + res.text)
        except Exception as e:
            st.error(_["err_ex"] + str(e))

    # 2. KROK: Lokální stahování SEC (Vyžaduje otevřené okno)
    if cloud_success:
        with st.spinner(_["spin_sec"]):
            try:
                sec_updater.update_sec_funds()
                st.success(_["succ"])
                st.balloons()
            except Exception as e:
                st.warning(f"⚠️ Cloud běží, ale SEC motor v PC narazil na problém: {e}")
