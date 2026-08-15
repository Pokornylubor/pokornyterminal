import streamlit as st
import pandas as pd
import requests
import zipfile
import io
import json
import os
import datetime

st.set_page_config(page_title="COT Reporty", page_icon="🏛️", layout="wide")

# --- JAZYKOVÝ SYSTÉM ---
if "lang" not in st.session_state:
    st.session_state.lang = "CZ"

selected_lang = st.sidebar.radio("🌐 Jazyk / Language:", ["CZ", "EN"], index=0 if st.session_state.lang == "CZ" else 1)
if selected_lang != st.session_state.lang:
    st.session_state.lang = selected_lang
    st.rerun()

t = {
    "CZ": {
        "title": "🏛️ COT Reporty (Commitments of Traders)",
        "desc": "Sleduj pozice 'Smart Money' a velkých fondů. Data se stahují přímo z americké komise CFTC.",
        "spin_data": "Stahuji data z vládních serverů CFTC (tohle může trvat pár vteřin)...",
        "err_data": "❌ Nelze stáhnout data z CFTC. Komise pravděpodobně blokuje spojení.",
        "h_univ": "🔍 Univerzální vyhledávač",
        "search_lbl": "✍️ Napiš, co hledáš (např. S&P, GOLD, CRUDE):",
        "sel_univ": "Vyber konkrétní trh z výsledků:",
        "btn_add": "⭐ Přidat do mého COT Watchlistu",
        "succ_add": "✅ Přidáno do Watchlistu!",
        "h_watch": "👀 Můj COT Watchlist",
        "sel_watch": "Vyber trh z Watchlistu:",
        "btn_rem": "🗑️ Odebrat z Watchlistu",
        "succ_rem": "✅ Odebráno!",
        "h_chart": "📈 Vývoj pozic (Net = Long mínus Short)",
        "chart_desc": "**Zeleně:** Commercials (Zajišťovatelé/Smart Money). **Červeně:** Non-Commercials (Fondy a Spekulanti)."
    },
    "EN": {
        "title": "🏛️ COT Reports (Commitments of Traders)",
        "desc": "Track positions of 'Smart Money' and large funds. Data downloaded directly from the US CFTC.",
        "spin_data": "Downloading data from CFTC government servers (may take a few seconds)...",
        "err_data": "❌ Failed to download CFTC data. Connection blocked.",
        "h_univ": "🔍 Universal Search",
        "search_lbl": "✍️ Type what you are looking for (e.g. S&P, GOLD, CRUDE):",
        "sel_univ": "Select specific market from results:",
        "btn_add": "⭐ Add to my COT Watchlist",
        "succ_add": "✅ Added to Watchlist!",
        "h_watch": "👀 My COT Watchlist",
        "sel_watch": "Select market from Watchlist:",
        "btn_rem": "🗑️ Remove from Watchlist",
        "succ_rem": "✅ Removed!",
        "h_chart": "📈 Positions History (Net = Long minus Short)",
        "chart_desc": "**Green:** Commercials (Hedgers/Smart Money). **Red:** Non-Commercials (Funds/Speculators)."
    }
}
_ = t[st.session_state.lang]

st.title(_["title"])
st.markdown(_["desc"])

WATCHLIST_FILE = "watchlist.json"

# --- CHYTRÉ NAČTENÍ DAT Z CFTC (Spojí letošní i loňský rok pro lepší graf) ---
@st.cache_data(ttl=3600*12) 
def load_cot_data():
    year = datetime.datetime.now().year
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    
    def fetch_year(y):
        url = f"https://www.cftc.gov/files/dea/history/deacot{y}.zip"
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    csv_filename = z.namelist()[0]
                    data = z.read(csv_filename)
                    return pd.read_csv(io.BytesIO(data), low_memory=False)
        except Exception:
            pass
        return pd.DataFrame()
        
    # Stáhne aktuální i minulý rok a spojí je dohromady pro hezčí a delší historii
    df_current = fetch_year(year)
    df_prev = fetch_year(year - 1)
    
    combined = pd.concat([df_current, df_prev], ignore_index=True)
    return combined

with st.spinner(_["spin_data"]):
    cot_df = load_cot_data()

if cot_df is None or cot_df.empty:
    st.error(_["err_data"])
    st.stop()

# Získání unikátních názvů všech trhů
markets = sorted(cot_df['Market and Exchange Names'].dropna().unique())

# --- NAČTENÍ WATCHLISTU ---
try:
    with open(WATCHLIST_FILE, "r") as f:
        data = json.load(f)
        if "cot_watchlist" not in data:
            data["cot_watchlist"] = []
