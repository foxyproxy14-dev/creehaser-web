"""
Modelos de la campaña.

Fundacion ─┬─ Evento ── Nino ── CambioRegalo
           └─ (organizadores: cuentas.Usuario)

Pensado desde el principio para varias fundaciones y varios eventos,
aunque por ahora solo exista "Fundación CreeHaSer · Navidad 2026".
"""
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from .imagenes import optimizar_imagen


def ruta_foto_nino(instance, filename):
    return f"ninos/{instance.evento_id or 'sin-evento'}/{uuid.uuid4().hex}.jpg"


def ruta_foto_entrega(instance, filename):
    return f"entregas/{instance.evento_id or 'sin-evento'}/{uuid.uuid4().hex}.jpg"


def ruta_logo(instance, filename):
    return f"fundaciones/{uuid.uuid4().hex}.png"


class Fundacion(models.Model):
    nombre = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    lema = models.CharField(max_length=200, blank=True)
    descripcion = models.TextField("descripción / historia", blank=True)
    telefono = models.CharField("teléfono", max_length=30, blank=True)
    email = models.EmailField("correo", blank=True)
    direccion = models.CharField("dirección", max_length=200, blank=True)
    ciudad = models.CharField(max_length=80, blank=True)
    horario = models.CharField("horario de atención", max_length=120, blank=True)
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    sitio_web = models.URLField(blank=True)
    logo = models.ImageField(upload_to=ruta_logo, blank=True)
    activa = models.BooleanField(default=True)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "fundación"
        verbose_name_plural = "fundaciones"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Evento(models.Model):
    class Tipo(models.TextChoices):
        ARBOL_REGALOS = "arbol_regalos", "Árbol de regalos"

    fundacion = models.ForeignKey(Fundacion, verbose_name="fundación", on_delete=models.CASCADE, related_name="eventos")
    nombre = models.CharField(max_length=120)
    slug = models.SlugField()
    tipo = models.CharField(max_length=30, choices=Tipo.choices, default=Tipo.ARBOL_REGALOS)
    descripcion = models.TextField("descripción", blank=True)
    fecha_inicio = models.DateField("inicio", null=True, blank=True)
    fecha_fin = models.DateField("fin", null=True, blank=True)
    monto_minimo = models.DecimalField(
        "monto mínimo por regalo (USD)", max_digits=8, decimal_places=2, default=Decimal("30.00"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    minutos_cancelacion = models.PositiveIntegerField(
        "minutos para que el padrino pueda cancelar", default=15,
    )
    instrucciones_entrega = models.TextField(
        "instrucciones de pago / entrega", blank=True,
        help_text="Se muestran al padrino cuando se le asignan niños.",
    )
    activo = models.BooleanField(default=True, help_text="Si está activo, el árbol acepta padrinos.")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "evento"
        verbose_name_plural = "eventos"
        ordering = ["-creado"]
        constraints = [
            models.UniqueConstraint(fields=["fundacion", "slug"], name="evento_slug_unico_por_fundacion"),
        ]

    def __str__(self):
        return f"{self.nombre} · {self.fundacion}"


class Nino(models.Model):
    class Sexo(models.TextChoices):
        NINA = "nina", "Niña"
        NINO = "nino", "Niño"

    class Estado(models.TextChoices):
        DISPONIBLE = "disponible", "Disponible"
        ASIGNADO = "asignado", "Asignado"
        RECIBIDO = "recibido", "Regalo recibido"
        ENTREGADO = "entregado", "Entregado"
        AGRADECIDO = "agradecido", "Agradecimiento enviado"

    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name="ninos")

    # Perfil (lo carga la fundación)
    nombre = models.CharField("primer nombre o alias", max_length=40)
    sexo = models.CharField(max_length=4, choices=Sexo.choices)
    edad = models.PositiveSmallIntegerField(validators=[MaxValueValidator(17)])
    estatura_cm = models.PositiveSmallIntegerField(
        "estatura (cm)", null=True, blank=True, validators=[MinValueValidator(40), MaxValueValidator(220)],
    )
    gustos = models.CharField("qué le gusta", max_length=150, blank=True)
    regalo_deseado = models.CharField("regalo que le gustaría", max_length=150, blank=True)
    foto = models.ImageField(upload_to=ruta_foto_nino, blank=True)

    # Apadrinamiento
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.DISPONIBLE, db_index=True)
    padrino = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="ninos_apadrinados",
    )
    asignado_en = models.DateTimeField("asignado el", null=True, blank=True)
    mensaje_padrino = models.TextField("mensaje del padrino para el niño", blank=True, max_length=600)
    regalo_padrino = models.CharField(
        "regalo que entregará el padrino", max_length=150, blank=True,
        help_text="Lo indica el padrino; puede ser distinto a lo que pidió el niño.",
    )

    # Gestión interna de la fundación
    nota_interna = models.TextField(blank=True)
    foto_entrega = models.ImageField(
        "foto de la entrega", upload_to=ruta_foto_entrega, blank=True,
        help_text="Sin rostro o con el rostro difuminado.",
    )

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "niño"
        verbose_name_plural = "niños"
        ordering = ["nombre"]
        indexes = [models.Index(fields=["evento", "estado"])]

    def __str__(self):
        return f"{self.nombre} ({self.edad} años)"

    @property
    def estatura_m(self):
        return f"{self.estatura_cm / 100:.2f}".replace(".", ",") + " m" if self.estatura_cm else ""

    def puede_cancelar(self, ahora=None):
        """El padrino puede cancelar durante los primeros minutos tras la asignación."""
        if self.estado != self.Estado.ASIGNADO or not self.asignado_en:
            return False
        ahora = ahora or timezone.now()
        return (ahora - self.asignado_en).total_seconds() < self.evento.minutos_cancelacion * 60

    def liberar(self):
        """Devuelve el niño al árbol (cancelación del padrino o decisión de la fundación)."""
        self.estado = self.Estado.DISPONIBLE
        self.padrino = None
        self.asignado_en = None
        self.mensaje_padrino = ""
        self.regalo_padrino = ""
        self.foto_entrega = None

    def save(self, *args, **kwargs):
        if self.foto and not getattr(self.foto, "_committed", True):
            optimizar_imagen(self.foto, lado_max=900)
        if self.foto_entrega and not getattr(self.foto_entrega, "_committed", True):
            optimizar_imagen(self.foto_entrega, lado_max=1400)
        super().save(*args, **kwargs)


class CambioRegalo(models.Model):
    """Historial de lo que el padrino dice que va a regalar (primera elección y cambios)."""

    nino = models.ForeignKey(Nino, verbose_name="niño", on_delete=models.CASCADE, related_name="cambios_regalo")
    padrino = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    regalo_anterior = models.CharField(max_length=150, blank=True)
    regalo_nuevo = models.CharField(max_length=150)
    motivo = models.CharField(max_length=200, blank=True)
    creado = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "cambio de regalo"
        verbose_name_plural = "historial de regalos"
        ordering = ["creado"]

    def __str__(self):
        return f"{self.nino}: {self.regalo_anterior or '—'} → {self.regalo_nuevo}"
