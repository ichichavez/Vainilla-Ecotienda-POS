@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Primero ejecuta instalar.bat
    pause
    exit /b 1
)

echo === Actualizando desde GitHub ===
where git >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git no esta instalado.
    echo Instala Git desde https://git-scm.com/download/win
    pause
    exit /b 1
)

git pull
if errorlevel 1 (
    echo ERROR: no se pudo actualizar. Revisa la conexion o el repo.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
pip install -r requirements.txt
echo.
echo Actualizacion completa. La base de datos local no se modifica.
pause
