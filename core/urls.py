from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("arbol/", views.proximamente, {"seccion": "arbol"}, name="arbol"),
    path("mi-panel/", views.proximamente, {"seccion": "mi-panel"}, name="mi_panel"),
    path("salud/", views.salud, name="salud"),
]
