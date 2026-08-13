@echo off
chcp 65001 >nul
cd /d "%~dp0"

if exist "%LOCALAPPDATA%\MinGit\cmd" (
    set "PATH=%LOCALAPPDATA%\MinGit\cmd;%PATH%"
)

call actualizar.bat
