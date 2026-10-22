import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os
import sys
import requests
from datetime import datetime

# --- INITIAL SETUP ---
st.set_page_config(page_title="POKORNY TERMINAL | VALUATION", layout="wide", initial_sidebar_state="collapsed")

# --- DIRECTORY MANAGEMENT ---
aktualni_slozka = os.path.dirname(os.path.abspath(__file__))
hlavni_slozka = os.path.dirname(aktualni_slozka) if os.path.basename(aktualni_slozka) == "pages" else aktualni_slozka
sys.path.append(hlavni_slozka)
WATCHLIST_FILE = os.path.join(hlavni_slozka, "watchlist.json")

import menu
menu.vykresli_menu()

# --- BYPASS YAHOO BLOCKING (SESSION USER-AGENT) ---
session = requests.Session()
session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'

# --- DICTIONARY ---
t = {
    "CZ": {
        "title": "🏛️ HLOUBKOVÝ ANALYTICKÝ TERMINÁL",
        "desc": "INSTITUCIONÁLNÍ ČASOVÁ OSA VÝKAZŮ, VALUACE, KONSENZUS A ZPRÁVY.",
        "db_select": "DATABÁZE",
        "custom_tick": "VLASTNÍ TICKER",
        "periodicity": "PERIODICITA MATICE:",
        "annual": "Roční (Annual)",
        "quarterly": "Kvartální (Quarterly)",
        "loading": "STAHOVÁNÍ VÝKAZŮ...",
        "err_data": "DATA PRO TENTO TICKER NEJSOU DOSTUPNÁ.",
        "tab_matrix": "📑 FINANČNÍ MATICE & VÝHLED",
        "tab_val": "📊 VALUACE & KPI",
        "tab_ana": "🎯 ANALYTICI & KONSENZUS",
        "tab_earn": "📅 EARNINGS & HISTORIE",
        "tab_news": "📰 NOVINKY & ČLÁNKY",
        "tab_raw": "🗄️ STRUKTUROVANÁ ROZVAHA",
        "targets_h": "Wall Street Konsenzus & Cílové Ceny",
        "t_low": "Bear Target",
        "t_mean": "Konsenzus (Mean)",
        "t_high": "Bull Target",
        "t_rec": "Doporučení",
        "t_num": "Počet analytiků",
        "met_val": "VALUACE",
        "met_mul": "MULTIPLIKÁTORY & LIKVIDITA",
        "met_mar": "MARŽE (KASKÁDA)",
        "met_ret": "RENTABILITA",
        "met_ltm": "LTM (TTM) DATA",
        "r_rev": "Tržby (Revenue)",
        "r_rev_growth": " ↳ Meziroční růst tržeb (YoY)",
        "r_gp": "Hrubý zisk (Gross Profit)",
        "r_gm": " ↳ Hrubá marže (Gross Margin)",
        "r_ebit": "Provozní zisk (Operating Income / EBIT)",
        "r_om": " ↳ Provozní marže (Operating Margin)",
        "r_ni": "Čistý zisk (Net Income)",
        "r_nm": " ↳ Čistá marže (Net Margin)",
        "r_eps": "Zisk na akcii (EPS)",
        "r_fcf": "Volné cash flow (Free Cash Flow)",
        "r_fcfm": " ↳ FCF marže",
        "currency_lbl": "Měna výkazů:",
        "convert_usd": "Převést výkazy z {curr} do USD (dle historických kurzů)",
        "raw_h": "STRUKTUROVANÁ DATABÁZE VÝKAZŮ:",
        "raw_c": "Vyčištěná data z výkazů.",
        "raw_inc": "1. INCOME STATEMENT (Výkaz zisků a ztrát)",
        "raw_bal": "2. BALANCE SHEET (Rozvaha)",
        "raw_cf": "3. CASH FLOW STATEMENT (Výkaz peněžních toků)",
        "raw_na": "Výkaz není dostupný.",
        "h_de": "Celkový dluh / Vlastní kapitál.",
        "h_cr": "Běžná likvidita: Krátkodobá aktiva / Krátkodobé závazky.",
        "h_qr": "Pohotová likvidita: (Krátkodobá aktiva - Zásoby) / Krátkodobé závazky.",
        "h_roe": "Return on Equity: Čistý zisk / Vlastní kapitál.",
        "h_roic": "Return on Invested Capital.",
        "h_roa": "Return on Assets.",
        "h_roce": "Return on Capital Employed.",
        "matrix_h": "Finanční časová osa",
        "kpi_h": "KPI Dashboard",
        "kpi_pe": "P/E (Trailing)",
        "kpi_fpe": "Forward P/E",
        "kpi_peg": "PEG Ratio",
        "kpi_ps": "Cena / Tržby (P/S)",
        "kpi_pfcf": "Cena / FCF",
        "kpi_evebitda": "EV / EBITDA",
        "kpi_pb": "Cena / Účetní hodnota (P/B)",
        "kpi_de": "Dluh / Vlastní kapitál",
        "kpi_cr": "Běžná likvidita",
        "kpi_qr": "Pohotová likvidita",
        "kpi_gm": "Hrubá marže",
        "kpi_ebitdam": "EBITDA marže",
        "kpi_om": "Provozní marže",
        "kpi_nm": "Čistá marže",
        "kpi_fcfm": "FCF marže",
        "kpi_roe": "ROE",
        "kpi_roic": "ROIC",
        "kpi_roa": "ROA",
        "kpi_roce": "ROCE",
        "kpi_roi": "ROI (Proxy)",
        "kpi_rev": "LTM Tržby",
        "kpi_ebitda": "LTM EBITDA",
        "kpi_ni": "LTM Čistý zisk",
        "kpi_fcf": "LTM FCF",
        "kpi_eps": "LTM EPS",
        "bal_h": "Rozvaha",
        "bal_na": "Rozvaha není k dispozici.",
        "est_q1": "Q+1 (Odhad)",
        "est_q2": "Q+2 (Odhad)",
        "earn_next_h": "Nadcházející kvartální report",
        "earn_hist_h": "Historie překonání odhadů (Beat / Miss)",
        "earn_date_lbl": "Termín",
        "earn_eps_lbl": "Odhad EPS",
        "earn_rev_lbl": "Očekávané tržby",
        "eh_date": "Kvartál",
        "eh_act": "Skutečné EPS",
        "eh_est": "Odhad EPS",
        "eh_diff": "Rozdíl",
        "eh_surp": "Překonání odhadu (%)",
        "eh_na1": "Oficiální datum příštího reportu zatím nebylo stanoveno.",
        "eh_na2": "Termín příštích earnings není momentálně k dispozici.",
        "eh_na3": "Historie kvartálních překonání není k dispozici.",
        "eh_na4": "Historie kvartálních earnings není dostupná.",
        "news_h": "Zpravodajský feed —",
        "news_pub": "Vydavatel",
        "news_date": "Vydáno",
        "news_na": "Aktuálně nejsou dostupné žádné zprávy."
    },
    "EN": {
        "title": "🏛️ DEEP INSTITUTIONAL TERMINAL",
        "desc": "INSTITUTIONAL FINANCIAL STATEMENTS TIMELINE, VALUATION, CONSENSUS & NEWS.",
        "db_select": "DATABASE",
        "custom_tick": "CUSTOM TICKER",
        "periodicity": "MATRIX PERIODICITY:",
        "annual": "Annual",
        "quarterly": "Quarterly",
        "loading": "LOADING STATEMENTS...",
        "err_data": "DATA FOR THIS TICKER NOT AVAILABLE.",
        "tab_matrix": "📑 FINANCIAL MATRIX & OUTLOOK",
        "tab_val": "📊 VALUATION & KPIs",
        "tab_ana": "🎯 ANALYSTS & CONSENSUS",
        "tab_earn": "📅 EARNINGS & TRACK RECORD",
        "tab_news": "📰 NEWS & ARTICLES",
        "tab_raw": "🗄️ STRUCTURED BALANCE SHEET",
        "targets_h": "Wall Street Consensus & Price Targets",
        "t_low": "Bear Target",
        "t_mean": "Consensus (Mean)",
        "t_high": "Bull Target",
        "t_rec": "Recommendation",
        "t_num": "Analyst Coverage",
        "met_val": "VALUATION",
        "met_mul": "MULTIPLES & LIQUIDITY",
        "met_mar": "MARGINS (CASCADE)",
        "met_ret": "PROFITABILITY",
        "met_ltm": "LTM (TTM) DATA",
        "r_rev": "Total Revenue",
        "r_rev_growth": " ↳ Revenue Growth (YoY)",
        "r_gp": "Gross Profit",
        "r_gm": " ↳ Gross Margin",
        "r_ebit": "Operating Income (EBIT)",
        "r_om": " ↳ Operating Margin",
        "r_ni": "Net Income",
        "r_nm": " ↳ Net Margin",
        "r_eps": "Diluted EPS",
        "r_fcf": "Free Cash Flow (FCF)",
        "r_fcfm": " ↳ FCF Margin",
        "currency_lbl": "Reporting Currency:",
        "convert_usd": "Convert statements from {curr} to USD (using historical rates)",
        "raw_h": "STRUCTURED STATEMENTS DATABASE:",
        "raw_c": "Cleaned statement data.",
        "raw_inc": "1. INCOME STATEMENT",
        "raw_bal": "2. BALANCE SHEET",
        "raw_cf": "3. CASH FLOW STATEMENT",
        "raw_na": "Statement not available.",
        "h_de": "Total Debt / Total Equity.",
        "h_cr": "Current Ratio: Current Assets / Current Liabilities.",
        "h_qr": "Quick Ratio.",
        "h_roe": "Return on Equity.",
        "h_roic": "Return on Invested Capital.",
        "h_roa": "Return on Assets.",
        "h_roce": "Return on Capital Employed.",
        "matrix_h": "Financial Timeline",
        "kpi_h": "KPI Dashboard",
        "kpi_pe": "P/E (Trailing)",
        "kpi_fpe": "Forward P/E",
        "kpi_peg": "PEG Ratio",
        "kpi_ps": "Price / Sales",
        "kpi_pfcf": "Price / FCF",
        "kpi_evebitda": "EV / EBITDA",
        "kpi_pb": "Price / Book",
        "kpi_de": "Debt / Equity",
        "kpi_cr": "Current Ratio",
        "kpi_qr": "Quick Ratio",
        "kpi_gm": "Gross Margin",
        "kpi_ebitdam": "EBITDA Margin",
        "kpi_om": "Operating Margin",
        "kpi_nm": "Net Margin",
        "kpi_fcfm": "FCF Margin",
        "kpi_roe": "ROE",
        "kpi_roic": "ROIC",
        "kpi_roa": "ROA",
        "kpi_roce": "ROCE",
        "kpi_roi": "ROI (Proxy)",
        "kpi_rev": "LTM Revenue",
        "kpi_ebitda": "LTM EBITDA",
        "kpi_ni": "LTM Net Income",
        "kpi_fcf": "LTM FCF",
        "kpi_eps": "LTM EPS",
        "bal_h": "Balance Sheet",
        "bal_na": "Balance sheet is not available.",
        "est_q1": "Q+1 (Est)",
        "est_q2": "Q+2 (Est)",
        "earn_next_h": "Upcoming Earnings Report",
        "earn_hist_h": "Earnings Surprise History (Beat / Miss)",
        "earn_date_lbl": "Date",
        "earn_eps_lbl": "Consensus EPS",
        "earn_rev_lbl": "Consensus Revenue",
        "eh_date": "Quarter",
        "eh_act": "Actual EPS",
        "eh_est": "Estimated EPS",
        "eh_diff": "Difference",
        "eh_surp": "Beat / Miss (%)",
        "eh_na1": "Official next earnings date not set yet.",
        "eh_na2": "Next earnings date is currently unavailable.",
        "eh_na3": "Earnings surprise history is not available.",
        "eh_na4": "Earnings history is currently unavailable.",
        "news_h": "News Feed —",
        "news_pub": "Publisher",
        "news_date": "Published",
        "news_na": "No news currently available."
    }
}
_ = t.get(st.session_state.get("lang", "CZ"), t["CZ"])

