import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os
import sys
import requests_cache
import plotly.graph_objects as go

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
        "title": "VALUACE & FUNDAMENTY",
        "desc": "HLOUBKOVÝ SCREENER FINANČNÍCH VÝKAZŮ A UKAZATELŮ.",
        "db_select": "DATABÁZE",
        "custom_tick": "VLASTNÍ TICKER",
        "loading": "STAHOVÁNÍ VÝKAZŮ...",
        "err_data": "DATA PRO TENTO TICKER NEJSOU DOSTUPNÁ.",
        "err_api": "⚠️ YAHOO FINANCE API LIMIT: Spojení bylo dočasně zablokováno (Rate Limit). Zkuste to za chvíli znovu.",
        "tab_dash": "📊 ANALYTICKÝ DASHBOARD",
        "tab_raw": "🗄️ STRUKTUROVANÉ VÝKAZY",
        "met_val": "VALUACE",
        "met_mul": "MULTIPLIKÁTORY & LIKVIDITA",
        "met_mar": "MARŽE (KASKÁDA)",
        "met_ret": "RENTABILITA",
        "met_ltm": "LTM (TTM) DATA",
        "h_chart": "VÝVOJ VÝKAZŮ: TRŽBY, EBITDA, ZISK (Včetně LTM)",
        "leg_rev": "Tržby (Revenue)",
        "leg_net": "Čistý zisk (Net Income)",
        "err_chart": "Došlo k chybě při zpracování výkazů:",
        "err_miss": "Data z výkazů chybí.",
        "raw_h": "STRUKTUROVANÁ DATABÁZE VÝKAZŮ:",
        "raw_c": "Vyčištěná data z výkazů ve formátu miliard (B) a milionů (M) dolarů.",
        "raw_inc": "1. INCOME STATEMENT (Výkaz zisků a ztrát)",
        "raw_bal": "2. BALANCE SHEET (Rozvaha)",
        "raw_cf": "3. CASH FLOW STATEMENT (Výkaz peněžních toků)",
        "raw_json": "4. KOMPLETNÍ METRIKY (Surový JSON)",
        "raw_json_btn": "Zobrazit kompletní neformátovaný JSON",
        "raw_na": "Výkaz není dostupný.",
        "h_de": "Výpočet: Celkový dluh / Vlastní kapitál. Čím nižší, tím méně je firma pákou zatížená.",
        "h_cr": "Běžná likvidita: Krátkodobá aktiva / Krátkodobé závazky. Ideálně > 1 (schopnost splatit dluhy do 1 roku).",
        "h_qr": "Pohotová likvidita (Acid-test): (Krátkodobá aktiva - Zásoby) / Krátkodobé závazky. Tvrdší měřítko přežití krize.",
        "h_roe": "Return on Equity: Čistý zisk / Vlastní kapitál. Kolik firma vydělává na peníze akcionářů.",
        "h_roic": "Return on Invested Capital: Čistý zisk / (Celkový dluh + Vlastní kapitál). Jak efektivně alokuje veškerý kapitál.",
        "h_roa": "Return on Assets: Čistý zisk / Celková aktiva.",
        "h_roce": "Return on Capital Employed: EBIT / (Celková aktiva - Krátkodobé závazky).",
        "h_roi": "Odhadovaná celková návratnost (Čistý zisk / Celková aktiva)."
    },
    "EN": {
        "title": "VALUATION & FUNDAMENTALS",
        "desc": "IN-DEPTH FINANCIAL STATEMENT AND RATIO SCREENER.",
        "db_select": "DATABASE",
        "custom_tick": "CUSTOM TICKER",
        "loading": "LOADING STATEMENTS...",
        "err_data": "DATA FOR THIS TICKER NOT AVAILABLE.",
        "err_api": "⚠️ YAHOO FINANCE API LIMIT: Connection temporarily blocked. Please try again later.",
        "tab_dash": "📊 ANALYTICS DASHBOARD",
        "tab_raw": "🗄️ STRUCTURED STATEMENTS",
        "met_val": "VALUATION",
        "met_mul": "MULTIPLES & LIQUIDITY",
        "met_mar": "MARGINS (CASCADE)",
        "met_ret": "PROFITABILITY",
        "met_ltm": "LTM (TTM) DATA",
        "h_chart": "FINANCIALS TREND: REVENUE, EBITDA, NET INCOME (Inc. LTM)",
        "leg_rev": "Total Revenue",
        "leg_net": "Net Income",
        "err_chart": "Error processing statements:",
        "err_miss": "Statement data is missing.",
        "raw_h": "STRUCTURED STATEMENTS DATABASE:",
        "raw_c": "Cleaned statement data formatted in Billions (B) and Millions (M).",
        "raw_inc": "1. INCOME STATEMENT",
        "raw_bal": "2. BALANCE SHEET",
        "raw_cf": "3. CASH FLOW STATEMENT",
        "raw_json": "4. COMPLETE METRICS (Raw JSON)",
        "raw_json_btn": "Show complete unformatted JSON",
        "raw_na": "Statement not available.",
        "h_de": "Calculation: Total Debt / Total Equity. Lower means less leverage.",
        "h_cr": "Current Ratio: Current Assets / Current Liabilities. Ideally > 1 (ability to pay debt within 1 year).",
        "h_qr": "Quick Ratio (Acid-test): (Current Assets - Inventory) / Current Liabilities. Stricter survival metric.",
        "h_roe": "Return on Equity: Net Income / Total Equity. How much the company generates on shareholder money.",
        "h_roic": "Return on Invested Capital: Net Income / (Total Debt + Total Equity). Capital allocation efficiency.",
        "h_roa": "Return on Assets: Net Income / Total Assets.",
        "h_roce": "Return on Capital Employed: EBIT / (Total Assets - Current Liabilities).",
        "h_roi": "Estimated Return on Investment (Net Income / Total Assets)."
    }
}
_ = t.get(st.session_state.get("lang", "CZ"), t["CZ"])

