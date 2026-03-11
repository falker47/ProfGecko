@echo off
:: Posizionati nella directory del bat (fix path relativi)
cd /d "%~dp0"

echo ============================================
echo   Prof. Gecko - Avvio Re-ingestion dati
echo ============================================
echo.

:: Verifica prerequisiti
if not exist "backend\.venv\Scripts\activate" (
    echo [ERRORE] backend\.venv non trovato!
    echo Esegui:  cd backend ^&^& python -m venv .venv ^&^& .venv\Scripts\activate ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)

echo Avvio Re-ingestion dati (--force)...
start "Prof. Gecko Ingestion" cmd /k "cd /d "%~dp0backend" && call .venv\Scripts\activate && python -m app.ingestion.run_ingestion --force"

echo.
echo Re-ingestion avviata in una nuova finestra in background.
pause
