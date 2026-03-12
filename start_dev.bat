@echo off
cd /d "%~dp0"

echo ============================================
echo   Prof. Gecko - Avvio ambiente di sviluppo
echo ============================================
echo.

if not exist "backend\.venv\Scripts\activate.bat" (
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

echo [1/2] Avvio Backend (FastAPI su porta 8000)...
start "ProfGecko-Backend" "%~dp0backend\_start_backend.bat"

echo [2/2] Avvio Frontend (Next.js su porta 3000)...
start "ProfGecko-Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo Tutti i servizi si stanno avviando in finestre separate.
echo - Backend:   http://localhost:8000
echo - Frontend:  http://localhost:3000
echo.
echo Premi un tasto per chiudere questa finestra (i servizi restano attivi).
pause
