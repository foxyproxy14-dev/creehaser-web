"""Reglas de negocio del apadrinamiento (separadas de las vistas para poder probarlas)."""
from django.db import transaction
from django.utils import timezone

from .avisos import avisar
from .models import CambioRegalo, Nino

MAX_POR_VEZ = 10


class ErrorApadrinamiento(Exception):
    pass


def disponibles(evento):
    return Nino.objects.filter(evento=evento, estado=Nino.Estado.DISPONIBLE)


@transaction.atomic
def asignar_al_azar(evento, padrino, cantidad, mensaje="", preferidos=None):
    """
    Asigna `cantidad` niños disponibles al azar.
    Bloquea las filas elegidas (FOR UPDATE SKIP LOCKED) para que dos personas
    que confirman al mismo tiempo nunca reciban al mismo niño.
    """
    if not evento or not evento.activo:
        raise ErrorApadrinamiento("El árbol no está abierto en este momento.")
    if not 1 <= cantidad <= MAX_POR_VEZ:
        raise ErrorApadrinamiento(f"Puedes elegir entre 1 y {MAX_POR_VEZ} regalos a la vez.")

    # Primero, los regalos que la persona tocó en el árbol (no sabe qué niño hay detrás de cada uno);
    # si alguno se lo ganó otra persona en ese instante, se completa al azar.
    elegidos = []
    if preferidos:
        elegidos = list(disponibles(evento).filter(pk__in=preferidos).select_for_update(skip_locked=True)[:cantidad])
    if len(elegidos) < cantidad:
        elegidos += list(disponibles(evento).exclude(pk__in=[n.pk for n in elegidos])
                         .select_for_update(skip_locked=True).order_by("?")[:cantidad - len(elegidos)])
    if len(elegidos) < cantidad:
        quedan = disponibles(evento).count()
        raise ErrorApadrinamiento(
            f"Solo quedan {quedan} regalo(s) disponibles. Elige menos e inténtalo de nuevo." if quedan
            else "¡Todos los niños ya tienen padrino! Gracias por tu interés."
        )

    ahora = timezone.now()
    for n in elegidos:
        n.estado, n.padrino, n.asignado_en = Nino.Estado.ASIGNADO, padrino, ahora
        n.mensaje_padrino, n.regalo_padrino = mensaje[:600], ""
        n.save(update_fields=["estado", "padrino", "asignado_en", "mensaje_padrino", "regalo_padrino", "actualizado"])

    lista = "\n".join(f"• {n.nombre} ({n.get_sexo_display().lower()}, {n.edad} años)" for n in elegidos)

    def aviso():  # se cuenta después de guardar, para que el número sea exacto
        quedan, total = disponibles(evento).count(), Nino.objects.filter(evento=evento).count()
        avisar(f"🎁 {'Nuevo regalo apadrinado' if cantidad == 1 else f'{cantidad} regalos apadrinados'}\n"
               f"Padrino: {padrino.get_full_name()} ({padrino.email})\n{lista}\nQuedan {quedan} de {total} disponibles")
    transaction.on_commit(aviso)
    return elegidos


def _mio(nino, padrino):
    if nino.padrino_id != padrino.id:
        raise ErrorApadrinamiento("Este niño no está asignado a tu cuenta.")


@transaction.atomic
def cancelar(nino, padrino):
    nino = Nino.objects.select_for_update().get(pk=nino.pk)
    _mio(nino, padrino)
    if not nino.puede_cancelar():
        raise ErrorApadrinamiento("Ya pasó el tiempo para cancelar. Escríbele a la fundación si necesitas un cambio.")
    nombre = nino.nombre
    nino.liberar()
    nino.save()
    nino.cambios_regalo.all().delete()
    transaction.on_commit(lambda: avisar(
        f"↩️ Regalo cancelado por el padrino\nPadrino: {padrino.get_full_name()}\nNiño: {nombre}"
    ))


@transaction.atomic
def definir_regalo(nino, padrino, texto, motivo=""):
    nino = Nino.objects.select_for_update().get(pk=nino.pk)
    _mio(nino, padrino)
    if nino.estado != Nino.Estado.ASIGNADO:
        raise ErrorApadrinamiento("La fundación ya recibió el regalo; no se puede cambiar.")
    texto, motivo = texto.strip()[:150], motivo.strip()[:200]
    if len(texto) < 3:
        raise ErrorApadrinamiento("Escribe qué regalo vas a entregar.")
    anterior = nino.regalo_padrino
    if texto == anterior:
        return nino
    CambioRegalo.objects.create(nino=nino, padrino=padrino, regalo_anterior=anterior, regalo_nuevo=texto, motivo=motivo)
    nino.regalo_padrino = texto
    nino.save(update_fields=["regalo_padrino", "actualizado"])
    if anterior:
        aviso = (f"✏️ Cambio de regalo\nPadrino: {padrino.get_full_name()}\nNiño: {nino.nombre} ({nino.edad} años)\n"
                 f"Antes: {anterior}\nAhora: {texto}" + (f"\nMotivo: {motivo}" if motivo else ""))
    else:
        aviso = (f"🎁 Regalo definido\nPadrino: {padrino.get_full_name()}\nNiño: {nino.nombre} ({nino.edad} años)\n"
                 f"Pidió: {nino.regalo_deseado}\nVa a dar: {texto}")
    transaction.on_commit(lambda: avisar(aviso))
    return nino


def guardar_mensaje(nino, padrino, mensaje):
    _mio(nino, padrino)
    if nino.estado not in (Nino.Estado.ASIGNADO, Nino.Estado.RECIBIDO):
        raise ErrorApadrinamiento("El regalo ya fue entregado; el mensaje ya no se puede cambiar.")
    nino.mensaje_padrino = mensaje.strip()[:600]
    nino.save(update_fields=["mensaje_padrino", "actualizado"])
    return nino
