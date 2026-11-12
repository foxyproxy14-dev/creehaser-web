from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    ordering = ("-date_joined",)
    list_display = ("email", "first_name", "last_name", "telefono", "es_organizador", "fundacion", "date_joined")
    list_filter = ("es_organizador", "fundacion", "is_staff", "is_active")
    search_fields = ("email", "first_name", "last_name", "telefono")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Datos personales", {"fields": ("first_name", "last_name", "telefono", "acepto_datos_en")}),
        ("Fundación", {"fields": ("es_organizador", "fundacion")}),
        ("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "telefono", "password1", "password2", "es_organizador", "fundacion"),
        }),
    )
