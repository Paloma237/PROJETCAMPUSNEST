from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Reservation
 
CSS = "w-full px-3 py-2 text-sm border border-gray-200 rounded-xl bg-gray-50 focus:outline-none focus:ring-2 focus:ring-secondary/50 transition"
 
 
class ReservationForm(forms.ModelForm):
    class Meta:
        model  = Reservation
        fields = ["date_debut", "date_fin"]
        widgets = {
            "date_debut": forms.DateInput(attrs={"class": CSS, "type": "date"}),
            "date_fin":   forms.DateInput(attrs={"class": CSS, "type": "date"}),
        }
 
    def clean(self):
        cleaned = super().clean()
        debut = cleaned.get("date_debut")
        fin   = cleaned.get("date_fin")
 
        if debut and fin:
            if debut < timezone.now().date():
                self.add_error("date_debut", "La date de début ne peut pas être dans le passé.")
            if fin <= debut:
                self.add_error("date_fin", "La date de fin doit être après la date de début.")
            if (fin - debut).days < 30:
                self.add_error("date_fin", "La durée minimale de réservation est de 30 jours.")
 
        return cleaned
 
 
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
