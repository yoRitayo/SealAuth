#!/bin/sh
# Gera o docker secret do JWT antes de subir com docker compose.
# Ordem: openssl rand (256+ bits) -> fallback para JWT_SECRET do .env.
set -e

DESTINO="secrets/jwt_secret.txt"
mkdir -p secrets

if [ -s "$DESTINO" ]; then
  echo "Segredo já existe em $DESTINO (remova o arquivo para gerar outro)"
  exit 0
fi

if SEGREDO=$(openssl rand -base64 48 2>/dev/null) && [ -n "$SEGREDO" ]; then
  printf '%s' "$SEGREDO" > "$DESTINO"
  echo "Segredo gerado com openssl"
else
  echo "openssl indisponível; usando JWT_SECRET do .env" >&2
  VALOR=$(grep -E '^JWT_SECRET=' .env | head -n 1 | cut -d= -f2- | sed 's/[[:space:]]*#.*$//; s/[[:space:]]*$//')
  if [ -z "$VALOR" ]; then
    echo "Erro: openssl indisponível e JWT_SECRET ausente no .env" >&2
    exit 1
  fi
  printf '%s' "$VALOR" > "$DESTINO"
fi

chmod 600 "$DESTINO"
