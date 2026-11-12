from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render

from campana.models import Evento, Fundacion, Nino


def inicio(request):
    """Página temporal mientras se construye el portal (parte 2)."""
    fundacion = Fundacion.objects.filter(activa=True).first()
    evento = Evento.objects.filter(activo=True).first()
    stats = None
    if evento:
        total = Nino.objects.filter(evento=evento).count()
        libres = Nino.objects.filter(evento=evento, estado=Nino.Estado.DISPONIBLE).count()
        stats = {"total": total, "con_padrino": total - libres}
    return render(request, "core/inicio.html", {"fundacion": fundacion, "evento": evento, "stats": stats})


def salud(request):
    """Comprobación para el proxy o un monitor: responde 200 si la app y la base de datos están bien."""
    try:
        with connection.cursor() as c:
            c.execute("SELECT 1")
        return JsonResponse({"estado": "ok"})
    except Exception:
        return JsonResponse({"estado": "error", "detalle": "base de datos no disponible"}, status=503)
