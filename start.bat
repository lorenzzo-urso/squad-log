@echo off
cd /d "%~dp0"
docker compose up -d
if errorlevel 1 (
    echo.
    echo Falha ao subir os containers. Verifique se o Docker Desktop esta aberto.
    pause
    exit /b 1
)
start http://localhost:8000
echo.
echo Timeline do Squad no ar em http://localhost:8000
pause
