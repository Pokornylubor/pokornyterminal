import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="13F Superinvestoři", page_icon="🐋", layout="wide")
st.title("🐋 13F Superinvestoři")
st.markdown("Historická data portfolií největších investorů na světě (z Dataromy).")

FILE_PATH = "superinvestors_db.csv"

if not os.path.exists(FILE_PATH):
    st.warning("⚠️ Datový soubor nebyl nalezen. Spusť nejprve program `updater.py`.")
else:
    # Bleskové načtení naší vlastní offline databáze
    df = pd.read_csv(FILE_PATH)
    
    if df.empty:
        st.info("Databáze je prázdná.")
    else:
        # Získání seznamu unikátních investorů
        investors = sorted(df['Investor'].dropna().unique())
        
        # Rozbalovací nabídka pro výběr investora
        selected_investor = st.selectbox("Vyber superinvestora k analýze:", investors)
        
        if selected_investor:
            # Filtrace dat jen pro vybraného investora
            investor_data = df[df['Investor'] == selected_investor]
            
            # Zobrazení data aktualizace (pokud se nám ho podařilo stáhnout)
            if 'Kvartal_Aktualizace' in investor_data.columns:
                kvartal = investor_data['Kvartal_Aktualizace'].iloc[0]
                st.info(f"📅 **Poslední známá aktualizace portfolia:** {kvartal}")
            
            # Schováme technické sloupce, které pro prohlížení nepotřebujeme
            display_df = investor_data.drop(columns=['Investor', 'Kvartal_Aktualizace', 'Investor_Code'], errors='ignore')
            
            # Zobrazení čisté tabulky přes celou šířku
            st.dataframe(display_df, use_container_width=True)