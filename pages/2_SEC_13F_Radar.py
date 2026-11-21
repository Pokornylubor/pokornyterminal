import streamlit as st
import pandas as pd
import json
import os
import sys
import random
import subprocess
import urllib.request
import urllib.error
from datetime import datetime
from zoneinfo import ZoneInfo

# --- INITIAL SETUP ---
st.set_page_config(page_title="POKORNY TERMINAL | 13F REPORTY", layout="wide", initial_sidebar_state="collapsed")

# --- DIRECTORY MANAGEMENT ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)
WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")
SEC_DATA_DIR = os.path.join(hlavni_slozka, "sec_data")
ARCHIVE_13F_FILE = os.path.join(hlavni_slozka, "sec_13f_archive.json")

try:
    import sec_updater
except Exception:
    pass

import menu
menu.vykresli_menu()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0"
]

# --- INSTITUTIONAL DARK CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
.stApp { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
.sec-sec-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    font-weight: 600;
    color: #71717A;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin: 18px 0 10px 0;
}
.sec-memo-box {
    width: 100%;
    padding: 24px 28px;
    background-color: #0D0F12;
    border: 1px solid #1F2227;
    border-radius: 6px;
    margin: 14px 0 18px 0;
}
.sec-memo-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #71717A;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid #1F2227;
}
</style>
""", unsafe_allow_html=True)

current_lang = st.session_state.get("lang", "CZ")

# --- DICTIONARY ---
t = {
    "CZ": {
        "title": "SEC 13F REPORTY",
        "desc": "BLESKOVÉ NAČÍTÁNÍ HISTORICKÝCH DAT PORTFOLIÍ ZE SEC EDGAR, AI ROZBOR A KONSENZUS SUPERINVESTORŮ.",
        "exp_db": "SPRÁVA DATABÁZE (PŘIDAT / UPRAVIT / SMAZAT)",
        "tab_ptf": "PORTFOLIO (13F)",
        "tab_ai": "AI ANALÝZA FONDU",
        "tab_master": "SOUHRN VŠECH 13F (SMART MONEY)",
        "sel_inv": "VÝBĚR A VYHLEDÁVÁNÍ 13F REPORTU:",
        "cik_lbl": "CIK KÓD:",
        "name_lbl": "NÁZEV FONDU:",
        "save_new": "ULOŽIT NOVÝ FOND",
        "edit_btn": "ULOŽIT ÚPRAVY",
        "succ_save": "SYSTÉM AKTUALIZOVÁN A ULOŽEN NA GITHUB.",
        "succ_edit": "FOND BYL ÚSPĚŠNĚ UPRAVEN A ULOŽEN.",
        "btn_upd": "VYNUTIT AKTUALIZACI (SEC)",
        "spin_upd": "STAHOVÁNÍ ČERSTVÝCH DAT PŘÍMO ZE SEC...",
        "warn_nodata": "DATA PRO TENTO REPORT NEJSOU STAŽENA. KLIKNĚTE NA 'VYNUTIT AKTUALIZACI'.",
        "ai_no_key": "Pro AI analýzu nastavte GROQ_API_KEY v Secrets a vyberte model v Nastavení.",
        "ai_sel_first": "Nejdříve vyberte fond v záložce PORTFOLIO (13F).",
        "ai_gen_btn": "Vygenerovat hloubkovou AI 13F analýzu fondu",
        "ai_spin": "AI zpracovává detailní rozbor 13F pozic, valuací a rotace kapitálu...",
        "ai_save": "Uložit do sec_13f_archive.json (GitHub)",
        "ai_saved_ok": "Analýza uložena do sec_13f_archive.json a synchronizována na GitHub.",
        "ai_already_saved": "Tato 13F analýza je již uložená.",
        "ai_hide": "Skrýt analýzu",
        "ai_chat_h": "KONZULTACE S AI NAD 13F REPORTEM",
        "ai_chat_ph": "Vyhledat...",
        "ai_new_chat": "Nový chat",
        "ai_saved_list": "ULOŽENÉ 13F ANALÝZY",
        "ai_load": "Načíst",
        "ai_del": "Smazat",
        "m_btn": "Vygenerovat institucionální Master 13F report všech subjektů (AI)",
        "m_spin": "Agregace všech subjektů a generování Master 13F reportu...",
        "m_copy_lbl": "PODKLAD PRO TÝDENNÍ TRŽNÍ VÝHLED (KOPÍROVATELNÝ MARKDOWN)",
        "m_saved_list": "ULOŽENÉ MASTER 13F SOUHRNY",
        "m_no_funds": "Ve složce sec_data/ zatím nejsou staženy žádné 13F reporty.",
        "m_top_own": "Nejčastěji držené akcie (Konsenzus)",
        "m_top_buy": "Nejvíce nakupované / nové pozice",
        "m_top_sell": "Nejvíce prodávané / redukované pozice"
    },
    "EN": {
        "title": "SEC 13F REPORTS",
        "desc": "HISTORICAL PORTFOLIO DATA FROM SEC EDGAR, AI FUND ANALYSIS & SUPERINVESTOR CONSENSUS.",
        "exp_db": "DATABASE MANAGEMENT (ADD / EDIT / DELETE)",
        "tab_ptf": "PORTFOLIO (13F)",
        "tab_ai": "AI FUND ANALYSIS",
        "tab_master": "MASTER 13F SYNTHESIS",
        "sel_inv": "SELECT AND SEARCH 13F REPORT:",
        "cik_lbl": "CIK CODE:",
        "name_lbl": "FUND NAME:",
        "save_new": "COMMIT NEW FUND",
        "edit_btn": "SAVE EDITS",
        "succ_save": "SYSTEM UPDATED AND COMMITTED TO GITHUB.",
        "succ_edit": "FUND SUCCESSFULLY EDITED AND SAVED.",
        "btn_upd": "FORCE UPDATE (SEC)",
        "spin_upd": "DOWNLOADING FRESH DATA FROM SEC...",
        "warn_nodata": "DATA FOR THIS REPORT NOT DOWNLOADED YET. CLICK 'FORCE UPDATE'.",
        "ai_no_key": "Configure GROQ_API_KEY in Secrets and select a model in Settings.",
        "ai_sel_first": "Select a fund in the PORTFOLIO (13F) tab first.",
        "ai_gen_btn": "Generate Deep AI 13F Fund Analysis",
        "ai_spin": "AI is generating deep 13F position, valuation and capital rotation analysis...",
        "ai_save": "Save to sec_13f_archive.json (GitHub)",
        "ai_saved_ok": "Analysis saved to sec_13f_archive.json and synced to GitHub.",
        "ai_already_saved": "This 13F analysis is already saved.",
        "ai_hide": "Hide analysis",
        "ai_chat_h": "AI 13F CONSULTATION",
        "ai_chat_ph": "Search...",
        "ai_new_chat": "Clear chat",
        "ai_saved_list": "SAVED 13F ANALYSES",
        "ai_load": "Load",
        "ai_del": "Delete",
        "m_btn": "Generate Institutional Master 13F Synthesis Across All Entities (AI)",
        "m_spin": "Aggregating all entities and generating Master 13F report...",
        "m_copy_lbl": "EXPORT FOR WEEKLY MARKET OUTLOOK (COPYABLE MARKDOWN)",
        "m_saved_list": "SAVED MASTER 13F SYNTHESES",
        "m_no_funds": "No downloaded 13F reports found in sec_data/ yet.",
        "m_top_own": "Most Owned Stocks (Consensus)",
        "m_top_buy": "Most Bought / New Positions",
        "m_top_sell": "Most Sold / Reduced Positions"
    }
}
_ = t.get(current_lang, t["CZ"])

st.title(_["title"])
st.caption(_["desc"])

# --- GITHUB & DATA HELPERS ---
def git_sync_file(file_path, commit_msg):
    try:
        if "GITHUB_TOKEN" in st.secrets:
            token = st.secrets["GITHUB_TOKEN"]
            owner = st.secrets["GITHUB_OWNER"]
            repo = st.secrets["GITHUB_REPO"]
            remote_url = f"https://{owner}:{token}@github.com/{owner}/{repo}.git"
            subprocess.run(["git", "config", "--global", "user.email", "bot@pokornyterminal.cz"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "config", "--global", "user.name", "Terminal Bot"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "pull", "--rebase", remote_url, "main"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "add", file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "commit", "-m", commit_msg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["git", "push", remote_url, "HEAD:main"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def load_full_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                if isinstance(d, dict):
                    if "saved_ciks" not in d:
                        d["saved_ciks"] = {}
                    return d
        except Exception:
            pass
    return {"portfolio": [], "watchlist": [], "saved_ciks": {}, "settings": {}}

def save_full_watchlist(data):
    with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    git_sync_file(WATCHLIST_FILE, "13F: Aktualizace seznamu fondu v watchlist.json")

def load_13f_archive():
    if os.path.exists(ARCHIVE_13F_FILE):
        try:
            with open(ARCHIVE_13F_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                if isinstance(d, list):
                    return d
        except Exception:
            pass
    return []

def save_13f_archive(archive_list, commit_msg="13F: Aktualizace sec_13f_archive.json"):
    with open(ARCHIVE_13F_FILE, "w", encoding="utf-8") as f:
        json.dump(archive_list, f, indent=4, ensure_ascii=False)
    git_sync_file(ARCHIVE_13F_FILE, commit_msg)

def format_val(val):
    if val is None or pd.isna(val) or val <= 0:
        return "N/A"
    if val >= 1e9:
        return f"${val / 1e9:,.2f} B"
    if val >= 1e6:
        return f"${val / 1e6:,.2f} M"
    return f"${val:,.0f}"

# --- GROQ / OPENAI DYNAMIC API ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_groq_available_models(api_klic):
    try:
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {api_klic}", "User-Agent": random.choice(USER_AGENTS)}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            items = json.loads(resp.read().decode("utf-8")).get("data", [])
            skip = ("whisper", "tts", "guard", "prompt-guard", "orpheus")
            return [m["id"] for m in items if m.get("id") and not any(s in m["id"].lower() for s in skip)]
    except Exception:
        return []

def call_llm_api(messages, api_klic, provider, model_name, temperature=0.2, timeout=45, max_tokens=2600):
    url = "https://api.groq.com/openai/v1/chat/completions" if provider == "Groq" else "https://api.openai.com/v1/chat/completions"
    models_to_try = [model_name]
    if provider == "Groq":
        for m in get_groq_available_models(api_klic):
            if m not in models_to_try:
                models_to_try.append(m)

    last_err = ""
    for mdl in models_to_try:
        payload = json.dumps({
            "model": mdl,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload,
            headers={"Authorization": f"Bearer {api_klic}", "Content-Type": "application/json", "User-Agent": random.choice(USER_AGENTS)},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            err_txt = e.read().decode("utf-8", errors="ignore")[:250]
            last_err = f"HTTP {e.code}: {err_txt}"
            if e.code in (400, 404, 413, 429) and mdl != models_to_try[-1]:
                continue
            raise RuntimeError(last_err)
    raise RuntimeError(last_err)

# --- 13F DATA COMPACT EXTRACTOR ---
def get_stock_col(df):
    for c in ["Stock", "Ticker", "Symbol", "Company", "Issuer"]:
        if c in df.columns:
            return c
    return df.columns[0]

def extract_fund_summary_dict(fund_name, meta, df):
    stock_col = get_stock_col(df)
    df_c = df.copy()
    if "% of Portfolio" in df_c.columns:
        df_c["_pct"] = pd.to_numeric(df_c["% of Portfolio"], errors="coerce").fillna(0.0)
        df_c = df_c.sort_values("_pct", ascending=False)
    else:
        df_c["_pct"] = 0.0

    top5 = round(float(df_c["_pct"].head(5).sum()), 2)
    top10 = round(float(df_c["_pct"].head(10).sum()), 2)

    def row_to_str(r):
        val_num = float(r["Value"]) if pd.notna(r.get("Value")) else None
        rep_p = f"${float(r['ReportedPrice*']):.2f}" if pd.notna(r.get("ReportedPrice*")) else "-"
        cur_p = f"${float(r['Current Price']):.2f}" if pd.notna(r.get("Current Price")) else "-"
        diff_p = f"{float(r['+/-Reported Price']):+.1f}%" if pd.notna(r.get("+/-Reported Price")) else "-"
        return f"{r.get(stock_col, '')} | Váha: {float(r.get('_pct', 0.0)):.2f}% | Aktivita: {r.get('RecentActivity', '')} | Hodnota: {format_val(val_num)} | RepCena: {rep_p} | AktCena: {cur_p} ({diff_p})"

    top_15 = [row_to_str(r) for _, r in df_c.head(15).iterrows()]

    act_col = df_c["RecentActivity"].astype(str) if "RecentActivity" in df_c.columns else pd.Series([""] * len(df_c))
    new_pos = [row_to_str(r) for _, r in df_c[act_col.str.contains("New|Buy", case=False, na=False)].head(10).iterrows()]
    adds = [row_to_str(r) for _, r in df_c[act_col.str.contains("Add", case=False, na=False)].head(10).iterrows()]
    reduces = [row_to_str(r) for _, r in df_c[act_col.str.contains("Reduce|Sell", case=False, na=False)].head(10).iterrows()]

    return {
        "fund": fund_name,
        "quarter": meta.get("kvartal", "N/A"),
        "report_date": meta.get("report_date", "N/A"),
        "total_positions": int(len(df_c)),
        "top5_concentration_pct": top5,
        "top10_concentration_pct": top10,
        "top_15_holdings": top_15,
        "new_positions": new_pos,
        "major_adds": adds,
        "major_reduces_sells": reduces
    }

def build_master_13f_aggregation(all_funds_dict, target_quarter=None):
    raw_funds = []
    for f_name, raw_cik in all_funds_dict.items():
        cik = str(raw_cik).zfill(10)
        csv_p = os.path.join(SEC_DATA_DIR, f"{cik}.csv")
        meta_p = os.path.join(SEC_DATA_DIR, f"{cik}_meta.json")
        if not (os.path.exists(csv_p) and os.path.exists(meta_p)):
            continue
        try:
            with open(meta_p, "r", encoding="utf-8") as fm:
                meta = json.load(fm)
            df = pd.read_csv(csv_p)
            if not df.empty:
                raw_funds.append((f_name, meta, df))
        except Exception:
            continue

    if not raw_funds:
        return [], [], [], pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    all_quarters = sorted({m.get("kvartal", "") for _, m, _ in raw_funds if m.get("kvartal")}, reverse=True)
    use_q = target_quarter if target_quarter in all_quarters else (all_quarters[0] if all_quarters else None)

    own_map, buy_map, sell_map = {}, {}, {}
    funds_meta_list = []
    funds_compact_lines = []

    for f_name, meta, df in raw_funds:
        if use_q and meta.get("kvartal") != use_q:
            continue
        stock_col = get_stock_col(df)
        short_f = f_name.split("(")[0].strip()

        df_f = df.copy()
        df_f["_pct"] = pd.to_numeric(df_f.get("% of Portfolio", 0), errors="coerce").fillna(0.0)
        df_f = df_f.sort_values("_pct", ascending=False)

        funds_meta_list.append({
            "fund": short_f,
            "quarter": meta.get("kvartal", ""),
            "positions": len(df_f)
        })

        act_s = df_f["RecentActivity"].astype(str) if "RecentActivity" in df_f.columns else pd.Series([""] * len(df_f))
        t3 = ", ".join([f"{r[stock_col]} {r['_pct']:.1f}%" for _, r in df_f.head(3).iterrows()])
        b3 = ", ".join([f"{r[stock_col]} ({r['RecentActivity']})" for _, r in df_f[act_s.str.contains("Buy|Add|New", case=False, na=False)].head(3).iterrows()])
        s3 = ", ".join([f"{r[stock_col]} ({r['RecentActivity']})" for _, r in df_f[act_s.str.contains("Reduce|Sell", case=False, na=False)].head(3).iterrows()])
        funds_compact_lines.append(f"- {short_f} ({len(df_f)} pozic): Top3=[{t3}] | Nákupy=[{b3}] | Prodeje=[{s3}]")

        for _, r in df_f.iterrows():
            stk = str(r.get(stock_col, "")).strip()
            if not stk or stk.lower() == "nan":
                continue
            pct = float(r["_pct"])
            act = str(r.get("RecentActivity", "")).strip()

            if stk not in own_map:
                own_map[stk] = {"Stock": stk, "Funds": 0, "Avg Weight %": 0.0, "_sum_w": 0.0, "Buyers": 0, "Sellers": 0, "Managers": []}
            own_map[stk]["Funds"] += 1
            own_map[stk]["_sum_w"] += pct
            if len(own_map[stk]["Managers"]) < 5:
                own_map[stk]["Managers"].append(short_f)

            if any(k in act for k in ("Buy", "Add", "New")):
                own_map[stk]["Buyers"] += 1
                if stk not in buy_map:
                    buy_map[stk] = {"Stock": stk, "Buy/Add Count": 0, "Managers": []}
                buy_map[stk]["Buy/Add Count"] += 1
                buy_map[stk]["Managers"].append(f"{short_f} ({act})")
            elif any(k in act for k in ("Reduce", "Sell")):
                own_map[stk]["Sellers"] += 1
                if stk not in sell_map:
                    sell_map[stk] = {"Stock": stk, "Sell/Reduce Count": 0, "Managers": []}
                sell_map[stk]["Sell/Reduce Count"] += 1
                sell_map[stk]["Managers"].append(f"{short_f} ({act})")

    for v in own_map.values():
        v["Avg Weight %"] = round(v["_sum_w"] / max(1, v["Funds"]), 2)
        v["Net_Fund_Count_Diff"] = v["Buyers"] - v["Sellers"]
        v["Managers"] = ", ".join(v["Managers"])
        del v["_sum_w"]
    for v in buy_map.values():
        v["Managers"] = ", ".join(v["Managers"][:6])
    for v in sell_map.values():
        v["Managers"] = ", ".join(v["Managers"][:6])

    df_own = pd.DataFrame(sorted(own_map.values(), key=lambda x: (x["Funds"], x["Avg Weight %"]), reverse=True)[:20])
    df_buy = pd.DataFrame(sorted(buy_map.values(), key=lambda x: x["Buy/Add Count"], reverse=True)[:20])
    df_sell = pd.DataFrame(sorted(sell_map.values(), key=lambda x: x["Sell/Reduce Count"], reverse=True)[:20])

    return all_quarters, funds_meta_list, funds_compact_lines, df_own, df_buy, df_sell

# --- LOAD DATA & SETTINGS ---
app_data = load_full_watchlist()
ALL_FUNDS = app_data.get("saved_ciks", {})
fund_names = sorted(list(ALL_FUNDS.keys()))
saved_settings = app_data.get("settings", {})

api_key = str(st.secrets.get("GROQ_API_KEY", "")).strip()
model_provider = st.session_state.get("ai_provider", saved_settings.get("ai_provider", "Groq"))
selected_model = st.session_state.get("ai_model", saved_settings.get("ai_model", ""))

# --- SESSION STATE ---
for k, v in [
    ("sec_sel_fund", None),
    ("sec_ai_memo", None),
    ("sec_ai_saved_id", None),
    ("sec_ai_chat", []),
    ("sec_master_obj", None),
    ("sec_master_saved_id", None)
]:
    if k not in st.session_state:
        st.session_state[k] = v

# --- SEKCE SPRÁVY DATABÁZE ---
with st.expander(_["exp_db"], expanded=False):
    akce = st.radio("Zvolte operaci:", ["Přidat", "Upravit", "Smazat"], horizontal=True, label_visibility="collapsed")
    st.markdown("---")

    if akce == "Přidat":
        cik_input = st.text_input(_["cik_lbl"], "").strip()
        novy_nazev = st.text_input(_["name_lbl"], "").strip()
        if cik_input and novy_nazev and st.button(_["save_new"], use_container_width=True):
            app_data["saved_ciks"][novy_nazev] = cik_input
            save_full_watchlist(app_data)
            st.success(_["succ_save"])
            st.rerun()

    elif akce == "Upravit":
        if not fund_names:
            st.info("Databáze je prázdná.")
        else:
            fond_k_uprave = st.selectbox("Vyber fond k úpravě:", options=fund_names)
            if fond_k_uprave:
                aktualni_cik = str(ALL_FUNDS[fond_k_uprave])
                novy_cik = st.text_input(_["cik_lbl"], aktualni_cik).strip()
                novy_nazev = st.text_input(_["name_lbl"], fond_k_uprave).strip()
                if st.button(_["edit_btn"], use_container_width=True):
                    if novy_nazev and novy_cik:
                        if novy_nazev != fond_k_uprave:
                            del app_data["saved_ciks"][fond_k_uprave]
                        app_data["saved_ciks"][novy_nazev] = novy_cik
                        save_full_watchlist(app_data)
                        st.success(_["succ_edit"])
                        st.rerun()
                    else:
                        st.warning("Název i CIK musí být vyplněny.")

    elif akce == "Smazat":
        if not fund_names:
            st.info("Databáze je prázdná.")
        else:
            fond_k_odstraneni = st.selectbox("Vyber fond k odstranění:", options=fund_names)
            if st.button("TRVALE SMAZAT FOND", use_container_width=True):
                del app_data["saved_ciks"][fond_k_odstraneni]
                save_full_watchlist(app_data)
                st.success(f"Fond '{fond_k_odstraneni}' byl odstraněn.")
                st.rerun()

st.markdown("---")

# --- MAIN TABS ---
tab_ptf, tab_ai, tab_master = st.tabs([_["tab_ptf"], _["tab_ai"], _["tab_master"]])

active_fund_name = None
active_cik = None
active_meta = None
active_df = None

with tab_ptf:
    if not fund_names:
        st.info("Databáze je prázdná. Přidejte fond v sekci 'SPRÁVA DATABÁZE'.")
    else:
        ph_search = "Vyhledat..." if current_lang == "CZ" else "Search..."
        vyber = st.selectbox(_["sel_inv"], options=fund_names, index=None, placeholder=ph_search)

        if vyber != st.session_state.sec_sel_fund:
            st.session_state.sec_sel_fund = vyber
            st.session_state.sec_ai_memo = None
            st.session_state.sec_ai_saved_id = None
            st.session_state.sec_ai_chat = []

        if vyber:
            active_fund_name = vyber
            active_cik = str(ALL_FUNDS[vyber]).zfill(10)
            csv_path = os.path.join(SEC_DATA_DIR, f"{active_cik}.csv")
            meta_path = os.path.join(SEC_DATA_DIR, f"{active_cik}_meta.json")

            c_upd = st.columns([4, 1])[1]
            with c_upd:
                if st.button(_["btn_upd"], use_container_width=True):
                    with st.spinner(_["spin_upd"]):
                        sec_updater.update_sec_funds(target_cik=active_cik)
                        git_sync_file("sec_data/", f"Okamžité stažení 13F reportu (CIK: {active_cik})")
                    st.rerun()

            if os.path.exists(csv_path) and os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    active_meta = json.load(f)
                active_df = pd.read_csv(csv_path)

                rep_str = "Reported:" if current_lang == "EN" else "Zobrazen report:"
                asof_str = "As of" if current_lang == "EN" else "Ke dni"
                last_str = "Last updated:" if current_lang == "EN" else "Naposledy staženo:"

                st.info(
                    f"**{vyber.split('(')[0].strip()}** | "
                    f"{rep_str} **{active_meta.get('kvartal', '')}** ({asof_str} {active_meta.get('report_date', '')}) | "
                    f"*{last_str} {active_meta.get('last_updated', '')}*"
                )

                df_disp = active_df.copy()
                df_disp[" "] = ""

                def style_df(row):
                    styles = [''] * len(row)
                    act_val = str(row.get('RecentActivity', ''))
                    if "Buy" in act_val or "Add" in act_val or "New" in act_val:
                        styles[2] = 'color: #26A69A; font-weight: bold;'
                    elif "Reduce" in act_val or "Sell" in act_val:
                        styles[2] = 'color: #EF5350; font-weight: bold;'
                    if pd.notnull(row.get('+/-Reported Price')):
                        try:
                            val = float(row['+/-Reported Price'])
                            if val > 0: styles[8] = 'color: #26A69A;'
                            elif val < 0: styles[8] = 'color: #EF5350;'
                        except Exception:
                            pass
                    return styles

                styled_df = df_disp.style.apply(style_df, axis=1).format({
                    "% of Portfolio": "{:.2f}%",
                    "Shares": "{:,.0f}",
                    "ReportedPrice*": "${:,.2f}",
                    "Value": "${:,.0f}",
                    "Current Price": lambda x: f"${x:,.2f}" if pd.notnull(x) else "",
                    "+/-Reported Price": lambda x: f"{x:+.2f}%" if pd.notnull(x) else "",
                    "52Week Low": lambda x: f"${x:,.2f}" if pd.notnull(x) else "",
                    "52Week High": lambda x: f"${x:,.2f}" if pd.notnull(x) else ""
                })
                st.dataframe(styled_df, use_container_width=True, hide_index=True, height=650)
            else:
                st.warning(_["warn_nodata"])

all_13f_archive = load_13f_archive()

with tab_ai:
    if not api_key or not selected_model:
        st.warning(_["ai_no_key"])
    elif not active_fund_name or active_df is None or active_meta is None:
        st.info(_["ai_sel_first"])
    else:
        short_fund = active_fund_name.split("(")[0].strip()
        fund_summary_dict = extract_fund_summary_dict(short_fund, active_meta, active_df)
        fund_json_str = json.dumps(fund_summary_dict, ensure_ascii=False, default=str)

        if st.button(_["ai_gen_btn"], type="primary", use_container_width=True):
            now_dt = datetime.now(ZoneInfo("Europe/Prague"))
            datum_str = now_dt.strftime("%d. %m. %Y %H:%M")
            lang_instr = "spisovnou, přirozenou češtinou bez cizích slov v hlavičkách tabulek" if current_lang == "CZ" else "in clean institutional English"
            prompt_13f = f"""Jsi seniorní institucionální akciový analytik a portfolio manažer. Dnešní datum je {datum_str}.
