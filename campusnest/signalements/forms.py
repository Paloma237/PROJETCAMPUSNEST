from django import forms
from .models import Signalement

CSS = "w-full px-3 py-2 text-sm border border-gray-200 rounded-xl bg-gray-50 focus:outline-none focus:ring-2 focus:ring-secondary/50 transition"

MOTIFS = [
    ("", "— Choisissez un motif —"),
    ("photos",        "Photos incorrectes ou trompeuses"),
    ("prix",          "Prix affiché différent du prix réel"),
    ("inexistante",   "Chambre inexistante ou indisponible"),
    ("etat",          "Chambre en mauvais état"),
    ("autre",         "Autre"),
]

class SignalementForm(forms.ModelForm):
    motif = forms.ChoiceField(
        choices=MOTIFS,
        widget=forms.Select(attrs={"class": CSS}),
    )

    class Meta:
        model  = Signalement
        fields = ["motif", "description"]
        widgets = {
            "description": forms.Textarea(attrs={
                "class": CSS + " resize-none",
                "rows": 4,
                "placeholder": "Décrivez le problème en détail...",
            }),
        }
