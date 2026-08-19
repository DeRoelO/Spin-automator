@echo off
echo ========================================================
echo SPIN Automator Installatie ^& Start Script
echo ========================================================

:: Controleer of Python is geinstalleerd
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [FOUT] Python is niet geinstalleerd of niet toegevoegd aan PATH!
    echo Download Python via de Microsoft Store of python.org ^(vink "Add to PATH" aan^).
    pause
    exit /b
)

:: Maak de virtuele omgeving (venv) aan als die nog niet bestaat
if not exist "venv\" (
    echo [+] Eerste installatie: virtuele omgeving ^(venv^) aanmaken...
    python -m venv venv
)

:: Activeer de virtuele omgeving
echo [+] Virtuele omgeving activeren...
call venv\Scripts\activate.bat

:: Installeer de benodigde Python pakketten
echo [+] Afhankelijkheden installeren...
pip install -r requirements.txt

:: Installeer de onzichtbare Playwright browser (Chromium)
echo [+] Webbrowser engine installeren ^(eenmalig, kan even duren^)...
playwright install chromium

:: Start de applicatie
echo [+] SPIN Automator wordt gestart in je browser...
streamlit run app.py

pause
