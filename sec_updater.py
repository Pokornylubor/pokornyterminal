import cloudscraper
import pandas as pd
import requests
import json
import os
import time
import re
import yfinance as yf
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WATCHLIST_FILE = os.path.join(BASE_DIR, "watchlist.json")
SEC_DATA_DIR = os.path.join(BASE_DIR, "sec_data")
os.makedirs(SEC_DATA_DIR, exist_ok=True)

SEC_HEADERS = {"User-Agent": "PokornyTerminal pokornyl98@gmail.com", "Accept-Encoding": "gzip, deflate"}

def preved_na_kvartal(datum_str):
    if not datum_str or len(datum_str) < 10: return "Neznámý kvartál"
    rok = datum_str[:4]
    mesic = datum_str[5:7]
    if mesic in ['01', '02', '03']: return f"Q1 {rok}"
    if mesic in ['04', '05', '06']: return f"Q2 {rok}"
    if mesic in ['07', '08', '09']: return f"Q3 {rok}"
    if mesic in ['10', '11', '12']: return f"Q4 {rok}"
    return datum_str

def guess_ticker(company_name):
    clean_name = re.sub(r'\b(COM|CL A|CLASS A|INC|CORP|LLC|PLC|LTD|HOLDINGS|GROUP|NEW|NV|CO)\b', '', company_name).strip()
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={requests.utils.quote(clean_name)}"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=2)
        if res.status_code == 200:
            for q in res.json().get('quotes', []):
                if q.get('quoteType') in ['EQUITY', 'ETF'] and '.' not in q.get('symbol', ''):
                    return q['symbol']
    except: pass
    return None

def get_13f_df(scraper, cik, acc_no_hyphens):
    acc_no_clean = acc_no_hyphens.replace('-', '')
    txt_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no_clean}/{acc_no_hyphens}.txt"
    try:
        txt_res = scraper.get(txt_url, headers=SEC_HEADERS, timeout=10)
        if txt_res.status_code == 200:
            blocks = re.findall(r'(?is)<[^>]*?infoTable[^>]*>(.*?)</[^>]*?infoTable>', txt_res.text)
            pos = []
            for block in blocks:
                issuer = re.search(r'(?is)<[^>]*?nameOfIssuer[^>]*>(.*?)</[^>]*?nameOfIssuer>', block)
                val = re.search(r'(?is)<[^>]*?value[^>]*>(.*?)</[^>]*?value>', block)
                shares = re.search(r'(?is)<[^>]*?sshPrnamt[^>]*>(.*?)</[^>]*?sshPrnamt>', block)
                if issuer and val and shares:
                    try:
                        pos.append({
                            "Stock": issuer.group(1).strip().upper(), 
                            "Value": float(val.group(1).strip().replace(',', '')),
                            "Shares": float(shares.group(1).strip().replace(',', ''))
                        })
                    except: pass
            if pos: return pd.DataFrame(pos).groupby("Stock").sum().reset_index()
    except: pass
    return None

