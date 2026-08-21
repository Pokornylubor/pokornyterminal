import streamlit as st
import requests

st.set_page_config(page_title="Aktualizace Dat", page_icon="🔄", layout="wide")

st.title("🔄 Aktualizační centrum (Cloud)")
st.markdown("Odesláním povelu se probudí servery GitHubu, které na pozadí stáhnou čerstvá data.")
st.markdown("---")

if st.button("🚀 Odeslat povel k aktualizaci dat", use_container_width=True):
    with st.spinner("Odesílám signál na GitHub..."):
        try:
            # Tady vložíš ten svůj klíč přímo sem do uvozovek! 
            token = "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"
            owner = "Pokornylubor"
            repo = "pokornyterminal"
            
            url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/aktualizace.yml/dispatches"
            
            res = requests.post(
                url, 
                headers={
                    "Accept": "application/vnd.github.v3+json", 
                    "Authorization": f"token {token}"
                }, 
                json={"ref": "main"}
            )
            
            if res.status_code == 204: 
                st.success("✅ Povel úspěšně přijat! Servery právě stahují data.")
                st.balloons()
            else: 
                st.error(f"❌ Server zamítl přístup. Kód chyby: {res.status_code}. Zpráva: {res.text}")
                
        except Exception as e:
            st.error(f"❌ Systémová chyba: {e}")
