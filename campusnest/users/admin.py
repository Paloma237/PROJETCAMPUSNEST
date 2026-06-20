from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# 1. Importation de tes modèles de l'application 'users'
from .models import Utilisateur, ProfilProprietaire, OTPCode, LogActivite



@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    """Configuration de l'affichage des utilisateurs personnalisés"""
    list_display = ('email', 'nom', 'prenom', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'nom', 'prenom', 'telephone')
    ordering = ('email',)
    
    # Desactiver le champ username s'il n'est pas utilisé
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('nom', 'prenom', 'telephone', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'role', 'password'),
        }),
    )


# APRÈS
@admin.register(ProfilProprietaire)
class ProfilProprietaireAdmin(admin.ModelAdmin):
    list_display  = ["utilisateur", "apercu_piece", "est_valide", "date_validation"]
    readonly_fields = ["apercu_piece_recto", "apercu_piece_verso"]

    @admin.display(description="Pièce d'identité")
    def apercu_piece(self, obj):
        from django.utils.html import format_html
        liens = []
        if obj.piece_identite_recto:
            liens.append(format_html('<a href="{}" target="_blank">Recto</a>', obj.piece_identite_recto.url))
        if obj.piece_identite_verso:
            liens.append(format_html('<a href="{}" target="_blank">Verso</a>', obj.piece_identite_verso.url))
        return format_html(" · ".join(str(l) for l in liens)) if liens else "—"

    @admin.display(description="Recto")
    def apercu_piece_recto(self, obj):
        from django.utils.html import format_html
        if obj.piece_identite_recto:
            return format_html('<img src="{}" style="max-height:200px;border-radius:8px"/>', obj.piece_identite_recto.url)
        return "—"

    @admin.display(description="Verso")
    def apercu_piece_verso(self, obj):
        from django.utils.html import format_html
        if obj.piece_identite_verso:
            return format_html('<img src="{}" style="max-height:200px;border-radius:8px"/>', obj.piece_identite_verso.url)
        return "—"
    list_filter = ('est_valide',)
    search_fields = ('utilisateur__email', 'utilisateur__nom', 'numero_piece')
    actions = ['valider_profils']

    @admin.action(description="Valider les profils sélectionnés")
    def valider_profils(self, request, queryset):
        for profil in queryset:
            profil.valider()


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'code', 'cree_le', 'utilise', 'est_expire')
    list_filter = ('utilise',)
    search_fields = ('utilisateur__email', 'code')


@admin.register(LogActivite)
class LogActiviteAdmin(admin.ModelAdmin):
    # CORRECTION ICI : On utilise 'date' à la place de 'timestamp'
    list_display = ('utilisateur', 'action', 'date', 'adresse_ip')
    list_filter = ('action', 'date')
    ordering = ('-date',)
    readonly_fields = ('utilisateur', 'action', 'detail', 'adresse_ip', 'date')

