from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from .models import LogActivite, Utilisateur


# ─────────────────────────────────────────────
#  Journalisation
# ─────────────────────────────────────────────

def enregistrer_log(request, utilisateur, action, detail=""):
    """Enregistre une action dans le journal d'activité."""
    adresse_ip = _get_ip(request)
    LogActivite.objects.create(
        utilisateur=utilisateur,
        action=action,
        detail=detail,
        adresse_ip=adresse_ip,
    )


def _get_ip(request):
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


# ─────────────────────────────────────────────
#  Décorateurs de rôle
# ─────────────────────────────────────────────

def role_requis(*roles):
    """
    Décorateur qui restreint une vue à certains rôles.

    Usage :
        @role_requis(Utilisateur.Role.ADMIN)
        def ma_vue(request): ...

        @role_requis(Utilisateur.Role.ADMIN, Utilisateur.Role.PROPRIETAIRE)
        def autre_vue(request): ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# Raccourcis pratiques
admin_requis       = role_requis(Utilisateur.Role.ADMIN)
proprietaire_requis = role_requis(Utilisateur.Role.PROPRIETAIRE)
client_requis      = role_requis(Utilisateur.Role.CLIENT)

# Propriétaire validé uniquement
def proprietaire_valide_requis(view_func):
    """Refuse l'accès si le propriétaire n'est pas encore validé par l'admin."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        if user.role != Utilisateur.Role.PROPRIETAIRE:
            raise PermissionDenied
        try:
            if not user.proprietaire.est_valide:
                return redirect("accounts:validation_en_attente")
        except Exception:
            return redirect("accounts:validation_en_attente")
        return view_func(request, *args, **kwargs)
    return wrapper