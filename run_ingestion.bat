@echo off
cd /d "%~dp0"

echo ============================================
echo   Prof. Gecko - Avvio Re-ingestion dati
echo ============================================
echo.

if not exist "backend\.venv\Scripts\activate.bat" (
    echo [ERRORE] backend\.venv non trovato!
    echo Esegui:  cd backend ^&^& python -m venv .venv ^&^& .venv\Scripts\activate ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)

echo Avvio Re-ingestion dati (--force)...
start "ProfGecko-Ingestion" "%~dp0backend\_start_ingestion.bat"

echo.
echo Re-ingestion avviata in una nuova finestra.
pause
