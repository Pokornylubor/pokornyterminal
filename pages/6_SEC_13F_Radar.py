import streamlit as st
import pandas as pd
import json
import os
import sys

# --- CENTRÁLNÍ PAMĚŤ A MENU ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)
WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")
SEC_DATA_DIR = os.path.join(hlavni_slozka, "sec_data")

# Importujeme náš nový motor pro případ manuálního vynucení
try:
    import sec_updater
except:
    pass

st.set_page_config(page_title="13F Superinvestoři", page_icon="🐋", layout="wide")
import menu
menu.vykresli_menu() 

st.title("🐋 13F Superinvestoři")
st.markdown("Historická data portfolií (Bleskové načítání ze SEC EDGAR).")

def save_data(data):
    with open(WATCHLIST_FILE, "w") as f: json.dump(data, f, indent=4)

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r") as f: return json.load(f)
        except: pass
    return {"saved_ciks": {}, "sec_favorites": []}

data = load_watchlist()
if "saved_ciks" not in data: data["saved_ciks"] = {}
if "sec_favorites" not in data: data["sec_favorites"] = []

PREDEFINED_FUNDS = {
    "Warren Buffett (Berkshire Hathaway)": "1067983",
    "Michael Burry (Scion Asset Management)": "1649339",
    "Stanley Druckenmiller (Duquesne Family Office)": "1536411",
    "Chris Hohn (TCI Fund Management)": "1647251",
    "Bill Ackman (Pershing Square)": "0002026053",
    "Ray Dalio (Bridgewater Associates)": "1350694",
    "David Tepper (Appaloosa)": "1009207",
    "Seth Klarman (Baupost Group)": "1061768",
    "Jim Simons (Renaissance Technologies)": "1037389",
    "Carl Icahn (Icahn Capital)": "921669"
}

ALL_FUNDS = PREDEFINED_FUNDS.copy()
ALL_FUNDS.update(data["saved_ciks"])
fund_names = sorted(list(ALL_FUNDS.keys()))
vychozi_vyber = [f for f in data["sec_favorites"] if f in fund_names]

with st.expander("⭐ Nastavit oblíbené", expanded=False):
    vybrani = st.multiselect("Moji oblíbenci:", options=fund_names, default=vychozi_vyber)
    if st.button("💾 Uložit na Cloud", use_container_width=True):
        data["sec_favorites"] = vybrani
        save_data(data)
        st.rerun()

st.markdown("---")
zobrazit_vse = st.checkbox("Zobrazit všechny", value=False)
nabidka = fund_names if (not vychozi_vyber or zobrazit_vse) else vychozi_vyber
nabidka.append("🔍 Jiný fond (Zadat CIK manuálně)")
vyber = st.selectbox("Vyber superinvestora:", nabidka)

if vyber == "🔍 Jiný fond (Zadat CIK manuálně)":
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1: cik_input = st.text_input("Zadej CIK:", "").strip()
    with c2: novy_nazev = st.text_input("Název pro uložení:", "").strip()
    with c3:
        st.markdown("<br>", unsafe_allow_html=True)
        if cik_input and novy_nazev and st.button("💾 Uložit nový fond", use_container_width=True):
            data["saved_ciks"][novy_nazev] = cik_input
            save_data(data)
            st.success("✅ Uloženo!")
            st.rerun()
else:
    cik = str(ALL_FUNDS[vyber]).zfill(10)
    csv_path = os.path.join(SEC_DATA_DIR, f"{cik}.csv")
    meta_path = os.path.join(SEC_DATA_DIR, f"{cik}_meta.json")
    
    col1, col2 = st.columns([4, 1])
    # Tlačítko pro manuální aktualizaci jednoho konkrétního fondu (kdyby náhodou chyběl)
    with col2:
        if st.button("🔄 Aktualizovat tento fond", use_container_width=True):
            with st.spinner("Stahuji čerstvá data přímo ze SEC..."):
                sec_updater.update_sec_funds(target_cik=cik)
            st.rerun()
            
    # Bleskové načtení dat
    if os.path.exists(csv_path) and os.path.exists(meta_path):
        with open(meta_path, "r") as f: meta = json.load(f)
        
        st.success(f"**{vyber.split('(')[0].strip()}** | Zobrazen report: **{meta['kvartal']}** (Ke dni {meta['report_date']}) | *Naposledy staženo: {meta['last_updated']}*")
        
        df = pd.read_csv(csv_path)
        df[" "] = "" # Vyčištění oddělovacího sloupce
        
        def style_df(row):
            styles = [''] * len(row)
            act_val = str(row['RecentActivity'])
            if "Buy" in act_val or "Add" in act_val: styles[2] = 'color: #00ff00;'
            elif "Reduce" in act_val: styles[2] = 'color: #ff4b4b;'
            
            if pd.notnull(row['+/-Reported Price']):
                try:
                    val = float(row['+/-Reported Price'])
                    if val > 0: styles[8] = 'color: #00ff00;' # Sloupec +/- je na indexu 8
                    elif val < 0: styles[8] = 'color: #ff4b4b;'
                except: pass
            return styles
            
        styled_df = df.style.apply(style_df, axis=1).format({
            "% of Portfolio": "{:.2f}%",
            "Shares": "{:,.0f}",
            "ReportedPrice*": "${:,.2f}",
            "Value": "${:,.0f}",
            "Current Price": lambda x: f"${x:,.2f}" if pd.notnull(x) else "",
            "+/-Reported Price": lambda x: f"{x:+.2f}%" if pd.notnull(x) else "",
            "52Week Low": lambda x: f"${x:,.2f}" if pd.notnull(x) else "",
            "52Week High": lambda x: f"${x:,.2f}" if pd.notnull(x) else ""
        })
        
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.warning("⚠️ Data pro tohoto investora ještě nejsou stažena. Klikni na tlačítko 'Aktualizovat tento fond' vpravo nahoře, nebo spusť hromadnou aktualizaci na Page 7.")
