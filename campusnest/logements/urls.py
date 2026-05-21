from django.urls import path
from . import views

app_name = "logements"

urlpatterns = [
    # Assurez-vous que c'est bien views.home_view et RIEN d'autre !
    path("", views.home_view, name="home"),
    
    path("cites/", views.liste_cites_view, name="liste_cites"),
    path("cites/<int:pk>/", views.detail_cite_view, name="detail_cite"),
    # ... le reste de vos URLs
]