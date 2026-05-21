from django import forms
from .models import MessageDeContact
 
CSS = "w-full px-3 py-2 text-sm border border-gray-200 rounded-xl bg-gray-50 focus:outline-none focus:ring-2 focus:ring-secondary/50 transition"
 
 
class MessageForm(forms.ModelForm):
    class Meta:
        model  = MessageDeContact
        fields = ["nom_expediteur", "telephone", "email", "objet_message", "message"]
        widgets = {
            "nom_expediteur": forms.TextInput(attrs={"class": CSS, "placeholder": "Votre nom complet"}),
            "telephone":      forms.TextInput(attrs={"class": CSS, "placeholder": "6XX XXX XXX"}),
            "email":          forms.EmailInput(attrs={"class": CSS, "placeholder": "votre@email.cm"}),
            "objet_message":  forms.TextInput(attrs={"class": CSS, "placeholder": "Objet du message"}),
            "message":        forms.Textarea(attrs={
                "class": CSS + " resize-none",
                "rows": 5,
                "placeholder": "Votre message...",
            }),
        }
 
 
class ReponseForm(forms.ModelForm):
    class Meta:
        model  = MessageDeContact
        fields = ["reponse_admin"]
        widgets = {
            "reponse_admin": forms.Textarea(attrs={
                "class": CSS + " resize-none",
                "rows": 5,
                "placeholder": "Votre réponse...",
            }),
        }
        labels = {"reponse_admin": "Réponse"}
