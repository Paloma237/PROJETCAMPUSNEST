from django.urls import path
from . import views

app_name = "contact"

urlpatterns = [
    # Contact général
    path("", views.contact_view, name="contact"),

    # Client ↔ Propriétaire
    path(
        "proprio/<int:proprietaire_pk>/chambre/<int:chambre_pk>/",
        views.contacter_proprietaire_view,
        name="contacter_proprietaire",
    ),
    path(
        "conversation/<int:pk>/",
        views.conversation_view,
        name="conversation",
    ),

    # Liste messages (client & propriétaire)
    path("mes-messages/", views.mes_messages_view, name="mes_messages"),

    # Admin
    path("admin/tous/",              views.tous_messages_admin_view, name="tous_messages_admin"),
    path("admin/<int:pk>/repondre/", views.repondre_message_view,    name="repondre_message"),
]