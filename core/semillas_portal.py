"""
Contenido inicial del portal (textos y fotos de la web actual de la fundación).
Cada bloque se carga solo si todavía está vacío: lo que la fundación edite en el panel nunca se pisa.
"""
from pathlib import Path

from django.core.files import File

from .models import Aliado, ConfiguracionSitio, EventoDestacado, Experiencia, FotoEventoDestacado, FotoGaleria

SEMILLAS = Path(__file__).resolve().parent / "semillas"

EXPERIENCIAS = [
    ("🚀", "Softskills Latam", "Jóvenes de distintos países fortalecen su liderazgo, propósito, toma de decisiones y "
                               "pensamiento crítico. Juntos somos red, somos cambio."),
    ("🤝", "Inspirados para Inspirar", "Encuentros donde jóvenes latinoamericanos descubren el poder del trabajo en "
                                       "equipo y la ciudadanía."),
    ("📻", "Brillando con Valores Radio", "Los niños aprenden y comparten valores con historias, música y alegría, "
                                          "descubriendo que brillar es vivir con amor y propósito."),
    ("💚", "Acompañando la Vida", "Haz un aporte y acompáñanos a sembrar esperanza en quienes más lo necesitan."),
]

GALERIA = [
    ("radio.jpg", "Brillando con Valores en la radio"),
    ("emisora.jpg", "Visita a la emisora"),
    ("visita.jpg", "Acompañando a nuestros abuelos"),
    ("abuelos.jpg", "Acompañando la Vida"),
]

ALIADOS = [
    ("dl-soluciones.jpg", "D&L Soluciones Integrales, C.A.", "https://dlsolucionesintegrales.com/"),
    ("academia-verde-innova.jpg", "Academia Verde Innova", ""),
    ("banco-alimentos-valledupar.jpg", "Banco de Alimentos de Valledupar", ""),
    ("pastoral-social-valledupar.jpg", "Secretariado de Pastoral Social de Valledupar", ""),
    ("unisal.jpg", "Universidad San Lorenzo (UNISAL)", ""),
    ("rlc.jpg", "RLC", ""),
    ("human-ecology.jpg", "Human Ecology", ""),
    ("global-coaching.jpg", "Global Coaching Federation", ""),
    ("idc-community.jpg", "IDC Community", ""),
    ("emotions-labs.jpg", "Emotions Labs", ""),
    ("latinas-en-expansion.jpg", "Latinas en Expansión", ""),
    ("talita-cumi.jpg", "Talita Cumi", ""),
    ("susser-kakao.jpg", "Süßer Kakao", ""),
    ("taller-de-nazaret.jpg", "Taller de Nazaret", ""),
    ("cli.jpg", "CLI", ""),
]


def _archivo(ruta):
    return File(open(SEMILLAS / ruta, "rb"), name=Path(ruta).name)


def cargar_portal(fundacion):
    hecho = []

    config = ConfiguracionSitio.actual()
    if not config.foto_quienes_somos and (SEMILLAS / "navidad.jpg").exists():
        with _archivo("navidad.jpg") as f:
            config.foto_quienes_somos.save("navidad.jpg", f, save=True)
        hecho.append("Portal: foto de «Quiénes somos» cargada")

    if not fundacion.experiencias.exists():
        for i, (icono, titulo, desc) in enumerate(EXPERIENCIAS):
            Experiencia.objects.create(fundacion=fundacion, icono=icono, titulo=titulo, descripcion=desc, orden=i)
        hecho.append(f"Portal: {len(EXPERIENCIAS)} experiencias")

    if not fundacion.eventos_destacados.exists():
        ev = EventoDestacado(
            fundacion=fundacion, nombre="Human Skills Latam 2026", antetitulo="¡El futuro es hoy!",
            titulo="Inspira • Lidera\nTransforma",
            descripcion="IV Encuentro Latinoamericano de Jóvenes Universitarios: competencias humanas para liderar el futuro.",
            boton_texto="¡INSCRÍBETE AQUÍ!",
            boton_url="https://docs.google.com/forms/d/e/1FAIpQLSeeDlZ37mdRcsjlO-7Onot23WvsW9upxSXD-cw1e9GSh6E29Q/viewform",
            titulo_carrusel="Jóvenes que nos acompañan este 2026",
        )
        with _archivo("humanskills.jpg") as f:
            ev.banner.save("humanskills.jpg", f, save=False)
        ev.save()
        fotos = sorted((SEMILLAS / "jovenes").glob("*.jpg"))
        for i, ruta in enumerate(fotos):
            foto = FotoEventoDestacado(evento=ev, descripcion="Ponente universitario de Human Skills Latam 2026", orden=i)
            with _archivo(f"jovenes/{ruta.name}") as f:
                foto.imagen.save(ruta.name, f, save=True)
        hecho.append(f"Portal: evento Human Skills Latam 2026 con {len(fotos)} fotos")

    if not fundacion.galeria.exists():
        for i, (archivo, titulo) in enumerate(GALERIA):
            foto = FotoGaleria(fundacion=fundacion, titulo=titulo, orden=i)
            with _archivo(archivo) as f:
                foto.imagen.save(archivo, f, save=True)
        hecho.append(f"Portal: {len(GALERIA)} fotos de galería")

    if not fundacion.aliados.exists():
        for i, (archivo, nombre, web) in enumerate(ALIADOS):
            aliado = Aliado(fundacion=fundacion, nombre=nombre, sitio_web=web, orden=i)
            with _archivo(f"aliados/{archivo}") as f:
                aliado.logo.save(archivo, f, save=True)
        hecho.append(f"Portal: {len(ALIADOS)} aliados")

    return hecho
