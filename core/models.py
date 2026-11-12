"""
Contenido editable del portal (lo que ve la gente al entrar a la web).
Todo se cambia desde /admin/ → Portal, sin tocar código.
"""
import uuid

from django.db import models

from campana.imagenes import optimizar_imagen


def ruta_galeria(instance, filename):
    return f"portal/galeria/{uuid.uuid4().hex}.jpg"


def ruta_evento(instance, filename):
    return f"portal/eventos/{uuid.uuid4().hex}.jpg"


def ruta_aliado(instance, filename):
    return f"portal/aliados/{uuid.uuid4().hex}.jpg"


def ruta_portada(instance, filename):
    return f"portal/portada/{uuid.uuid4().hex}.jpg"


class ImagenOptimizadaMixin:
    """Optimiza los campos de imagen indicados al guardar (tamaño máximo en píxeles)."""

    campos_imagen = {}

    def save(self, *args, **kwargs):
        for nombre, lado in self.campos_imagen.items():
            f = getattr(self, nombre)
            if f and not getattr(f, "_committed", True):
                optimizar_imagen(f, lado_max=lado)
        super().save(*args, **kwargs)


class ConfiguracionSitio(ImagenOptimizadaMixin, models.Model):
    """Ajustes generales del portal. Solo existe un registro."""

    class Deco(models.TextChoices):
        AUTO = "auto", "Automática por fechas"
        SIEMPRE = "on", "Siempre activa"
        NUNCA = "off", "Desactivada"

    # Portada (campaña)
    portada_etiqueta = models.CharField("etiqueta superior", max_length=60, default="🎄 NAVIDAD CREEHASER 2026")
    portada_titulo_1 = models.CharField("título (línea 1)", max_length=60, default="Un Regalo,")
    portada_titulo_2 = models.CharField("título (línea 2, en rojo)", max_length=60, default="Una Sonrisa")
    portada_texto = models.TextField(
        "texto de portada",
        default="Cada regalo de nuestro árbol guarda a un niño o niña que espera la Navidad. "
                "Elige los que quieras, conoce a quién le tocó tu regalo y regálale una sonrisa este diciembre.",
    )

    # Quiénes somos
    foto_quienes_somos = models.ImageField("foto de «Quiénes somos»", upload_to=ruta_portada, blank=True)
    foto_quienes_somos_texto = models.CharField("texto sobre la foto", max_length=80, blank=True,
                                                default="Celebrando la Navidad en comunidad")
    texto_gratitud = models.TextField(
        "texto sobre la campaña (debajo de la historia)", blank=True,
        default="Con esta campaña también enseñamos a nuestros niños el valor de la gratitud: cada regalo llega "
                "acompañado del mensaje de su padrino, y ellos elevan una oración por quien pensó en ellos.",
    )

    # Decoración navideña
    decoracion = models.CharField("decoración navideña", max_length=4, choices=Deco.choices, default=Deco.AUTO)
    decoracion_desde = models.CharField("desde (día/mes)", max_length=5, default="01/11",
                                        help_text="Formato DD/MM, por ejemplo 01/11")
    decoracion_hasta = models.CharField("hasta (día/mes)", max_length=5, default="06/01",
                                        help_text="Formato DD/MM, por ejemplo 06/01")

    campos_imagen = {"foto_quienes_somos": 1400}

    class Meta:
        verbose_name = "configuración del sitio"
        verbose_name_plural = "configuración del sitio"

    def __str__(self):
        return "Configuración del sitio"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def actual(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Ordenable(models.Model):
    orden = models.PositiveSmallIntegerField(default=0, help_text="Menor número = aparece primero.")
    activo = models.BooleanField("visible", default=True)

    class Meta:
        abstract = True
        ordering = ["orden", "id"]


class Experiencia(Ordenable):
    fundacion = models.ForeignKey("campana.Fundacion", on_delete=models.CASCADE, related_name="experiencias")
    icono = models.CharField("ícono (emoji)", max_length=8, default="💚")
    titulo = models.CharField("título", max_length=80)
    descripcion = models.TextField("descripción", max_length=400)

    class Meta(Ordenable.Meta):
        verbose_name = "experiencia"
        verbose_name_plural = "experiencias"

    def __str__(self):
        return self.titulo


class EventoDestacado(ImagenOptimizadaMixin, Ordenable):
    """Eventos de la sección «Eventos» (por ejemplo, Human Skills Latam)."""

    fundacion = models.ForeignKey("campana.Fundacion", on_delete=models.CASCADE, related_name="eventos_destacados")
    nombre = models.CharField(max_length=100, help_text="Nombre interno, por ejemplo «Human Skills Latam 2026».")
    banner = models.ImageField(upload_to=ruta_evento, blank=True)
    antetitulo = models.CharField(max_length=80, blank=True, default="¡El futuro es hoy!")
    titulo = models.CharField("título", max_length=100)
    descripcion = models.TextField("descripción", blank=True)
    boton_texto = models.CharField("texto del botón", max_length=40, blank=True, default="¡INSCRÍBETE AQUÍ!")
    boton_url = models.URLField("enlace del botón", blank=True)
    titulo_carrusel = models.CharField(
        "título del carrusel", max_length=100, blank=True,
        help_text="Por ejemplo «Jóvenes que nos acompañan este 2026». Vacío = sin título.",
    )

    campos_imagen = {"banner": 1400}

    class Meta(Ordenable.Meta):
        verbose_name = "evento destacado"
        verbose_name_plural = "eventos destacados"

    def __str__(self):
        return self.nombre


class FotoEventoDestacado(ImagenOptimizadaMixin, models.Model):
    evento = models.ForeignKey(EventoDestacado, on_delete=models.CASCADE, related_name="fotos")
    imagen = models.ImageField(upload_to=ruta_evento)
    descripcion = models.CharField("descripción", max_length=120, blank=True)
    orden = models.PositiveSmallIntegerField(default=0)

    campos_imagen = {"imagen": 900}

    class Meta:
        verbose_name = "foto del carrusel"
        verbose_name_plural = "fotos del carrusel"
        ordering = ["orden", "id"]

    def __str__(self):
        return self.descripcion or f"Foto {self.pk}"


class FotoGaleria(ImagenOptimizadaMixin, Ordenable):
    fundacion = models.ForeignKey("campana.Fundacion", on_delete=models.CASCADE, related_name="galeria")
    imagen = models.ImageField(upload_to=ruta_galeria)
    titulo = models.CharField("texto sobre la foto", max_length=80, blank=True)

    campos_imagen = {"imagen": 1400}

    class Meta(Ordenable.Meta):
        verbose_name = "foto de la galería"
        verbose_name_plural = "galería"

    def __str__(self):
        return self.titulo or f"Foto {self.pk}"


class Aliado(ImagenOptimizadaMixin, Ordenable):
    fundacion = models.ForeignKey("campana.Fundacion", on_delete=models.CASCADE, related_name="aliados")
    nombre = models.CharField(max_length=100)
    logo = models.ImageField(upload_to=ruta_aliado)
    sitio_web = models.URLField("sitio web", blank=True, help_text="Si lo pones, el logo será un enlace.")

    campos_imagen = {"logo": 500}

    class Meta(Ordenable.Meta):
        verbose_name = "aliado"
        verbose_name_plural = "aliados"

    def __str__(self):
        return self.nombre
