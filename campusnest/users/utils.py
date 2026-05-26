# campusnest/users/utils.py

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from campusnest.users.models import LogActivite, Utilisateur


# ─────────────────────────────────────────────
#  Journalisation
# ─────────────────────────────────────────────

def enregistrer_log(request, utilisateur, action, detail=""):
    """Enregistre une action dans le journal d'activité."""
    LogActivite.objects.create(
        utilisateur=utilisateur,
        action=action,
        detail=detail,
        adresse_ip=_get_ip(request),
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
    """Restreint une vue à certains rôles."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# Raccourcis
admin_requis        = role_requis(Utilisateur.Role.ADMIN)
proprietaire_requis = role_requis(Utilisateur.Role.PROPRIETAIRE)
client_requis       = role_requis(Utilisateur.Role.CLIENT)


# ─────────────────────────────────────────────
#  Propriétaire validé uniquement
# ─────────────────────────────────────────────

def proprietaire_valide_requis(view_func):
    """Refuse l'accès si le propriétaire n'est pas encore validé par l'admin."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user

        # 1. Doit être propriétaire
        if user.role != Utilisateur.Role.PROPRIETAIRE:
            raise PermissionDenied

        # 2. Vérifier la validation — related_name correct : profil_proprietaire
        try:
            est_valide = user.profil_proprietaire.est_valide  # ✅ underscore
        except Exception:
            est_valide = False

        if not est_valide:
            return redirect("users:validation_en_attente")

        return view_func(request, *args, **kwargs)

    return wrapper