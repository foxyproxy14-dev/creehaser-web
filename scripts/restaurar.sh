#!/bin/sh
# Restaura un respaldo de la base de datos (y opcionalmente de las fotos).
# Uso:   ./scripts/restaurar.sh backups/db_2026-12-01_0330.sql.gz [backups/media_2026-12-01_0330.tar.gz]
# ¡OJO! Reemplaza los datos actuales por los del respaldo.
set -e
cd "$(dirname "$0")/.."
. ./.env

DB_FILE="$1"
MEDIA_FILE="$2"
[ -f "$DB_FILE" ] || { echo "Indica el archivo de respaldo de la base de datos (.sql.gz)"; exit 1; }

printf "Esto REEMPLAZA la base de datos actual por %s. Escribe SI para continuar: " "$DB_FILE"
read -r OK
[ "$OK" = "SI" ] || { echo "Cancelado."; exit 1; }

docker compose stop web
docker compose exec -T db psql -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE IF EXISTS \"$POSTGRES_DB\";"
docker compose exec -T db psql -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE \"$POSTGRES_DB\" OWNER \"$POSTGRES_USER\";"
gunzip -c "$DB_FILE" | docker compose exec -T db psql -q -U "$POSTGRES_USER" -d "$POSTGRES_DB"

if [ -n "$MEDIA_FILE" ] && [ -f "$MEDIA_FILE" ]; then
  echo "Restaurando fotos..."
  docker compose start web
  docker compose exec -T web sh -c "rm -rf /data/media/* && tar -C /data -xzf -" < "$MEDIA_FILE"
fi

docker compose up -d
echo "Restauración terminada."
