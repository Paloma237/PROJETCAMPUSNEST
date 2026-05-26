from django.urls import path
from . import views
 
app_name = "users"

urlpatterns = [
    # Auth
    path("connexion/",   views.connexion_view,   name="connexion"),
    path("deconnexion/", views.deconnexion_view, name="deconnexion"),
    path("inscription/", views.inscription_view, name="inscription"),

    # Reset mot de passe — flux OTP en 3 étapes
    path("mot-de-passe-oublie/", views.mot_de_passe_oublie_view, name="mot_de_passe_oublie"),
    path("verifier-otp/",        views.verifier_otp_view,        name="verifier_otp"),
    path("renvoyer-otp/",        views.renvoyer_otp_view,        name="renvoyer_otp"),
    path("nouveau-mot-de-passe/", views.nouveau_mot_de_passe_view, name="nouveau_mot_de_passe"),

    # Validation propriétaire
    path("inscription/verifier-email/", views.verifier_otp_inscription_view, name="verifier_otp_inscription"),
    path("inscription/renvoyer-otp/", views.renvoyer_otp_inscription_view, name="renvoyer_otp_inscription"),
    path("validation-en-attente/", views.validation_en_attente_view, name="validation_en_attente"),

    # Profil & dashboards
    path("profil/",                  views.profil_view,                 name="profil"),
    path("dashboard/",               views.dashboard_view,              name="dashboard"),
    path("dashboard/client/",        views.client_dashboard_view,       name="client_dashboard"),
    path("dashboard/proprietaire/",  views.proprietaire_dashboard_view, name="proprietaire_dashboard"),
    path("dashboard/admin/",         views.admin_dashboard_view,        name="admin_dashboard"),

    # Actions admin
    path("valider/<int:pk>/",   views.valider_proprietaire_view, name="valider_proprietaire"),
    path("suspendre/<int:pk>/", views.suspendre_compte_view,     name="suspendre_compte"),
]
