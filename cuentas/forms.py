from django import forms
from django.contrib.auth import authenticate, get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone

Usuario = get_user_model()


class RegistroForm(forms.ModelForm):
    password1 = forms.CharField(label="Contraseña", strip=False,
                                widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "placeholder": "Mínimo 8 caracteres"}))
    password2 = forms.CharField(label="Repite la contraseña", strip=False,
                                widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    acepto = forms.BooleanField(
        label="Autorizo a la fundación el tratamiento de mis datos personales para gestionar esta campaña (Ley 1581 de 2012).",
        error_messages={"required": "Debes autorizar el tratamiento de datos para continuar."},
    )

    class Meta:
        model = Usuario
        fields = ["first_name", "last_name", "email", "telefono"]
        labels = {"first_name": "Nombre", "last_name": "Apellido", "email": "Correo", "telefono": "Teléfono / WhatsApp"}
        widgets = {
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "telefono": forms.TextInput(attrs={"autocomplete": "tel", "placeholder": "+57 300 000 0000"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ("first_name", "last_name", "telefono"):
            self.fields[f].required = True

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe una cuenta con ese correo. Inicia sesión.")
        return email

    def clean_telefono(self):
        tel = self.cleaned_data["telefono"].strip()
        if sum(c.isdigit() for c in tel) < 7:
            raise forms.ValidationError("Escribe un teléfono válido.")
        return tel

    def clean(self):
        datos = super().clean()
        p1, p2 = datos.get("password1"), datos.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        elif p1:
            usuario = Usuario(email=datos.get("email", ""), first_name=datos.get("first_name", ""),
                              last_name=datos.get("last_name", ""))
            try:
                password_validation.validate_password(p1, usuario)
            except forms.ValidationError as e:
                self.add_error("password1", e)
        return datos

    def save(self, commit=True):
        u = super().save(commit=False)
        u.set_password(self.cleaned_data["password1"])
        u.acepto_datos_en = timezone.now()
        if commit:
            u.save()
        return u


class IngresoForm(AuthenticationForm):
    username = forms.EmailField(label="Correo", widget=forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True}))
    error_messages = {
        "invalid_login": "Correo o contraseña incorrectos.",
        "inactive": "Esta cuenta está desactivada.",
    }

    def clean(self):
        email = (self.cleaned_data.get("username") or "").strip().lower()
        password = self.cleaned_data.get("password")
        if email and password:
            self.user_cache = authenticate(self.request, email=email, password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)
        return self.cleaned_data


class MisDatosForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ["first_name", "last_name", "telefono"]
        labels = {"first_name": "Nombre", "last_name": "Apellido", "telefono": "Teléfono / WhatsApp"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.required = True
