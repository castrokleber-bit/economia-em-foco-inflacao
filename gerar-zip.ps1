# gerar-zip.ps1 — empacota o app para distribuição ao time
# Exclui .venv, __pycache__, .env e outros arquivos desnecessários.
# Salva o ZIP na Área de Trabalho.

$nome    = "economia-em-foco-inflacao"
$raiz    = $PSScriptRoot
$desktop = [Environment]::GetFolderPath("Desktop")
$destino = Join-Path $desktop "$nome.zip"
$tmp     = Join-Path $env:TEMP "${nome}_tmp"

Write-Host ""
Write-Host "Gerando ZIP de distribuicao..."
Write-Host "Origem : $raiz"
Write-Host "Destino: $destino"
Write-Host ""

# Limpa pasta temporária anterior
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
New-Item -ItemType Directory -Path $tmp | Out-Null
$pasta_zip = Join-Path $tmp $nome
New-Item -ItemType Directory -Path $pasta_zip | Out-Null

# Copia com exclusões via robocopy
# /E  = subpastas (incluindo vazias)
# /XD = excluir diretórios
# /XF = excluir arquivos (padrões)
# /NFL /NDL /NJH /NJS = silencioso
robocopy $raiz $pasta_zip /E `
    /XD ".venv" "__pycache__" ".pytest_cache" "output" ".git" ".mypy_cache" ".claude" `
    /XF ".env" "*.pyc" "*.pyo" "_golden_*.txt" "gerar-zip.ps1" "*.zip" `
    /NFL /NDL /NJH /NJS | Out-Null

# Compacta
if (Test-Path $destino) { Remove-Item $destino -Force }
Compress-Archive -Path $pasta_zip -DestinationPath $destino

# Limpeza
Remove-Item $tmp -Recurse -Force

# Resultado
$tamanho = [math]::Round((Get-Item $destino).Length / 1MB, 1)
Write-Host "Pronto! ZIP gerado com sucesso."
Write-Host "Arquivo : $destino"
Write-Host "Tamanho : $tamanho MB"
Write-Host ""
Write-Host "Para distribuir: envie o arquivo pelo Teams ou coloque"
Write-Host "numa pasta compartilhada da rede CNI."
Write-Host ""