Na základě PŘESNĚ TĚCHTO 13F dat subjektu {short_fund} (kvartál {active_meta.get('kvartal', '')}) vypracuj podrobný institucionální report {lang_instr} (rozsah cca 500–700 slov, začni rovnou bodem 1).

PŘÍSNÁ PRAVIDLA:
- Piš výhradně spisovnou češtinou, nikdy nepoužívej slova jako „Título“ ani zastaralé fráze („oživení po pandemii“, „metaverse“).
- Neuváděj žádné odhady celkového AUM fondu.
- „Buy 100 %“ znamená otevření zcela nové pozice v daném kvartálu; „Add“ znamená navýšení již existující pozice.
- Používej výhradně čísla z přiložených dat a nevymýšlej si cizí tickery.

1. **STRUKTURA PORTFOLIA, KONCENTRACE & HLAVNÍ SÁZKY**
   - Rozeber počet pozic ({fund_summary_dict.get('total_positions', 0)}) a koncentraci v Top 5 ({fund_summary_dict.get('top5_concentration_pct', 0)} %) a Top 10 ({fund_summary_dict.get('top10_concentration_pct', 0)} %).
   - Rozeber jednotlivě 5 až 7 největších pozic včetně jejich přesné váhy v portfoliu a co o investičním stylu vypovídají.

