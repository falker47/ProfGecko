@echo off
:: Posizionati nella directory del bat (fix path relativi)
cd /d "%~dp0"

echo ============================================
echo   Prof. Gecko - Pre-push check (simula CI)
echo ============================================
echo.

set ERRORS=0

:: ---- BACKEND ----
echo [1/4] Backend - Syntax check (compileall)...
cd /d "%~dp0backend"
call .venv\Scripts\activate
python -m compileall -q app/
if errorlevel 1 (
    echo        *** FALLITO: errori di sintassi Python ***
    set ERRORS=1
) else (
    echo        OK
)

echo [2/4] Backend - Ruff lint...
pip show ruff >nul 2>&1 || pip install ruff >nul 2>&1
ruff check app/
if errorlevel 1 (
    echo        *** FALLITO: errori ruff ***
    set ERRORS=1
) else (
    echo        OK
)

:: ---- FRONTEND ----
cd /d "%~dp0frontend"

echo [3/4] Frontend - ESLint...
call npx next lint
if errorlevel 1 (
    echo        *** FALLITO: errori ESLint ***
    set ERRORS=1
) else (
    echo        OK
)

echo [4/4] Frontend - Build...
call npm run build
if errorlevel 1 (
    echo        *** FALLITO: errori build ***
    set ERRORS=1
) else (
    echo        OK
)

:: ---- RIEPILOGO ----
echo.
echo ============================================
if %ERRORS%==0 (
    echo   TUTTO OK - Puoi pushare tranquillamente!
) else (
    echo   CI FALLIREBBE - Correggi gli errori sopra
)
echo ============================================
pause
