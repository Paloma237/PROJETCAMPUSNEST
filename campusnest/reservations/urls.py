from django.urls import path
from . import views

app_name = "reservations"

urlpatterns = [
    # ── Étudiant ─────────────────────────────────────────────────────
    path("reserver/<int:chambre_pk>/",  views.reserver_view,                   name="reserver"),
    path("mes-reservations/",           views.mes_reservations_view,            name="mes_reservations"),
    path("<int:pk>/",                   views.detail_reservation_view,          name="detail"),
    path("<int:pk>/annuler/",           views.annuler_reservation_client_view,  name="annuler_client"),

    # ── Propriétaire ─────────────────────────────────────────────────
    path("recues/",                     views.reservations_recues_view,         name="recues"),
    path("<int:pk>/traiter/",           views.traiter_reservation_view,         name="traiter"),
    path("<int:pk>/annuler-proprio/",   views.annuler_reservation_proprio_view, name="annuler_proprio"),
    path("historique/",                 views.historique_reservations_view,     name="historique"),

    # ── Admin ─────────────────────────────────────────────────────────
    path("admin/toutes/",               views.toutes_reservations_view,         name="toutes"),
]