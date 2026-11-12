from django.contrib import admin
from django.utils.html import format_html

from .models import Aliado, ConfiguracionSitio, EventoDestacado, Experiencia, FotoEventoDestacado, FotoGaleria


def miniatura(campo, alto=48, redonda=False):
    @admin.display(description="")
    def _m(self, obj):
        f = getattr(obj, campo)
        if not f:
            return "—"
        radio = "50%" if redonda else "8px"
        return format_html('<img src="{}" style="height:{}px;max-width:120px;object-fit:contain;border-radius:{}">', f.url, alto, radio)
    return _m


@admin.register(ConfiguracionSitio)
class ConfiguracionSitioAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Portada", {"fields": ("portada_etiqueta", "portada_titulo_1", "portada_titulo_2", "portada_texto")}),
        ("Quiénes somos", {"fields": ("foto_quienes_somos", "foto_quienes_somos_texto", "texto_gratitud")}),
        ("Decoración navideña", {
            "fields": ("decoracion", "decoracion_desde", "decoracion_hasta"),
            "description": "Luces, nieve, adornos, el Nacimiento junto al logo y la animación de bienvenida.",
        }),
    )

    def has_add_permission(self, request):
        return not ConfiguracionSitio.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Experiencia)
class ExperienciaAdmin(admin.ModelAdmin):
    list_display = ("icono", "titulo", "fundacion", "orden", "activo")
    list_display_links = ("icono", "titulo")
    list_editable = ("orden", "activo")
    list_filter = ("fundacion", "activo")


class FotoEventoInline(admin.TabularInline):
    model = FotoEventoDestacado
    extra = 3
    fields = ("vista", "imagen", "descripcion", "orden")
    readonly_fields = ("vista",)
    vista = miniatura("imagen", 70)


@admin.register(EventoDestacado)
class EventoDestacadoAdmin(admin.ModelAdmin):
    list_display = ("vista", "nombre", "fundacion", "orden", "activo")
    list_display_links = ("vista", "nombre")
    list_editable = ("orden", "activo")
    inlines = [FotoEventoInline]
    vista = miniatura("banner")
    fields = ("fundacion", "nombre", "banner", "antetitulo", "titulo", "descripcion",
              "boton_texto", "boton_url", "titulo_carrusel", "orden", "activo")


@admin.register(FotoGaleria)
class FotoGaleriaAdmin(admin.ModelAdmin):
    list_display = ("vista", "titulo", "fundacion", "orden", "activo")
    list_display_links = ("vista", "titulo")
    list_editable = ("orden", "activo")
    vista = miniatura("imagen", 60)


@admin.register(Aliado)
class AliadoAdmin(admin.ModelAdmin):
    list_display = ("vista", "nombre", "sitio_web", "orden", "activo")
    list_display_links = ("vista", "nombre")
    list_editable = ("orden", "activo")
    search_fields = ("nombre",)
    vista = miniatura("logo", 40)
