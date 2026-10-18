# Gera o docker secret do JWT antes de subir o compose (Windows).
# Ordem: openssl rand (256+ bits) -> fallback para JWT_SECRET do .env.
$ErrorActionPreference = "Stop"

$destino = "secrets/jwt_secret.txt"
New-Item -ItemType Directory -Force -Path "secrets" | Out-Null

if ((Test-Path $destino) -and ((Get-Item $destino).Length -gt 0)) {
    Write-Host "Segredo já existe em $destino (remova o arquivo para gerar outro)"
    exit 0
}

$segredo = $null
if (Get-Command openssl -ErrorAction SilentlyContinue) {
    $segredo = (& openssl rand -base64 48 2>$null)
}

if ($segredo) {
    Write-Host "Segredo gerado com openssl"
} else {
    Write-Host "openssl indisponível; usando JWT_SECRET do .env" -ForegroundColor Yellow
    $linha = Get-Content .env | Where-Object { $_ -match '^JWT_SECRET=' } | Select-Object -First 1
    if (-not $linha) {
        Write-Error "openssl indisponível e JWT_SECRET ausente no .env"
        exit 1
    }
    # Remove o valor após "=", o comentário inline e espaços
    $segredo = (($linha -replace '^JWT_SECRET=', '') -replace '\s*#.*$', '').Trim()
    if (-not $segredo) {
        Write-Error "openssl indisponível e JWT_SECRET vazio no .env"
        exit 1
    }
}

# Sem BOM e sem quebra de linha final, igual ao gerador em sh
[System.IO.File]::WriteAllText((Join-Path (Get-Location) $destino), $segredo.Trim())
