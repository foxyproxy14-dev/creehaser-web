"""Optimización de fotos subidas: corrige la orientación, reduce el tamaño y guarda como JPG."""
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps


def optimizar_imagen(campo, lado_max=1200, calidad=82):
    campo.file.seek(0)
    img = Image.open(campo.file)
    img = ImageOps.exif_transpose(img)  # respeta la orientación de las fotos del celular
    if img.mode not in ("RGB", "L"):
        fondo = Image.new("RGB", img.size, (255, 255, 255))
        fondo.paste(img, mask=img.convert("RGBA").split()[-1])
        img = fondo
    img.thumbnail((lado_max, lado_max))
    salida = BytesIO()
    img.convert("RGB").save(salida, format="JPEG", quality=calidad, optimize=True)  # sin metadatos EXIF (ubicación GPS, etc.)
    campo.file = ContentFile(salida.getvalue(), name="foto.jpg")
