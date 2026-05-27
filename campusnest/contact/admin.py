from django.contrib import admin
from .models import MessageDeContact
@admin.register(MessageDeContact)
class MessageDeContactAdmin(admin.ModelAdmin):
    list_display = ("nom_expediteur", "email", "objet_message", "est_lu", "date_envoi")
    list_filter = ["date_envoi"]
    search_fields = ("nom_expediteur", "email", "objet_message", "message")
    readonly_fields = ("date_envoi",)
    actions = ["marquer_comme_lu"]

    def marquer_comme_lu(self, request, queryset):
        updated_count = queryset.update(est_lu=True)
        self.message_user(request, f"{updated_count} message(s) marqué(s) comme lu(s).")
    marquer_comme_lu.short_description = "Marquer les messages sélectionnés comme lu(s)"