st.title(_["title"])
st.caption(_["desc"])
st.markdown("---")

def load_data():
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list): return {"portfolio": data, "watchlist": []}
                return data
        except: pass
    return {"portfolio": ["AAPL", "MSFT", "AMAT", "GOOGL"], "watchlist": []}

data = load_data()
all_tickers = list(dict.fromkeys(data.get("portfolio", []) + data.get("watchlist", [])))

def format_statements(df):
    if df is None or df.empty: return pd.DataFrame()
    styled = df.copy()
    styled.columns = [str(col)[:10] for col in styled.columns]
    def format_val(x):
        if pd.isna(x): return "-"
        if isinstance(x, (int, float)):
            if abs(x) >= 1e9: return f"${x/1e9:,.2f} B"
            if abs(x) >= 1e6: return f"${x/1e6:,.2f} M"
            return f"${x:,.2f}"
        return str(x)
    for col in styled.columns: styled[col] = styled[col].apply(format_val)
    return styled

def get_ltm_from_quarterly(df, keys):
    if df is None or df.empty: return None
    for key in keys:
        if key in df.index:
            vals = df.loc[key].iloc[:4]
            if len(vals) == 4 and not vals.isna().all(): return vals.sum()
    return None

c1, c2, c3 = st.columns([2, 2, 4])
sel_tick = c1.selectbox(_["db_select"], [""] + all_tickers)
custom_tick = c2.text_input(_["custom_tick"], value="")

final_tick = custom_tick.upper().strip() if custom_tick.strip() else sel_tick

