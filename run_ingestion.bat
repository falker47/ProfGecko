@echo off
:: Posizionati nella directory del bat (fix path relativi)
cd /d "%~dp0"

echo ============================================
echo   Prof. Gallade - Avvio Re-ingestion dati
echo ============================================
echo.

echo Avvio Re-ingestion dati (--force)...
start "Prof. Gallade Ingestion" cmd /k "cd /d "%~dp0backend" && call .venv\Scripts\activate && python -m app.ingestion.run_ingestion --force"

echo.
echo Re-ingestion avviata in una nuova finestra in background.
pause
