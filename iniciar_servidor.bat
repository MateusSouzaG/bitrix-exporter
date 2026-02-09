@echo off
cd /d "%~dp0"
echo Iniciando Bitrix24 Exporter a partir de: %CD%
echo.
echo Apos iniciar, acesse: http://localhost:8001
echo Para parar: Ctrl+C
echo.
python -m uvicorn app:app --host 0.0.0.0 --port 8001
pause
