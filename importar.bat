@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Primero ejecuta instalar.bat
    pause
    exit /b 1
)

echo === Importar base de datos ===
echo.
echo ATENCION: Reemplaza ventas, clientes, productos, etc.
echo Solo se importan usuarios SUPERADMIN del respaldo.
echo Los demas usuarios del respaldo NO se copian.
echo.
echo Se crea un respaldo de seguridad en la carpeta backups\ antes de importar.
echo.

set /p DBFILE="Ruta del archivo .db a importar: "
if "%DBFILE%"=="" (
    echo Cancelado.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
python importar_db.py "%DBFILE%"
echo.
pause
