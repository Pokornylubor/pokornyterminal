import streamlit as st
import requests
import subprocess
import os
import sys

st.set_page_config(page_title="Aktualizace Dat", page_icon="🔄", layout="wide")
st.title("🔄 Aktualizační centrum")
st.markdown("---")

# ==========================================
# ☁️ CLOUD: Dataroma a 4F Insideři
# ==========================================
st.markdown("### ☁️ Fáze 1: Dataroma a Insideři (Cloud)")
st.markdown("Tato část využije servery GitHubu. Stáhne historii Insiderů (40 stran) a 13F Superinvestory.")

if st.button("🚀 Spustit cloudové stahování (GitHub)", use_container_width=True):
    with st.spinner("Odesílám signál na cloud..."):
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
                st.success("✅ Signál přijat! Cloud na pozadí stahuje data (potrvá to pár minut).")
            else: 
                st.error(f"❌ Cloud zamítl přístup. Kód: {res.status_code}. {res.text}")
                
        except Exception as e:
            st.error(f"❌ Chyba spojení s cloudem: {e}")

st.markdown("---")

# ==========================================
# 💻 LOKÁL: SEC Data + Automatický odesílač
# ==========================================
st.markdown("### 💻 Fáze 2: SEC Fondy (Lokální PC)")
st.markdown("Tato část využije výkon tvého PC k očištění SEC dat a **automaticky je odešle na GitHub**.")

if st.button("🚀 Spustit lokální stahování SEC", use_container_width=True):
    with st.status("Stahuji data SEC a odesílám na cloud...", expanded=True) as status:
        try:
            aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
            hlavni_slozka = os.path.dirname(aktualni_slozka)
            cesta_sec = os.path.join(hlavni_slozka, "sec_updater.py")
            
            if os.path.exists(cesta_sec):
                # 1. Stahování dat
                st.write("⏳ Stahuji SEC data (vyčištěná od opcí)...")
                subprocess.run([sys.executable, cesta_sec], cwd=hlavni_slozka, check=True)
                st.write("✅ SEC data stažena k tobě do PC.")
                
                # 2. Automatický Git
                st.write("🔄 Slaďuji PC s cloudem...")
                subprocess.run(["git", "pull", "origin", "main", "--no-edit"], cwd=hlavni_slozka)
                
                st.write("⬆️ Připravuji odeslání...")
                subprocess.run(["git", "add", "."], cwd=hlavni_slozka, check=True)
                
                # Zkusíme commit. Pokud nejsou žádná nová data, vyhodí to chybu, kterou ignorujeme
                commit = subprocess.run(["git", "commit", "-m", "Aktualizace SEC dat (Lokál)"], cwd=hlavni_slozka, capture_output=True)
                
                if commit.returncode == 0:
                    st.write("☁️ Nahrávám nová data na GitHub...")
                    subprocess.run(["git", "push"], cwd=hlavni_slozka, check=True)
                    status.update(label="✅ Vše hotovo a úspěšně odesláno na GitHub!", state="complete", expanded=False)
                    st.balloons()
                else:
                    status.update(label="✅ Staženo, ale data se od včerejška nezměnila (vše už na GitHubu je).", state="complete", expanded=False)
                    
            else:
                status.update(label="❌ Soubor sec_updater.py nenalezen.", state="error")
                
        except Exception as e:
            status.update(label="❌ Chyba při zpracování", state="error")
            st.error(f"Detail: {e}")