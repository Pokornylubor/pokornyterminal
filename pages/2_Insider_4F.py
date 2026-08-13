import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Insider 4F", page_icon="🕵️", layout="wide")
st.title("🕵️ Insider 4F Transakce")
st.markdown("Nejnovější nákupy a prodeje (OpenInsider). Zobrazuje 1000 nejaktuálnějších transakcí.")

FILE_PATH = "insider_4f_db.csv"

if not os.path.exists(FILE_PATH):
    st.warning("⚠️ Datový soubor nebyl nalezen. Spusť nejprve program `updater.py`.")
else:
    # Bleskové načtení databáze
    df = pd.read_csv(FILE_PATH)
    
    if df.empty:
        st.info("Databáze je prázdná.")
    else:
        # Přidáme vyhledávací políčko pro rychlou filtraci tickeru
        search_ticker = st.text_input("🔍 Hledat konkrétní Ticker (např. AAPL, MSFT):").upper().strip()
        
        if search_ticker:
            # Zobrazí jen řádky, kde sloupec Ticker přesně odpovídá hledanému
            display_df = df[df['Ticker'] == search_ticker]
        else:
            display_df = df
            
        st.write(f"Zobrazeno **{len(display_df)}** transakcí:")
        st.dataframe(display_df, use_container_width=True)