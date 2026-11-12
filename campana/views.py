import hashlib

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import servicios
from .models import Evento, Nino


def evento_activo():
    return Evento.objects.filter(activo=True).select_related("fundacion").order_by("-creado").first()


def orden_del_arbol(evento):
    """Orden estable pero mezclado de los niños en el árbol: la posición de un regalo no delata nada."""
    ninos = list(Nino.objects.filter(evento=evento).values("id", "estado", "padrino_id")) if evento else []
    ninos.sort(key=lambda n: hashlib.sha256(f"{evento.pk}-{n['id']}".encode()).hexdigest())
    return ninos


def arbol(request):
    """
    Árbol de regalos. Por privacidad, la página solo recibe el ESTADO de cada regalo
    (libre / con padrino / tuyo): los datos de un niño solo los ve su padrino después de confirmar.
    """
    evento = evento_activo()
    ninos = orden_del_arbol(evento)
    uid = request.user.id if request.user.is_authenticated else None
    slots = "".join(
        "f" if n["estado"] == Nino.Estado.DISPONIBLE else ("m" if uid and n["padrino_id"] == uid else "t")
        for n in ninos
    )
    return render(request, "campana/arbol.html", {
        "evento": evento,
        "slots": slots,
        "libres": slots.count("f"),
        "total": len(slots),
        "mios": slots.count("m"),
        "max_por_vez": servicios.MAX_POR_VEZ,
    })


@login_required
def confirmar(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    evento = evento_activo()
    orden = [n["id"] for n in orden_del_arbol(evento)]
    try:
        posiciones = sorted({int(x) for x in request.POST.getlist("slot")})
        cantidad = len(posiciones) or int(request.POST.get("cantidad", "0"))
    except ValueError:
        posiciones, cantidad = [], 0
    preferidos = [orden[i] for i in posiciones if 0 <= i < len(orden)]
    if not request.POST.get("acepto"):
        messages.error(request, "Debes aceptar el compromiso para continuar.")
        return redirect("arbol")
    try:
        elegidos = servicios.asignar_al_azar(evento, request.user, cantidad, request.POST.get("mensaje", ""), preferidos)
    except servicios.ErrorApadrinamiento as e:
        messages.error(request, str(e))
        return redirect("arbol")
    request.session["recien_asignados"] = [n.pk for n in elegidos]
    return redirect("revelar")


@login_required
def revelar(request):
    ids = request.session.pop("recien_asignados", None)
    if not ids:
        return redirect("mi_panel")
    ninos = list(Nino.objects.filter(pk__in=ids, padrino=request.user).select_related("evento"))
    return render(request, "campana/revelar.html", {"ninos": ninos, "evento": ninos[0].evento if ninos else None})


@login_required
def mi_panel(request):
    ninos = (Nino.objects.filter(padrino=request.user).select_related("evento")
             .prefetch_related("cambios_regalo").order_by("-asignado_en", "nombre"))
    evento = evento_activo()
    monto = evento.monto_minimo if evento else 0
    return render(request, "campana/mi_panel.html", {
        "ninos": ninos, "evento": evento, "total_minimo": monto * len(ninos),
        "pasos": ["Asignado", "Recibido", "Entregado", "Gracias"],
    })


def _nino_mio(request, pk):
    return get_object_or_404(Nino, pk=pk, padrino=request.user)


@login_required
@require_POST
def nino_regalo(request, pk):
    try:
        servicios.definir_regalo(_nino_mio(request, pk), request.user, request.POST.get("regalo", ""), request.POST.get("motivo", ""))
        messages.success(request, "¡Listo! La fundación ya sabe qué vas a regalar.")
    except servicios.ErrorApadrinamiento as e:
        messages.error(request, str(e))
    return redirect(f"/mi-panel/#nino-{pk}")


@login_required
@require_POST
def nino_mensaje(request, pk):
    try:
        servicios.guardar_mensaje(_nino_mio(request, pk), request.user, request.POST.get("mensaje", ""))
        messages.success(request, "Mensaje guardado. Se imprimirá y acompañará tu regalo.")
    except servicios.ErrorApadrinamiento as e:
        messages.error(request, str(e))
    return redirect(f"/mi-panel/#nino-{pk}")


@login_required
@require_POST
def nino_cancelar(request, pk):
    try:
        servicios.cancelar(_nino_mio(request, pk), request.user)
        messages.info(request, "Regalo cancelado. El niño volvió al árbol.")
    except servicios.ErrorApadrinamiento as e:
        messages.error(request, str(e))
    return redirect("mi_panel")
