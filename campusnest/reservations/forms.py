from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Reservation
from campusnest.logements.models import DateVisiteChambre
 
CSS = "w-full px-3 py-2 text-base border border-gray-200 rounded-xl bg-gray-50 focus:outline-none focus:ring-2 focus:ring-secondary/50 transition"

class ReservationForm(forms.ModelForm):

    date_visite = forms.ModelChoiceField(
        queryset=DateVisiteChambre.objects.none(),
        label="Date de visite souhaitée",
        empty_label="— Choisir une date —",
        widget=forms.Select(attrs={"class": "w-full border border-gray-300 rounded-xl px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-primary/40"}),
    )

    class Meta:
        model  = Reservation
        fields = ["date_debut", "date_fin"]
        widgets = {
            "date_debut": forms.DateInput(
                attrs={"type": "date", "class": "w-full border border-gray-300 rounded-xl px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-primary/40"}
            ),
            "date_fin": forms.DateInput(
                attrs={"type": "date", "class": "w-full border border-gray-300 rounded-xl px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-primary/40"}
            ),
        }

    def __init__(self, *args, chambre=None, **kwargs):
        super().__init__(*args, **kwargs)
        if chambre is not None:
            from django.utils import timezone
            self.fields["date_visite"].queryset = DateVisiteChambre.objects.filter(
                chambre=chambre,
                date__gte=timezone.now().date(),
            ).order_by("date")

    def clean(self):
        cleaned = super().clean()
        debut = cleaned.get("date_debut")
        fin   = cleaned.get("date_fin")
        if debut and fin:
            if fin <= debut:
                raise forms.ValidationError("La date de fin doit être postérieure à la date de début.")
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Extraire la date réelle de l'objet DateVisiteChambre sélectionné
        date_visite_obj = self.cleaned_data.get("date_visite")
        if date_visite_obj:
            instance.date_visite = date_visite_obj.date
        if commit:
            instance.save()
        return instance
 
 
class DateVisiteForm(forms.Form):
    date_visite = forms.DateField(
        label="Date de visite souhaitée",
        widget=forms.DateInput(attrs={"class": CSS, "type": "date"}),
    )
 
    def clean_date_visite(self):
        date = self.cleaned_data.get("date_visite")
        if date and date < timezone.now().date():
            raise ValidationError("La date de visite ne peut pas être dans le passé.")
        return date
"""
campusnest/reservations/forms.py
"""






class AccepterReservationForm(forms.Form):
    """
    Formulaire rempli par le PROPRIÉTAIRE lors de l'acceptation d'une réservation.
    Il renseigne le lieu et l'heure de la visite (la date a déjà été choisie par le client).
    """
    lieu_visite = forms.CharField(
        label="Lieu de la visite",
        max_length=255,
        widget=forms.TextInput(attrs={
            "placeholder": "Ex : Entrée principale de la cité, Bâtiment A...",
            "class": "w-full border border-gray-300 rounded-xl px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-primary/40",
        }),
    )
    heure_visite = forms.TimeField(
        label="Heure de la visite",
        widget=forms.TimeInput(attrs={
            "type": "time",
            "class": "w-full border border-gray-300 rounded-xl px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-primary/40",
        }),
    )