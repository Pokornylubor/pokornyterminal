import streamlit as st
import subprocess
import os
import sys

st.set_page_config(page_title="Aktualizace Dat", page_icon="🔄", layout="wide")

st.title("🔄 Aktualizační centrum")
st.markdown("Kliknutím na tlačítko níže spustíš stahování nejnovějších dat přímo do svého počítače. Využívá se lokální výkon stroje.")
st.markdown("---")

if st.button("🚀 Spustit aktualizaci (Lokálně)", use_container_width=True):
    with st.status("Stahuji data (nezavírej toto okno, může to chvíli trvat)...", expanded=True) as status:
        try:
            # Zjištění správné cesty ke skriptům
            aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
            hlavni_slozka = os.path.dirname(aktualni_slozka)
            
            cesta_updater = os.path.join(hlavni_slozka, "updater.py")
            cesta_sec = os.path.join(hlavni_slozka, "sec_updater.py")
            
            # KROK 1: Spuštění původního Dataroma a Insider motoru
            st.write("⏳ 1/2: Stahuji Dataromu a Insidery...")
            subprocess.run([sys.executable, cesta_updater], cwd=hlavni_slozka, check=True)
            
            # KROK 2: Spuštění SEC motoru (vyčištěné fondy bez opcí)
            if os.path.exists(cesta_sec):
                st.write("⏳ 2/2: Stahuji SEC data (vyčištěná od opcí)...")
                subprocess.run([sys.executable, cesta_sec], cwd=hlavni_slozka, check=True)
            
            status.update(label="✅ Aktualizace dokončena!", state="complete", expanded=False)
            st.success("Všechna data byla úspěšně stažena a uložena! Můžeš přejít na ostatní záložky.")
            st.balloons()
            
        except subprocess.CalledProcessError as e:
            status.update(label="❌ Nastala chyba při stahování", state="error")
            st.error("Některý ze skriptů narazil na problém (např. dočasná chyba spojení s burzou). Zkus to za chvíli znovu.")
        except Exception as e:
            status.update(label="❌ Systémová chyba", state="error")
            st.error(f"Detail chyby: {e}")
