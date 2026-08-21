import streamlit as st
import pandas as pd
import requests
import zipfile
import io
import json
import os
import sys
import datetime
import base64

# --- CENTRÁLNÍ PAMĚŤ A MENU ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)
WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")

st.set_page_config(page_title="COT Reporty", page_icon="🏛️", layout="wide")
import menu
menu.vykresli_menu()

t = {
    "CZ": {
        "title": "🏛️ COT Reporty (Commitments of Traders)",
        "desc": "Tracking positions of Commercials (Hedgers/Smart Money) and Non-Commercials (Funds and Speculators). Data z CFTC.",
        "spin_data": "Stahuji data...", "err_data": "❌ Nelze stáhnout data z CFTC.", "h_univ": "🔍 Univerzální vyhledávač",
        "search_lbl": "✍️ Napiš, co hledáš (např. S&P, GOLD):", "sel_univ": "Vyber trh z výsledků:",
        "btn_add": "⭐ Přidat a uložit do Cloudu", "succ_add": "✅ Přidáno a synchronizováno!",
        "h_watch": "👀 Můj COT Watchlist", "sel_watch": "Vyber trh z Watchlistu:",
        "btn_rem": "🗑️ Odebrat", "succ_rem": "✅ Odebráno!", "h_chart": "📈 Vývoj pozic (Net)",
        "chart_desc": "**Zeleně:** Commercials. **Červeně:** Non-Commercials."
    },
    "EN": {
        "title": "🏛️ COT Reports",
        "desc": "Tracking positions of Commercials (Hedgers/Smart Money) and Non-Commercials (Funds and Speculators). CFTC data.",
        "spin_data": "Downloading...", "err_data": "❌ Connection blocked.", "h_univ": "🔍 Universal Search",
        "search_lbl": "✍️ Search (e.g. S&P, GOLD):", "sel_univ": "Select market:",
        "btn_add": "⭐ Add & Save to Cloud", "succ_add": "✅ Added and synced!",
        "h_watch": "👀 My COT Watchlist", "sel_watch": "Select market:",
        "btn_rem": "🗑️ Remove", "succ_rem": "✅ Removed!", "h_chart": "📈 Positions History",
        "chart_desc": "**Green:** Commercials. **Red:** Non-Commercials."
    }
}
_ = t.get(st.session_state.lang, t["CZ"])

st.title(_["title"])
st.markdown(_["desc"])

def save_data(data):
    with open(WATCHLIST_FILE, "w") as f: json.dump(data, f, indent=4)
    try:
        if "GITHUB_TOKEN" in st.secrets:
            token, owner, repo = st.secrets["GITHUB_TOKEN"], st.secrets["GITHUB_OWNER"], st.secrets["GITHUB_REPO"]
            url, headers = f"https://api.github.com/repos/{owner}/{repo}/contents/watchlist.json", {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
            sha = requests.get(url, headers=headers).json().get("sha")
            payload = {"message": "Cloud sync COT Watchlistu", "content": base64.b64encode(json.dumps(data, indent=4).encode("utf-8")).decode("utf-8"), "branch": "main"}
            if sha: payload["sha"] = sha
            requests.put(url, headers=headers, json=payload)
    except Exception: pass

@st.cache_data(ttl=3600*12) 
def load_cot_data():
    year = datetime.datetime.now().year
    headers = {"User-Agent": "Lubor Pokorny (pokornyl98@gmail.com)"}
    def fetch_year(y):
        try:
            res = requests.get(f"https://www.cftc.gov/files/dea/history/deacot{y}.zip", headers=headers, timeout=15)
            if res.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(res.content)) as z: return pd.read_csv(io.BytesIO(z.read(z.namelist()[0])), low_memory=False)
        except: pass
        return pd.DataFrame()
    return pd.concat([fetch_year(year), fetch_year(year - 1)], ignore_index=True)

