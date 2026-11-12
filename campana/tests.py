import datetime
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image

from .models import CambioRegalo, Evento, Fundacion, Nino

Usuario = get_user_model()


class BaseTest(TestCase):
    def setUp(self):
        call_command("datos_iniciales", "--demo", verbosity=0)
        self.evento = Evento.objects.get(slug="navidad-2026")
        self.padrino = Usuario.objects.create_user("ana@correo.com", "clave-segura-123", first_name="Ana", last_name="López")


class DatosInicialesTest(BaseTest):
    def test_no_duplica_al_repetir(self):
        call_command("datos_iniciales", "--demo", verbosity=0)
        self.assertEqual(Fundacion.objects.count(), 1)
        self.assertEqual(Evento.objects.count(), 1)
        self.assertEqual(Nino.objects.count(), 6)


class UsuarioTest(TestCase):
    def test_login_por_correo_normalizado(self):
        u = Usuario.objects.create_user("Pepe@Correo.COM", "clave-segura-123")
        self.assertEqual(u.email, "pepe@correo.com")
        self.assertTrue(self.client.login(email="pepe@correo.com", password="clave-segura-123"))

    def test_superusuario_es_organizador(self):
        u = Usuario.objects.create_superuser("admin@creehaser.org", "clave-segura-123")
        self.assertTrue(u.es_organizador and u.is_staff and u.is_superuser)


class NinoTest(BaseTest):
    def test_ventana_de_cancelacion(self):
        n = Nino.objects.filter(evento=self.evento).first()
        n.estado, n.padrino, n.asignado_en = Nino.Estado.ASIGNADO, self.padrino, timezone.now()
        self.assertTrue(n.puede_cancelar())
        self.assertFalse(n.puede_cancelar(timezone.now() + datetime.timedelta(minutes=16)))

    def test_liberar_limpia_apadrinamiento(self):
        n = Nino.objects.filter(evento=self.evento).first()
        n.estado, n.padrino, n.asignado_en, n.regalo_padrino = Nino.Estado.ASIGNADO, self.padrino, timezone.now(), "Lámpara"
        n.liberar()
        self.assertEqual((n.estado, n.padrino, n.regalo_padrino), (Nino.Estado.DISPONIBLE, None, ""))

    def test_historial_de_regalo(self):
        n = Nino.objects.filter(evento=self.evento).first()
        CambioRegalo.objects.create(nino=n, padrino=self.padrino, regalo_nuevo="Lámpara de constelaciones")
        CambioRegalo.objects.create(nino=n, padrino=self.padrino, regalo_anterior="Lámpara de constelaciones",
                                    regalo_nuevo="Set de planetas", motivo="No la conseguí")
        self.assertEqual(list(n.cambios_regalo.values_list("regalo_nuevo", flat=True)),
                         ["Lámpara de constelaciones", "Set de planetas"])

    def test_estatura_en_metros(self):
        self.assertEqual(Nino(estatura_cm=115).estatura_m, "1,15 m")


@override_settings(MEDIA_ROOT="/tmp/creehaser-test-media")
class FotoTest(BaseTest):
    def test_foto_se_reduce_y_guarda_como_jpg(self):
        buf = BytesIO()
        Image.new("RGBA", (3000, 2000), (200, 30, 30, 255)).save(buf, "PNG")
        n = Nino.objects.filter(evento=self.evento).first()
        n.foto = SimpleUploadedFile("foto.png", buf.getvalue(), content_type="image/png")
        n.save()
        n.refresh_from_db()
        self.assertTrue(n.foto.name.endswith(".jpg"))
        with Image.open(n.foto.path) as img:
            self.assertLessEqual(max(img.size), 900)
            self.assertEqual(img.format, "JPEG")


class VistasTest(BaseTest):
    def test_inicio_y_salud(self):
        r = self.client.get("/")
        self.assertContains(r, "Fundación CreeHaSer")
        self.assertContains(r, "0 de 6 niños con padrino")
        self.assertEqual(self.client.get("/salud/").json(), {"estado": "ok"})