st.title(_["title"])
st.caption(_["desc"])
st.markdown("---")

def load_data():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list): return {"portfolio": data, "watchlist": []}
                return data
        except: pass
    return {"portfolio": ["AAPL", "MSFT", "AMAT", "GOOGL", "ASML"], "watchlist": []}

data = load_data()
all_tickers = list(dict.fromkeys(data.get("portfolio", []) + data.get("watchlist", [])))

col_sel1, col_sel2, col_sel3 = st.columns([2, 2, 3])
sel_tick = col_sel1.selectbox(_["db_select"], [""] + all_tickers)
custom_tick = col_sel2.text_input(_["custom_tick"], value="")
period_type = col_sel3.radio(_["periodicity"], [_["annual"], _["quarterly"]], horizontal=True)

final_tick = custom_tick.upper().strip() if custom_tick.strip() else sel_tick

def format_val(val, currency_code, is_pct=False, is_eps=False, force_currency=False):
    if val is None or pd.isna(val) or val == "-": return "-"
    try:
        val = float(val)
    except:
        return str(val)
        
    if is_pct:
        return f"{val * 100:+.1f} %"
    if is_eps:
        return f"{val:.2f} {currency_code}"
    if abs(val) >= 1e9:
        return f"{val / 1e9:,.2f} B" + (f" {currency_code}" if force_currency else "")
    if abs(val) >= 1e6:
        return f"{val / 1e6:,.2f} M" + (f" {currency_code}" if force_currency else "")
    return f"{val:,.2f}" + (f" {currency_code}" if force_currency else "")

