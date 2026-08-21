import streamlit as st
import requests

st.set_page_config(page_title="Aktualizace Dat", page_icon="🔄", layout="wide")

st.title("🔄 Aktualizační centrum (Cloud)")
st.markdown("Odesláním povelu se probudí servery GitHubu, které na pozadí stáhnou čerstvá data (13F Dataroma a 4F Insideři).")
st.markdown("---")

if st.button("🚀 Odeslat povel k aktualizaci dat", use_container_width=True):
    with st.spinner("Odesílám signál na GitHub..."):
        try:
            # Tady si Python sám sáhne do složky .streamlit pro tvůj klíč
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
                st.success("✅ Povel úspěšně přijat! Servery právě stahují data (potrvá to několik minut).")
                st.balloons()
            else: 
                st.error(f"❌ Server zamítl přístup. Kód chyby: {res.status_code}. Zpráva: {res.text}")
                
        except KeyError as e:
            st.error(f"❌ Chybí bezpečnostní klíč: {e}. Zkontroluj složku .streamlit/secrets.toml")
        except Exception as e:
            st.error(f"❌ Systémová chyba: {e}")
