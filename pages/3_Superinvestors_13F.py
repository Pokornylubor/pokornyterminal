import streamlit as st
import pandas as pd
import os
import json

st.set_page_config(page_title="13F Superinvestoři", page_icon="🐋", layout="wide")
st.title("🐋 13F Superinvestoři")
st.markdown("Historická data portfolií největších investorů na světě (z Dataromy).")

WATCHLIST_FILE = "watchlist.json"
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
        
        # --- 1. NAČTENÍ OBLÍBENÝCH Z JSONU ---
        try:
            with open(WATCHLIST_FILE, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"portfolio": [], "watchlist": [], "superinvestors": []}
            
        ulozeni_investori = data.get("superinvestors", [])
        # Ochrana proti překlepům - vybere jen ty, co v CSV opravdu existují
        vychozi_vyber = [inv for inv in ulozeni_investori if inv in investors]
        
        # --- 2. SPRÁVA OBLÍBENÝCH (Schovaná v liště, ať neruší) ---
        with st.expander("⭐ Nastavit oblíbené Superinvestory", expanded=False):
            st.markdown("Vyber si legendy, které chceš mít vždy po ruce jako první.")
            vybrani_oblibenci = st.multiselect(
                "Moji oblíbenci:",
                options=investors,
                default=vychozi_vyber
            )
            
            if st.button("💾 Uložit výběr", use_container_width=True):
                data["superinvestors"] = vybrani_oblibenci
                with open(WATCHLIST_FILE, "w") as f:
                    json.dump(data, f, indent=4)
                st.success("✅ Tvoji oblíbenci byli uloženi!")
                st.rerun() # Obnoví stránku, aby se změna hned projevila v nabídce
                
        st.markdown("---")
        
        # --- 3. ZOBRAZENÍ PORTFOLIA ---
        # Chytrá logika: Pokud má oblíbené, nabídneme je jako první.
        if vychozi_vyber:
            zobrazit_vse = st.checkbox("Zobrazit všechny (i ty, co nemám v oblíbených)")
            nabidka = investors if zobrazit_vse else vychozi_vyber
        else:
            nabidka = investors
            
        # Rozbalovací nabídka pro výběr investora
        selected_investor = st.selectbox("Vyber superinvestora k analýze:", nabidka)
        
        if selected_investor:
            # Filtrace dat jen pro vybraného investora
            investor_data = df[df['Investor'] == selected_investor]
            
            # Zobrazení data aktualizace
            if 'Kvartal_Aktualizace' in investor_data.columns:
                kvartal = investor_data['Kvartal_Aktualizace'].iloc[0]
                st.info(f"📅 **Poslední známá aktualizace portfolia:** {kvartal}")
            
            # Schováme technické sloupce
            display_df = investor_data.drop(columns=['Investor', 'Kvartal_Aktualizace', 'Investor_Code'], errors='ignore')
            
            # Zobrazení čisté tabulky přes celou šířku
            st.dataframe(display_df, use_container_width=True)