2. **NEJDŮLEŽITĚJŠÍ NÁKUPY A NOVÉ POZICE (OFENZIVNÍ ALOKACE)**
   - Podrobně rozeber všechny významné nové pozice („Buy 100 %“) a největší navýšení („Add“), uveď přesná procenta změny a váhu v portfoliu.

3. **VÝRAZNÉ REDUKCE A KOMPLETNÍ VÝSTUPY (REALIZACE ZISKŮ)**
   - Detailně rozeber největší redukce a prodeje, uveď přesná čísla a zhodnoť, zda jde o vybírání zisků, nebo o odchod ze sektoru.

4. **VALUAČNÍ PŘÍLEŽITOSTI & ZÁVĚR PRO INVESTORA**
   - Porovnej nahlášené ceny (`RepCena`) s aktuální tržní cenou (`AktCena`) a vypíchni tituly, které se nyní obchodují pod nahlášenou cenou.

Data 13F:
{fund_json_str}"""
            with st.spinner(_["ai_spin"]):
                try:
                    memo_txt = call_llm_api([{"role": "user", "content": prompt_13f}], api_key, model_provider, selected_model, temperature=0.2, timeout=45, max_tokens=2600)
                    rep_id = f"{now_dt.strftime('%Y%m%d_%H%M%S')}_13F_{active_cik}"
                    st.session_state.sec_ai_memo = {
                        "id": rep_id,
                        "datum": datum_str,
                        "typ": "13F FOND",
                        "cik": active_cik,
                        "fond": short_fund,
                        "kvartal": active_meta.get("kvartal", ""),
                        "hlavni_nadpis": f"13F Analýza: {short_fund} ({active_meta.get('kvartal', '')})",
                        "obsah": memo_txt,
                        "chat": []
                    }
                    st.session_state.sec_ai_saved_id = None
                    st.session_state.sec_ai_chat = []
                except Exception as e:
                    st.error(f"AI Error: {e}")

        if st.session_state.sec_ai_memo:
            m_obj = st.session_state.sec_ai_memo
            st.markdown(
                f'<div class="sec-memo-box">'
                f'<div class="sec-memo-meta">{m_obj.get("datum", "")}  ·  13F ANALÝZA  ·  {m_obj.get("fond", "")} ({m_obj.get("kvartal", "")})</div>',
                unsafe_allow_html=True
            )
            st.markdown(m_obj.get("obsah", ""))
            st.markdown('</div>', unsafe_allow_html=True)

            saved_chat_len = len(m_obj.get("chat", []))
            curr_chat_len = len(st.session_state.sec_ai_chat)
            has_unsaved_chat = (st.session_state.sec_ai_saved_id == m_obj["id"] and curr_chat_len != saved_chat_len)

            c_a1, c_a2 = st.columns([4, 1.2])
            with c_a1:
                if st.session_state.sec_ai_saved_id == m_obj["id"] and not has_unsaved_chat:
                    st.info(_["ai_already_saved"])
                else:
                    btn_lbl = (
                        f"Aktualizovat 13F Analýzu + Chat ({curr_chat_len} zpráv) na GitHub"
                        if has_unsaved_chat else _["ai_save"]
                    )
                    if st.button(btn_lbl, key="save_13f_btn"):
                        arch = load_13f_archive()
                        m_obj["chat"] = list(st.session_state.sec_ai_chat)
                        idx_ex = next((i for i, x in enumerate(arch) if x.get("id") == m_obj["id"]), None)
                        if idx_ex is not None:
                            arch[idx_ex] = m_obj
                        else:
                            arch.insert(0, m_obj)
                        save_13f_archive(arch, commit_msg=f"13F: Uložena analýza {short_fund} ({m_obj.get('kvartal', '')})")
                        st.session_state.sec_ai_memo = m_obj
                        st.session_state.sec_ai_saved_id = m_obj["id"]
                        st.success(_["ai_saved_ok"])
            with c_a2:
                if st.button(_["ai_hide"], use_container_width=True, key="hide_13f_btn"):
                    st.session_state.sec_ai_memo = None
                    st.session_state.sec_ai_saved_id = None
                    st.rerun()

        c_ch1, c_ch2 = st.columns([5, 1.2])
        c_ch1.markdown(f'<div class="sec-sec-label">{_["ai_chat_h"]}</div>', unsafe_allow_html=True)
        if st.session_state.sec_ai_chat:
            if c_ch2.button(_["ai_new_chat"], use_container_width=True, key="clr_13f_chat"):
                st.session_state.sec_ai_chat = []
                st.rerun()

        for msg in st.session_state.sec_ai_chat:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if q_13f := st.chat_input(_["ai_chat_ph"], key="sec_13f_chat_input"):
            st.session_state.sec_ai_chat.append({"role": "user", "content": q_13f})
            with st.chat_message("user"):
                st.markdown(q_13f)
            with st.chat_message("assistant"):
                with st.spinner(_["ai_spin"]):
                    lang_reply = "Odpovídej čistou češtinou, podrobně a věcně." if current_lang == "CZ" else "Answer in clean, detailed English."
                    msgs = [{"role": "system", "content": f"Jsi Senior Equity Analyst. Máš přesný výtah 13F portfolia subjektu {short_fund}: {fund_json_str}. {lang_reply}"}]
                    for m in st.session_state.sec_ai_chat[-6:-1]:
                        msgs.append({"role": m["role"], "content": m["content"]})
                    msgs.append({"role": "user", "content": q_13f})
                    try:
                        ans = call_llm_api(msgs, api_key, model_provider, selected_model, temperature=0.2, timeout=30, max_tokens=1200)
                    except Exception as e:
                        ans = f"AI Error ({e})."
                    st.markdown(ans)
            if not ans.startswith("AI Error"):
                st.session_state.sec_ai_chat.append({"role": "assistant", "content": ans})
                st.rerun()

        saved_fund_memos = [r for r in all_13f_archive if r.get("typ") == "13F FOND" and r.get("cik") == active_cik]
        if saved_fund_memos:
            st.markdown("---")
            st.markdown(f'<div class="sec-sec-label">{_["ai_saved_list"]} ({short_fund}) · {len(saved_fund_memos)}</div>', unsafe_allow_html=True)
            for sm in saved_fund_memos:
                chat_cnt = len(sm.get("chat", []))
                chat_tag = f" · {chat_cnt} zpráv" if chat_cnt > 0 else ""
                c1, c2, c3 = st.columns([5, 1, 1])
                c1.markdown(f"`{sm.get('datum', '')}` · **{sm.get('hlavni_nadpis', '')}**{chat_tag}")
                if c2.button(_["ai_load"], key=f"load_13f_{sm.get('id')}", use_container_width=True):
                    st.session_state.sec_ai_memo = sm
                    st.session_state.sec_ai_saved_id = sm.get("id")
                    st.session_state.sec_ai_chat = list(sm.get("chat", []))
                    st.rerun()
                if c3.button(_["ai_del"], key=f"del_13f_{sm.get('id')}", use_container_width=True):
                    new_arch = [r for r in all_13f_archive if r.get("id") != sm.get("id")]
                    save_13f_archive(new_arch, commit_msg=f"13F: Smazána analýza {short_fund}")
                    if st.session_state.sec_ai_memo and st.session_state.sec_ai_memo.get("id") == sm.get("id"):
                        st.session_state.sec_ai_memo = None
                        st.session_state.sec_ai_chat = []
                    st.rerun()

with tab_master:
    all_quarters, funds_meta_list, funds_compact_lines, df_own, df_buy, df_sell = build_master_13f_aggregation(ALL_FUNDS)

    if not funds_meta_list:
        st.info(_["m_no_funds"])
    else:
        active_q = all_quarters[0] if all_quarters else ""
        st.caption(f"Agregováno **{len(funds_meta_list)}** subjektů výhradně za nejnovější kvartál **{active_q}** ze složky `sec_data/`.")
        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            st.markdown(f'<div class="sec-sec-label">{_["m_top_own"]}</div>', unsafe_allow_html=True)
            if not df_own.empty:
                st.dataframe(df_own, use_container_width=True, hide_index=True, height=320)
        with mc2:
            st.markdown(f'<div class="sec-sec-label">{_["m_top_buy"]}</div>', unsafe_allow_html=True)
            if not df_buy.empty:
                st.dataframe(df_buy, use_container_width=True, hide_index=True, height=320)
        with mc3:
            st.markdown(f'<div class="sec-sec-label">{_["m_top_sell"]}</div>', unsafe_allow_html=True)
            if not df_sell.empty:
                st.dataframe(df_sell, use_container_width=True, hide_index=True, height=320)

        st.markdown("---")
        if not api_key or not selected_model:
            st.warning(_["ai_no_key"])
        else:
            if st.button(_["m_btn"], type="primary", use_container_width=True):
                now_dt = datetime.now(ZoneInfo("Europe/Prague"))
                datum_str = now_dt.strftime("%d. %m. %Y %H:%M")
                q_label = active_q or now_dt.strftime("%Y")

                own_lines = "\n".join([f"- {r['Stock']}: drží {r['Funds']} subjektů | průměrná váha v PTF {r['Avg Weight %']}% | čistý rozdíl počtu fondů (kupující mínus prodávající) = {r['Net_Fund_Count_Diff']:+d} fondů ({r['Managers']})" for _, r in df_own.head(15).iterrows()]) if not df_own.empty else "-"
                buy_lines = "\n".join([f"- {r['Stock']}: {r['Buy/Add Count']}x nákup/navýšení ({r['Managers']})" for _, r in df_buy.head(15).iterrows()]) if not df_buy.empty else "-"
                sell_lines = "\n".join([f"- {r['Stock']}: {r['Sell/Reduce Count']}x prodej/redukce ({r['Managers']})" for _, r in df_sell.head(15).iterrows()]) if not df_sell.empty else "-"
                funds_lines_txt = "\n".join(funds_compact_lines)

                lang_instr = "výhradně spisovnou, přirozenou češtinou bez překlepů" if current_lang == "CZ" else "in clean institutional English"
                master_prompt = f"""Jsi seniorní institucionální akciový analytik. Tvým úkolem je vytvořit hutný, analyticky přesný a kompletní „MASTER 13F SOUHRN“ pro čtvrtletí {q_label} (data zveřejněná v listopadu 2026) napříč {len(funds_meta_list)} sledovanými subjekty výhradně na základě níže přiložených dat z hlášení 13F.
