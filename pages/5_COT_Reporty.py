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
import plotly.graph_objects as go

# --- INITIAL SETUP ---
st.set_page_config(page_title="POKORNY TERMINAL | COT", layout="wide", initial_sidebar_state="collapsed")

# --- DIRECTORY MANAGEMENT ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)
WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")

import menu
menu.vykresli_menu()

# --- DICTIONARY ---
t = {
    "CZ": {
        "title": "COT REPORTY (Commitments of Traders)",
        "desc": "ANALÝZA POZIC 'SMART MONEY' (COMMERCIALS) VS SPEKULANTŮ (NON-COMMERCIALS).",
        "spin_data": "STAHOVÁNÍ HISTORICKÝCH DAT Z CFTC...", 
        "err_data": "SYS ERR: SPOJENÍ S CFTC BLOKOVÁNO.", 
        "search_lbl": "VLASTNÍ VYHLEDÁVÁNÍ TRHU", 
        "sel_univ": "VÝBĚR Z DATABÁZE CFTC",
        "btn_add": "ULOŽIT DO WATCHLISTU", 
        "succ_add": "SYSTÉM AKTUALIZOVÁN.",
        "h_watch": "MŮJ COT WATCHLIST", 
        "sel_watch": "ULOŽENÉ TRHY",
        "btn_rem": "ODEBRAT Z WATCHLISTU", 
        "succ_rem": "ODSTRANĚNO.",
        "db_empty": "DATABÁZE JE PRÁZDNÁ.",
        "tab_chart": "📊 GRAF NET POZIC",
        "tab_raw": "🗄️ SUROVÁ DATA (CFTC)",
        "help_title": "📖 JAK ČÍST TENTO GRAF (NÁPOVĚDA)",
        "help_text": """
**Základní pravidlo:** Trh je hra s nulovým součtem. Kde jeden kupuje, druhý prodává. Osa Y ukazuje tzv. Net pozice (Long kontrakty mínus Short kontrakty).

* 🟢 **Zelená linka (Commercials / Smart Money):** Velké instituce, banky, korporace. Trh často používají k zajištění. Sledujeme u nich **obraty a extrémy**. Pokud jsou extrémně v mínusu (short) a začnou prudce růst, trh se pravděpodobně otočí nahoru.
* 🔴 **Červená linka (Non-Commercials / Spekulanti):** Hedge fondy a trend-followeři. Většinou dělají přesný opak toho, co Smart Money.

**Co v grafu hledat (Roztažení gumy):**
Nehledej překřížení nulové osy. Hledej momenty, kdy se od sebe zelená a červená linka **extrémně vzdálí**. Znamená to, že napětí na trhu je na maximu. Spekulanti sází vše na jeden směr, ale Smart Money stojí tvrdě proti nim. V 90 % případů vyhrají Smart Money a trh následně prudce změní směr.
""",
        "leg_comm": "Commercials (Zajišťovatelé)",
        "leg_nonc": "Non-Commercials (Spekulanti)",
        "err_hist": "Pro tento trh není dostatek historických dat (kontrakt pravděpodobně zanikl, nebo ještě neexistoval).",
        "raw_title": "KOMPLETNÍ ZÁZNAM CFTC:",
        "raw_desc": "Pohled do všech dostupných sloupců a kategorií pro vybraný trh."
    },
    "EN": {
        "title": "COT REPORTS (Commitments of Traders)",
        "desc": "POSITION TRACKING: 'SMART MONEY' (COMMERCIALS) VS SPECULATORS (NON-COMMERCIALS).",
        "spin_data": "DOWNLOADING CFTC HISTORY...", 
        "err_data": "SYS ERR: CFTC CONNECTION BLOCKED.", 
        "search_lbl": "CUSTOM MARKET SEARCH", 
        "sel_univ": "SELECT FROM CFTC DATABASE",
        "btn_add": "COMMIT TO WATCHLIST", 
        "succ_add": "SYSTEM UPDATED.",
        "h_watch": "MY COT WATCHLIST", 
        "sel_watch": "SAVED MARKETS",
        "btn_rem": "REMOVE FROM WATCHLIST", 
        "succ_rem": "REMOVED.",
        "db_empty": "DATABASE IS EMPTY.",
        "tab_chart": "📊 NET POSITIONS CHART",
        "tab_raw": "🗄️ RAW CFTC DATA",
        "help_title": "📖 HOW TO READ THIS CHART (HELP)",
        "help_text": """
**Basic Rule:** The market is a zero-sum game. Where one buys, another must sell. The Y-axis shows Net positions (Long contracts minus Short contracts).

* 🟢 **Green Line (Commercials / Smart Money):** Large institutions, banks, corporations. They often use the market for hedging. We look for **reversals and extremes** here. If they are extremely negative (short) and suddenly spike upwards, the market will likely turn up.
* 🔴 **Red Line (Non-Commercials / Speculators):** Hedge funds and trend-followers. They usually do the exact opposite of Smart Money.

**What to look for (The Rubber Band Effect):**
Do not look for zero-line crossovers. Look for moments when the green and red lines **diverge extremely** from each other. This means market tension is at a maximum. Speculators are betting heavily in one direction, but Smart Money is standing firmly against them. 90% of the time, Smart Money wins, and the market sharply reverses.
""",
        "leg_comm": "Commercials (Hedgers)",
        "leg_nonc": "Non-Commercials (Speculators)",
        "err_hist": "Not enough historical data for this market (contract may be discontinued or newly added).",
        "raw_title": "COMPLETE CFTC RECORD:",
        "raw_desc": "View all available columns and categories for the selected market."
    }
}
_ = t.get(st.session_state.get("lang", "CZ"), t["CZ"])

