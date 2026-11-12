from campana.models import Fundacion

from .models import ConfiguracionSitio


def sitio(request):
    """Datos que necesitan todas las páginas (cabecera, pie y decoración)."""
    return {
        "config": ConfiguracionSitio.actual(),
        "fundacion": Fundacion.objects.filter(activa=True).order_by("id").first(),
    }
