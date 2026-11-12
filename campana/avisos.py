"""
Avisos a los organizadores por Telegram.

Si TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID están en el .env, envía el mensaje al grupo.
Si no, solo lo deja en el registro (docker compose logs web). Nunca rompe la petición del usuario.
"""
import json
import logging
import threading
import urllib.request

from django.conf import settings

log = logging.getLogger("campana.avisos")


def _enviar(texto):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    datos = json.dumps({"chat_id": settings.TELEGRAM_CHAT_ID, "text": texto, "disable_web_page_preview": True}).encode()
    req = urllib.request.Request(url, data=datos, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=8).read()
    except Exception as e:  # noqa: BLE001 - un fallo de Telegram no debe afectar a la web
        log.warning("No se pudo enviar el aviso a Telegram: %s", e)


def avisar(texto):
    log.info("AVISO: %s", texto.replace("\n", " | "))
    if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
        threading.Thread(target=_enviar, args=(texto,), daemon=True).start()
