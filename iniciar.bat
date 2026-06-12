@echo off
chcp 65001 >nul
title Economia em Foco — Inflação

cd /d "%~dp0"

:: Primeira vez: criar venv e instalar dependências
if not exist ".venv\Scripts\uvicorn.exe" (
    echo.
    echo [1/3] Criando ambiente Python...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo ERRO: Python nao encontrado. Instale Python 3.11+ e tente novamente.
        echo Download: https://www.python.org/downloads/
        pause
        exit /b 1
    )

    echo [2/3] Instalando dependencias ^(aguarde ~1 min na primeira vez^)...
    .venv\Scripts\pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo.
        echo ERRO: Falha ao instalar dependencias. Verifique a conexao com a internet.
        pause
        exit /b 1
    )

    echo [3/3] Pronto!
    echo.
)

:: Subir o servidor
echo Iniciando servidor em http://127.0.0.1:8000 ...
echo Para encerrar: feche esta janela.
echo.

:: Abrir o browser apos 2 segundos
start "" /b cmd /c "timeout /t 2 >nul && start http://127.0.0.1:8000"

.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000
