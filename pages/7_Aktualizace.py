import streamlit as st
import requests
import os
import sys

# --- CENTRÁLNÍ PAMĚŤ A MENU ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)

st.set_page_config(page_title="Aktualizace Dat", page_icon="🎛️", layout="centered")
import menu
menu.vykresli_menu()

t = {
    "CZ": {
        "title": "🎛️ Dálkové ovládání cloudu", "desc": "Manuálně spusť stahování 13F z Dataromy (GitHub zátěž).",
        "btn": "🚀 Odeslat povel k aktualizaci", "spin": "Odesílám signál...", "succ": "✅ Povel odeslán!",
        "err_gh": "❌ Chyba GitHubu: ", "err_ex": "❌ Chyba Secrets: "
    },
    "EN": {
        "title": "🎛️ Cloud Remote Control", "desc": "Manually trigger 13F download from Dataroma.",
        "btn": "🚀 Send Update Command", "spin": "Sending signal...", "succ": "✅ Command sent!",
        "err_gh": "❌ GitHub error: ", "err_ex": "❌ Secrets error: "
    }
}
_ = t.get(st.session_state.lang, t["CZ"])

st.title(_["title"])
st.markdown(_["desc"])

if st.button(_["btn"], use_container_width=True):
    with st.spinner(_["spin"]):
        try:
            token, owner, repo = st.secrets["GITHUB_TOKEN"], st.secrets["GITHUB_OWNER"], st.secrets["GITHUB_REPO"]
            url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/aktualizace.yml/dispatches"
            res = requests.post(url, headers={"Accept": "application/vnd.github.v3+json", "Authorization": f"token {token}"}, json={"ref": "main"})
            if res.status_code == 204: st.success(_["succ"]); st.balloons()
            else: st.error(_["err_gh"] + res.text)
        except Exception as e:
            st.error(_["err_ex"] + str(e))
