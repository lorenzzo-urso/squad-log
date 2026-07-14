@echo off
cd /d "%~dp0"
if not exist backups mkdir backups
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TS=%%i
docker compose exec -T app tar czf - /data > "backups\backup_%TS%.tar.gz"
if errorlevel 1 (
    echo.
    echo Falha ao gerar o backup. Verifique se o Docker Desktop esta aberto e o container rodando.
    pause
    exit /b 1
)
echo.
echo Backup salvo em backups\backup_%TS%.tar.gz
pause
