#!/bin/sh
# Prepara la app cada vez que arranca el contenedor:
# espera a la base de datos, aplica migraciones y recopila los archivos estáticos.
set -e

echo "Esperando a la base de datos..."
python - <<'PY'
import os, sys, time
import psycopg
for i in range(60):
    try:
        psycopg.connect(
            dbname=os.environ["POSTGRES_DB"], user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"], host=os.environ.get("POSTGRES_HOST", "db"),
            port=os.environ.get("POSTGRES_PORT", "5432"), connect_timeout=3,
        ).close()
        sys.exit(0)
    except Exception as e:
        print(f"  aún no responde ({e.__class__.__name__}), reintentando...")
        time.sleep(2)
print("La base de datos no respondió a tiempo.")
sys.exit(1)
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput --verbosity 0
python manage.py datos_iniciales

exec "$@"
