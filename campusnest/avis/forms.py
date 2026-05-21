from django import forms
from django.core.exceptions import ValidationError
from .models import Avis
 
CSS = "w-full px-3 py-2 text-sm border border-gray-200 rounded-xl bg-gray-50 focus:outline-none focus:ring-2 focus:ring-secondary/50 transition"
 
 
class AvisForm(forms.ModelForm):
    note = forms.ChoiceField(
        choices=[(i, f"{i} étoile{'s' if i > 1 else ''}") for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={"class": "sr-only"}),
        label="Note",
    )
 
    class Meta:
        model  = Avis
        fields = ["note", "commentaire"]
        widgets = {
            "commentaire": forms.Textarea(attrs={
                "class": CSS + " resize-none",
                "rows": 4,
                "placeholder": "Décrivez votre expérience dans cette chambre...",
            }),
        }
 
    def clean_note(self):
        note = int(self.cleaned_data.get("note", 0))
        if not 1 <= note <= 5:
            raise ValidationError("La note doit être comprise entre 1 et 5.")
        return note
