from django.urls import path

from . import views

urlpatterns = [
    path("arbol/", views.arbol, name="arbol"),
    path("arbol/confirmar/", views.confirmar, name="confirmar"),
    path("arbol/tus-ninos/", views.revelar, name="revelar"),
    path("mi-panel/", views.mi_panel, name="mi_panel"),
    path("mi-panel/nino/<int:pk>/regalo/", views.nino_regalo, name="nino_regalo"),
    path("mi-panel/nino/<int:pk>/mensaje/", views.nino_mensaje, name="nino_mensaje"),
    path("mi-panel/nino/<int:pk>/cancelar/", views.nino_cancelar, name="nino_cancelar"),
]
