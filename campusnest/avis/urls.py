"""
campusnest/avis/urls.py
"""
from django.urls import path
from . import views
from campusnest.avis import views

app_name = "avis"

urlpatterns = [

    # ── Étudiant ────────────────────────────────────────────
    path("chambre/<int:chambre_pk>/laisser/", views.laisser_avis_view,  name="laisser"),
    path("<int:pk>/supprimer/",               views.supprimer_avis_view, name="supprimer"),

    # ── Admin ───────────────────────────────────────────────
    path("admin/",                    views.liste_avis_admin_view,          name="liste_admin"),
    path("admin/<int:pk>/moderer/",   views.moderer_avis_view,              name="moderer"),
    path("admin/<int:pk>/publier/",   views.publier_avis_view,              name="publier"),
    path("admin/<int:pk>/supprimer/", views.supprimer_avis_admin_view,      name="supprimer_admin"),
    
    # ── Vues propriétaire (NOUVELLES) ──
    path("mes-avis/",                 views.liste_avis_proprietaire_view, name="liste_proprietaire"),
    path("signaler/<int:pk>/",        views.signaler_avis_view,           name="signaler"),

]
