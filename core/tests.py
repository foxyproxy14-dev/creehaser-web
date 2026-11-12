import shutil

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings

from campana.models import Fundacion, Nino

from .models import Aliado, ConfiguracionSitio, EventoDestacado, Experiencia, FotoGaleria

MEDIA = "/tmp/creehaser-test-media-portal"


@override_settings(MEDIA_ROOT=MEDIA)
class PortalTest(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        call_command("datos_iniciales", verbosity=0)
        self.fundacion = Fundacion.objects.get(slug="creehaser")

    def test_contenido_inicial_cargado(self):
        self.assertEqual(Experiencia.objects.count(), 4)
        self.assertEqual(FotoGaleria.objects.count(), 4)
        self.assertEqual(Aliado.objects.count(), 15)
        ev = EventoDestacado.objects.get()
        self.assertEqual(ev.fotos.count(), 25)
        self.assertTrue(ConfiguracionSitio.actual().foto_quienes_somos)
        self.assertTrue(self.fundacion.mision and self.fundacion.vision and self.fundacion.esencia)

    def test_no_pisa_lo_editado(self):
        self.fundacion.mision = "Misión editada por la fundación"
        self.fundacion.save()
        Experiencia.objects.filter(titulo="Softskills Latam").update(titulo="Editada")
        call_command("datos_iniciales", verbosity=0)
        self.fundacion.refresh_from_db()
        self.assertEqual(self.fundacion.mision, "Misión editada por la fundación")
        self.assertTrue(Experiencia.objects.filter(titulo="Editada").exists())
        self.assertEqual(Experiencia.objects.count(), 4)

    def test_actualiza_historia_corta_de_la_version_1(self):
        self.fundacion.descripcion = ("Hace más de 10 años nació un sueño: sembrar esperanza y transformar vidas. "
                                      "Acompañamos a niños, jóvenes y familias en su crecimiento personal y espiritual.")
        self.fundacion.save()
        call_command("datos_iniciales", verbosity=0)
        self.fundacion.refresh_from_db()
        self.assertIn("dar es la forma más hermosa de recibir", self.fundacion.descripcion)

    def test_portada_muestra_todas_las_secciones(self):
        r = self.client.get("/")
        for texto in ["Un Regalo,", "¿Cómo funciona?", "Human Skills Latam 2026", "Jóvenes que nos acompañan este 2026",
                      "NUESTRA HISTORIA", "NUESTRO ADN", "Misión", "Softskills Latam", "Nuestra galería",
                      "Nuestros aliados", "https://dlsolucionesintegrales.com/", "Calle 18B, Valledupar, Cesar",
                      "output=embed", "¡Muy pronto abriremos el árbol!", 'data-deco="auto"']:
            self.assertContains(r, texto)

    def test_contador_del_arbol(self):
        call_command("datos_iniciales", "--demo", verbosity=0)
        n = Nino.objects.first()
        n.estado = Nino.Estado.ASIGNADO
        n.save()
        self.assertContains(self.client.get("/"), "1 de 6 niños ya tienen padrino")

    def test_secciones_ocultas_sin_contenido(self):
        Aliado.objects.update(activo=False)
        r = self.client.get("/")
        self.assertNotContains(r, "Nuestros aliados")
        self.assertNotContains(r, 'data-go="aliados"')

    def test_configuracion_unica(self):
        ConfiguracionSitio(decoracion="off").save()
        self.assertEqual(ConfiguracionSitio.objects.count(), 1)
        self.assertContains(self.client.get("/"), 'data-deco="off"')

    def test_paginas_proximamente(self):
        self.assertContains(self.client.get("/arbol/"), "El Árbol de la Navidad")
        self.assertContains(self.client.get("/mi-panel/"), "Mi panel de padrino")

    def test_enlace_panel_solo_para_organizadores(self):
        self.assertNotContains(self.client.get("/"), "⚙️ Panel fundación")
        u = get_user_model().objects.create_user("org@creehaser.org", "clave-segura-123", es_organizador=True)
        self.client.force_login(u)
        self.assertContains(self.client.get("/"), "⚙️ Panel fundación")
