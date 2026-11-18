@echo off
cd /d "%~dp0"
where pyw >nul 2>nul
if %errorlevel%==0 (
    start "" pyw -3 tpose.py
    exit /b
)
where pythonw >nul 2>nul
if %errorlevel%==0 (
    start "" pythonw tpose.py
    exit /b
)
echo No se encontro Python. Usa "Tpose.exe" o instala Python 3.10+ con Pillow.
pause
