@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Primero ejecuta instalar.bat
    pause
    exit /b 1
)

echo Crea o actualiza el usuario definido en setup_user.py
echo Edita ese archivo antes si queres otro usuario/contrasena.
echo.
call .venv\Scripts\activate.bat
python setup_user.py
echo.
pause
