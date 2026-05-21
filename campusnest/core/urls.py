# from django.urls import path
# from campusnest.core.views.accueil_view import ListeCitesView
# from campusnest.users.views.pageAcceuil_views import AccueilView
# #from campusnest.core.views.detail_chambre_view import DetailChambreView
# from campusnest.core.views.liste_chambre_view  import ListeCambreView
# from campusnest.core.views.detail_cite_view    import DetailCiteView

# from campusnest.core.views.proprietaire_view  import (
#     MesCitesView,
#     CreerCiteView,
#     AjouterChambreView,
# )

# app_name = "core"

# urlpatterns = [
#     # ── Public ──────────────────────────────────────────
#     path('',          ListeCambreView.as_view(),  name='liste_chambres'),
#    # path('chambres/<uuid:pk>/', DetailChambreView.as_view(), name='detail_chambre'),
#     path('cites/<uuid:pk>/',    DetailCiteView.as_view(),    name='detail_cite'),

#     # ── Espace propriétaire ─────────────────────────────
#     path('proprietaire/cites/',
#          MesCitesView.as_view(),   name='mes_cites'),
#     path('proprietaire/cites/creer/',
#          CreerCiteView.as_view(),  name='creer_cite'),
#     path('proprietaire/cites/<uuid:cite_pk>/ajouter-chambre/',
#          AjouterChambreView.as_view(), name='ajouter_chambre'),
#     path('liste_cite',ListeCitesView.as_view(),name='liste_chambres')
# ]