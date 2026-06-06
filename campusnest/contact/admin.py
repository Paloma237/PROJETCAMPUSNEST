from django.contrib import admin
from .models import MessageContact, Conversation, MessageConversation


@admin.register(MessageContact)
class MessageContactAdmin(admin.ModelAdmin):
    list_display  = ["nom_expediteur", "email", "objet", "est_lu", "date_envoi"]
    list_filter   = ["est_lu"]
    search_fields = ["nom_expediteur", "email", "objet"]
    readonly_fields = ["date_envoi"]


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display  = ["client", "proprietaire", "chambre", "date_creation"]
    readonly_fields = ["date_creation"]


@admin.register(MessageConversation)
class MessageConversationAdmin(admin.ModelAdmin):
    list_display  = ["auteur", "conversation", "est_lu", "date_envoi"]
    list_filter   = ["est_lu"]
    readonly_fields = ["date_envoi"]