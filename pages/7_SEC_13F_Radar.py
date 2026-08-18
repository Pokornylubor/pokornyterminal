import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

st.set_page_config(page_title="SEC 13F Radar", page_icon="🏛️", layout="wide")

if "lang" not in st.session_state:
    st.session_state.lang = "CZ"

# ZDE SI DOPLŇ SVŮJ E-MAIL PRO AMERICKOU VLÁDU!
SEC_HEADERS = {
    "User-Agent": "Lubor Pokorny (pokornyl98@gmail.com)" 
}

SUPERINVESTORS = {
    "Warren Buffett (Berkshire)": "1067983",
    "Michael Burry (Scion)": "1649339",
    "Ray Dalio (Bridgewater)": "1350694",
    "Stanley Druckenmiller (Duquesne)": "1501697",
    "Bill Ackman (Pershing Square)": "1336528",
    "Howard Marks (Oaktree)": "1403256",
    "Seth Klarman (Baupost)": "868702",
    "David Tepper (Appaloosa)": "1006438",
    "Jim Simons (Renaissance)": "1037389",
    "Bill Gates (Gates Foundation)": "1166559",
    "🔍 Jiný fond (Zadat CIK ručně)": "CUSTOM"
}

st.title("🏛️ SEC EDGAR 13F Radar")
st.markdown("Přímé napojení na americkou komisi SEC. Zobrazuje **aktuální portfolia** a **změny oproti minulému čtvrtletí**.")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    vyber = st.selectbox("Vyber Superinvestora / Fond:", list(SUPERINVESTORS.keys()))
with col2:
    if SUPERINVESTORS[vyber] == "CUSTOM":
        cik_input = st.text_input("Zadej vlastní CIK kód (jen čísla):", "").strip()
    else:
        st.write("") 
        cik_input = SUPERINVESTORS[vyber]

# --- Pomocná funkce pro stažení a rozluštění jednoho 13F XML ---
def parse_13f_xml(cik_padded, accession_no):
    acc_clean = accession_no.replace("-", "")
    url_index = f"https://www.sec.gov/Archives/edgar/data/{cik_padded}/{acc_clean}/index.json"
    res_idx = requests.get(url_index, headers=SEC_HEADERS)
    xml_filename = "infotable.xml" # Výchozí název
    
    if res_idx.status_code == 200:
        for item in res_idx.json().get("directory", {}).get("item", []):
            if item["name"].endswith(".xml") and "primary_doc" not in item["name"]:
                xml_filename = item["name"]
                break
                
    url_xml = f"https://www.sec.gov/Archives/edgar/data/{cik_padded}/{acc_clean}/{xml_filename}"
    res_xml = requests.get(url_xml, headers=SEC_HEADERS)
    
    if res_xml.status_code != 200:
        return pd.DataFrame()
        
    soup = BeautifulSoup(res_xml.content, 'xml')
    positions = []
    
    for info in soup.find_all('infoTable'):
        try:
            name = info.find('nameOfIssuer').text.upper() if info.find('nameOfIssuer') else ""
            titleClass = info.find('titleOfClass').text.upper() if info.find('titleOfClass') else ""
            value = float(info.find('value').text) * 1000 
            
            shrs_tag = info.find('shrsOrPrnAmt')
            shares = float(shrs_tag.find('sshPrnamt').text) if shrs_tag and shrs_tag.find('sshPrnamt') else 0
            
            positions.append({"Akcie (Název)": name, "Typ (COM=Akcie)": titleClass, "Hodnota ($)": value, "Ks Akcií": shares})
        except Exception:
            continue
            
    if not positions:
        return pd.DataFrame()
        
    df = pd.DataFrame(positions)
    # Sloučení stejných akcií a tříd
    return df.groupby(["Akcie (Název)", "Typ (COM=Akcie)"]).sum().reset_index()


