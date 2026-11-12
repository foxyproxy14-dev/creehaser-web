from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UsuarioManager(BaseUserManager):
    """Los usuarios inician sesión con su correo (no con nombre de usuario)."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("El correo es obligatorio.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("es_organizador", True)
        if not extra.get("is_staff") or not extra.get("is_superuser"):
            raise ValueError("El superusuario debe tener is_staff e is_superuser.")
        return self._create_user(email, password, **extra)


class Usuario(AbstractUser):
    """
    Cuenta de la plataforma.
    - Padrinos: se registran desde la web.
    - Organizadores: personal de una fundación, con acceso al panel.
    """

    username = None
    email = models.EmailField("correo", unique=True)
    telefono = models.CharField("teléfono / WhatsApp", max_length=30, blank=True)
    es_organizador = models.BooleanField(
        "organizador",
        default=False,
        help_text="Puede entrar al panel de la fundación.",
    )
    fundacion = models.ForeignKey(
        "campana.Fundacion",
        verbose_name="fundación",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="organizadores",
        help_text="Solo para organizadores: fundación a la que pertenece.",
    )
    acepto_datos_en = models.DateTimeField(
        "autorizó tratamiento de datos",
        null=True,
        blank=True,
        help_text="Fecha en que aceptó la política de datos (Ley 1581 de 2012).",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UsuarioManager()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        nombre = self.get_full_name()
        return f"{nombre} <{self.email}>" if nombre else self.email
