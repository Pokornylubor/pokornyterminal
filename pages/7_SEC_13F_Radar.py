import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="SEC 13F Radar", page_icon="🏛️", layout="wide")

if "lang" not in st.session_state:
    st.session_state.lang = "CZ"

selected_lang = st.sidebar.radio("🌐 Jazyk / Language:", ["CZ", "EN"], index=0 if st.session_state.lang == "CZ" else 1)
if selected_lang != st.session_state.lang:
    st.session_state.lang = selected_lang
    st.rerun()

t = {
    "CZ": {
        "title": "🏛️ SEC EDGAR 13F Radar",
        "desc": "Přímé napojení na americkou komisi SEC. Stahuj oficiální nákupy těch největších hráčů.",
        "lbl_select": "Vyber Superinvestora / Fond:",
        "lbl_custom": "Zadej vlastní CIK kód:",
        "btn_fetch": "Stáhnout 13F Report",
        "spin_search": "Prohledávám databázi SEC EDGAR...",
        "spin_xml": "Zpracovávám vládní XML dokumenty...",
        "err_cik": "❌ CIK musí obsahovat pouze čísla.",
        "err_sec": "❌ Chyba připojení na SEC. Zkontroluj hlavičku s e-mailem.",
        "err_no_13f": "❌ Tento fond nemá žádný nedávný 13F-HR report.",
        "succ": "✅ 13F Report úspěšně načten:",
        "h_table": "Držené Pozice (Podle velikosti v USD)",
        "col_name": "Název Akcie",
        "col_class": "Třída/Druh",
        "col_val": "Hodnota (USD)",
        "col_shares": "Počet akcií"
    },
    "EN": {
        "title": "🏛️ SEC EDGAR 13F Radar",
        "desc": "Direct connection to the US SEC. Download official trades of the biggest players.",
        "lbl_select": "Select Superinvestor / Fund:",
        "lbl_custom": "Enter custom CIK code:",
        "btn_fetch": "Download 13F Report",
        "spin_search": "Searching SEC EDGAR database...",
        "spin_xml": "Parsing government XML documents...",
        "err_cik": "❌ CIK must contain only numbers.",
        "err_sec": "❌ SEC connection error. Check your email header.",
        "err_no_13f": "❌ No recent 13F-HR report found for this fund.",
        "succ": "✅ 13F Report successfully loaded:",
        "h_table": "Held Positions (By Value in USD)",
        "col_name": "Issuer Name",
        "col_class": "Class/Title",
        "col_val": "Value (USD)",
        "col_shares": "Shares Count"
    }
}
_ = t[st.session_state.lang]

# --- HLAVIČKA PRO VLÁDU ---
# ZDE DOPLŇ SVŮJ SKUTEČNÝ E-MAIL! (Např. lubos.pokorny@gmail.com)
SEC_HEADERS = {
    "User-Agent": "Lubor Pokorny (pokornyl98@gmail.com)" 
}

# --- ZLATÝ SEZNAM FONDŮ ---
SUPERINVESTORS = {
    "Warren Buffett (Berkshire Hathaway)": "1067983",
    "Michael Burry (Scion Asset Management)": "1649339",
    "Ray Dalio (Bridgewater Associates)": "1350694",
    "Bill Ackman (Pershing Square)": "1336528",
    "Howard Marks (Oaktree Capital)": "1403256",
    "Seth Klarman (Baupost Group)": "868702",
    "Stanley Druckenmiller (Duquesne Family Office)": "1501697",
    "David Tepper (Appaloosa Management)": "1006438",
    "Jim Simons (Renaissance Technologies)": "1037389",
    "Bill Gates (Gates Foundation Trust)": "1166559",
    "🔍 Jiný fond (Zadat CIK ručně)": "CUSTOM"
}

st.title(_["title"])
st.markdown(_["desc"])
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    vyber = st.selectbox(_["lbl_select"], list(SUPERINVESTORS.keys()))

with col2:
    if SUPERINVESTORS[vyber] == "CUSTOM":
        cik_input = st.text_input(_["lbl_custom"], "").strip()
    else:
        st.write("") # Prázdné místo, aby se nerozhodil design
        cik_input = SUPERINVESTORS[vyber]

if st.button(_["btn_fetch"], type="primary"):
    if not cik_input.isdigit():
        st.error(_["err_cik"])
        st.stop()
        
    cik_padded = cik_input.zfill(10) # Doplnění nulami na 10 znaků (požadavek SEC)
    
    with st.spinner(_["spin_search"]):
        url_submissions = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
        res = requests.get(url_submissions, headers=SEC_HEADERS)
        
        if res.status_code != 200:
            st.error(f"{_['err_sec']} (Kód {res.status_code})")
            st.stop()
            
        data = res.json()
        filings = data.get("filings", {}).get("recent", {})
        
        latest_13f_idx = None
        for i, form in enumerate(filings.get("form", [])):
            if form == "13F-HR":
                latest_13f_idx = i
                break
                
        if latest_13f_idx is None:
            st.error(_["err_no_13f"])
            st.stop()
            
        accession_number = filings["accessionNumber"][latest_13f_idx]
        acc_no_clean = accession_number.replace("-", "")
        
    with st.spinner(_["spin_xml"]):
        url_index = f"https://www.sec.gov/Archives/edgar/data/{cik_padded}/{acc_no_clean}/index.json"
        res_idx = requests.get(url_index, headers=SEC_HEADERS)
        xml_filename = None
        
        if res_idx.status_code == 200:
            idx_data = res_idx.json()
            for file_info in idx_data["directory"]["item"]:
                name = file_info["name"]
                if name.endswith(".xml") and "primary_doc" not in name:
                    xml_filename = name
                    break
                    
        if not xml_filename:
            xml_filename = "infotable.xml"
            
        url_xml = f"https://www.sec.gov/Archives/edgar/data/{cik_padded}/{acc_no_clean}/{xml_filename}"
        res_xml = requests.get(url_xml, headers=SEC_HEADERS)
        
        if res_xml.status_code != 200:
            st.error(f"Nepodařilo se stáhnout XML data z: {url_xml}")
            st.stop()
            
        soup = BeautifulSoup(res_xml.content, 'xml')
        positions = []
        
        for infoTable in soup.find_all('infoTable'):
            try:
                name = infoTable.find('nameOfIssuer').text if infoTable.find('nameOfIssuer') else ""
                titleClass = infoTable.find('titleOfClass').text if infoTable.find('titleOfClass') else ""
                value = float(infoTable.find('value').text) * 1000 
                
                shrs_tag = infoTable.find('shrsOrPrnAmt')
                shares = float(shrs_tag.find('sshPrnamt').text) if shrs_tag and shrs_tag.find('sshPrnamt') else 0
                
                positions.append({
                    _["col_name"]: name.upper(),
                    _["col_class"]: titleClass.upper(),
                    _["col_val"]: value,
                    _["col_shares"]: shares
                })
            except Exception:
                continue
                
    if positions:
        df = pd.DataFrame(positions)
        df = df.groupby([_["col_name"], _["col_class"]]).sum().reset_index()
        df = df.sort_values(by=_["col_val"], ascending=False).reset_index(drop=True)
        
        st.success(_["succ"])
        st.markdown(f"**Fond:** {vyber} | **Zdrojový dokument (XML):** [Zobrazit na webu SEC]({url_xml})")
        
        st.subheader(_["h_table"])
        
        formatted_df = df.style.format({
            _["col_val"]: "${:,.0f}",
            _["col_shares"]: "{:,.0f}"
        })
        st.dataframe(formatted_df, use_container_width=True)
