from django.urls import path
from campusnest.favoris import views

app_name = "favoris"

urlpatterns = [
    path("toggle/<int:chambre_pk>/", views.toggle_favori_view, name="toggle"),
    path("mes-favoris/",             views.mes_favoris_view,   name="mes_favoris"),
]