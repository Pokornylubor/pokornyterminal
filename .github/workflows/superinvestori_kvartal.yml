name: Kvartální Aktualizace (Superinvestoři)

on:
  schedule:
    # Spustí se 16. dne v měsíci ve 4:00 ráno, POUZE v únoru(2), květnu(5), srpnu(8) a listopadu(11)
    - cron: '0 4 16 2,5,8,11 *'
  workflow_dispatch:

jobs:
  aktualizace:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Instalace knihoven
        run: pip install -r requirements.txt
        
      - name: Nastavení práv k zápisu na GitHub
        run: |
          git config --global user.name "GitHub Actions Bot"
          git config --global user.email "actions@github.com"
          
      - name: Spuštění stahování POUZE Superinvestorů
        run: python updater.py superinvestors