if final_tick:
    with st.spinner(f"{_['loading']} {final_tick}..."):
        try:
            # Implementace Cache paměti (24 hodin = 86400 vteřin) a agresivního maskování
            session = requests_cache.CachedSession('yfinance_cache', expire_after=86400)
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            })
            
            tkr = yf.Ticker(final_tick, session=session)
            info = tkr.info
            
            if not info:
                st.error(_["err_data"])
            else:
                financials = tkr.financials
                balance_sheet = tkr.balance_sheet
                cashflow = tkr.cashflow
                q_fin = tkr.quarterly_financials
                q_cf = tkr.quarterly_cashflow
                
                short_name = info.get("shortName", final_tick)
                market_cap = info.get("marketCap")
                
                total_rev_ltm = get_ltm_from_quarterly(q_fin, ['Total Revenue']) or info.get("totalRevenue")
                net_income_ltm = get_ltm_from_quarterly(q_fin, ['Net Income', 'Net Income Common Stockholders']) or info.get("netIncomeToCommon", info.get("netIncome"))
                ebitda_ltm = get_ltm_from_quarterly(q_fin, ['Normalized EBITDA', 'EBITDA']) or info.get("ebitda")
                
                fcf = get_ltm_from_quarterly(q_cf, ['Free Cash Flow'])
                if fcf is None:
                    ocf = get_ltm_from_quarterly(q_cf, ['Operating Cash Flow'])
                    capex = get_ltm_from_quarterly(q_cf, ['Capital Expenditure'])
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
                
                if not balance_sheet.empty:
                    try:
                        total_debt = balance_sheet.loc['Total Debt'].iloc[0] if 'Total Debt' in balance_sheet.index else 0
                        stockholders_eq = balance_sheet.loc['Stockholders Equity'].iloc[0] if 'Stockholders Equity' in balance_sheet.index else 0
                        total_assets = balance_sheet.loc['Total Assets'].iloc[0] if 'Total Assets' in balance_sheet.index else 0
                        current_liab = balance_sheet.loc['Total Current Liabilities'].iloc[0] if 'Total Current Liabilities' in balance_sheet.index else 0
                        invested_capital = total_debt + stockholders_eq
                        capital_employed = total_assets - current_liab
                        if stockholders_eq and stockholders_eq > 0: calc_debt_eq = total_debt / stockholders_eq
                    except Exception:
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
                     except Exception: pass
                if net_income_ltm and 'total_assets' in locals() and total_assets > 0: roi = net_income_ltm / total_assets 

                tab_dash, tab_raw = st.tabs([_["tab_dash"], _["tab_raw"]])
                
                with tab_dash:
                    st.subheader(f"{short_name} ({final_tick})")
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    def fmt(val, is_pct=False, is_currency=False):
                        if val is None: return "N/A"
                        if is_pct: return f"{val*100:.2f} %"
                        if is_currency: 
                            if val >= 1e9: return f"${val/1e9:.2f}B"
                            if val >= 1e6: return f"${val/1e6:.2f}M"
                            return f"${val:,.2f}"
                        return f"{val:.2f}"
                        
                    col1.markdown(f"**{_['met_val']}**")
                    col1.metric("P/E (Trailing)", fmt(pe))
                    col1.metric("Forward P/E", fmt(fwd_pe))
                    col1.metric("PEG Ratio", fmt(peg))
                    col1.metric("Price / Sales", fmt(ps))
                    col1.metric("Price / FCF", fmt(p_fcf))
                    
                    col2.markdown(f"**{_['met_mul']}**")
                    col2.metric("EV / EBITDA", fmt(ev_ebitda))
                    col2.metric("Price / Book", fmt(pb))
                    col2.metric("Debt / Equity", fmt(calc_debt_eq), help=_["h_de"])
                    col2.metric("Current Ratio", fmt(current_ratio), help=_["h_cr"])
                    col2.metric("Quick Ratio", fmt(quick_ratio), help=_["h_qr"])
                    
                    col3.markdown(f"**{_['met_mar']}**")
                    col3.metric("Gross Margin", fmt(gross_margin, True))
                    col3.metric("EBITDA Margin", fmt(ebitda_margin, True))
                    col3.metric("Operating Margin", fmt(op_margin, True))
                    col3.metric("Profit Margin (Net)", fmt(profit_margin, True))
                    col3.metric("FCF Margin", fmt(fcf_margin, True))
                    
                    col4.markdown(f"**{_['met_ret']}**")
                    col4.metric("ROE", fmt(roe, True), help=_["h_roe"])
                    col4.metric("ROIC", fmt(roic, True), help=_["h_roic"])
                    col4.metric("ROA", fmt(roa, True), help=_["h_roa"])
                    col4.metric("ROCE", fmt(roce, True), help=_["h_roce"])
                    col4.metric("ROI (Proxy)", fmt(roi, True), help=_["h_roi"])

                    col5.markdown(f"**{_['met_ltm']}**")
                    col5.metric("LTM Revenue", fmt(total_rev_ltm, is_currency=True))
                    col5.metric("LTM EBITDA", fmt(ebitda_ltm, is_currency=True))
                    col5.metric("LTM Net Income", fmt(net_income_ltm, is_currency=True)) 
                    col5.metric("LTM FCF", fmt(fcf, is_currency=True))
                    col5.metric("LTM EPS", fmt(eps_ltm))
                    
                    st.markdown("---")
                    st.subheader(_["h_chart"])
                    
                    if not financials.empty:
                        try:
                            chart_df = pd.DataFrame()
                            if 'Total Revenue' in financials.index: chart_df['Tržby'] = financials.loc['Total Revenue'][::-1]
                            if 'EBITDA' in financials.index: chart_df['EBITDA'] = financials.loc['EBITDA'][::-1]
                            elif 'Normalized EBITDA' in financials.index: chart_df['EBITDA'] = financials.loc['Normalized EBITDA'][::-1]
                            if 'Net Income' in financials.index: chart_df['Čistý zisk'] = financials.loc['Net Income'][::-1]
                            elif 'Net Income Common Stockholders' in financials.index: chart_df['Čistý zisk'] = financials.loc['Net Income Common Stockholders'][::-1]
                            
                            chart_df.index = [str(d.year) for d in chart_df.index]
                            
                            ltm_data = {}
                            if 'Tržby' in chart_df.columns and total_rev_ltm: ltm_data['Tržby'] = total_rev_ltm
                            if 'EBITDA' in chart_df.columns and ebitda_ltm: ltm_data['EBITDA'] = ebitda_ltm
                            if 'Čistý zisk' in chart_df.columns and net_income_ltm: ltm_data['Čistý zisk'] = net_income_ltm
                            if ltm_data: chart_df = pd.concat([chart_df, pd.DataFrame([ltm_data], index=['LTM'])])
                            
                            fig = go.Figure()
                            if 'Tržby' in chart_df.columns: fig.add_trace(go.Bar(x=chart_df.index, y=chart_df['Tržby'], name=_["leg_rev"], marker_color='#2962FF'))
                            if 'EBITDA' in chart_df.columns: fig.add_trace(go.Bar(x=chart_df.index, y=chart_df['EBITDA'], name='EBITDA', marker_color='#FFA726'))
                            if 'Čistý zisk' in chart_df.columns: fig.add_trace(go.Bar(x=chart_df.index, y=chart_df['Čistý zisk'], name=_["leg_net"], marker_color='#26A69A'))
                            
                            fig.update_layout(template="plotly_dark", barmode='group', margin=dict(l=0, r=0, t=10, b=0), height=450, hovermode='x unified', yaxis=dict(fixedrange=False, showgrid=True, gridcolor='#2B2B2B'), xaxis=dict(fixedrange=False, showgrid=False))
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        except Exception as e: st.caption(f"{_['err_chart']} {str(e)}")
                    else: st.caption(_["err_miss"])

                with tab_raw:
                    st.subheader(f"{_['raw_h']} {final_tick}")
                    st.caption(_["raw_c"])
                    
                    st.markdown(f"### {_['raw_inc']}")
                    if not financials.empty: st.dataframe(format_statements(financials), use_container_width=True)
                    else: st.info(_["raw_na"])
                        
                    st.markdown(f"### {_['raw_bal']}")
                    if not balance_sheet.empty: st.dataframe(format_statements(balance_sheet), use_container_width=True)
                    else: st.info(_["raw_na"])
                        
                    st.markdown(f"### {_['raw_cf']}")
                    if not cashflow.empty: st.dataframe(format_statements(cashflow), use_container_width=True)
                    else: st.info(_["raw_na"])
                        
                    st.markdown(f"### {_['raw_json']}")
                    with st.expander(_["raw_json_btn"], expanded=False): st.json(info)
                    
        except Exception as e:
            if "YFRateLimitError" in str(type(e).__name__) or "429" in str(e):
                st.error(_["err_api"])
            else:
                st.error(f"SYS ERR: {str(e)}")
