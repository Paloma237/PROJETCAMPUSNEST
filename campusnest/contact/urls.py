from django.urls import path
from . import views

app_name = "contact"

urlpatterns = [

    # ── Public ──────────────────────────────────────────────
    path("",                                   views.contact_view,               name="contact"),

    # ── Étudiant ────────────────────────────────────────────
    path("proprio/<int:proprio_pk>/",          views.contacter_proprietaire_view,     name="contacter_proprio"),
    path("mes-messages/",                      views.mes_messages_view,          name="mes_messages"),
    path("messages-envoyes/",                  views.messages_envoyes_view,      name="messages_envoyes"),
    path("message/<int:pk>/",                  views.detail_message_view,        name="detail"),

    # ── Admin ───────────────────────────────────────────────
    path("admin/tous/",              views.tous_messages_admin_view,  name="tous"),
    path("admin/<int:pk>/repondre/", views.repondre_message_view,       name="repondre"),
]