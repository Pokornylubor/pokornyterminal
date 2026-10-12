name: Denní Aktualizace (Insiders)

on:
  schedule:
    - cron: '0 4 * * *' # Spustí se KAŽDÝ DEN ve 4:00 ráno (5:00 CZ času)
  workflow_dispatch: # Ponechá ti i ruční tlačítko na webu

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
          
      - name: Spuštění stahování POUZE Insiderů
        run: python updater.py insiders