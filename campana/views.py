import csv
import hashlib

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotAllowed
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import servicios
from .forms import EstadoNinoForm, GestionNinoForm
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


def _fundacion_organizador(request):
    if not request.user.es_organizador:
        return None
    if request.user.fundacion_id:
        return request.user.fundacion
    if request.user.is_superuser:
        evento = evento_activo()
        return evento.fundacion if evento else None
    return None


@login_required
def panel_organizador(request):
    fundacion = _fundacion_organizador(request)
    if not fundacion:
        return HttpResponseForbidden("Esta cuenta no tiene una fundación asignada.")
    evento = Evento.objects.filter(fundacion=fundacion).order_by("-activo", "-creado").first()
    ninos = Nino.objects.none()
    if evento:
        ninos = Nino.objects.filter(evento=evento).select_related("padrino").order_by("nombre")
        estado = request.GET.get("estado", "")
        buscar = request.GET.get("q", "").strip()
        if estado:
            ninos = ninos.filter(estado=estado)
        if buscar:
            ninos = ninos.filter(Q(nombre__icontains=buscar) | Q(padrino__email__icontains=buscar)
                                 | Q(padrino__first_name__icontains=buscar) | Q(padrino__last_name__icontains=buscar)
                                 | Q(regalo_padrino__icontains=buscar))
    resumen = {x["estado"]: x["total"] for x in Nino.objects.filter(evento=evento).values("estado").annotate(total=Count("id"))} if evento else {}
    return render(request, "campana/panel_organizador.html", {
        "evento": evento, "ninos": ninos, "resumen": resumen, "estados": Nino.Estado.choices,
        "total": sum(resumen.values()), "con_padrino": sum(v for k, v in resumen.items() if k != Nino.Estado.DISPONIBLE),
    })


@login_required
def organizador_nino(request, pk=None):
    fundacion = _fundacion_organizador(request)
    if not fundacion:
        return HttpResponseForbidden("Esta cuenta no tiene una fundación asignada.")
    evento = Evento.objects.filter(fundacion=fundacion).order_by("-activo", "-creado").first()
    if not evento:
        messages.error(request, "Primero crea un evento para la fundación.")
        return redirect("panel_organizador")
    nino = get_object_or_404(Nino, pk=pk, evento__fundacion=fundacion) if pk else None
    form = GestionNinoForm(request.POST or None, request.FILES or None, instance=nino)
    if request.method == "POST" and form.is_valid():
        guardado = form.save(commit=False)
        guardado.evento = evento
        guardado.save()
        messages.success(request, f"Datos de {guardado.nombre} guardados.")
        return redirect("panel_organizador")
    return render(request, "campana/organizador_nino.html", {"form": form, "nino": nino, "evento": evento})


@login_required
@require_POST
def organizador_estado(request, pk):
    fundacion = _fundacion_organizador(request)
    if not fundacion:
        return HttpResponseForbidden("Esta cuenta no tiene una fundación asignada.")
    nino = get_object_or_404(Nino.objects.select_related("padrino", "evento"), pk=pk, evento__fundacion=fundacion)
    anterior = nino.estado
    form = EstadoNinoForm(request.POST, request.FILES, instance=nino)
    if form.is_valid():
        nino = form.save()
        messages.success(request, f"Estado de {nino.nombre}: {nino.get_estado_display()}.")
        if anterior != Nino.Estado.AGRADECIDO and nino.estado == Nino.Estado.AGRADECIDO and nino.padrino:
            enlace = request.build_absolute_uri(f"/certificado/{nino.pk}/")
            send_mail(
                f"Gracias por apadrinar a {nino.nombre}",
                f"El regalo fue entregado. Puedes ver e imprimir tu certificado aquí:\n{enlace}",
                None, [nino.padrino.email], fail_silently=True,
            )
    else:
        messages.error(request, "Revisa el estado, la nota o la fotografía.")
    return redirect("panel_organizador")


@login_required
def exportar_campana(request):
    fundacion = _fundacion_organizador(request)
    if not fundacion:
        return HttpResponseForbidden("Esta cuenta no tiene una fundación asignada.")
    evento = Evento.objects.filter(fundacion=fundacion).order_by("-activo", "-creado").first()
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="campana-{evento.slug if evento else "sin-evento"}.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(["Niño", "Edad", "Estado", "Padrino", "Correo", "Teléfono", "Regalo pedido", "Regalo confirmado", "Asignado el", "Nota interna"])
    for n in Nino.objects.filter(evento=evento).select_related("padrino").order_by("nombre") if evento else []:
        writer.writerow([n.nombre, n.edad, n.get_estado_display(), n.padrino.get_full_name() if n.padrino else "",
                         n.padrino.email if n.padrino else "", n.padrino.telefono if n.padrino else "",
                         n.regalo_deseado, n.regalo_padrino, n.asignado_en or "", n.nota_interna])
    return response


@login_required
def certificado(request, pk):
    nino = get_object_or_404(Nino.objects.select_related("padrino", "evento__fundacion"), pk=pk)
    es_org = bool(_fundacion_organizador(request) and nino.evento.fundacion_id == _fundacion_organizador(request).pk)
    if nino.padrino_id != request.user.id and not es_org:
        return HttpResponseForbidden("Este certificado no pertenece a tu cuenta.")
    if nino.estado != Nino.Estado.AGRADECIDO:
        messages.info(request, "El certificado estará disponible cuando la fundación complete la entrega.")
        return redirect("mi_panel" if not es_org else "panel_organizador")
    return render(request, "campana/certificado.html", {"nino": nino})

