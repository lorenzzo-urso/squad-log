@echo off
cd /d "%~dp0"
docker compose down
if errorlevel 1 (
    echo.
    echo Falha ao encerrar os containers. Verifique se o Docker Desktop esta aberto.
    pause
    exit /b 1
)
echo.
echo Timeline do Squad encerrada.
pause
