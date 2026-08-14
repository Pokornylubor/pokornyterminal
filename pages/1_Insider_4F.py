import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Insider Trading", page_icon="🕵️‍♂️", layout="wide")

if "lang" not in st.session_state:
    st.session_state.lang = "CZ"

selected_lang = st.sidebar.radio("🌐 Jazyk / Language:", ["CZ", "EN"], index=0 if st.session_state.lang == "CZ" else 1)
if selected_lang != st.session_state.lang:
    st.session_state.lang = selected_lang
    st.rerun()

t = {
    "CZ": {
        "title": "🕵️‍♂️ Insider Nákupy (Form 4)",
        "desc": "Nejnovější nákupy a prodeje (OpenInsider). Zobrazuje kompletní staženou historii transakcí.",
        "warn_file": "⚠️ Datový soubor nebyl nalezen. Spusť nejprve program `updater.py`.",
        "disp_trans": "Zobrazeno **{}** transakcí:"
    },
    "EN": {
        "title": "🕵️‍♂️ Insider Trading (Form 4)",
        "desc": "Latest insider buys and sells (OpenInsider). Showing the complete downloaded transaction history.",
        "warn_file": "⚠️ Data file not found. Run `updater.py` first.",
        "disp_trans": "Showing **{}** transactions:"
    }
}
_ = t[st.session_state.lang]

st.title(_["title"])
st.markdown(_["desc"])

FILE_PATH = "insider_4f_db.csv"

if not os.path.exists(FILE_PATH):
    st.warning(_["warn_file"])
else:
    df = pd.read_csv(FILE_PATH)
    st.write(_["disp_trans"].format(len(df)))
    st.dataframe(df, use_container_width=True)