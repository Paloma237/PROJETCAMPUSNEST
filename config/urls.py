"""
campusnest/urls.py  —  URLs globales du projet CampusNest IUT-FV
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from django.views import defaults as default_views


urlpatterns = [
    # ─── Racine : redirige vers la page d'accueil ────────────────
    path("", include("campusnest.logements.urls", namespace="logements")),               # home = liste des cités
    
        # ─── Admin Django ────────────────────────────────────────────
    path("admin/", admin.site.urls),

    # ─── Authentification ────────────────────────────────────────
    path("comptes/", include("campusnest.users.urls", namespace="users")),
    
    # ─── Réservations ────────────────────────────────────────────
    path("reservations/", include("campusnest.reservations.urls", namespace="reservations")),

     # ─── Avis ────────────────────────────────────────────────────
    path("avis/", include("campusnest.avis.urls", namespace="avis")),

    # ─── Signalements ────────────────────────────────────────────
    path("signalements/", include("campusnest.signalements.urls", namespace="signalements")),

    # ─── Contact ─────────────────────────────────────────────────
    path("contact/", include("campusnest.contact.urls", namespace="contact")),
    
    # ─── Favoris ─────────────────────────────────────────────────
    path("favoris/", include("campusnest.favoris.urls", namespace="favoris")),
    
    # ─── Paiements ───────────────────────────────────────────────
    path("paiements/", include("campusnest.paiements.urls", namespace="paiements")),
]

# ─── Servir les fichiers media en développement ──────────────────
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
            *urlpatterns,
        ]
