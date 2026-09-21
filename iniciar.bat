@echo off
setlocal
title Nota de Inflacao - IPCA / IPCA-15

:: ---------------------------------------------------------------------------
:: Uso local (opcional). O normal e usar a pagina publicada no GitHub Pages;
:: este script existe so para rodar offline ou testar uma alteracao antes de
:: publicar.
::
:: A pagina e 100% estatica e fala direto com as APIs do IBGE e do BCB, entao
:: nao precisa de venv, de dependencia nenhuma e nem do FastAPI: basta um
:: servidor de arquivos. Nao dá para abrir o index.html com duplo clique
:: porque modulos ES sao bloqueados em file:// — por isso o servidor.
:: ---------------------------------------------------------------------------

where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERRO: Python nao encontrado no PATH.
    echo Instale em https://www.python.org/downloads/ marcando "Add to PATH".
    echo.
    pause
    exit /b 1
)

echo.
echo  Servindo a pagina em http://127.0.0.1:8777
echo  Feche esta janela para parar.
echo.

start "" http://127.0.0.1:8777
python -m http.server 8777 --bind 127.0.0.1 --directory "%~dp0site"

endlocal
