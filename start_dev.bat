@echo off
:: Posizionati nella directory del bat (fix path relativi)
cd /d "%~dp0"

echo ============================================
echo   Prof. Gecko - Avvio ambiente di sviluppo
echo ============================================
echo.

:: Verifica prerequisiti
if not exist "backend\.venv\Scripts\activate" (
    echo [ERRORE] backend\.venv non trovato!
    echo Esegui:  cd backend ^&^& python -m venv .venv ^&^& .venv\Scripts\activate ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)
if not exist "frontend\node_modules" (
    echo [ERRORE] frontend\node_modules non trovato!
    echo Esegui:  cd frontend ^&^& npm install
    pause
    exit /b 1
)

:: Avvia il backend in una nuova finestra
echo [1/2] Avvio Backend (FastAPI su porta 8000)...
start "Prof. Gecko Backend" cmd /k "cd /d "%~dp0backend" && call .venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

:: Avvia il frontend in una nuova finestra
echo [2/2] Avvio Frontend (Next.js su porta 3000)...
start "Prof. Gecko Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo Tutti i servizi si stanno avviando in finestre separate.
echo - Backend:   http://localhost:8000
echo - Frontend:  http://localhost:3000
echo.
echo Premi un tasto per chiudere questa finestra (i servizi restano attivi).
pause
