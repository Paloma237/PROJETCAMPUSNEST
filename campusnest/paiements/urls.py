"""
campusnest/paiements/urls.py
"""
from django.urls import path
from . import views

app_name = "paiements"

urlpatterns = [
    path("reserver/<int:reservation_pk>/payer/", views.initier_paiement_view,    name="initier"),
    path("<int:pk>/confirmation/",               views.confirmation_paiement_view, name="confirmation"),
]