def update_sec_funds(target_cik=None):
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    
    try:
        with open(WATCHLIST_FILE, "r") as f: data = json.load(f)
        custom_ciks = data.get("saved_ciks", {})
    except: custom_ciks = {}

    ALL_FUNDS = {
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
    ALL_FUNDS.update(custom_ciks)

    for name, cik in ALL_FUNDS.items():
        cik_str = str(cik).zfill(10)
        if target_cik and cik_str != str(target_cik).zfill(10): continue
        
        print(f"🔄 Aktualizuji SEC data: {name}...")
        try:
            res = scraper.get(f"https://data.sec.gov/submissions/CIK{cik_str}.json", headers=SEC_HEADERS, timeout=10)
            if res.status_code == 200:
                recent = res.json().get("filings", {}).get("recent", {})
                forms, acc_nums, report_dates, filing_dates = recent.get("form", []), recent.get("accessionNumber", []), recent.get("reportDate", []), recent.get("filingDate", [])
                
                valid_filings = []
                for i in range(len(forms)):
                    if "13F" in str(forms[i]).upper() and "NT" not in str(forms[i]).upper():
                        r_date = report_dates[i] if (i < len(report_dates) and report_dates[i]) else (filing_dates[i] if i < len(filing_dates) else "1900-01-01")
                        valid_filings.append({"acc_num": acc_nums[i], "report_date": r_date, "filing_date": filing_dates[i]})
                
                if valid_filings:
                    valid_filings.sort(key=lambda x: x["filing_date"], reverse=True)
                    unique_quarters = {}
                    for f in valid_filings:
                        if f["report_date"] not in unique_quarters: unique_quarters[f["report_date"]] = f
                    
                    sorted_quarters = sorted(list(unique_quarters.values()), key=lambda x: x["report_date"], reverse=True)
                    latest_filing = sorted_quarters[0]
                    df_latest = get_13f_df(scraper, cik_str, latest_filing["acc_num"])
                    
                    if df_latest is not None and not df_latest.empty:
                        df_latest["% of Portfolio"] = (df_latest["Value"] / df_latest["Value"].sum()) * 100
                        df_latest["ReportedPrice*"] = df_latest.apply(lambda r: (r["Value"] / r["Shares"]) if r["Shares"] > 0 else 0, axis=1)
                        df_latest["RecentActivity"] = ""
                        
                        if len(sorted_quarters) > 1:
                            df_prev = get_13f_df(scraper, cik_str, sorted_quarters[1]["acc_num"])
                            if df_prev is not None and not df_prev.empty:
                                df_merged = pd.merge(df_latest, df_prev[["Stock", "Shares"]], on="Stock", how="left", suffixes=("", "_prev"))
                                def calc_activity(row):
                                    if pd.isna(row["Shares_prev"]) or row["Shares_prev"] == 0: return "Buy 100%"
                                    diff = row["Shares"] - row["Shares_prev"]
                                    if diff == 0: return ""
                                    pct_change = (diff / row["Shares_prev"]) * 100
                                    return f"Add {pct_change:,.2f}%" if pct_change > 0 else f"Reduce {abs(pct_change):,.2f}%"
                                df_latest["RecentActivity"] = df_merged.apply(calc_activity, axis=1)
                        
                        df_latest = df_latest.sort_values(by="% of Portfolio", ascending=False)
                        top_df = df_latest.head(150).copy()
                        bottom_df = df_latest.iloc[150:].copy()
                        top_df["Ticker_Guess"] = top_df["Stock"].apply(guess_ticker)
                        bottom_df["Ticker_Guess"] = None
                        df_latest = pd.concat([top_df, bottom_df])
                        
                        valid_tickers = df_latest["Ticker_Guess"].dropna().unique().tolist()
                        market_data = {}
                        if valid_tickers:
                            try:
                                hist = yf.download(valid_tickers, period="1y", group_by="ticker", progress=False, ignore_tz=True)
                                for tkr in valid_tickers:
                                    th = hist if len(valid_tickers) == 1 else hist[tkr]
                                    if not th.empty: market_data[tkr] = {"Current Price": th["Close"].iloc[-1], "52Week Low": th["Low"].min(), "52Week High": th["High"].max()}
                            except: pass
                        
                        df_latest["Current Price"] = df_latest["Ticker_Guess"].map(lambda x: market_data.get(x, {}).get("Current Price", None))
                        df_latest["52Week Low"] = df_latest["Ticker_Guess"].map(lambda x: market_data.get(x, {}).get("52Week Low", None))
                        df_latest["52Week High"] = df_latest["Ticker_Guess"].map(lambda x: market_data.get(x, {}).get("52Week High", None))
                        df_latest["+/-Reported Price"] = df_latest.apply(
                            lambda r: ((r["Current Price"] - r["ReportedPrice*"]) / r["ReportedPrice*"]) * 100 if pd.notnull(r["Current Price"]) and r["ReportedPrice*"] > 0 else None, axis=1)
                        df_latest[" "] = ""
                        
                        final_cols = ["Stock", "% of Portfolio", "RecentActivity", "Shares", "ReportedPrice*", "Value", " ", "Current Price", "+/-Reported Price", "52Week Low", "52Week High"]
                        df_final = df_latest[final_cols]
                        
                        # Uložení CSV a Metadat
                        df_final.to_csv(os.path.join(SEC_DATA_DIR, f"{cik_str}.csv"), index=False)
                        meta = {
                            "fund_name": name,
                            "report_date": latest_filing['report_date'],
                            "kvartal": preved_na_kvartal(latest_filing['report_date']),
                            "last_updated": datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                        }
                        with open(os.path.join(SEC_DATA_DIR, f"{cik_str}_meta.json"), "w") as f:
                            json.dump(meta, f)
                        print(f"✅ Uloženo: {name}")
        
        # TADY JE TA ZMĚNA: Přeskakujeme chybu, dáváme 10s pauzu a jedeme plynule dál
        except Exception as e: 
            print(f"⚠️ Chyba u {name} ({e}). Dávám serveru SEC 10s vydechnout a přeskakuji na další...")
            time.sleep(10)
            continue
            
        # Standardní bezpečnostní pauza mezi fondy, když se to stáhne úspěšně
        time.sleep(1) 

if __name__ == "__main__":
    update_sec_funds()