Celý výstup musí mít rozsah cca 700–800 slov, aby se bezpečně dokončil až do posledního slova bodu 5 bez useknutí (začni rovnou bodem 1).

PŘÍSNÁ PRAVIDLA:
1. JAZYK A OBDOBÍ: Piš {lang_instr}. Analyzuješ výhradně čtvrtletí {q_label} – vždy v celém textu uváděj přesně toto období ({q_label}) a nikdy ho nezaměňuj za jiné čtvrtletí. Nikdy nepoužívej cizí slova v hlavičkách tabulek (vždy „Titul“, nikdy „Título“).
2. DEFINICE METRIK (ZÁKAZ ZÁMĚNY JEDNOTEK A ROLÍ):
   - „Čistý rozdíl počtu fondů“ (`Net_Fund_Count_Diff`) je POČET KUPUJÍCÍCH FONDŮ MÍNUS POČET PRODÁVAJÍCÍCH FONDŮ. NIKDY k němu nepřidávej znak %!
   - Procenta (%) uváděj POUZE u změny pozice konkrétního fondu nebo váhy v portfoliu.
   - Rozlišuj striktně „Buy 100 %“ (= otevření zcela nové pozice) od „Add“ (= navýšení již držené pozice, např. Add 435.53 % není nová pozice, ale navýšení).
   - Přísně rozlišuj SUBJEKT (manažer/firma podávající 13F hlášení) a TITUL (držená akcie v portfoliu). Pokud je podavatelem hlášení samotná firma (korporátní 13F), jde o její investiční portfolio, nikdy nepřipisuj držbu akcii samotné.
