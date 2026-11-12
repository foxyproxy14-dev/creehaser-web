"""
Crea la fundación y el evento de Navidad si todavía no existen.
Se puede ejecutar todas las veces que quieras: no duplica nada.

    python manage.py datos_iniciales
    python manage.py datos_iniciales --demo   # además, niños de ejemplo para probar
"""
import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from campana.models import Evento, Fundacion, Nino
from core.semillas_portal import cargar_portal

NINOS_DEMO = [
    ("Sofía", "nina", 6, 110, "dibujar y los unicornios", "Set de colores y cuaderno de dibujo"),
    ("Mateo", "nino", 8, 128, "el fútbol", "Balón de fútbol"),
    ("Valentina", "nina", 7, 121, "bailar y cantar", "Micrófono de juguete"),
    ("Santiago", "nino", 5, 107, "los dinosaurios", "Dinosaurios de juguete"),
    ("Isabella", "nina", 9, 131, "leer cuentos", "Libros de aventuras"),
    ("Nicolás", "nino", 7, 117, "el espacio", "Cohete de juguete"),
]


class Command(BaseCommand):
    help = "Crea la Fundación CreeHaSer y el evento Navidad 2026 (y niños de ejemplo con --demo)."

    def add_arguments(self, parser):
        parser.add_argument("--demo", action="store_true", help="Agregar niños de ejemplo (solo para pruebas).")

    @transaction.atomic
    def handle(self, *args, **opts):
        say = self.stdout.write if opts.get("verbosity", 1) > 0 else (lambda *_: None)
        fundacion, creada = Fundacion.objects.get_or_create(
            slug="creehaser",
            defaults=dict(
                nombre="Fundación CreeHaSer",
                lema="Creer y Hacer hacen el Ser",
                descripcion=(
                    "Hace más de 10 años nació un sueño: sembrar esperanza y transformar vidas. "
                    "Acompañamos a niños, jóvenes y familias en su crecimiento personal y espiritual."
                ),
                telefono="+57 314 644 0909",
                email="fundacioncreehaser@gmail.com",
                direccion="Calle 18B",
                ciudad="Valledupar, Cesar",
                latitud=Decimal("10.451128"),
                longitud=Decimal("-73.269424"),
                sitio_web="https://www.fundacioncreehaser.org/",
            ),
        )
        say(("Creada" if creada else "Ya existía") + f": {fundacion}")

        evento, creado = Evento.objects.get_or_create(
            fundacion=fundacion,
            slug="navidad-2026",
            defaults=dict(
                nombre="Un Regalo, Una Sonrisa · Navidad 2026",
                fecha_inicio=datetime.date(2026, 11, 15),
                fecha_fin=datetime.date(2026, 12, 20),
                monto_minimo=Decimal("30.00"),
                minutos_cancelacion=15,
                instrucciones_entrega="La fundación te contactará con los datos para el pago o la entrega del regalo.",
            ),
        )
        say(("Creado" if creado else "Ya existía") + f": {evento}")

        textos = dict(
            frase="Transformamos vidas desde el amor y la educación emocional",
            descripcion=(
                "Hace más de 10 años nació un sueño: sembrar esperanza y transformar vidas. Desde entonces, un grupo "
                "de profesionales y voluntarios ha trabajado con el corazón, convencidos de que dar es la forma más "
                "hermosa de recibir. Acompañamos a niños, jóvenes y familias en su crecimiento personal y espiritual, "
                "sembrando cada día semillas de amor y fe."
            ),
            adn_subtitulo="Apoyando a niños, jóvenes y familias en su crecimiento personal y espiritual.",
            mision=(
                "Impulsar el desarrollo humano, espiritual y socioemocional de niños, jóvenes y familias a través de "
                "programas educativos y comunitarios que fortalezcan la convivencia y el liderazgo con propósito."
            ),
            esencia=(
                "Somos una comunidad que une corazones, talentos y fe para fortalecer valores, promover la convivencia "
                "y oportunidades de desarrollo. Creemos en la educación, la espiritualidad y el coaching como caminos "
                "para construir paz desde el amor."
            ),
            vision=(
                "Ser reconocidos en Latinoamérica como una institución líder en educación emocional y formación en "
                "valores, generando transformaciones sostenibles en la sociedad."
            ),
        )
        # Rellena solo lo que esté vacío (o el texto corto de la primera versión): nunca pisa lo editado en el panel
        TEXTO_CORTO_V1 = "Hace más de 10 años nació un sueño: sembrar esperanza y transformar vidas. Acompañamos"
        cambiados = [k for k in textos if not getattr(fundacion, k)
                     or (k == "descripcion" and fundacion.descripcion.startswith(TEXTO_CORTO_V1))]
        for k in cambiados:
            setattr(fundacion, k, textos[k])
        if cambiados:
            fundacion.save()

        for linea in cargar_portal(fundacion):
            say(linea)

        if opts["demo"]:
            n = 0
            for nombre, sexo, edad, cm, gustos, regalo in NINOS_DEMO:
                _, c = Nino.objects.get_or_create(
                    evento=evento, nombre=nombre,
                    defaults=dict(sexo=sexo, edad=edad, estatura_cm=cm, gustos=gustos, regalo_deseado=regalo),
                )
                n += c
            say(f"Niños de ejemplo agregados: {n}")
