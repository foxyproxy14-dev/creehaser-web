import datetime
import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import CambioRegalo, Evento, Nino
from .servicios import ErrorApadrinamiento, asignar_al_azar

Usuario = get_user_model()


@override_settings(MEDIA_ROOT="/tmp/creehaser-test-media-flujo")
class FlujoPadrinoTest(TestCase):
    def setUp(self):
        call_command("datos_iniciales", "--demo", verbosity=0)
        self.evento = Evento.objects.get(slug="navidad-2026")
        self.ana = Usuario.objects.create_user("ana@correo.com", "Navidad-2026!", first_name="Ana", last_name="López")
        self.beto = Usuario.objects.create_user("beto@correo.com", "Navidad-2026!", first_name="Beto", last_name="Ruiz")

    # --- cuentas ---
    def test_registro_completo_e_inicio_de_sesion(self):
        r = self.client.post("/cuenta/registro/?next=/arbol/", {
            "first_name": "Carla", "last_name": "Pérez", "email": "Carla@Correo.com", "telefono": "+57 300 123 4567",
            "password1": "Navidad-2026!", "password2": "Navidad-2026!", "acepto": "on", "next": "/arbol/"})
        self.assertRedirects(r, "/arbol/")
        u = Usuario.objects.get(email="carla@correo.com")
        self.assertIsNotNone(u.acepto_datos_en)
        self.client.post("/cuenta/salir/")
        r = self.client.post("/cuenta/ingresar/", {"username": "carla@correo.com", "password": "Navidad-2026!"})
        self.assertRedirects(r, "/mi-panel/")

    def test_registro_valida_errores(self):
        r = self.client.post("/cuenta/registro/", {
            "first_name": "X", "last_name": "Y", "email": "ana@correo.com", "telefono": "12",
            "password1": "abc", "password2": "abd"})
        for txt in ["Ya existe una cuenta con ese correo", "Escribe un teléfono válido", "no coinciden",
                    "Debes autorizar el tratamiento de datos"]:
            self.assertContains(r, txt)

    def test_ingreso_incorrecto(self):
        r = self.client.post("/cuenta/ingresar/", {"username": "ana@correo.com", "password": "mala"})
        self.assertContains(r, "Correo o contraseña incorrectos")

    def test_recuperar_clave_envia_enlace(self):
        self.client.post("/cuenta/recuperar/", {"email": "ana@correo.com"})
        self.assertEqual(len(mail.outbox), 1)
        enlace = re.search(r"http://testserver(/cuenta/recuperar/\S+/)", mail.outbox[0].body).group(1)
        r = self.client.get(enlace, follow=True)
        r = self.client.post(r.redirect_chain[-1][0], {"new_password1": "Nueva-Clave-2026", "new_password2": "Nueva-Clave-2026"})
        self.assertRedirects(r, "/cuenta/recuperar/listo/")
        self.assertTrue(self.client.login(email="ana@correo.com", password="Nueva-Clave-2026"))

    # --- árbol ---
    def test_arbol_no_revela_datos_de_los_ninos(self):
        r = self.client.get("/arbol/")
        self.assertContains(r, 'data-slots="ffffff"')
        for n in Nino.objects.all():
            self.assertNotContains(r, n.nombre)

    def test_confirmar_requiere_sesion(self):
        r = self.client.post("/arbol/confirmar/", {"cantidad": 1, "acepto": "1"})
        self.assertEqual(r.status_code, 302)
        self.assertIn("/cuenta/ingresar/", r["Location"])
        self.assertEqual(Nino.objects.filter(estado="asignado").count(), 0)

    def test_confirmar_varios_y_revelar(self):
        self.client.force_login(self.ana)
        r = self.client.post("/arbol/confirmar/", {"cantidad": 3, "acepto": "1", "mensaje": "¡Feliz Navidad!"})
        self.assertRedirects(r, "/arbol/tus-ninos/", fetch_redirect_response=False)
        mios = Nino.objects.filter(padrino=self.ana)
        self.assertEqual(mios.count(), 3)
        self.assertTrue(all(n.mensaje_padrino == "¡Feliz Navidad!" for n in mios))
        r = self.client.get("/arbol/tus-ninos/")
        for n in mios:
            self.assertContains(r, n.nombre)
        slots = re.search(r'data-slots="(\w+)"', self.client.get("/arbol/").content.decode()).group(1)
        self.assertEqual(slots.count("m"), 3)

    def test_el_regalo_tocado_es_el_que_se_asigna(self):
        from .views import orden_del_arbol
        self.client.force_login(self.ana)
        self.client.post("/arbol/confirmar/", {"slot": ["0", "4"], "acepto": "1"})
        slots = re.search(r'data-slots="(\w+)"', self.client.get("/arbol/").content.decode()).group(1)
        self.assertEqual((slots[0], slots[4], slots.count("m")), ("m", "m", 2))
        orden = orden_del_arbol(self.evento)
        self.assertEqual({orden[0]["padrino_id"], orden[4]["padrino_id"]}, {self.ana.pk})

    def test_sin_aceptar_no_asigna(self):
        self.client.force_login(self.ana)
        self.client.post("/arbol/confirmar/", {"cantidad": 2})
        self.assertEqual(Nino.objects.filter(padrino=self.ana).count(), 0)

    def test_nunca_asigna_el_mismo_nino_dos_veces(self):
        a = asignar_al_azar(self.evento, self.ana, 4)
        b = asignar_al_azar(self.evento, self.beto, 2)
        self.assertFalse({n.pk for n in a} & {n.pk for n in b})
        with self.assertRaisesMessage(ErrorApadrinamiento, "Todos los niños ya tienen padrino"):
            asignar_al_azar(self.evento, self.beto, 1)

    def test_no_permite_mas_de_los_disponibles(self):
        with self.assertRaisesMessage(ErrorApadrinamiento, "Solo quedan 6"):
            asignar_al_azar(self.evento, self.ana, 7)

    # --- panel del padrino ---
    def _asignar(self, usuario=None, n=1):
        return asignar_al_azar(self.evento, usuario or self.ana, n)[0]

    def test_definir_y_cambiar_regalo_con_historial(self):
        nino = self._asignar()
        self.client.force_login(self.ana)
        self.client.post(f"/mi-panel/nino/{nino.pk}/regalo/", {"regalo": "Lámpara de constelaciones"})
        self.client.post(f"/mi-panel/nino/{nino.pk}/regalo/", {"regalo": "Set de planetas", "motivo": "No conseguí la lámpara"})
        nino.refresh_from_db()
        self.assertEqual(nino.regalo_padrino, "Set de planetas")
        h = list(CambioRegalo.objects.filter(nino=nino).values_list("regalo_anterior", "regalo_nuevo", "motivo"))
        self.assertEqual(h, [("", "Lámpara de constelaciones", ""), ("Lámpara de constelaciones", "Set de planetas", "No conseguí la lámpara")])
        self.assertContains(self.client.get("/mi-panel/"), "Set de planetas")

    def test_no_cambia_regalo_cuando_ya_se_recibio(self):
        nino = self._asignar()
        Nino.objects.filter(pk=nino.pk).update(estado="recibido")
        self.client.force_login(self.ana)
        self.client.post(f"/mi-panel/nino/{nino.pk}/regalo/", {"regalo": "Otra cosa"})
        nino.refresh_from_db()
        self.assertEqual(nino.regalo_padrino, "")

    def test_no_puede_tocar_ninos_ajenos(self):
        nino = self._asignar(self.beto)
        self.client.force_login(self.ana)
        self.assertEqual(self.client.post(f"/mi-panel/nino/{nino.pk}/regalo/", {"regalo": "Algo"}).status_code, 404)
        self.assertEqual(self.client.post(f"/mi-panel/nino/{nino.pk}/cancelar/").status_code, 404)
        self.assertNotContains(self.client.get("/mi-panel/"), nino.nombre)

    def test_cancelar_dentro_y_fuera_del_plazo(self):
        nino = self._asignar()
        self.client.force_login(self.ana)
        self.client.post(f"/mi-panel/nino/{nino.pk}/cancelar/")
        nino.refresh_from_db()
        self.assertEqual((nino.estado, nino.padrino_id), ("disponible", None))

        nino = self._asignar()
        Nino.objects.filter(pk=nino.pk).update(asignado_en=timezone.now() - datetime.timedelta(minutes=20))
        self.client.post(f"/mi-panel/nino/{nino.pk}/cancelar/")
        nino.refresh_from_db()
        self.assertEqual(nino.padrino_id, self.ana.pk)

    def test_mensaje_editable(self):
        nino = self._asignar()
        self.client.force_login(self.ana)
        self.client.post(f"/mi-panel/nino/{nino.pk}/mensaje/", {"mensaje": "Con cariño"})
        nino.refresh_from_db()
        self.assertEqual(nino.mensaje_padrino, "Con cariño")

    def test_panel_requiere_sesion(self):
        self.assertIn("/cuenta/ingresar/", self.client.get("/mi-panel/")["Location"])

    def test_mis_datos(self):
        self.client.force_login(self.ana)
        self.client.post("/cuenta/mis-datos/", {"form": "datos", "first_name": "Ana María", "last_name": "López", "telefono": "+57 301 000 0000"})
        self.ana.refresh_from_db()
        self.assertEqual(self.ana.first_name, "Ana María")
