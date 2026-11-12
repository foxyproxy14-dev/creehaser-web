# CreeHaSer Web

Web de la **Fundación CreeHaSer** (Valledupar, Colombia) y su campaña navideña
**"Un Regalo, Una Sonrisa"**: un árbol de regalos donde cada regalo representa a un
niño o niña; los padrinos eligen regalos, se les asignan niños al azar y la
fundación gestiona todo desde su panel.

## Estado

| Parte | Estado |
|---|---|
| Prototipo visual (`prototipo/`) | ✅ Validado con la fundación |
| Versión real (Django + PostgreSQL) | 🚧 En construcción |

### Prototipo
`prototipo/index.html` es la maqueta funcional (solo navegador, datos de ejemplo).
Sirve como referencia de diseño y comportamiento para la versión real.
Ábrelo directamente en el navegador.

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