3. ZÁKAZ HALUCINACÍ: Nepoužívej zastaralé fráze („pandemie“, „metaverse“), neuváděj odhady AUM a pečlivě ověřuj sektorové zařazení každé firmy (nezaměňuj zdravotnictví, energetiku, průmysl, finance a technologie).
4. KONZISTENCE: Komentář v bodě 1 musí 100% odpovídat tabulkám v bodech 2 a 3. Pokud je akcie v tabulce prodejů, popiš ji v úvodu jako historicky drženou jádrovou pozici, kde probíhá výběr zisků.

POŽADOVANÁ STRUKTURA VÝSTUPU:

1. **MAKRO & SEKTOROVÉ TRENDY SMART MONEY ({q_label})**
   - Ve 2–3 hutných odstavcích shrň hlavní rotaci kapitálu za období {q_label} (odliv vs. příliv podle rozdílu v počtu fondů).

2. **KONSENZUÁLNÍ NÁKUPY A NOVÉ POZICE**
   - Tabulka: | Titul | Počet kupujících fondů | Přehled aktivit (Manažer a změna) | (vyber 8 až 9 nejvýznamnějších titulů z dat včetně velkých technologických a tržních lídrů)
   - Pod tabulkou 3 stručné odrážky s interpretací nákupních trendů.