st.title(_["title"])
st.caption(_["desc"])
st.markdown("---")

def save_data(data):
    with open(WATCHLIST_FILE, "w") as f: json.dump(data, f, indent=4)
    try:
        if "GITHUB_TOKEN" in st.secrets:
            token, owner, repo = st.secrets["GITHUB_TOKEN"], st.secrets["GITHUB_OWNER"], st.secrets["GITHUB_REPO"]
            url, headers = f"https://api.github.com/repos/{owner}/{repo}/contents/watchlist.json", {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
            sha = requests.get(url, headers=headers).json().get("sha")
            payload = {"message": "SYS: COT Watchlist Sync", "content": base64.b64encode(json.dumps(data, indent=4).encode("utf-8")).decode("utf-8"), "branch": "main"}
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

c1, c2 = st.columns([1, 1])
vybrany_trh = None
markets = sorted(cot_df['Market and Exchange Names'].dropna().unique())

with c1:
    st.markdown(f"**{_['search_lbl']}**")
    search_term = st.text_input("Hledat", label_visibility="collapsed").strip().lower()
    nabidka_trhu = [m for m in markets if search_term in m.lower()] if search_term else markets
    univ_trh = st.selectbox(_["sel_univ"], [""] + nabidka_trhu)
    
    if univ_trh:
        vybrany_trh = univ_trh
        if univ_trh not in data["cot_watchlist"]:
            if st.button(_["btn_add"], use_container_width=True):
                data["cot_watchlist"].append(univ_trh)
                save_data(data); st.success(_["succ_add"]); st.rerun()

with c2:
    st.markdown(f"**{_['h_watch']}**")
    if not data["cot_watchlist"]: 
        st.caption(_["db_empty"])
    else:
        watch_trh = st.selectbox(_["sel_watch"], [""] + sorted(data["cot_watchlist"]))
        if watch_trh:
            vybrany_trh = watch_trh
            if st.button(_["btn_rem"], use_container_width=True):
                data["cot_watchlist"].remove(watch_trh)
                save_data(data); st.success(_["succ_rem"]); st.rerun()

if vybrany_trh:
    st.markdown("---")
    
    df_market = cot_df[cot_df['Market and Exchange Names'] == vybrany_trh].copy()
    can_plot = True
    
    try:
        # --- AGRESIVNÍ PARSOVÁNÍ DATA ---
        date_series = None
        for col_name in ['Report_Date_as_YYYY-MM-DD', 'As of Date in Form YYYY-MM-DD', 'Report_Date_as_MM_DD_YYYY', 'As of Date in Form YYMMDD']:
            if col_name in df_market.columns:
                if 'YYMMDD' in col_name:
                    # Ochrana před Pandas Float Bugem (.0)
                    clean = df_market[col_name].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(6)
                    date_series = pd.to_datetime(clean, format='%y%m%d', errors='coerce')
                else:
                    date_series = pd.to_datetime(df_market[col_name], errors='coerce')
                
                if date_series.notna().any(): break
        
        # Fallback vyhledávač
        if date_series is None or not date_series.notna().any():
            possible_cols = [c for c in df_market.columns if 'date' in c.lower() or 'as of' in c.lower()]
            for c in possible_cols:
                parsed = pd.to_datetime(df_market[c], errors='coerce')
                if parsed.notna().any():
                    date_series = parsed; break
                
                clean = df_market[c].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(6)
                parsed = pd.to_datetime(clean, format='%y%m%d', errors='coerce')
                if parsed.notna().any():
                    date_series = parsed; break

        if date_series is not None and date_series.notna().any():
            df_market['Date'] = date_series
            df_market = df_market.dropna(subset=['Date']).sort_values('Date')
        else:
            st.error("CHYBA: Časová osa (Datum) v datech CFTC chybí nebo je v neznámém formátu. Podívejte se do Surových dat.")
            can_plot = False

        # --- AGRESIVNÍ PARSOVÁNÍ SLOUPCŮ POZIC ---
        def get_col(possible_lists, exc=[]):
            for inc in possible_lists:
                col = next((c for c in df_market.columns if all(k in c.lower() for k in inc) and not any(k in c.lower() for k in exc)), None)
                if col: return col
            return None

        # CFTC střídá plná slova a zkratky (Commercial vs Comm, NonCommercial vs NonComm)
        c_long = get_col([['commercial', 'long', 'all'], ['comm', 'long', 'all'], ['commercial', 'long'], ['comm', 'long']], ['non'])
        c_short = get_col([['commercial', 'short', 'all'], ['comm', 'short', 'all'], ['commercial', 'short'], ['comm', 'short']], ['non'])
        nc_long = get_col([['non', 'commercial', 'long', 'all'], ['noncomm', 'long', 'all'], ['non', 'commercial', 'long'], ['noncomm', 'long']])
        nc_short = get_col([['non', 'commercial', 'short', 'all'], ['noncomm', 'short', 'all'], ['non', 'commercial', 'short'], ['noncomm', 'short']])
        
        if can_plot and not all([c_long, c_short, nc_long, nc_short]):
            st.error("CHYBA: Názvy sloupců (Commercial / Non-Commercial) byly CFTC přejmenovány. Podívejte se do Surových dat.")
            can_plot = False
            
        if can_plot:
            df_market['Net Commercials'] = pd.to_numeric(df_market[c_long], errors='coerce') - pd.to_numeric(df_market[c_short], errors='coerce')
            df_market['Net Non-Commercials'] = pd.to_numeric(df_market[nc_long], errors='coerce') - pd.to_numeric(df_market[nc_short], errors='coerce')
        
        tab_dash, tab_raw = st.tabs([_["tab_chart"], _["tab_raw"]])
        
        with tab_dash:
            if can_plot and len(df_market) > 1: 
                st.subheader(vybrany_trh)
                
                with st.expander(_["help_title"]):
                    st.markdown(_["help_text"])
                
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=df_market['Date'], y=df_market['Net Commercials'], 
                    mode='lines', line=dict(color='#26A69A', width=2), 
                    name=_["leg_comm"], fill='tozeroy', fillcolor='rgba(38, 166, 154, 0.1)'
                ))
                
                fig.add_trace(go.Scatter(
                    x=df_market['Date'], y=df_market['Net Non-Commercials'], 
                    mode='lines', line=dict(color='#EF5350', width=2), 
                    name=_["leg_nonc"], fill='tozeroy', fillcolor='rgba(239, 83, 80, 0.1)'
                ))
                
                fig.add_hline(y=0, line_dash="solid", line_color="#787B86", opacity=0.5)

                fig.update_layout(
                    template="plotly_dark",
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=500,
                    hovermode='x unified',
                    yaxis=dict(fixedrange=False, showgrid=True, gridcolor='#2B2B2B', zeroline=False),
                    xaxis=dict(fixedrange=False, showgrid=False)
                )
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            elif can_plot: 
                st.warning(_["err_hist"])
                
        with tab_raw:
            st.subheader(f"{_['raw_title']} {vybrany_trh}")
            st.caption(_["raw_desc"])
            clean_df = df_market.drop(columns=['Date', 'Market and Exchange Names'], errors='ignore').copy()
            st.dataframe(clean_df.iloc[::-1], use_container_width=True, hide_index=True)
            
    except Exception as e: st.error(f"SYS ERR: {e}")
