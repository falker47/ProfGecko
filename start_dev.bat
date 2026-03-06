@echo off
:: Posizionati nella directory del bat (fix path relativi)
cd /d "%~dp0"

echo ============================================
echo   Prof. Gallade - Avvio ambiente di sviluppo
echo ============================================
echo.

:: Avvia il backend in una nuova finestra
echo [1/3] Avvio Backend (FastAPI su porta 8000)...
start "Prof. Gallade Backend" cmd /k "cd /d "%~dp0backend" && call .venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

:: Avvia il frontend in una nuova finestra
echo [2/3] Avvio Frontend (Next.js su porta 3000)...
start "Prof. Gallade Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo Tutti i servizi si stanno avviando in finestre separate.
echo - Backend:   http://localhost:8000
echo - Frontend:  http://localhost:3000
pause
