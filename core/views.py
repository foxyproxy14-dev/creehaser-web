from django.db import connection
from django.db.models import Count, Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import render

from campana.models import Evento, Nino

from .models import FotoEventoDestacado


def _evento_activo():
    return Evento.objects.filter(activo=True).select_related("fundacion").order_by("-creado").first()


def _resumen_arbol(evento):
    if not evento:
        return {"total": 0, "con_padrino": 0, "porcentaje": 0}
    datos = Nino.objects.filter(evento=evento).aggregate(
        total=Count("id"), libres=Count("id", filter=Q(estado=Nino.Estado.DISPONIBLE)),
    )
    total, con_padrino = datos["total"], datos["total"] - datos["libres"]
    return {
        "total": total,
        "con_padrino": con_padrino,
        "porcentaje": round(con_padrino * 100 / total) if total else 0,
    }


def inicio(request):
    evento = _evento_activo()
    fundacion = evento.fundacion if evento else None
    ctx = {"evento": evento, "arbol": _resumen_arbol(evento)}
    if fundacion:
        ctx.update(
            fundacion=fundacion,
            experiencias=fundacion.experiencias.filter(activo=True),
            eventos_destacados=fundacion.eventos_destacados.filter(activo=True).prefetch_related(
                Prefetch("fotos", queryset=FotoEventoDestacado.objects.order_by("orden", "id"))
            ),
            galeria=fundacion.galeria.filter(activo=True),
            aliados=fundacion.aliados.filter(activo=True),
        )
    return render(request, "core/inicio.html", ctx)


def salud(request):
    """Comprobación para el proxy o un monitor: responde 200 si la app y la base de datos están bien."""
    try:
        with connection.cursor() as c:
            c.execute("SELECT 1")
        return JsonResponse({"estado": "ok"})
    except Exception:
        return JsonResponse({"estado": "error", "detalle": "base de datos no disponible"}, status=503)
