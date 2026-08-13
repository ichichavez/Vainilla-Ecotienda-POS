@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Primero ejecuta instalar.bat
    pause
    exit /b 1
)

echo === Actualizando desde GitHub ===
echo.

REM Respaldo automatico de la base antes de actualizar
if exist "ventas.db" (
    echo Respaldando base de datos...
    call .venv\Scripts\activate.bat
    python -c "from utils.backup import backup_full; r=backup_full('backups'); c=r['counts']; print('Respaldo completo OK:', r['folder']); print('Productos:', c.get('productos',0), 'Clientes:', c.get('clientes',0), 'Ventas:', c.get('ventas',0))"
    if errorlevel 1 (
        echo ADVERTENCIA: no se pudo respaldar. Abortando update.
        pause
        exit /b 1
    )
    echo.
)

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
echo Actualizacion completa.
echo La base de datos local NO se modifica.
echo Respaldo (si habia datos) en la carpeta backups\
pause
