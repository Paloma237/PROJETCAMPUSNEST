from django.urls import path
from . import views

app_name = "signalements"

urlpatterns = [

    # ── Étudiant ────────────────────────────────────────────
    path("signaler/<int:chambre_pk>/", views.signaler_logement_view,       name="signaler"),
    path("mes-signalements/",          views.mes_signalements_view, name="mes_signalements"),

    # ── Admin ───────────────────────────────────────────────
    path("",                   views.liste_signalements_view,   name="liste"),
    path("<int:pk>/",          views.detail_signalement_view,  name="detail"),
    path("<int:pk>/traiter/",  views.traiter_signalement_view, name="traiter"),
    path("<int:pk>/cloturer/", views.cloturer_signalement_view, name="cloturer"),
]