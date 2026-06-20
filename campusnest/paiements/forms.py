"""
campusnest/paiements/forms.py
"""
from django import forms
from .models import Paiement
from campusnest.paiements.service import valider_numero


class PaiementForm(forms.ModelForm):

    class Meta:
        model  = Paiement
        fields = ["operateur", "numero_telephone"]
        widgets = {
            "operateur": forms.RadioSelect(),
            "numero_telephone": forms.TextInput(attrs={
                "placeholder": "Ex : 677 000 000",
                "class": "form-control",
            }),
        }
        labels = {
            "operateur":        "Choisissez votre opérateur",
            "numero_telephone": "Numéro Mobile Money",
        }

    def clean(self):
        cleaned_data = super().clean()
        operateur = cleaned_data.get("operateur")
        numero    = cleaned_data.get("numero_telephone")

        if operateur and numero:
            ok, message = valider_numero(numero, operateur)
            if not ok:
                raise forms.ValidationError(message)

        return cleaned_data