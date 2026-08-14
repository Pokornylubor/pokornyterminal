@echo off
cls
echo ==================================================
echo              POKORNY TERMINAL - START
echo ==================================================
echo.
echo [1] Rychly start (Spusti aplikaci ihned)
echo [2] Aktualizace (Stahne nova data - trva cca 15 minut)
echo.
set /p volba="Vyber moznost (zadej 1 nebo 2 a stiskni Enter): "

if "%volba%"=="2" (
    echo.
    echo --------------------------------------------------
    echo SPOUSTIM ROBOTA NA STAHOVANI DAT...
    echo (Proces potrva cca 10-15 minut)
    echo --------------------------------------------------
    python updater.py
    echo.
    echo Data uspesne stazena!
)

echo.
echo Zapinam webove rozhrani Streamlit...
streamlit run Dashboard.py