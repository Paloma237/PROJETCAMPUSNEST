from django.contrib import admin
from django.template.defaultfilters import truncatechars
from .models import Cite, Chambre, PhotoCity, PhotoChambre

# ==============================================================================
# CONFIGURATION DES PHOTOS EN INLINE (IMBRIQUÉES)
# ==============================================================================

class PhotoCityInline(admin.TabularInline):
    model = PhotoCity
    fk_name = 'city'  # Indique explicitement à Django d'utiliser le champ 'city'
    extra = 1
    fields = ('image', 'legende', 'est_principale')


class PhotoChambreInline(admin.TabularInline):
    model = PhotoChambre
    extra = 1
    fields = ('image', 'legende', 'est_principale')

@admin.register(Cite)
class CiteAdmin(admin.ModelAdmin):
    list_display = ('nom', 'adresse', 'proprietaire', 'est_actif')
    list_editable = ('est_actif',)
    list_filter = ('est_actif', 'adresse', 'date_creation')
    search_fields = ('nom', 'adresse', 'proprietaire__email', 'proprietaire__nom')
    inlines = [PhotoCityInline]
    
    fieldsets = (
        ("Informations Générales", {
            'fields': ('nom', 'proprietaire', 'adresse', 'description')
        }),
        ("Géolocalisation", {
            'fields': ('latitude', 'longitude'),
            'classes': ('collapse',)
        }),
        ("Modération & Statut (Suppression douce)", {
            'fields': ('est_actif', 'motif_suppression'),
            'description': "Pour suspendre cette cité, décochez 'Est actif' et expliquez pourquoi au propriétaire."
        }),
    )


from django.template.defaultfilters import truncatechars # À ajouter si tu choisis cette option

@admin.register(Chambre)
class ChambreAdmin(admin.ModelAdmin):
    list_display = ('id', 'cite', 'type', 'loyer', 'apercu_description', 'est_disponible', 'est_actif')
    list_editable = ('est_actif', 'est_disponible')
    list_filter = ('est_actif', 'est_disponible', 'type', 'etat', 'cite__nom')
    search_fields = ('cite__nom', 'type', 'description')
    inlines = [PhotoChambreInline]
    
    fieldsets = (
        ("Liaison", {
            'fields': ('cite',)
        }),
        ("Caractéristiques de la Chambre", {
            'fields': ('type', 'loyer', 'superficie', 'etat', 'est_disponible', 'description')
        }),
        ("Équipements & Commodités", {
            'fields': ('meublee', 'wc_interieur', 'cuisine', 'internet', 'eau_courante', 'electricite'),
            'classes': ('wide',)
        }),
        ("Modération & Statut", {
            'fields': ('est_actif', 'motif_suppression'),
        }),
    )
    @admin.display(description="Description")
    def apercu_description(self, obj):
        return truncatechars(obj.description, 50)

@admin.register(PhotoCity)
class PhotoCityAdmin(admin.ModelAdmin):
    list_display = ('id', 'city', 'image', 'est_principale')
    list_filter = ('est_principale', 'city')


@admin.register(PhotoChambre)
class PhotoChambreAdmin(admin.ModelAdmin):
    list_display = ('id', 'chambre', 'image', 'est_principale')
    list_filter = ('est_principale', 'chambre__cite')