except Exception:
    data = {"cot_watchlist": []}

# --- UI ROZDĚLENÍ ---
col1, col2 = st.columns(2)

vybrany_trh = None

with col1:
    st.markdown(f"### {_['h_univ']}")
    
    search_term = st.text_input(_["search_lbl"], "").strip().lower()
    
    if search_term:
        filtered_markets = [m for m in markets if search_term in m.lower()]
    else:
        filtered_markets = markets
        
    univ_trh = st.selectbox(_["sel_univ"], ["--- Vyber ---"] + filtered_markets)
    
    if univ_trh != "--- Vyber ---":
        vybrany_trh = univ_trh
        if st.button(_["btn_add"], use_container_width=True):
            if univ_trh not in data["cot_watchlist"]:
                data["cot_watchlist"].append(univ_trh)
                with open(WATCHLIST_FILE, "w") as f:
                    json.dump(data, f, indent=4)
                st.success(_["succ_add"])
                st.rerun()

with col2:
    st.markdown(f"### {_['h_watch']}")
    if not data["cot_watchlist"]:
        st.info("Zatím prázdný. Vyhledej si trh vlevo a přidej si ho sem.")
    else:
        watch_trh = st.selectbox(_["sel_watch"], ["--- Vyber ---"] + sorted(data["cot_watchlist"]))
        if watch_trh != "--- Vyber ---":
            vybrany_trh = watch_trh
            if st.button(_["btn_rem"], use_container_width=True):
                data["cot_watchlist"].remove(watch_trh)
                with open(WATCHLIST_FILE, "w") as f:
                    json.dump(data, f, indent=4)
                st.success(_["succ_rem"])
                st.rerun()

# --- VYKRESLENÍ GRAFU ---
if vybrany_trh:
    st.markdown("---")
    st.subheader(f"{_['h_chart']}: {vybrany_trh}")
    st.markdown(_["chart_desc"])
    
    df_market = cot_df[cot_df['Market and Exchange Names'] == vybrany_trh].copy()
    
    try:
        # Pevně vynutíme správný sloupec s datem, aby nedošlo ke kolizi formátů
        date_cols = df_market.columns.tolist()
        if 'Report_Date_as_YYYY-MM-DD' in date_cols:
            df_market['Date'] = pd.to_datetime(df_market['Report_Date_as_YYYY-MM-DD'], errors='coerce')
        elif 'Report_Date_as_MM_DD_YYYY' in date_cols:
            df_market['Date'] = pd.to_datetime(df_market['Report_Date_as_MM_DD_YYYY'], errors='coerce')
        else:
            fallback_col = [c for c in date_cols if 'as of' in c.lower()][0]
            df_market['Date'] = pd.to_datetime(df_market[fallback_col].astype(str).str.zfill(6), format='%y%m%d', errors='coerce')
            
        df_market = df_market.dropna(subset=['Date'])
        df_market = df_market.sort_values('Date')
        
        # Dynamické vyhledání správných sloupců pro Long/Short pozice
        def get_col(keywords_include, keywords_exclude=[]):
            for c in df_market.columns:
                cl = c.lower()
                if all(k in cl for k in keywords_include) and not any(k in cl for k in keywords_exclude):
                    return c
            return None

        c_long = get_col(['commercial', 'long', 'all'], ['non']) or get_col(['commercial', 'long'], ['non'])
        c_short = get_col(['commercial', 'short', 'all'], ['non']) or get_col(['commercial', 'short'], ['non'])
        nc_long = get_col(['non', 'commercial', 'long', 'all']) or get_col(['non', 'commercial', 'long'])
        nc_short = get_col(['non', 'commercial', 'short', 'all']) or get_col(['non', 'commercial', 'short'])
        
        # Výpočty s převedením na čistá čísla
        df_market['Net Commercials'] = pd.to_numeric(df_market[c_long], errors='coerce') - pd.to_numeric(df_market[c_short], errors='coerce')
        df_market['Net Non-Commercials'] = pd.to_numeric(df_market[nc_long], errors='coerce') - pd.to_numeric(df_market[nc_short], errors='coerce')
        
        if df_market.empty or len(df_market) < 2:
            st.warning("Málo platných dat pro vykreslení historie (zřejmě chybí záznamy pro tento trh).")
        else:
            chart_data = df_market.set_index('Date')[['Net Commercials', 'Net Non-Commercials']]
            st.line_chart(chart_data, color=["#2ca02c", "#d62728"]) 
            
    except Exception as e:
        st.error(f"Při vykreslování grafu došlo k chybě (CFTC pravděpodobně změnila strukturu reportu): {e}")
