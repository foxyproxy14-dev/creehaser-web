# Despliegue en la VM

Guía para levantar CreeHaSer Web con Docker detrás de tu proxy inverso.

## Requisitos

- VM con Debian 12 / Ubuntu 24.04, Docker + Docker Compose y Git.
- Un dominio o subdominio apuntando a tu proxy inverso.

## 1. Clonar el repositorio

```bash
cd /opt/creehaser
git clone https://github.com/foxyproxy14-dev/creehaser-web.git .
```

> El repositorio es privado: GitHub te pedirá usuario y un *token* personal
> (Settings → Developer settings → Personal access tokens) en lugar de la contraseña.

## 2. Configurar el `.env`

```bash
cp .env.example .env
openssl rand -base64 48   # copia el resultado en DJANGO_SECRET_KEY
openssl rand -base64 24   # copia el resultado en POSTGRES_PASSWORD
nano .env
```

Ajusta como mínimo:

| Variable | Qué poner |
|---|---|
| `DJANGO_SECRET_KEY` | La clave larga generada |
| `POSTGRES_PASSWORD` | La contraseña generada |
| `DJANGO_ALLOWED_HOSTS` | Tu dominio y la IP de la VM, separados por coma |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://tu-dominio` |
| `HTTP_PORT` | Puerto al que apuntará tu proxy (por defecto `8080`) |

> ¿Vas a probar primero por `http://IP:8080` sin HTTPS? Pon temporalmente
> `DJANGO_SECURE_COOKIES=false` y agrega `http://IP:8080` a `DJANGO_CSRF_TRUSTED_ORIGINS`.
> Vuelve a `true` cuando ya entres por el dominio con HTTPS.

## 3. Levantar

```bash
docker compose up -d --build
docker compose ps          # los 3 servicios deben estar "running" / "healthy"
docker compose logs -f web # ver que migró sin errores (Ctrl+C para salir)
```

Al arrancar, la app crea sola las tablas y la Fundación CreeHaSer con el evento Navidad 2026.

## 4. Crear tu usuario administrador

```bash
docker compose exec web python manage.py createsuperuser
```

Entra en `https://tu-dominio/admin/` con ese correo y contraseña.

Para cargar niños de ejemplo y probar (bórralos antes de la campaña real):

```bash
docker compose exec web python manage.py datos_iniciales --demo
```

## 5. Proxy inverso

Apunta tu dominio a `http://IP-DE-LA-VM:8080` y asegúrate de que el proxy envíe
estas cabeceras (Nginx Proxy Manager y Caddy ya lo hacen por defecto):

```nginx
proxy_set_header Host              $host;
proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
client_max_body_size 12M;
```

Comprobación de salud: `https://tu-dominio/salud/` debe responder `{"estado": "ok"}`.

## 6. Respaldos

```bash
./scripts/respaldo.sh                 # respaldo manual (base de datos + fotos) en backups/
crontab -e                            # respaldo diario a las 3:30 am:
30 3 * * * cd /opt/creehaser && ./scripts/respaldo.sh >> backups/respaldo.log 2>&1
```

Restaurar: `./scripts/restaurar.sh backups/db_FECHA.sql.gz backups/media_FECHA.tar.gz`

Copia de vez en cuando la carpeta `backups/` fuera de la VM.

## 7. Actualizar a una versión nueva

```bash
cd /opt/creehaser
./scripts/respaldo.sh
git pull
docker compose up -d --build
```

## Comandos útiles

| Para… | Comando |
|---|---|
| Ver estado | `docker compose ps` |
| Ver registros | `docker compose logs -f web` |
| Reiniciar | `docker compose restart web` |
| Apagar | `docker compose down` (los datos se conservan) |
| Consola de Django | `docker compose exec web python manage.py shell` |
| Entrar a la base de datos | `docker compose exec db psql -U creehaser creehaser` |

> ⚠️ Nunca uses `docker compose down -v`: la `-v` borra los volúmenes con la base de datos y las fotos.
