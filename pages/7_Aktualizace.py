import streamlit as st
import requests

st.set_page_config(page_title="Aktualizace Dat", page_icon="🔄", layout="wide")

st.title("🔄 Aktualizační centrum cloudu")
st.markdown("Odesláním povelu se probudí servery GitHubu a stáhnou data na pozadí.")

st.markdown("---")

if st.button("🚀 Odeslat povel k aktualizaci všech dat", use_container_width=True):
    with st.spinner("Navazuji spojení se servery GitHubu..."):
        try:
            token = st.secrets["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"]
            owner = st.secrets["Pokornylubor"]
            repo = st.secrets["pokornyterminal"]
            
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
                st.success("✅ Povel úspěšně přijat! Cloudový motor se právě nastartoval na pozadí.")
                st.balloons()
            else: 
                st.error(f"❌ Server zamítl přístup. Zpráva od GitHubu: {res.text}")
                
        except Exception as e:
            st.error(f"❌ Nastala neočekávaná chyba spojení: {e}")
