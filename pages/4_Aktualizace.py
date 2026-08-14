import streamlit as st
import requests

st.set_page_config(page_title="Aktualizace Dat", page_icon="🎛️", layout="centered")

if "lang" not in st.session_state:
    st.session_state.lang = "CZ"

selected_lang = st.sidebar.radio("🌐 Jazyk / Language:", ["CZ", "EN"], index=0 if st.session_state.lang == "CZ" else 1)
if selected_lang != st.session_state.lang:
    st.session_state.lang = selected_lang
    st.rerun()

t = {
    "CZ": {
        "title": "🎛️ Dálkové ovládání cloudu",
        "desc": "Zde můžeš **manuálně spustit** stahování nových dat na serverech GitHubu. Tvůj prohlížeč přitom nezamrzne.",
        "info": "💡 **Jak to funguje:** Kliknutím odešleš tajný povel. GitHub na pozadí spustí robota, který stáhne 20 000 transakcí 4F a kompletní 13F. Data se objeví za cca 15 minut.",
        "btn": "🚀 Odeslat povel k aktualizaci (13F + 4F)",
        "spin": "Odesílám signál na servery...",
        "succ": "✅ Povel úspěšně odeslán! GitHub právě zapnul motory.",
        "succ_sub": "Můžeš tuto stránku klidně zavřít. Až se za 15 minut vrátíš, tabulky budou plné nových dat.",
        "err_gh": "❌ Nastala chyba při komunikaci s GitHubem: ",
        "err_ex": "❌ Došlo k chybě (Zkontroluj Streamlit Secrets): "
    },
    "EN": {
        "title": "🎛️ Cloud Remote Control",
        "desc": "Here you can **manually trigger** the download of new data on GitHub servers. Your browser won't freeze.",
        "info": "💡 **How it works:** By clicking, you send a secret command. GitHub runs a background bot that downloads 20,000 4F transactions and complete 13F data. Data will appear in approx. 15 minutes.",
        "btn": "🚀 Send Update Command (13F + 4F)",
        "spin": "Sending signal to servers...",
        "succ": "✅ Command successfully sent! GitHub just fired up the engines.",
        "succ_sub": "You can safely close this page. When you return in 15 minutes, tables will be full of new data.",
        "err_gh": "❌ Error communicating with GitHub: ",
        "err_ex": "❌ An error occurred (Check Streamlit Secrets): "
    }
}
_ = t[st.session_state.lang]

st.title(_["title"])
st.markdown(_["desc"])
st.info(_["info"])

if st.button(_["btn"], use_container_width=True):
    with st.spinner(_["spin"]):
        try:
            token = st.secrets["GITHUB_TOKEN"]
            owner = st.secrets["GITHUB_OWNER"]
            repo = st.secrets["GITHUB_REPO"]
            
            url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/aktualizace.yml/dispatches"
            headers = {"Accept": "application/vnd.github.v3+json", "Authorization": f"token {token}"}
            data = {"ref": "main"}
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 204:
                st.success(_["succ"])
                st.balloons()
                st.markdown(_["succ_sub"])
            else:
                st.error(_["err_gh"] + response.text)
                
        except Exception as e:
            st.error(_["err_ex"] + str(e))