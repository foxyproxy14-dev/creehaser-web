from django.contrib import admin
from django.utils.html import format_html

from .models import CambioRegalo, Evento, Fundacion, Nino


@admin.register(Fundacion)
class FundacionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "ciudad", "telefono", "email", "activa")
    prepopulated_fields = {"slug": ("nombre",)}
    search_fields = ("nombre",)


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "fundacion", "tipo", "fecha_inicio", "fecha_fin", "monto_minimo", "activo")
    list_filter = ("fundacion", "tipo", "activo")
    prepopulated_fields = {"slug": ("nombre",)}


class CambioRegaloInline(admin.TabularInline):
    model = CambioRegalo
    extra = 0
    can_delete = False
    readonly_fields = ("creado", "padrino", "regalo_anterior", "regalo_nuevo", "motivo")
    fields = readonly_fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Nino)
class NinoAdmin(admin.ModelAdmin):
    list_display = ("miniatura", "nombre", "sexo", "edad", "estatura_cm", "estado", "padrino", "regalo_padrino", "asignado_en")
    list_display_links = ("miniatura", "nombre")
    list_filter = ("evento", "estado", "sexo")
    search_fields = ("nombre", "padrino__email", "padrino__first_name", "padrino__last_name", "regalo_padrino")
    autocomplete_fields = ("padrino",)
    readonly_fields = ("asignado_en", "creado", "actualizado", "vista_foto")
    inlines = [CambioRegaloInline]
    fieldsets = (
        ("Perfil del niño", {"fields": ("evento", "nombre", "sexo", "edad", "estatura_cm", "gustos", "regalo_deseado", "foto", "vista_foto")}),
        ("Apadrinamiento", {"fields": ("estado", "padrino", "asignado_en", "regalo_padrino", "mensaje_padrino")}),
        ("Gestión interna", {"fields": ("nota_interna", "foto_entrega", "creado", "actualizado")}),
    )

    @admin.display(description="")
    def miniatura(self, obj):
        if obj.foto:
            return format_html('<img src="{}" style="width:36px;height:36px;border-radius:50%;object-fit:cover">', obj.foto.url)
        return "—"

    @admin.display(description="vista previa")
    def vista_foto(self, obj):
        if obj.foto:
            return format_html('<img src="{}" style="max-width:220px;border-radius:12px">', obj.foto.url)
        return "Sin foto"


@admin.register(CambioRegalo)
class CambioRegaloAdmin(admin.ModelAdmin):
    list_display = ("creado", "nino", "padrino", "regalo_anterior", "regalo_nuevo", "motivo")
    list_filter = ("nino__evento",)
    search_fields = ("nino__nombre", "regalo_nuevo", "padrino__email")
    readonly_fields = ("creado",)
