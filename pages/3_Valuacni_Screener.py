import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os
import sys
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
        "title": "FUNDAMENTY & VALUACE",
        "desc": "HLOUBKOVÝ SCREENER FINANČNÍCH VÝKAZŮ A UKAZATELŮ.",
        "db_select": "DATABÁZE",
        "custom_tick": "VLASTNÍ TICKER",
        "loading": "STAHOVÁNÍ VÝKAZŮ...",
        "err_data": "DATA PRO TENTO TICKER NEJSOU DOSTUPNÁ."
    },
    "EN": {
        "title": "FUNDAMENTALS & VALUATION",
        "desc": "IN-DEPTH FINANCIAL STATEMENT AND RATIO SCREENER.",
        "db_select": "DATABASE",
        "custom_tick": "CUSTOM TICKER",
        "loading": "LOADING STATEMENTS...",
        "err_data": "DATA FOR THIS TICKER NOT AVAILABLE."
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

# --- OVLÁDACÍ PANEL ---
c1, c2, c3 = st.columns([2, 2, 4])
sel_tick = c1.selectbox(_["db_select"], [""] + all_tickers)
custom_tick = c2.text_input(_["custom_tick"], value="")

final_tick = custom_tick.upper().strip() if custom_tick.strip() else sel_tick

if final_tick:
    with st.spinner(f"{_['loading']} {final_tick}..."):
        tkr = yf.Ticker(final_tick)
        info = tkr.info
        financials = tkr.financials
        
        # Získání metrik
        short_name = info.get("shortName", final_tick)
        pe = info.get("trailingPE")
        fwd_pe = info.get("forwardPE")
        peg = info.get("pegRatio")
        pb = info.get("priceToBook")
        ev_ebitda = info.get("enterpriseToEbitda")
        debt_eq = info.get("debtToEquity")
        
        # Marže a rentabilita
        roe = info.get("returnOnEquity")
        roa = info.get("returnOnAssets")
        gross_margin = info.get("grossMargins")
        op_margin = info.get("operatingMargins")
        profit_margin = info.get("profitMargins")
        
        # LTM (TTM) Data a dopočítání EBITDA marže
        total_rev_ltm = info.get("totalRevenue")
        ebitda_ltm = info.get("ebitda")
        eps_ltm = info.get("trailingEps")
        
        ebitda_margin = None
        if ebitda_ltm and total_rev_ltm and total_rev_ltm > 0:
            ebitda_margin = ebitda_ltm / total_rev_ltm

    if info:
        st.subheader(f"METRIKY: {short_name} ({final_tick})")
        
        # --- TABULKA VALUACE, RENTABILITY A LTM ---
        col1, col2, col3, col4, col5 = st.columns(5)
        
        def fmt(val, is_pct=False, is_currency=False):
            if val is None: return "N/A"
            if is_pct: return f"{val*100:.2f} %"
            if is_currency: 
                if val >= 1e9: return f"${val/1e9:.2f}B"
                if val >= 1e6: return f"${val/1e6:.2f}M"
                return f"${val:,.2f}"
            return f"{val:.2f}"
            
        col1.markdown("**VALUACE**")
        col1.metric("P/E (Trailing)", fmt(pe))
        col1.metric("Forward P/E", fmt(fwd_pe))
        col1.metric("PEG Ratio", fmt(peg))
        
        col2.markdown("**MULTIPLIKÁTORY**")
        col2.metric("EV / EBITDA", fmt(ev_ebitda))
        col2.metric("Price / Book", fmt(pb))
        col2.metric("Debt / Equity", fmt(debt_eq))
        
        col3.markdown("**MARŽE (KASKÁDA)**")
        col3.metric("Gross Margin", fmt(gross_margin, True))
        col3.metric("EBITDA Margin", fmt(ebitda_margin, True))
        col3.metric("Operating Margin", fmt(op_margin, True))
        
        col4.markdown("**RENTABILITA & ZISK**")
        col4.metric("Profit Margin (Net)", fmt(profit_margin, True))
        col4.metric("ROE", fmt(roe, True))
        col4.metric("ROA", fmt(roa, True))

        col5.markdown("**LTM (TTM) DATA**")
        col5.metric("LTM Revenue", fmt(total_rev_ltm, is_currency=True))
        col5.metric("LTM EBITDA", fmt(ebitda_ltm, is_currency=True))
        col5.metric("LTM EPS", fmt(eps_ltm, is_currency=True))
        
        st.markdown("---")
        
        # --- VÝKAZ ZISKŮ A ZTRÁT (BAR CHART S LTM) ---
        st.subheader("VÝVOJ VÝKAZŮ: TRŽBY, EBITDA, ZISK (Včetně LTM)")
        
        if not financials.empty:
            try:
                chart_df = pd.DataFrame()
                
                # Získání historických dat
                if 'Total Revenue' in financials.index:
                    chart_df['Tržby'] = financials.loc['Total Revenue'][::-1]
                
                if 'EBITDA' in financials.index:
                    chart_df['EBITDA'] = financials.loc['EBITDA'][::-1]
                elif 'Normalized EBITDA' in financials.index:
                    chart_df['EBITDA'] = financials.loc['Normalized EBITDA'][::-1]
                    
                if 'Net Income' in financials.index:
                    chart_df['Čistý zisk'] = financials.loc['Net Income'][::-1]
                elif 'Net Income Common Stockholders' in financials.index:
                    chart_df['Čistý zisk'] = financials.loc['Net Income Common Stockholders'][::-1]
                
                # Očistění indexu na roky
                chart_df.index = [str(d.year) for d in chart_df.index]
                
                # Tvrdé vytvoření a připojení LTM řádku (Safe Pandas Concat)
                ltm_data = {}
                if 'Tržby' in chart_df.columns and total_rev_ltm:
                    ltm_data['Tržby'] = total_rev_ltm
                if 'EBITDA' in chart_df.columns and ebitda_ltm:
                    ltm_data['EBITDA'] = ebitda_ltm
                if 'Čistý zisk' in chart_df.columns:
                    net_ltm = info.get("netIncomeToCommon", info.get("netIncome"))
                    if net_ltm: ltm_data['Čistý zisk'] = net_ltm
                
                if ltm_data:
                    df_ltm = pd.DataFrame([ltm_data], index=['LTM'])
                    chart_df = pd.concat([chart_df, df_ltm])
                
                fig = go.Figure()
                
                if 'Tržby' in chart_df.columns:
                    fig.add_trace(go.Bar(x=chart_df.index, y=chart_df['Tržby'], name='Tržby (Revenue)', marker_color='#2962FF'))
                if 'EBITDA' in chart_df.columns:
                    fig.add_trace(go.Bar(x=chart_df.index, y=chart_df['EBITDA'], name='EBITDA', marker_color='#FFA726'))
                if 'Čistý zisk' in chart_df.columns:
                    fig.add_trace(go.Bar(x=chart_df.index, y=chart_df['Čistý zisk'], name='Čistý zisk (Net Income)', marker_color='#26A69A'))
                
                fig.update_layout(
                    template="plotly_dark",
                    barmode='group',
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=450,
                    hovermode='x unified',
                    yaxis=dict(fixedrange=False, showgrid=True, gridcolor='#2B2B2B'),
                    xaxis=dict(fixedrange=False, showgrid=False)
                )
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            except Exception as e:
                st.caption(f"Došlo k chybě při zpracování výkazů: {str(e)}")
        else:
            st.caption("Data z výkazů chybí.")
            
    else:
        st.error(_["err_data"])