if final_tick:
    with st.spinner(f"{_['loading']} {final_tick}..."):
        tkr = yf.Ticker(final_tick, session=session)
        
        try:
            info = tkr.info or {}
        except:
            info = {}
            
        is_quarterly = (period_type == _["quarterly"])
        
        try:
            financials = tkr.quarterly_financials if is_quarterly else tkr.financials
        except:
            financials = pd.DataFrame()
            
        try:
            cashflow = tkr.quarterly_cashflow if is_quarterly else tkr.cashflow
        except:
            cashflow = pd.DataFrame()
            
        try:
            balance_sheet = tkr.balance_sheet
        except:
            balance_sheet = pd.DataFrame()

        if financials is None or financials.empty:
            st.error(_["err_data"])
            st.stop()
            
        short_name = info.get("shortName", final_tick)
        curr_price = info.get("currentPrice", info.get("regularMarketPrice", 0.0))
        currency_code = info.get("financialCurrency", info.get("currency", "USD"))
        trading_currency = info.get("currency", "USD")
        market_cap = info.get("marketCap")
        
        # --- MĚNOVÝ PŘEVODNÍK (FX TRANSLATION) ---
        convert_to_usd = False
        display_currency = currency_code
        fx_hist = pd.DataFrame()
        latest_fx = 1.0

        if currency_code != "USD":
            convert_to_usd = st.toggle(f"💱 {_['convert_usd'].replace('{curr}', currency_code)}", value=False)
            if convert_to_usd:
                display_currency = "USD"
                try:
                    fx_tkr = yf.Ticker(f"{currency_code}USD=X", session=session)
                    fx_hist = fx_tkr.history(period="10y")
                    if not fx_hist.empty:
                        latest_fx = float(fx_hist['Close'].iloc[-1])
                except:
                    pass

        def get_rate(d):
            if not convert_to_usd: return 1.0
            if fx_hist.empty: return latest_fx
            try:
                dt = pd.to_datetime(d)
                if dt.tzinfo is None and fx_hist.index.tz is not None:
                    dt = dt.tz_localize('UTC')
                elif dt.tzinfo is not None and fx_hist.index.tz is None:
                    dt = dt.tz_localize(None)
                idx = fx_hist.index.get_indexer([dt], method='nearest')[0]
                return float(fx_hist['Close'].iloc[idx])
            except:
                return latest_fx

        q_fin_for_kpi = tkr.quarterly_financials if not is_quarterly else financials
        q_cf_for_kpi = tkr.quarterly_cashflow if not is_quarterly else cashflow
        
        def get_ltm_from_quarterly(df, keys):
            if df is None or df.empty: return None
            for key in keys:
                if key in df.index:
                    vals = df.loc[key].iloc[:4]
                    if len(vals) == 4 and not vals.isna().all(): return vals.sum()
            return None

        total_rev_ltm = get_ltm_from_quarterly(q_fin_for_kpi, ['Total Revenue']) or info.get("totalRevenue")
        net_income_ltm = get_ltm_from_quarterly(q_fin_for_kpi, ['Net Income', 'Net Income Common Stockholders']) or info.get("netIncomeToCommon", info.get("netIncome"))
        ebitda_ltm = get_ltm_from_quarterly(q_fin_for_kpi, ['Normalized EBITDA', 'EBITDA']) or info.get("ebitda")
        
        fcf = get_ltm_from_quarterly(q_cf_for_kpi, ['Free Cash Flow'])
        if fcf is None:
            ocf = get_ltm_from_quarterly(q_cf_for_kpi, ['Operating Cash Flow'])
            capex = get_ltm_from_quarterly(q_cf_for_kpi, ['Capital Expenditure'])
            if ocf and capex is not None: fcf = ocf - abs(capex)
            else: fcf = info.get("freeCashflow")
                
        eps_ltm = info.get("trailingEps") 
        pe = info.get("trailingPE")
        fwd_pe = info.get("forwardPE")
        peg = info.get("pegRatio")
        ps = info.get("priceToSalesTrailing12Months")
        pb = info.get("priceToBook")
        ev_ebitda = info.get("enterpriseToEbitda")
        p_fcf = (market_cap / fcf) if market_cap and fcf and fcf > 0 else None
        
        current_ratio = info.get("currentRatio")
        quick_ratio = info.get("quickRatio")
        
        calc_debt_eq = None
        roic, roce, roi = None, None, None 
        
        if balance_sheet is not None and not balance_sheet.empty:
            try:
                total_debt = balance_sheet.loc['Total Debt'].iloc[0] if 'Total Debt' in balance_sheet.index else 0
                stockholders_eq = balance_sheet.loc['Stockholders Equity'].iloc[0] if 'Stockholders Equity' in balance_sheet.index else 0
                total_assets = balance_sheet.loc['Total Assets'].iloc[0] if 'Total Assets' in balance_sheet.index else 0
                current_liab = balance_sheet.loc['Total Current Liabilities'].iloc[0] if 'Total Current Liabilities' in balance_sheet.index else 0
                invested_capital = total_debt + stockholders_eq
                capital_employed = total_assets - current_liab
                if stockholders_eq and stockholders_eq > 0: calc_debt_eq = total_debt / stockholders_eq
            except:
                invested_capital, capital_employed, total_assets = 0, 0, 0
        
        roe = info.get("returnOnEquity")
        roa = info.get("returnOnAssets")
        gross_margin = info.get("grossMargins")
        op_margin = info.get("operatingMargins")
        profit_margin = info.get("profitMargins")
        
        ebitda_margin = (ebitda_ltm / total_rev_ltm) if ebitda_ltm and total_rev_ltm and total_rev_ltm > 0 else None
        fcf_margin = (fcf / total_rev_ltm) if fcf and total_rev_ltm and total_rev_ltm > 0 else None
        
        if net_income_ltm and 'invested_capital' in locals() and invested_capital > 0: roic = net_income_ltm / invested_capital
        if not financials.empty and 'capital_employed' in locals() and capital_employed > 0:
             try:
                 ebit = financials.loc['EBIT'].iloc[0] if 'EBIT' in financials.index else (financials.loc['Operating Income'].iloc[0] if 'Operating Income' in financials.index else 0)
                 if ebit: roce = ebit / capital_employed
             except: pass
        if net_income_ltm and 'total_assets' in locals() and total_assets > 0: roi = net_income_ltm / total_assets 

        st.markdown("---")

        tab_matrix, tab_val, tab_ana, tab_earn, tab_news, tab_raw = st.tabs([_["tab_matrix"], _["tab_val"], _["tab_ana"], _["tab_earn"], _["tab_news"], _["tab_raw"]])

        with tab_matrix:
            st.subheader(f"{_['matrix_h']} — {_['currency_lbl']} {display_currency}")
            
            matrix_dict = {}
            last_hist_year = 2024
            
            if not financials.empty:
                hist_cols = sorted(financials.columns)
                last_hist_year = hist_cols[-1].year
                
                for col in hist_cols:
                    rate = get_rate(col)
                    col_label = f"{col.year}-Q{col.quarter}" if is_quarterly else str(col.year)
                    matrix_dict[col_label] = {}
                    
                    rev = financials.loc["Total Revenue", col] if "Total Revenue" in financials.index else None
                    matrix_dict[col_label][_["r_rev"]] = (rev * rate) if pd.notna(rev) else None
                    
                    gp = financials.loc["Gross Profit", col] if "Gross Profit" in financials.index else None
                    matrix_dict[col_label][_["r_gp"]] = (gp * rate) if pd.notna(gp) else None
                    
                    ebit = financials.loc["Operating Income", col] if "Operating Income" in financials.index else (financials.loc["EBIT", col] if "EBIT" in financials.index else None)
                    matrix_dict[col_label][_["r_ebit"]] = (ebit * rate) if pd.notna(ebit) else None
                    
                    ni = financials.loc["Net Income Common Stockholders", col] if "Net Income Common Stockholders" in financials.index else (financials.loc["Net Income", col] if "Net Income" in financials.index else None)
                    matrix_dict[col_label][_["r_ni"]] = (ni * rate) if pd.notna(ni) else None
                    
                    eps = financials.loc["Diluted EPS", col] if "Diluted EPS" in financials.index else (financials.loc["Basic EPS", col] if "Basic EPS" in financials.index else None)
                    matrix_dict[col_label][_["r_eps"]] = (eps * rate) if pd.notna(eps) else None
                    
                    fcf_val = None
                    if not cashflow.empty and col in cashflow.columns:
                        if "Free Cash Flow" in cashflow.index:
                            fcf_val = cashflow.loc["Free Cash Flow", col]
                        elif "Operating Cash Flow" in cashflow.index and "Capital Expenditure" in cashflow.index:
                            fcf_val = cashflow.loc["Operating Cash Flow", col] - abs(cashflow.loc["Capital Expenditure", col])
                    matrix_dict[col_label][_["r_fcf"]] = (fcf_val * rate) if pd.notna(fcf_val) else None

            if not is_quarterly:
                ltm_col = "LTM"
                rate = latest_fx if convert_to_usd else 1.0
                matrix_dict[ltm_col] = {}
                matrix_dict[ltm_col][_["r_rev"]] = (total_rev_ltm * rate) if pd.notna(total_rev_ltm) else None
                matrix_dict[ltm_col][_["r_gp"]] = (get_ltm_from_quarterly(q_fin_for_kpi, ["Gross Profit"]) * rate) if get_ltm_from_quarterly(q_fin_for_kpi, ["Gross Profit"]) is not None else None
                matrix_dict[ltm_col][_["r_ebit"]] = (get_ltm_from_quarterly(q_fin_for_kpi, ["Operating Income", "EBIT"]) * rate) if get_ltm_from_quarterly(q_fin_for_kpi, ["Operating Income", "EBIT"]) is not None else None
                matrix_dict[ltm_col][_["r_ni"]] = (net_income_ltm * rate) if pd.notna(net_income_ltm) else None
                matrix_dict[ltm_col][_["r_eps"]] = (eps_ltm * rate) if pd.notna(eps_ltm) else None
                matrix_dict[ltm_col][_["r_fcf"]] = (fcf * rate) if pd.notna(fcf) else None

            try:
                rev_est = tkr.revenue_estimate
                eps_est = tkr.earnings_estimate
                
                if is_quarterly:
                    est_keys = [("0q", _["est_q1"]), ("+1q", _["est_q2"])]
                else:
                    est_keys = [("0y", f"{last_hist_year + 1}E"), ("+1y", f"{last_hist_year + 2}E")]
                    
                for k, label in est_keys:
                    col_name = label
                    rate = latest_fx if convert_to_usd else 1.0
                    matrix_dict[col_name] = {}
                    
                    e_val = eps_est.loc[k, "avg"] if (eps_est is not None and not eps_est.empty and k in eps_est.index and "avg" in eps_est.columns) else None
                    matrix_dict[col_name][_["r_eps"]] = (e_val * rate) if pd.notna(e_val) else None
                    
                    r_val = rev_est.loc[k, "avg"] if (rev_est is not None and not rev_est.empty and k in rev_est.index and "avg" in rev_est.columns) else None
                    matrix_dict[col_name][_["r_rev"]] = (r_val * rate) if pd.notna(r_val) else None
                    matrix_dict[col_name][_["r_gp"]] = None
                    matrix_dict[col_name][_["r_ebit"]] = None
                    
                    shares = info.get("sharesOutstanding")
                    matrix_dict[col_name][_["r_ni"]] = (e_val * rate * shares) if (pd.notna(e_val) and shares) else None
                    matrix_dict[col_name][_["r_fcf"]] = None
            except:
                pass

            df_matrix = pd.DataFrame(matrix_dict)
            
            if _["r_rev"] in df_matrix.index:
                rev_series = pd.to_numeric(df_matrix.loc[_["r_rev"]], errors='coerce')
                clean_series = rev_series.drop("LTM", errors="ignore")
                growth_series = clean_series.pct_change()
                if "LTM" in df_matrix.columns:
                    growth_series["LTM"] = None
                df_matrix.loc[_["r_rev_growth"]] = growth_series
                
                for m_lbl, p_lbl in [(_["r_gm"], _["r_gp"]), (_["r_om"], _["r_ebit"]), (_["r_nm"], _["r_ni"]), (_["r_fcfm"], _["r_fcf"])]:
                    if p_lbl in df_matrix.index:
                        df_matrix.loc[m_lbl] = pd.to_numeric(df_matrix.loc[p_lbl], errors='coerce') / rev_series

            ordered_rows = [
                _["r_rev"],
                _["r_rev_growth"],
                _["r_gp"],
                _["r_gm"],
                _["r_ebit"],
                _["r_om"],
                _["r_ni"],
                _["r_nm"],
                _["r_eps"],
                _["r_fcf"],
                _["r_fcfm"]
            ]
            
            existing_ordered = [r for r in ordered_rows if r in df_matrix.index]
            df_matrix = df_matrix.reindex(existing_ordered)

            df_display = df_matrix.copy().astype(object)
            pct_rows = [_["r_rev_growth"], _["r_gm"], _["r_om"], _["r_nm"], _["r_fcfm"]]
            
            for r in df_display.index:
                is_pct = (r in pct_rows)
                is_eps = (r == _["r_eps"])
                df_display.loc[r] = df_display.loc[r].apply(lambda x: format_val(x, display_currency, is_pct=is_pct, is_eps=is_eps, force_currency=(not is_pct and not is_eps)))

            st.table(df_display)

        with tab_val:
            st.subheader(f"{short_name} ({final_tick}) — {_['kpi_h']}")
            vkpi1, vkpi2, vkpi3, vkpi4, vkpi5 = st.columns(5)
            
            def fmt_kpi(val, is_pct=False, is_curr=False, curr_label="USD"):
                if val is None or pd.isna(val): return "N/A"
                if is_pct: return f"{val*100:.2f} %"
                if is_curr: 
                    if val >= 1e9: return f"{val/1e9:.2f}B {curr_label}"
                    if val >= 1e6: return f"{val/1e6:.2f}M {curr_label}"
                    return f"{val:,.2f} {curr_label}"
                return f"{val:.2f}"
                
            vkpi1.markdown(f"**{_['met_val']}**")
            vkpi1.metric(_["kpi_pe"], fmt_kpi(pe))
            vkpi1.metric(_["kpi_fpe"], fmt_kpi(fwd_pe))
            vkpi1.metric(_["kpi_peg"], fmt_kpi(peg))
            vkpi1.metric(_["kpi_ps"], fmt_kpi(ps))
            vkpi1.metric(_["kpi_pfcf"], fmt_kpi(p_fcf))
            
            vkpi2.markdown(f"**{_['met_mul']}**")
            vkpi2.metric(_["kpi_evebitda"], fmt_kpi(ev_ebitda))
            vkpi2.metric(_["kpi_pb"], fmt_kpi(pb))
            vkpi2.metric(_["kpi_de"], fmt_kpi(calc_debt_eq))
            vkpi2.metric(_["kpi_cr"], fmt_kpi(current_ratio))
            vkpi2.metric(_["kpi_qr"], fmt_kpi(quick_ratio))
            
            vkpi3.markdown(f"**{_['met_mar']}**")
            vkpi3.metric(_["kpi_gm"], fmt_kpi(gross_margin, True))
            vkpi3.metric(_["kpi_ebitdam"], fmt_kpi(ebitda_margin, True))
            vkpi3.metric(_["kpi_om"], fmt_kpi(op_margin, True))
            vkpi3.metric(_["kpi_nm"], fmt_kpi(profit_margin, True))
            vkpi3.metric(_["kpi_fcfm"], fmt_kpi(fcf_margin, True))
            
            vkpi4.markdown(f"**{_['met_ret']}**")
            vkpi4.metric(_["kpi_roe"], fmt_kpi(roe, True))
            vkpi4.metric(_["kpi_roic"], fmt_kpi(roic, True))
            vkpi4.metric(_["kpi_roa"], fmt_kpi(roa, True))
            vkpi4.metric(_["kpi_roce"], fmt_kpi(roce, True))
            vkpi4.metric(_["kpi_roi"], fmt_kpi(roi, True))

            vkpi5.markdown(f"**{_['met_ltm']}**")
            fx_m = latest_fx if convert_to_usd else 1.0
            vkpi5.metric(_["kpi_rev"], fmt_kpi(total_rev_ltm * fx_m if total_rev_ltm else None, is_curr=True, curr_label=display_currency))
            vkpi5.metric(_["kpi_ebitda"], fmt_kpi(ebitda_ltm * fx_m if ebitda_ltm else None, is_curr=True, curr_label=display_currency))
            vkpi5.metric(_["kpi_ni"], fmt_kpi(net_income_ltm * fx_m if net_income_ltm else None, is_curr=True, curr_label=display_currency)) 
            vkpi5.metric(_["kpi_fcf"], fmt_kpi(fcf * fx_m if fcf else None, is_curr=True, curr_label=display_currency))
            vkpi5.metric(_["kpi_eps"], fmt_kpi(eps_ltm, is_curr=True, curr_label=trading_currency))

        with tab_ana:
            st.subheader(_["targets_h"])
            
            target_low = info.get("targetLowPrice", curr_price)
            target_mean = info.get("targetMeanPrice", curr_price)
            target_high = info.get("targetHighPrice", curr_price)
            rec_mean = info.get("recommendationKey", "N/A").upper()
            num_analysts = info.get("numberOfAnalystOpinions", "N/A")

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric(_["t_low"], f"{target_low:.2f} {trading_currency}", f"{(target_low - curr_price) / curr_price * 100:+.1f}%" if curr_price else "N/A")
            c2.metric(_["t_mean"], f"{target_mean:.2f} {trading_currency}", f"{(target_mean - curr_price) / curr_price * 100:+.1f}%" if curr_price else "N/A")
            c3.metric(_["t_high"], f"{target_high:.2f} {trading_currency}", f"{(target_high - curr_price) / curr_price * 100:+.1f}%" if curr_price else "N/A")
            c4.metric(_["t_rec"], rec_mean)
            c5.metric(_["t_num"], num_analysts)

        with tab_earn:
            st.subheader(_["earn_next_h"])
            try:
                cal = tkr.calendar
                next_date = None
                if isinstance(cal, dict) and 'Earnings Date' in cal:
                    dates = cal['Earnings Date']
                    if len(dates) > 0:
                        next_date = dates[0]
                
                if next_date:
                    eps_est_val = None
                    rev_est_val = None
                    try:
                        eps_est_val = tkr.earnings_estimate.loc["0q", "avg"]
                        rev_est_val = tkr.revenue_estimate.loc["0q", "avg"]
                    except:
                        pass
                        
                    ec1, ec2, ec3 = st.columns(3)
                    ec1.metric(_["earn_date_lbl"], next_date.strftime("%d. %m. %Y"))
                    ec2.metric(_["earn_eps_lbl"], f"${eps_est_val:.2f}" if pd.notna(eps_est_val) else "N/A")
                    
                    rev_str = "N/A"
                    if pd.notna(rev_est_val):
                        if rev_est_val >= 1e9: rev_str = f"${rev_est_val/1e9:.2f} B"
                        elif rev_est_val >= 1e6: rev_str = f"${rev_est_val/1e6:.2f} M"
                        else: rev_str = f"${rev_est_val:,.2f}"
                        
                    ec3.metric(_["earn_rev_lbl"], rev_str)
                else:
                    st.info(_["eh_na1"])
            except:
                st.info(_["eh_na2"])
                
            st.markdown("---")
            st.subheader(_["earn_hist_h"])
            try:
                eh = tkr.earnings_history
                if eh is not None and not eh.empty:
                    df_eh = eh.copy()
                    
                    if isinstance(df_eh.index, pd.DatetimeIndex):
                        df_eh.index = df_eh.index.strftime("%Y-%m-%d")
                        df_eh.index.name = _["eh_date"]
                    elif "quarter" in df_eh.columns:
                        df_eh["quarter"] = pd.to_datetime(df_eh["quarter"]).dt.strftime("%Y-%m-%d")
                    
                    eh_map = {
                        "epsActual": _["eh_act"],
                        "epsEstimate": _["eh_est"],
                        "epsDifference": _["eh_diff"],
                        "surprisePercent": _["eh_surp"]
                    }
                    df_eh = df_eh.rename(columns=eh_map)
                    
                    if _["eh_diff"] in df_eh.columns:
                        df_eh[_["eh_diff"]] = df_eh[_["eh_diff"]].apply(lambda x: f"{x:+.2f}" if pd.notna(x) else "-")
                    if _["eh_surp"] in df_eh.columns:
                        df_eh[_["eh_surp"]] = df_eh[_["eh_surp"]].apply(lambda x: f"{x*100:+.2f} %" if pd.notna(x) else "-")
                        
                    st.table(df_eh)
                else:
                    st.info(_["eh_na3"])
            except:
                st.info(_["eh_na4"])

        with tab_news:
            st.subheader(f"{_['news_h']} {short_name} ({final_tick})")
            try:
                news_list = tkr.news
                if news_list and len(news_list) > 0:
                    for article in news_list[:12]:
                        title = article.get("title", "")
                        publisher = article.get("publisher", "N/A")
                        link = article.get("link", "#")
                        pub_time = article.get("providerPublishTime")
                        
                        if pub_time:
                            dt = pd.to_datetime(pub_time, unit='s').strftime("%d. %m. %Y %H:%M")
                        else:
                            dt = "N/A"
                            
                        st.markdown(f"### [{title}]({link})")
                        st.caption(f"🏢 {_['news_pub']}: **{publisher}** | 🕒 {_['news_date']}: **{dt}**")
                        st.markdown("---")
                else:
                    st.info(_["news_na"])
            except:
                st.info(_["news_na"])

        with tab_raw:
            st.subheader(f"{_['bal_h']} — {final_tick}")
            if not balance_sheet.empty:
                bs_display = balance_sheet.copy()
                for col in bs_display.columns:
                    rate = get_rate(col)
                    bs_display[col] = bs_display[col] * rate if pd.notna(bs_display[col]).any() else bs_display[col]
                    
                bs_display.columns = [c.strftime("%Y-%m-%d") for c in bs_display.columns]
                for col in bs_display.columns:
                    bs_display[col] = bs_display[col].apply(lambda x: format_val(x, display_currency, force_currency=True))
                
                st.table(bs_display)
            else:
                st.info(_["bal_na"])