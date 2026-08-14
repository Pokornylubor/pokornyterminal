import streamlit as st
import requests

st.set_page_config(page_title="Aktualizace Dat", page_icon="🎛️", layout="centered")
st.title("🎛️ Dálkové ovládání cloudu")
st.markdown("Zde můžeš **manuálně spustit** stahování nových dat na serverech GitHubu (Mimo pravidelnou noční automatiku). Tvůj prohlížeč přitom nezamrzne.")

st.info("💡 **Jak to funguje:** Kliknutím odešleš tajný povel. GitHub na pozadí spustí robota, který stáhne 20 000 transakcí 4F a kompletní 13F. Data se v aplikaci objeví za cca 15 minut.")

if st.button("🚀 Odeslat povel k aktualizaci (13F + 4F)", use_container_width=True):
    with st.spinner("Odesílám signál na servery..."):
        try:
            # Načtení tajných klíčů ze Streamlit trezoru
            token = st.secrets["GITHUB_TOKEN"]
            owner = st.secrets["GITHUB_OWNER"]
            repo = st.secrets["GITHUB_REPO"]
            
            # Cesta přímo k tvé automatice
            url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/aktualizace.yml/dispatches"
            
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "Authorization": f"token {token}"
            }
            # Spouštíme z hlavní větve (main)
            data = {"ref": "main"}
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 204:
                st.success("✅ Povel úspěšně odeslán! GitHub právě zapnul motory.")
                st.balloons()
                st.markdown("Můžeš tuto stránku klidně zavřít. Až se za 15 minut vrátíš a proklikneš tabulky, budou plné nových dat.")
            else:
                st.error(f"❌ Nastala chyba při komunikaci s GitHubem: {response.text}")
                
        except Exception as e:
            st.error(f"❌ Došlo k chybě (Zkontroluj, zda máš v Nastavení Streamlitu vyplněné Secrets): {e}")