3. **DISTRIBUCE, REDUKCE A VÝBĚR ZISKŮ**
   - Tabulka: | Titul | Počet prodávajících fondů | Rozsah redukce a hlavní prodejci | (vyber 8 až 9 nejvýznamnějších titulů z dat včetně velkých technologických titulů, pokud jsou v datech)
   - Pod tabulkou 3 stručné odrážky k výběru zisků.

4. **PŘEHLED KLÍČOVÝCH TAHŮ HLAVNÍCH SUBJEKTŮ**
   - U 8 hlavních fondů/subjektů uveď přesně 1 stručnou větu (hlavní sázky, nákup vs. prodej; rozlišuj novou pozici vs. navýšení). Bez odhadů AUM.

5. **AKČNÍ VÝSTUP PRO TÝDENNÍ TRŽNÍ VÝHLED**
   - 5 stručných, konkrétních investičních tezí a titulů k prověření v Terminálu.

NEJČASTĚJI DRŽENÉ AKCIE ({q_label}):
{own_lines}

NEJVÍCE NAKUPOVANÉ / NOVÉ POZICE ({q_label}):
{buy_lines}

NEJVÍCE PRODÁVANÉ / REDUKOVANÉ POZICE ({q_label}):
{sell_lines}

PŘEHLED JEDNOTLIVÝCH SUBJEKTŮ ({q_label}):
{funds_lines_txt}"""

                with st.spinner(_["m_spin"]):
                    try:
                        master_txt = call_llm_api([{"role": "user", "content": master_prompt}], api_key, model_provider, selected_model, temperature=0.2, timeout=50, max_tokens=2800)
                        rep_id = f"{now_dt.strftime('%Y%m%d_%H%M%S')}_MASTER_13F"
                        st.session_state.sec_master_obj = {
                            "id": rep_id,
                            "datum": datum_str,
                            "typ": "MASTER 13F",
                            "kvartal": q_label,
                            "pocet_fondu": len(funds_meta_list),
                            "hlavni_nadpis": f"Master 13F Souhrn ({q_label} · {len(funds_meta_list)} subjektů)",
                            "obsah": master_txt
                        }
                        st.session_state.sec_master_saved_id = None
                    except Exception as e:
                        st.error(f"AI Error: {e}")

            if st.session_state.sec_master_obj:
                mo = st.session_state.sec_master_obj
                st.markdown(
                    f'<div class="sec-memo-box">'
                    f'<div class="sec-memo-meta">{mo.get("datum", "")}  ·  MASTER 13F SOUHRN  ·  {mo.get("kvartal", "")} ({mo.get("pocet_fondu", "")} subjektů)</div>',
                    unsafe_allow_html=True
                )
                st.markdown(mo.get("obsah", ""))
                st.markdown('</div>', unsafe_allow_html=True)

                cm1, cm2 = st.columns([4, 1.2])
                with cm1:
                    if st.session_state.sec_master_saved_id == mo["id"]:
                        st.info(_["ai_already_saved"])
                    else:
                        if st.button(_["ai_save"], key="save_master_13f"):
                            arch = load_13f_archive()
                            arch.insert(0, mo)
                            save_13f_archive(arch, commit_msg=f"13F: Uložen Master 13F souhrn ({mo.get('kvartal', '')})")
                            st.session_state.sec_master_saved_id = mo["id"]
                            st.success(_["ai_saved_ok"])
                with cm2:
                    if st.button(_["ai_hide"], use_container_width=True, key="hide_master_13f"):
                        st.session_state.sec_master_obj = None
                        st.session_state.sec_master_saved_id = None
                        st.rerun()

                with st.expander(_["m_copy_lbl"], expanded=False):
                    export_md = f"# {mo.get('hlavni_nadpis', '')}\nDatum: {mo.get('datum', '')}\n\n{mo.get('obsah', '')}"
                    st.code(export_md, language="markdown")

            saved_masters = [r for r in all_13f_archive if r.get("typ") == "MASTER 13F"]
            if saved_masters:
                st.markdown("---")
                st.markdown(f'<div class="sec-sec-label">{_["m_saved_list"]} · {len(saved_masters)}</div>', unsafe_allow_html=True)
                for sm in saved_masters:
                    c1, c2, c3 = st.columns([5, 1, 1])
                    c1.markdown(f"`{sm.get('datum', '')}` · **{sm.get('hlavni_nadpis', '')}**")
                    if c2.button(_["ai_load"], key=f"load_m13f_{sm.get('id')}", use_container_width=True):
                        st.session_state.sec_master_obj = sm
                        st.session_state.sec_master_saved_id = sm.get("id")
                        st.rerun()
                    if c3.button(_["ai_del"], key=f"del_m13f_{sm.get('id')}", use_container_width=True):
                        new_arch = [r for r in all_13f_archive if r.get("id") != sm.get("id")]
                        save_13f_archive(new_arch, commit_msg="13F: Smazán Master 13F souhrn")
                        if st.session_state.sec_master_obj and st.session_state.sec_master_obj.get("id") == sm.get("id"):
                            st.session_state.sec_master_obj = None
                        st.rerun()