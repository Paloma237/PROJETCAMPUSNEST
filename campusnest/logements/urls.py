"""
campusnest/logements/urls.py
"""
from django.urls import path
from . import views

app_name = "logements"

urlpatterns = [

    # ── Public ──────────────────────────────────────────────
    path("",                          views.home_view,          name="home"),
    path("cites/",                    views.liste_cites_view,   name="liste_cites"),
    path("cites/<int:pk>/",           views.detail_cite_view,   name="detail_cite"),
    path("chambres/<int:pk>/",        views.detail_chambre_view, name="detail_chambre"),

    # ── Propriétaire — Cités ────────────────────────────────
    path("mes-cites/",                        views.mes_cites_view,       name="mes_cites"),
    path("mes-cites/ajouter/",                views.ajouter_cite_view,    name="ajouter_cite"),
    path("mes-cites/<int:pk>/modifier/",      views.modifier_cite_view,   name="modifier_cite"),
    path("mes-cites/<int:pk>/supprimer/",     views.supprimer_cite_view,  name="supprimer_cite"),

    # ── Propriétaire — Chambres ─────────────────────────────
    path("mes-cites/<int:cite_pk>/chambres/ajouter/", views.ajouter_chambre_view,      name="ajouter_chambre"),
    path("chambres/<int:pk>/modifier/",               views.modifier_chambre_view,     name="modifier_chambre"),
    path("chambres/<int:pk>/supprimer/",              views.supprimer_chambre_view,    name="supprimer_photo_chambre"),
    path("chambres/<int:pk>/disponibilite/",          views.toggle_disponibilite_view, name="toggle_disponibilite"),
    path("chambres/",                                 views.liste_chambres_view,       name="liste_chambres"),
    # ── Propriétaire — Photos ───────────────────────────────
    #path("photos/<int:pk>/supprimer/",       views.supprimer_photo_view,  name="supprimer_photo"),

    # ── Admin ───────────────────────────────────────────────
    path("admin/liste/",              views.liste_admin_view,             name="liste_admin"),
    path("admin/<int:pk>/supprimer/", views.supprimer_logement_admin_view, name="supprimer_admin"),
  #  path("photos/cite/<int:pk>/supprimer/",    views.supprimer_photo_cite_view,    name="supprimer_photo_cite"),
#path("photos/chambre/<int:pk>/supprimer/", views.supprimer_photo_chambre_view, name="supprimer_photo_chambre"),
]