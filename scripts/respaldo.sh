#!/bin/sh
# Respaldo de la base de datos y de las fotos subidas.
# Uso (desde la carpeta del proyecto):   ./scripts/respaldo.sh
# Para respaldo diario automático, agrega a crontab -e:
#   30 3 * * * cd /opt/creehaser && ./scripts/respaldo.sh >> backups/respaldo.log 2>&1
set -e
cd "$(dirname "$0")/.."
. ./.env

DESTINO="backups"
FECHA=$(date +%Y-%m-%d_%H%M)
DIAS_A_GUARDAR=${DIAS_A_GUARDAR:-14}
mkdir -p "$DESTINO"

echo "[$FECHA] Respaldando base de datos..."
docker compose exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner | gzip > "$DESTINO/db_$FECHA.sql.gz"

echo "[$FECHA] Respaldando fotos..."
docker compose exec -T web tar -C /data -czf - media > "$DESTINO/media_$FECHA.tar.gz"

echo "[$FECHA] Borrando respaldos de más de $DIAS_A_GUARDAR días..."
find "$DESTINO" -name "db_*.sql.gz" -mtime +"$DIAS_A_GUARDAR" -delete
find "$DESTINO" -name "media_*.tar.gz" -mtime +"$DIAS_A_GUARDAR" -delete

echo "[$FECHA] Listo:"
ls -lh "$DESTINO" | tail -n 4