# --- Hlavní logika ---
if st.button("Stáhnout 13F Data vč. Změn", type="primary"):
    if not cik_input.isdigit():
        st.error("CIK musí obsahovat pouze čísla.")
        st.stop()
        
    cik_padded = cik_input.zfill(10)
    
    with st.spinner("Prohledávám databázi SEC EDGAR a stahuji 2 poslední kvartály..."):
        url_submissions = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
        res = requests.get(url_submissions, headers=SEC_HEADERS)
        
        if res.status_code != 200:
            st.error(f"Chyba připojení na SEC. Zkontroluj email v kódu. Kód chyby: {res.status_code}")
            st.stop()
            
        data = res.json()
        filings = data.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        
        # Najdeme indexy dvou posledních 13F-HR reportů (vč. amendmentů)
        hr_indices = [i for i, f in enumerate(forms) if "13F-HR" in f]
        
        if not hr_indices:
            st.error("Tento fond nemá žádný nedávný 13F-HR report (neinvestuje nad 100M USD do veřejných akcií).")
            st.stop()
            
        # Stahování aktuálního čtvrtletí
        idx_curr = hr_indices[0]
        acc_curr = filings["accessionNumber"][idx_curr]
        date_curr = filings["filingDate"][idx_curr]
        
        df_curr = parse_13f_xml(cik_padded, acc_curr)
        time.sleep(0.1) # Ohleduplnost k serverům SEC
        
        # Stahování předchozího čtvrtletí (pro výpočet změn)
        df_prev = pd.DataFrame()
        date_prev = "Nenalezeno"
        if len(hr_indices) > 1:
            idx_prev = hr_indices[1]
            acc_prev = filings["accessionNumber"][idx_prev]
            date_prev = filings["filingDate"][idx_prev]
            df_prev = parse_13f_xml(cik_padded, acc_prev)
            
    if df_curr.empty:
        st.error("Nepodařilo se rozluštit XML soubor tohoto fondu.")
        st.stop()

    # --- Zpracování dat a výpočty ---
    total_value = df_curr["Hodnota ($)"].sum()
    df_curr["% Portfolia"] = (df_curr["Hodnota ($)"] / total_value) * 100

    if not df_prev.empty:
        df_prev = df_prev.rename(columns={"Ks Akcií": "Minulé Ks"})
        # Propojíme aktuální s minulým
        df_merged = pd.merge(df_curr, df_prev[["Akcie (Název)", "Typ (COM=Akcie)", "Minulé Ks"]], on=["Akcie (Název)", "Typ (COM=Akcie)"], how="left")
        df_merged["Minulé Ks"] = df_merged["Minulé Ks"].fillna(0)
        df_merged["Změna (Ks)"] = df_merged["Ks Akcií"] - df_merged["Minulé Ks"]
    else:
        df_merged = df_curr.copy()
        df_merged["Změna (Ks)"] = 0
        
    # Finální úprava sloupců a seřazení od největší pozice
    df_merged = df_merged[["Akcie (Název)", "Typ (COM=Akcie)", "% Portfolia", "Změna (Ks)", "Ks Akcií", "Hodnota ($)"]]
    df_merged = df_merged.sort_values(by="% Portfolia", ascending=False).reset_index(drop=True)
    
    st.success(f"✅ Data úspěšně načtena! Aktuální report z: **{date_curr}** (Srovnáno s reportem z: **{date_prev}**)")
    st.subheader(f"Portfolio Fondu ({vyber})")

    # Barvičkář - funkce pro stylování změn
    def style_change(val):
        if pd.isna(val) or val == 0:
            return ""
        return 'color: #00ff00; font-weight: bold;' if val > 0 else 'color: #ff4b4b; font-weight: bold;'

    # Vykreslení
    formatted_df = df_merged.style.format({
        "% Portfolia": "{:.2f} %",
        "Změna (Ks)": "{:+,.0f}", # Plus a mínus znaménka
        "Ks Akcií": "{:,.0f}",
        "Hodnota ($)": "${:,.0f}"
    }).map(style_change, subset=["Změna (Ks)"])
    
    st.dataframe(formatted_df, use_container_width=True, height=600)
