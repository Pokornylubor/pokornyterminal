import streamlit as st
import pandas as pd
import requests
import zipfile
import io
import json
import os
import sys
import datetime

# --- CENTRÁLNÍ PAMĚŤ A MENU ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)
WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")

st.set_page_config(page_title="COT Reporty", page_icon="🏛️", layout="wide")
import menu
menu.vykresli_menu()

t = {
    "CZ": {"title": "🏛️ COT Reporty", "desc": "Pozice velkých fondů z CFTC."},
    "EN": {"title": "🏛️ COT Reports", "desc": "Positions of large funds from CFTC."}
}
_ = t.get(st.session_state.lang, t["CZ"])

st.title(_["title"])
st.markdown(_["desc"])

@st.cache_data(ttl=3600*12) 
def load_cot_data():
    year = datetime.datetime.now().year
    headers = {"User-Agent": "Lubor Pokorny (pokornyl98@gmail.com)"}
    
    def fetch_year(y):
        try:
            response = requests.get(f"https://www.cftc.gov/files/dea/history/deacot{y}.zip", headers=headers, timeout=15)
            if response.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    return pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), low_memory=False)
        except: pass
        return pd.DataFrame()
        
    return pd.concat([fetch_year(year), fetch_year(year - 1)], ignore_index=True)

with st.spinner("..."): cot_df = load_cot_data()

if cot_df is not None and not cot_df.empty:
    markets = sorted(cot_df['Market and Exchange Names'].dropna().unique())
    vybrany_trh = st.selectbox("Trh / Market:", ["---"] + markets)
    if vybrany_trh != "---":
        df_market = cot_df[cot_df['Market and Exchange Names'] == vybrany_trh].copy()
        date_cols = df_market.columns.tolist()
        if 'Report_Date_as_YYYY-MM-DD' in date_cols: df_market['Date'] = pd.to_datetime(df_market['Report_Date_as_YYYY-MM-DD'], errors='coerce')
        else: df_market['Date'] = pd.to_datetime(df_market[[c for c in date_cols if 'as of' in c.lower()][0]].astype(str).str.zfill(6), format='%y%m%d', errors='coerce')
        
        c_long = [c for c in df_market.columns if 'commercial' in c.lower() and 'long' in c.lower() and 'non' not in c.lower()][0]
        c_short = [c for c in df_market.columns if 'commercial' in c.lower() and 'short' in c.lower() and 'non' not in c.lower()][0]
        nc_long = [c for c in df_market.columns if 'non' in c.lower() and 'commercial' in c.lower() and 'long' in c.lower()][0]
        nc_short = [c for c in df_market.columns if 'non' in c.lower() and 'commercial' in c.lower() and 'short' in c.lower()][0]
        
        df_market['Net Commercials'] = pd.to_numeric(df_market[c_long], errors='coerce') - pd.to_numeric(df_market[c_short], errors='coerce')
        df_market['Net Non-Commercials'] = pd.to_numeric(df_market[nc_long], errors='coerce') - pd.to_numeric(df_market[nc_short], errors='coerce')
        
        st.line_chart(df_market.set_index('Date')[['Net Commercials', 'Net Non-Commercials']].dropna(), color=["#2ca02c", "#d62728"])
