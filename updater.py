import cloudscraper
import pandas as pd
from bs4 import BeautifulSoup
import time
import random
import io

def get_update_period(soup):
    """Zkusí najít informaci o tom, ze kterého kvartálu data z Dataromy pocházejí."""
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
                            except:
                                pass
    except:
        pass
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
                    
        print(f"Nalezeno {len(investors)} investorů. Spouštím cyklus...")
        
        all_holdings = []
        
        for idx, inv in enumerate(investors, 1):
            print(f"[{idx}/{len(investors)}] Stahuji: {inv['name']}")
            url = f"https://www.dataroma.com/m/holdings.php?m={inv['code']}"
            
            # OBRNĚNÝ BLOK: Zkusí to až 3x, než to vzdá
            for pokus in range(3):
                try:
                    res = scraper.get(url, timeout=15)
                    soup_inv = BeautifulSoup(res.text, 'html.parser')
                    period = get_update_period(soup_inv)
                    
                    html_data = io.StringIO(res.text)
                    tables = pd.read_html(html_data)
                    
                    if tables:
                        df = tables[0]
                        if 'History' in df.columns:
                            df = df.drop(columns=['History'])
                        
                        df['Investor'] = inv['name']
                        df['Kvartal_Aktualizace'] = period
                        all_holdings.append(df)
                    break # Pokud to vyjde, vyskočí z cyklu pokusů a jde na dalšího investora
                    
                except Exception as e:
                    print(f"   ⚠️ Výpadek spojení. Zkouším znovu ({pokus + 1}/3)...")
                    time.sleep(5) # Počká 5 vteřin před dalším pokusem
            
            # Náhodná pauza pro zmatení obrany Dataromy
            time.sleep(random.uniform(4, 8)) 
            
        if all_holdings:
            final_db = pd.concat(all_holdings, ignore_index=True)
            final_db.to_csv('superinvestors_db.csv', index=False)
            print(f"✅ HOTOVO! 13F Superinvestoři uloženi do 'superinvestors_db.csv'.")
        else:
            print("❌ Nepodařilo se stáhnout žádná data z Dataromy.")
            
    except Exception as e:
        print(f"❌ Kritická chyba při načítání hlavní stránky: {e}")

if __name__ == "__main__":
    master_scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    
    print("Spouštím hlavní aktualizační program Pokorný Terminal...")
    update_superinvestors(master_scraper)
    
    print("\nCELÝ PROCES DOKONČEN. Data jsou připravena pro aplikaci.")
