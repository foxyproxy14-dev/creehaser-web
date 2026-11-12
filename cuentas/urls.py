from django.urls import path

from . import views

urlpatterns = [
    path("registro/", views.registro, name="registro"),
    path("ingresar/", views.Ingreso.as_view(), name="ingresar"),
    path("salir/", views.salir, name="salir"),
    path("mis-datos/", views.mis_datos, name="mis_datos"),
    path("recuperar/", views.RecuperarClave.as_view(), name="recuperar"),
    path("recuperar/enviado/", views.RecuperarEnviado.as_view(), name="recuperar_enviado"),
    path("recuperar/<uidb64>/<token>/", views.NuevaClave.as_view(), name="nueva_clave"),
    path("recuperar/listo/", views.ClaveCambiada.as_view(), name="clave_cambiada"),
]
