# CreeHaSer Web

Web de la **Fundación CreeHaSer** (Valledupar, Colombia) y su campaña navideña
**"Un Regalo, Una Sonrisa"**: un árbol de regalos donde cada regalo representa a un
niño o niña; los padrinos eligen regalos, se les asignan niños al azar y la
fundación gestiona todo desde su panel.

## Estado

| Parte | Estado |
|---|---|
| Prototipo visual (`prototipo/`) | ✅ Validado con la fundación |
| Parte 1 · Base: Django, PostgreSQL, Docker, modelos y admin | ✅ |
| Parte 2 · Portal de la fundación (contenido editable) | ✅ |
| Parte 3 · Árbol, cuentas y panel de padrino | ⏳ |
| Parte 4 · Panel de organizadores, Telegram y correos | ⏳ |

### Prototipo
`prototipo/index.html` es la maqueta funcional (solo navegador, datos de ejemplo).
Sirve como referencia de diseño y comportamiento para la versión real.
Ábrelo directamente en el navegador.

## Puesta en marcha

Ver **[docs/DESPLIEGUE.md](docs/DESPLIEGUE.md)**. En resumen:

```bash
cp .env.example .env   # y rellenarlo
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
```

## Editar el contenido del portal

Todo se cambia desde `/admin/`, sin tocar código:

| Quiero cambiar… | Dónde |
|---|---|
| Títulos y texto de la portada, foto de «Quiénes somos», decoración navideña | Portal → Configuración del sitio |
| Historia, frase, misión, esencia, visión, dirección, horario, teléfono, ubicación del mapa | Campaña → Fundaciones |
| Tarjetas de «Experiencias» | Portal → Experiencias |
| Sección «Eventos» (banner, botón, carrusel de fotos) | Portal → Eventos destacados |
| Fotos de la galería | Portal → Galería |
| Logos de aliados y su enlace | Portal → Aliados |

Cada lista tiene columnas **orden** y **visible** para reordenar u ocultar sin borrar.
Una sección sin contenido visible desaparece sola de la página y del menú.

## Estructura

```
config/      configuración de Django
cuentas/     usuarios (padrinos y organizadores, inicio de sesión con correo)
campana/     fundaciones, eventos, niños e historial de regalos
core/        portal público
nginx/       servidor web delante de Django
scripts/     arranque, respaldo y restauración
prototipo/   maqueta validada (referencia de diseño)
```

## Desarrollo local (sin Docker)

```bash
pip install -r requirements.txt
DJANGO_DEBUG=true python manage.py migrate
DJANGO_DEBUG=true python manage.py datos_iniciales --demo
DJANGO_DEBUG=true python manage.py test
```
Sin variables `POSTGRES_*` usa SQLite.

## Funcionalidades (versión real)

- **Portal de la fundación**: historia, ADN (misión, esencia, visión), experiencias,
  eventos (Human Skills Latam), galería, aliados y contacto con mapa.
- **Árbol de regalos**: registro obligatorio, selección de varios regalos,
  asignación aleatoria de niños y vista previa al confirmar.
- **Panel del padrino**: niños asignados, qué quiere cada uno, regalo que entregará
  (editable, con historial), mensaje para el niño, estado, foto de entrega y certificado.
- **Panel de organizadores**: gestión de niños (con foto), regalos de padrinos con
  historial de cambios, padrinos registrados, estados, exportación y ajustes.
- **Notificaciones** por Telegram a los organizadores.
- **Decoración navideña automática** por fechas (configurable).
- Preparado para **varias fundaciones y eventos** a futuro.

## Stack

- Python 3 + Django
- PostgreSQL
- Docker Compose (despliegue en LXC detrás de proxy inverso)
- Bot de Telegram y SMTP para notificaciones

## Seguridad y privacidad

- `.env` con secretos **nunca** se sube al repositorio (ver `.env.example`).
- Fotos y datos de los niños y padrinos viven en la base de datos y en `media/`
  del servidor, **nunca** en Git.
- Ley 1098 de 2006 (infancia y adolescencia) y Ley 1581 de 2012 (protección de datos).
