from django import forms

from .models import Nino


class GestionNinoForm(forms.ModelForm):
    class Meta:
        model = Nino
        fields = (
            "nombre", "sexo", "edad", "estatura_cm", "gustos", "regalo_deseado", "foto",
            "estado", "nota_interna", "foto_entrega",
        )
        widgets = {
            "nota_interna": forms.Textarea(attrs={"rows": 3}),
        }


class EstadoNinoForm(forms.ModelForm):
    class Meta:
        model = Nino
        fields = ("estado", "nota_interna", "foto_entrega")
        widgets = {"nota_interna": forms.Textarea(attrs={"rows": 3})}

