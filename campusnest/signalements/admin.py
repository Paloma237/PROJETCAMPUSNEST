from django.contrib import admin

# Register your models here.
from .models import Signalement

@admin.register(Signalement)
class SignalementAdmin(admin.ModelAdmin):
    list_display = ('chambre', 'client', 'statut','motif','date_signalement')
    list_filter = ('statut', 'motif', 'date_signalement')
    search_fields = ('chambre__cite__nom', 'client__email', 'description')
    actions = ['traiter_signalements', 'cloturer_signalements']