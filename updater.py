import cloudscraper
import pandas as pd
from bs4 import BeautifulSoup
import time
import random
import io

def get_update_period(soup):
    try:
        text_blocks = soup.find_all(['p', 'span', 'div'])
        for block in text_blocks:
            text = block.get_text()
            if 'Updated 13F portfolio' in text or 'Q' in text:
                if '202' in text:
                    words = text.split()
                    for i, word in enumerate(words):
                        if 'Q' in word and len(word) == 2:
                            try:
                                year = words[i+1]
                                return f"{word} {year}"
                            except: pass
    except: pass
    return "Neznámý kvartál"

def update_superinvestors(scraper):
    print("\n--- FÁZE 1: STAHUJI 13F SUPERINVESTORY (DATAROMA) ---")
    base_url = "https://www.dataroma.com/m/home.php"
    try:
        response = scraper.get(base_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        investors = []
        for link in soup.find_all('a', href=True):
            if 'holdings.php?m=' in link['href']:
                code = link['href'].split('=')[1]
                name = link.text.strip()
                if code not in [i['code'] for i in investors] and name: 
                    investors.append({'code': code, 'name': name})
                    
        all_holdings = []
        for idx, inv in enumerate(investors, 1):
            print(f"[{idx}/{len(investors)}] Stahuji: {inv['name']}")
            url = f"https://www.dataroma.com/m/holdings.php?m={inv['code']}"
            for pokus in range(3):
                try:
                    res = scraper.get(url, timeout=15)
                    soup_inv = BeautifulSoup(res.text, 'html.parser')
                    period = get_update_period(soup_inv)
                    tables = pd.read_html(io.StringIO(res.text))
                    if tables:
                        df = tables[0]
                        if 'History' in df.columns: df = df.drop(columns=['History'])
                        df['Investor'] = inv['name']
                        df['Kvartal_Aktualizace'] = period
                        all_holdings.append(df)
                    break 
                except Exception as e:
                    time.sleep(5) 
            time.sleep(random.uniform(4, 8)) 
            
        if all_holdings:
            pd.concat(all_holdings, ignore_index=True).to_csv('superinvestors_db.csv', index=False)
            print(f"✅ HOTOVO! 13F Superinvestoři uloženi.")
    except Exception as e:
        print(f"❌ Kritická chyba (Dataroma): {e}")

def update_insiders(scraper):
    print("\n--- FÁZE 2: STAHUJI MASIVNÍ DATA 4F INSIDERŮ (OPENINSIDER) ---")
    all_insider_data = []
    pages_to_scrape = 200
    
    for page in range(1, pages_to_scrape + 1):
        print(f"Stahuji stranu {page}/{pages_to_scrape} (1000 transakcí na stranu)...")
        url = f"http://openinsider.com/screener?s=&o=&pl=&ph=&ll=&lh=&fd=730&fdr=&td=0&tdr=&fdlyl=&fdlyh=&daysago=&xp=1&xs=1&vl=&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=0&cnt=1000&page={page}"
        try:
            response = scraper.get(url, timeout=15)
            tables = pd.read_html(io.StringIO(response.text))
            if tables:
                df = max(tables, key=len)
                if isinstance(df.columns, pd.Index): df.columns = df.columns.astype(str).str.strip()
                for col in ['X', '1d', '1w', '1m', '6m']:
                    if col in df.columns: df = df.drop(columns=[col])
                all_insider_data.append(df)
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            # TADY JE TA ZMĚNA: Přeskakujeme chybu, dáváme 10s pauzu a jedeme dál
            print(f"⚠️ Stránka {page} selhala ({e}). Dávám serveru 10s vydechnout a jedu dál...")
            time.sleep(10)
            continue 

    if all_insider_data:
        final_df = pd.concat(all_insider_data, ignore_index=True)
        final_df.to_csv('insider_4f_db.csv', index=False)
        print(f"✅ HOTOVO! Úspěšně uloženo {len(final_df)} Insider transakcí do databáze.")

if __name__ == "__main__":
    master_scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    print("Spouštím aktualizaci (Pokorný Terminal)...")
    update_superinvestors(master_scraper)
    update_insiders(master_scraper)
    print("\nData jsou připravena!")
