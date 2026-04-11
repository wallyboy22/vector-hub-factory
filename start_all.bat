@echo off
echo ========================================
echo   Vector Hub Factory - Iniciar Servidor
echo ========================================
echo.
echo Iniciando o servidor unificado FastAPI na porta 8000...
echo.
echo Acesse o Hub: http://localhost:8000/
echo.
.\.venv\Scripts\python.exe -m uvicorn src.api:app --port 8000 
