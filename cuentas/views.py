from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme

from campana.avisos import avisar

from .forms import IngresoForm, MisDatosForm, RegistroForm


def _siguiente(request, defecto="mi_panel"):
    nxt = request.POST.get("next") or request.GET.get("next")
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return nxt
    return reverse_lazy(defecto)


def registro(request):
    if request.user.is_authenticated:
        return redirect(_siguiente(request))
    form = RegistroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = form.save()
        login(request, usuario, backend="django.contrib.auth.backends.ModelBackend")
        avisar(f"🙋 Nuevo padrino registrado\n{usuario.get_full_name()}\n{usuario.email} · {usuario.telefono}")
        messages.success(request, f"¡Bienvenido, {usuario.first_name}! Tu cuenta está lista.")
        return redirect(_siguiente(request))
    return render(request, "cuentas/registro.html", {"form": form, "next": request.GET.get("next", "")})


class Ingreso(auth_views.LoginView):
    template_name = "cuentas/ingreso.html"
    authentication_form = IngresoForm
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        return reverse_lazy("mi_panel")

    def form_valid(self, form):
        messages.success(self.request, f"Hola de nuevo, {form.get_user().first_name or ''}".strip())
        return super().form_valid(form)


def salir(request):
    if request.method == "POST":
        from django.contrib.auth import logout
        logout(request)
        messages.info(request, "Sesión cerrada.")
    return redirect("inicio")


@login_required
def mis_datos(request):
    datos = MisDatosForm(request.POST if request.POST.get("form") == "datos" else None, instance=request.user)
    clave = PasswordChangeForm(request.user, request.POST if request.POST.get("form") == "clave" else None)
    if request.method == "POST":
        if request.POST.get("form") == "datos" and datos.is_valid():
            datos.save()
            messages.success(request, "Datos guardados.")
            return redirect("mis_datos")
        if request.POST.get("form") == "clave" and clave.is_valid():
            update_session_auth_hash(request, clave.save())
            messages.success(request, "Contraseña cambiada.")
            return redirect("mis_datos")
    return render(request, "cuentas/mis_datos.html", {"datos": datos, "clave": clave})


class RecuperarClave(auth_views.PasswordResetView):
    template_name = "cuentas/recuperar.html"
    email_template_name = "cuentas/correo_recuperar.txt"
    subject_template_name = "cuentas/correo_recuperar_asunto.txt"
    success_url = reverse_lazy("recuperar_enviado")


class RecuperarEnviado(auth_views.PasswordResetDoneView):
    template_name = "cuentas/recuperar_enviado.html"


class NuevaClave(auth_views.PasswordResetConfirmView):
    template_name = "cuentas/nueva_clave.html"
    success_url = reverse_lazy("clave_cambiada")


class ClaveCambiada(auth_views.PasswordResetCompleteView):
    template_name = "cuentas/clave_cambiada.html"
