from django import forms
from .models import MessageContact, MessageConversation


class MessageContactForm(forms.ModelForm):
    class Meta:
        model  = MessageContact
        fields = ["nom_expediteur", "email", "telephone", "objet", "message"]
        widgets = {
            "nom_expediteur": forms.TextInput(attrs={
                "placeholder": "Votre nom complet",
                "class": "w-full px-3 py-2.5 text-base border border-gray-200 rounded-xl "
                         "bg-gray-50 focus:outline-none focus:ring-2 focus:ring-secondary/50 transition",
            }),
            "email": forms.EmailInput(attrs={
                "placeholder": "votre@email.com",
                "class": "w-full px-3 py-2.5 text-base border border-gray-200 rounded-xl "
                         "bg-gray-50 focus:outline-none focus:ring-2 focus:ring-secondary/50 transition",
            }),
            "telephone": forms.TextInput(attrs={
                "placeholder": "Ex : +237 6XX XXX XXX",
                "class": "w-full px-3 py-2.5 text-base border border-gray-200 rounded-xl "
                         "bg-gray-50 focus:outline-none focus:ring-2 focus:ring-secondary/50 transition",
            }),
            "objet": forms.TextInput(attrs={
                "placeholder": "Ex : Question sur un logement",
                "class": "w-full px-3 py-2.5 text-base border border-gray-200 rounded-xl "
                         "bg-gray-50 focus:outline-none focus:ring-2 focus:ring-secondary/50 transition",
            }),
            "message": forms.Textarea(attrs={
                "placeholder": "Écrivez votre message...",
                "rows": 5,
                "class": "w-full px-3 py-2.5 text-base border border-gray-200 rounded-xl "
                         "bg-gray-50 focus:outline-none focus:ring-2 focus:ring-secondary/50 "
                         "transition resize-none",
            }),
        }


class ReponseAdminForm(forms.ModelForm):
    class Meta:
        model  = MessageContact
        fields = ["reponse_admin"]
        widgets = {
            "reponse_admin": forms.Textarea(attrs={
                "placeholder": "Rédigez votre réponse...",
                "rows": 6,
                "class": "w-full px-3 py-2.5 text-base border border-gray-200 rounded-xl "
                         "bg-gray-50 focus:outline-none focus:ring-2 focus:ring-secondary/50 "
                         "transition resize-none",
            }),
        }


class MessageConversationForm(forms.ModelForm):
    class Meta:
        model  = MessageConversation
        fields = ["contenu"]
        widgets = {
            "contenu": forms.Textarea(attrs={
                "placeholder": "Écrivez votre message...",
                "rows": 3,
                "class": "w-full px-3 py-2.5 text-base border border-gray-200 rounded-xl "
                         "bg-gray-50 focus:outline-none focus:ring-2 focus:ring-secondary/50 "
                         "transition resize-none",
            }),
        }