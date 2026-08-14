import streamlit as st
import pandas as pd
import os
import json

st.set_page_config(page_title="13F Superinvestors", page_icon="🐋", layout="wide")

if "lang" not in st.session_state:
    st.session_state.lang = "CZ"

selected_lang = st.sidebar.radio("🌐 Jazyk / Language:", ["CZ", "EN"], index=0 if st.session_state.lang == "CZ" else 1)
if selected_lang != st.session_state.lang:
    st.session_state.lang = selected_lang
    st.rerun()

t = {
    "CZ": {
        "title": "🐋 13F Superinvestoři",
        "desc": "Historická data portfolií největších investorů na světě (z Dataromy).",
        "warn_file": "⚠️ Datový soubor nebyl nalezen. Spusť nejprve program `updater.py`.",
        "empty_db": "Databáze je prázdná.",
        "exp_title": "⭐ Nastavit oblíbené Superinvestory",
        "exp_desc": "Vyber si legendy, které chceš mít vždy po ruce jako první.",
        "multi_fav": "Moji oblíbenci:",
        "btn_save": "💾 Uložit výběr",
        "succ_save": "✅ Tvoji oblíbenci byli uloženi!",
        "check_all": "Zobrazit všechny (i ty, co nemám v oblíbených)",
        "sel_inv": "Vyber superinvestora k analýze:",
        "last_upd": "📅 **Poslední známá aktualizace portfolia:**"
    },
    "EN": {
        "title": "🐋 13F Superinvestors",
        "desc": "Historical portfolio data of the world's greatest investors (from Dataroma).",
        "warn_file": "⚠️ Data file not found. Run `updater.py` first.",
        "empty_db": "Database is empty.",
        "exp_title": "⭐ Set Favorite Superinvestors",
        "exp_desc": "Select the legends you want to keep handy.",
        "multi_fav": "My favorites:",
        "btn_save": "💾 Save Selection",
        "succ_save": "✅ Your favorites have been saved!",
        "check_all": "Show all (including non-favorites)",
        "sel_inv": "Select a superinvestor for analysis:",
        "last_upd": "📅 **Last known portfolio update:**"
    }
}
_ = t[st.session_state.lang]

st.title(_["title"])
st.markdown(_["desc"])

WATCHLIST_FILE = "watchlist.json"
FILE_PATH = "superinvestors_db.csv"

if not os.path.exists(FILE_PATH):
    st.warning(_["warn_file"])
else:
    df = pd.read_csv(FILE_PATH)
    if df.empty:
        st.info(_["empty_db"])
    else:
        investors = sorted(df['Investor'].dropna().unique())
        
        try:
            with open(WATCHLIST_FILE, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"portfolio": [], "watchlist": [], "superinvestors": []}
            
        ulozeni_investori = data.get("superinvestors", [])
        vychozi_vyber = [inv for inv in ulozeni_investori if inv in investors]
        
        with st.expander(_["exp_title"], expanded=False):
            st.markdown(_["exp_desc"])
            vybrani_oblibenci = st.multiselect(_["multi_fav"], options=investors, default=vychozi_vyber)
            
            if st.button(_["btn_save"], use_container_width=True):
                data["superinvestors"] = vybrani_oblibenci
                with open(WATCHLIST_FILE, "w") as f:
                    json.dump(data, f, indent=4)
                st.success(_["succ_save"])
                st.rerun()
                
        st.markdown("---")
        
        if vychozi_vyber:
            zobrazit_vse = st.checkbox(_["check_all"])
            nabidka = investors if zobrazit_vse else vychozi_vyber
        else:
            nabidka = investors
            
        selected_investor = st.selectbox(_["sel_inv"], nabidka)
        
        if selected_investor:
            investor_data = df[df['Investor'] == selected_investor]
            if 'Kvartal_Aktualizace' in investor_data.columns:
                kvartal = investor_data['Kvartal_Aktualizace'].iloc[0]
                st.info(f"{_['last_upd']} {kvartal}")
            
            display_df = investor_data.drop(columns=['Investor', 'Kvartal_Aktualizace', 'Investor_Code'], errors='ignore')
            st.dataframe(display_df, use_container_width=True)