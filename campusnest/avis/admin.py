from django.contrib import admin
from .models import Avis
# Register your models here.

@admin.register(Avis)
class AvisAdmin(admin.ModelAdmin):
    list_display = ('client', 'chambre', 'note', 'date_avis')
    list_filter = ('note', 'date_creation')
    search_fields = ('client__email', 'chambre__cite__nom')

    def date_avis(self, obj):
        return obj.date_creation.strftime('%d/%m/%Y')
    date_avis.short_description = 'Date'
    date_avis.admin_order_field = 'date_creation'