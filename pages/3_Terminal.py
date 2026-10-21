import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os
import sys

# --- INITIAL SETUP ---
st.set_page_config(page_title="POKORNY TERMINAL | VALUATION", layout="wide", initial_sidebar_state="collapsed")

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
        "title": "🏛️ HLOUBKOVÝ ANALYTICKÝ TERMINÁL",
        "desc": "KOMPLEXNÍ INSTITUCIONÁLNÍ POHLED: MATICE VÝKAZŮ, VALUACE, KONSENZY A EARNINGS.",
        "db_select": "DATABÁZE",
        "custom_tick": "VLASTNÍ TICKER",
        "periodicity": "PERIODICITA MATICE:",
        "annual": "Roční (Annual)",
        "quarterly": "Kvartální (Quarterly)",
        "loading": "STAHOVÁNÍ ŽIVÝCH DAT...",
        "err_data": "DATA PRO TENTO TICKER NEJSOU DOSTUPNÁ.",
        "tab_matrix": "📑 FINANČNÍ MATICE & VÝHLED",
        "tab_val": "📊 VALUACE & KPI",
        "tab_ana": "🎯 ANALYTICI & REVIZE",
        "tab_earn": "📅 EARNINGS & HISTORIE",
        "tab_raw": "🗄️ STRUKTUROVANÁ ROZVAHA",
        "targets_h": "Wall Street Konsenzus & Cílové Ceny",
        "t_low": "Bear Target",
        "t_mean": "Konsenzus (Mean)",
        "t_high": "Bull Target",
        "t_rec": "Doporučení",
        "t_num": "Počet analytiků",
        "rev_h": "Historie revizí odhadů (Posledních 30 dní)",
        "earn_next_h": "Nadcházející kvartální report",
        "earn_hist_h": "Historie překonání odhadů (Beat / Miss)",
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
        "per_0q": "Aktuální kvartál",
        "per_1q": "Příští kvartál",
        "per_0y": "Aktuální rok",
        "per_1y": "Příští rok",
        "rev_col_per": "Období",
        "rev_up7": "Zvýšeno (7 dní)",
        "rev_up30": "Zvýšeno (30 dní)",
        "rev_down7": "Sníženo (7 dní)",
        "rev_down30": "Sníženo (30 dní)",
        "eh_date": "Kvartál",
        "eh_act": "Skutečné EPS",
        "eh_est": "Odhad EPS",
        "eh_diff": "Rozdíl (Beat/Miss)",
        "eh_surp": "Překvapení (%)",
        "earn_date_lbl": "Termín příštích earnings",
        "earn_eps_lbl": "Očekávaný EPS odhad"
    },
    "EN": {
        "title": "🏛️ DEEP INSTITUTIONAL TERMINAL",
        "desc": "COMPREHENSIVE ANALYSIS: FINANCIAL MATRIX, VALUATION, CONSENSUS & EARNINGS.",
        "db_select": "DATABASE",
        "custom_tick": "CUSTOM TICKER",
        "periodicity": "MATRIX PERIODICITY:",
        "annual": "Annual",
        "quarterly": "Quarterly",
        "loading": "PULLING LIVE DATA...",
        "err_data": "DATA FOR THIS TICKER NOT AVAILABLE.",
        "tab_matrix": "📑 FINANCIAL MATRIX & OUTLOOK",
        "tab_val": "📊 VALUATION & KPIs",
        "tab_ana": "🎯 ANALYSTS & REVISIONS",
        "tab_earn": "📅 EARNINGS & TRACK RECORD",
        "tab_raw": "🗄️ STRUCTURED BALANCE SHEET",
        "targets_h": "Wall Street Consensus & Price Targets",
        "t_low": "Bear Target",
        "t_mean": "Consensus (Mean)",
        "t_high": "Bull Target",
        "t_rec": "Recommendation",
        "t_num": "Analyst Coverage",
        "rev_h": "Estimate Revisions History (Last 30 Days)",
        "earn_next_h": "Upcoming Earnings Report",
        "earn_hist_h": "Earnings Surprise History (Beat / Miss)",
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
        "per_0q": "Current Quarter",
        "per_1q": "Next Quarter",
        "per_0y": "Current Year",
        "per_1y": "Next Year",
        "rev_col_per": "Period",
        "rev_up7": "Up (Last 7D)",
        "rev_up30": "Up (Last 30D)",
        "rev_down7": "Down (Last 7D)",
        "rev_down30": "Down (Last 30D)",
        "eh_date": "Quarter",
        "eh_act": "Actual EPS",
        "eh_est": "Estimated EPS",
        "eh_diff": "Difference",
        "eh_surp": "Surprise (%)",
        "earn_date_lbl": "Next Earnings Date",
        "earn_eps_lbl": "Consensus EPS Estimate"
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
        try:
            tkr = yf.Ticker(final_tick)
            info = tkr.info
        except:
            info = {}
            
        if not info or ("currentPrice" not in info and "regularMarketPrice" not in info and "longName" not in info):
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
                    fx_tkr = yf.Ticker(f"{currency_code}USD=X")
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

        is_quarterly = (period_type == _["quarterly"])
        
        # Bezpečné načítání výkazů s ošetřením chyb
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
            
        q_fin_for_kpi = tkr.quarterly_financials if not is_quarterly else financials
        q_cf_for_kpi = tkr.quarterly_cashflow if not is_quarterly else cashflow
        
        # --- LTM VÝPOČTY PRO KPI DASHBOARD ---
        def sum_ltm(df, row_names):
            if df is None or df.empty: return None
            for row in row_names:
                if row in df.index:
                    vals = df.loc[row].iloc[:4]
                    if len(vals) == 4 and not vals.isna().all(): return vals.sum()
            return None

        total_rev_ltm = sum_ltm(q_fin_for_kpi, ['Total Revenue']) or info.get("totalRevenue")
        net_income_ltm = sum_ltm(q_fin_for_kpi, ['Net Income', 'Net Income Common Stockholders']) or info.get("netIncomeToCommon", info.get("netIncome"))
        ebitda_ltm = sum_ltm(q_fin_for_kpi, ['Normalized EBITDA', 'EBITDA']) or info.get("ebitda")
        
        fcf = sum_ltm(q_cf_for_kpi, ['Free Cash Flow'])
        if fcf is None and q_cf_for_kpi is not None and not q_cf_for_kpi.empty:
            ocf = sum_ltm(q_cf_for_kpi, ['Operating Cash Flow'])
            capex = sum_ltm(q_cf_for_kpi, ['Capital Expenditure'])
            if ocf and capex is not None: fcf = ocf - abs(capex)
            else: fcf = info.get("freeCashflow")

        eps_ltm_kpi = info.get("trailingEps") 
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
        if net_income_ltm and 'total_assets' in locals() and total_assets > 0: roi = net_income_ltm / total_assets 
        if financials is not None and not financials.empty and 'capital_employed' in locals() and capital_employed > 0:
             try:
                 ebit = financials.loc['EBIT'].iloc[0] if 'EBIT' in financials.index else (financials.loc['Operating Income'].iloc[0] if 'Operating Income' in financials.index else 0)
                 if ebit: roce = ebit / capital_employed
             except: pass

        st.markdown("---")

        tab_matrix, tab_val, tab_ana, tab_earn, tab_raw = st.tabs([
            _["tab_matrix"], _["tab_val"], _["tab_ana"], _["tab_earn"], _["tab_raw"]
        ])

        with tab_matrix:
            st.subheader(f"Finanční časová osa — {_['currency_lbl']} {display_currency}")
            
            matrix_dict = {}
            last_hist_year = 2024
            
            if financials is not None and not financials.empty:
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
                    if cashflow is not None and not cashflow.empty and col in cashflow.columns:
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
                matrix_dict[ltm_col][_["r_gp"]] = (sum_ltm(q_fin_for_kpi, ["Gross Profit"]) * rate) if sum_ltm(q_fin_for_kpi, ["Gross Profit"]) is not None else None
                matrix_dict[ltm_col][_["r_ebit"]] = (sum_ltm(q_fin_for_kpi, ["Operating Income", "EBIT"]) * rate) if sum_ltm(q_fin_for_kpi, ["Operating Income", "EBIT"]) is not None else None
                matrix_dict[ltm_col][_["r_ni"]] = (net_income_ltm * rate) if pd.notna(net_income_ltm) else None
                
                ltm_eps_matrix = sum_ltm(q_fin_for_kpi, ["Diluted EPS", "Basic EPS"])
                matrix_dict[ltm_col][_["r_eps"]] = (ltm_eps_matrix * rate) if pd.notna(ltm_eps_matrix) else None
                matrix_dict[ltm_col][_["r_fcf"]] = (fcf * rate) if pd.notna(fcf) else None

            try:
                rev_est = tkr.revenue_estimate
                eps_est = tkr.earnings_estimate
                
                if is_quarterly:
                    est_keys = [("0q", "Q+1 (Est)"), ("+1q", "Q+2 (Est)")]
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
            st.subheader(f"{short_name} ({final_tick}) — KPI Dashboard")
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
            vkpi1.metric("P/E (Trailing)", fmt_kpi(pe))
            vkpi1.metric("Forward P/E", fmt_kpi(fwd_pe))
            vkpi1.metric("PEG Ratio", fmt_kpi(peg))
            vkpi1.metric("Price / Sales", fmt_kpi(ps))
            vkpi1.metric("Price / FCF", fmt_kpi(p_fcf))
            
            vkpi2.markdown(f"**{_['met_mul']}**")
            vkpi2.metric("EV / EBITDA", fmt_kpi(ev_ebitda))
            vkpi2.metric("Price / Book", fmt_kpi(pb))
            vkpi2.metric("Debt / Equity", fmt_kpi(calc_debt_eq))
            vkpi2.metric("Current Ratio", fmt_kpi(current_ratio))
            vkpi2.metric("Quick Ratio", fmt_kpi(quick_ratio))
            
            vkpi3.markdown(f"**{_['met_mar']}**")
            vkpi3.metric("Gross Margin", fmt_kpi(gross_margin, True))
            vkpi3.metric("EBITDA Margin", fmt_kpi(ebitda_margin, True))
            vkpi3.metric("Operating Margin", fmt_kpi(op_margin, True))
            vkpi3.metric("Profit Margin (Net)", fmt_kpi(profit_margin, True))
            vkpi3.metric("FCF Margin", fmt_kpi(fcf_margin, True))
            
            vkpi4.markdown(f"**{_['met_ret']}**")
            vkpi4.metric("ROE", fmt_kpi(roe, True))
            vkpi4.metric("ROIC", fmt_kpi(roic, True))
            vkpi4.metric("ROA", fmt_kpi(roa, True))
            vkpi4.metric("ROCE", fmt_kpi(roce, True))
            vkpi4.metric("ROI (Proxy)", fmt_kpi(roi, True))

            vkpi5.markdown(f"**{_['met_ltm']}**")
            fx_m = latest_fx if convert_to_usd else 1.0
            vkpi5.metric("LTM Revenue", fmt_kpi(total_rev_ltm * fx_m if total_rev_ltm else None, is_curr=True, curr_label=display_currency))
            vkpi5.metric("LTM EBITDA", fmt_kpi(ebitda_ltm * fx_m if ebitda_ltm else None, is_curr=True, curr_label=display_currency))
            vkpi5.metric("LTM Net Income", fmt_kpi(net_income_ltm * fx_m if net_income_ltm else None, is_curr=True, curr_label=display_currency)) 
            vkpi5.metric("LTM FCF", fmt_kpi(fcf * fx_m if fcf else None, is_curr=True, curr_label=display_currency))
            vkpi5.metric("LTM EPS", fmt_kpi(eps_ltm_kpi, is_curr=True, curr_label=trading_currency))

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
            
            st.markdown("---")
            st.subheader(_["rev_h"])
            try:
                revs = tkr.eps_revisions
                if revs is not None and not revs.empty:
                    st.dataframe(revs, use_container_width=True)
                else:
                    st.info("Historie revizí odhadů není pro tento ticker dostupná.")
            except:
                st.info("Historie revizí odhadů není k dispozici.")

        with tab_earn:
            st.subheader(_["earn_next_h"])
            try:
                ed = tkr.get_earnings_dates(limit=6)
                if ed is not None and not ed.empty:
                    now = pd.Timestamp.now(tz='UTC')
                    if ed.index.tz is None:
                        ed.index = ed.index.tz_localize('UTC')
                    else:
                        ed.index = ed.index.tz_convert('UTC')
                        
                    future_ed = ed[ed.index >= now]
                    if not future_ed.empty:
                        next_date = future_ed.index.min()
                        next_eps = future_ed.loc[next_date, "EPS Estimate"]
                        if isinstance(next_eps, pd.Series): next_eps = next_eps.iloc[0]
                        
                        ec1, ec2 = st.columns(2)
                        ec1.metric(_["earn_date_lbl"], next_date.strftime("%d. %m. %Y (%H:%M)"))
                        ec2.metric(_["earn_eps_lbl"], f"${next_eps:.2f}" if pd.notna(next_eps) else "N/A")
                    else:
                        st.info("Oficiální datum příštího reportu zatím nebylo stanoveno.")
                else:
                    st.info("Kalendář výsledků není dostupný.")
            except:
                st.info("Nepodařilo se načíst budoucí earnings.")
                
            st.markdown("---")
            st.subheader(_["earn_hist_h"])
            try:
                eh = tkr.earnings_history
                if eh is not None and not eh.empty:
                    st.dataframe(eh, use_container_width=True)
                else:
                    st.info("Historie kvartálních překvapení není k dispozici.")
            except:
                st.info("Historie kvartálních earnings není dostupná.")

        with tab_raw:
            st.subheader(f"Balance Sheet — {final_tick}")
            if not balance_sheet.empty:
                bs_display = balance_sheet.copy()
                for col in bs_display.columns:
                    rate = get_rate(col)
                    bs_display[col] = bs_display[col] * rate if pd.notna(bs_display[col]).any() else bs_display[col]
                    
                bs_display.columns = [c.strftime("%Y-%m-%d") for c in bs_display.columns]
                for col in bs_display.columns:
                    bs_display[col] = bs_display[col].apply(lambda x: format_val(x, display_currency, force_currency=True))
                st.dataframe(bs_display, use_container_width=True)
            else:
                st.info("Rozvaha není k dispozici.")