@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist "iniciar.bat" (
    echo No se encontro iniciar.bat en esta carpeta.
    pause
    exit /b 1
)

set "TARGET=%~dp0iniciar.bat"
set "WORKDIR=%~dp0"
set "SHORTCUT=%USERPROFILE%\Desktop\Vainilla Ecotienda POS.lnk"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $sc = $ws.CreateShortcut('%SHORTCUT%'); ^
   $sc.TargetPath = '%TARGET%'; ^
   $sc.WorkingDirectory = '%WORKDIR%'; ^
   $sc.WindowStyle = 7; ^
   $sc.Description = 'Punto de Venta Vainilla Ecotienda'; ^
   $sc.Save(); ^
   Write-Host 'Acceso directo creado en el Escritorio.'"

if errorlevel 1 (
    echo ERROR: no se pudo crear el acceso directo.
    pause
    exit /b 1
)

echo.
echo Listo: "Vainilla Ecotienda POS" en el Escritorio.
pause
