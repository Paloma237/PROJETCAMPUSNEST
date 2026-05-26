from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur
from .models import ProfilProprietaire

@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    # Les colonnes qui vont s'afficher sur ton écran en tableau
    list_display = ("email", "username", "role", "is_active", "is_staff")
    
    # Rendre le champ 'role' modifiable directement depuis la liste sans ouvrir le profil !
    list_editable = ("role", "is_active")
    
    # Les filtres interactifs sur le panneau de droite (que tu as déjà en partie)
    list_filter = ("role", "is_active", "is_staff", "is_superuser")
    
    # Recherche rapide
    search_fields = ("email", "username", "first_name", "last_name")
    
    # Classement par défaut par rôle, puis par email
    ordering = ("role", "email")

    # Configuration des formulaires de modification dans l'admin
    fieldsets = UserAdmin.fieldsets + (
        ("Informations CampusNest", {"fields": ("role",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Informations CampusNest", {"fields": ("role",)}),
    )
@admin.register(ProfilProprietaire)
class ProprietaireAdmin(admin.ModelAdmin):
    # Les colonnes qui vont s'afficher dans la liste des propriétaires
    list_display = ("utilisateur", "est_valide")
    
    # Rendre la case "est_valide" modifiable directement en un clic dans la liste !
    list_editable = ("est_valide",)
    
    # Ajouter un filtre rapide sur le côté droit
    list_filter = ("est_valide",)
    
    # Permettre la recherche par l'email ou le username de l'utilisateur lié
    search_fields = ("utilisateur__email", "utilisateur__username")