with st.spinner(_["spin_data"]): cot_df = load_cot_data()
if cot_df is None or cot_df.empty: st.error(_["err_data"]); st.stop()

try:
    with open(WATCHLIST_FILE, "r") as f: data = json.load(f)
    if "cot_watchlist" not in data: data["cot_watchlist"] = []
except: data = {"cot_watchlist": []}

col1, col2 = st.columns(2)
vybrany_trh = None
markets = sorted(cot_df['Market and Exchange Names'].dropna().unique())

with col1:
    st.markdown(f"### {_['h_univ']}")
    search_term = st.text_input(_["search_lbl"]).strip().lower()
    univ_trh = st.selectbox(_["sel_univ"], ["---"] + ([m for m in markets if search_term in m.lower()] if search_term else markets))
    if univ_trh != "---":
        vybrany_trh = univ_trh
        if st.button(_["btn_add"], use_container_width=True):
            if univ_trh not in data["cot_watchlist"]:
                data["cot_watchlist"].append(univ_trh)
                save_data(data); st.success(_["succ_add"]); st.rerun()

with col2:
    st.markdown(f"### {_['h_watch']}")
    if not data["cot_watchlist"]: st.info("Zatím prázdný.")
    else:
        watch_trh = st.selectbox(_["sel_watch"], ["---"] + sorted(data["cot_watchlist"]))
        if watch_trh != "---":
            vybrany_trh = watch_trh
            if st.button(_["btn_rem"], use_container_width=True):
                data["cot_watchlist"].remove(watch_trh)
                save_data(data); st.success(_["succ_rem"]); st.rerun()

if vybrany_trh:
    st.markdown("---")
    st.subheader(f"{_['h_chart']}: {vybrany_trh}")
    st.markdown(_["chart_desc"])
    
    df_market = cot_df[cot_df['Market and Exchange Names'] == vybrany_trh].copy()
    try:
        date_cols = df_market.columns.tolist()
        if 'Report_Date_as_YYYY-MM-DD' in date_cols: df_market['Date'] = pd.to_datetime(df_market['Report_Date_as_YYYY-MM-DD'], errors='coerce')
        elif 'Report_Date_as_MM_DD_YYYY' in date_cols: df_market['Date'] = pd.to_datetime(df_market['Report_Date_as_MM_DD_YYYY'], errors='coerce')
        else: df_market['Date'] = pd.to_datetime(df_market[[c for c in date_cols if 'as of' in c.lower()][0]].astype(str).str.zfill(6), format='%y%m%d', errors='coerce')
        df_market = df_market.dropna(subset=['Date']).sort_values('Date')
        
        def get_col(inc, exc=[]): return next((c for c in df_market.columns if all(k in c.lower() for k in inc) and not any(k in c.lower() for k in exc)), None)
        c_long = get_col(['commercial', 'long', 'all'], ['non']) or get_col(['commercial', 'long'], ['non'])
        c_short = get_col(['commercial', 'short', 'all'], ['non']) or get_col(['commercial', 'short'], ['non'])
        nc_long = get_col(['non', 'commercial', 'long', 'all']) or get_col(['non', 'commercial', 'long'])
        nc_short = get_col(['non', 'commercial', 'short', 'all']) or get_col(['non', 'commercial', 'short'])
        
        df_market['Net Commercials'] = pd.to_numeric(df_market[c_long], errors='coerce') - pd.to_numeric(df_market[c_short], errors='coerce')
        df_market['Net Non-Commercials'] = pd.to_numeric(df_market[nc_long], errors='coerce') - pd.to_numeric(df_market[nc_short], errors='coerce')
        
        if len(df_market) > 1: st.line_chart(df_market.set_index('Date')[['Net Commercials', 'Net Non-Commercials']], color=["#2ca02c", "#d62728"]) 
        else: st.warning("Málo dat.")
    except Exception as e: st.error(f"Chyba grafu: {e}")
