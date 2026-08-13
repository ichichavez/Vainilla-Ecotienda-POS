@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo === Vainilla Ecotienda POS - Instalacion ===
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta en el PATH.
    echo Instala Python 3.10+ desde https://www.python.org/downloads/
    echo Marca la opcion "Add python.exe to PATH".
    pause
    exit /b 1
)

python --version
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Creando entorno virtual...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: no se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
)

echo Instalando dependencias...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: fallo la instalacion de dependencias.
    pause
    exit /b 1
)

if not exist "assets\productos" mkdir "assets\productos"

echo.
echo === Instalacion lista ===
echo.
echo Siguiente paso:
echo   1. Edita setup_user.py  (usuario y contrasena)
echo   2. Ejecuta:  crear_usuario.bat
echo   3. Ejecuta:  iniciar.bat
echo.
pause
