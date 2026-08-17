@echo off
chcp 65001 >nul
title Economia em Foco — Inflação

cd /d "%~dp0"

:: Aviso: caminhos muito longos estouram o limite do Windows (260 caracteres)
:: e quebram a instalacao das dependencias (ex: pacote anthropic).
for /f %%L in ('powershell -NoProfile -Command "$PWD.Path.Length"') do set "PATHLEN=%%L"
if %PATHLEN% GTR 130 (
    echo.
    echo AVISO: o caminho desta pasta tem %PATHLEN% caracteres.
    echo O Windows limita caminhos de arquivo a 260 caracteres, e a instalacao
    echo das dependencias pode falhar ^(erro tipico: OSError / No such file or directory^).
    echo.
    echo Se a instalacao falhar no proximo passo, mova esta pasta para um caminho
    echo mais curto, por exemplo C:\Apps\economia-em-foco-inflacao, e rode de novo.
    echo.
)

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
        echo ERRO: Falha ao instalar dependencias.
        echo Isso pode ser falta de conexao com a internet OU caminho de pasta
        echo muito longo ^(limite do Windows: 260 caracteres^). O caminho atual
        echo desta pasta tem %PATHLEN% caracteres.
        echo Se for isso, mova a pasta do projeto para um caminho mais curto
        echo ^(ex: C:\Apps\economia-em-foco-inflacao^) e rode iniciar.bat novamente.
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
