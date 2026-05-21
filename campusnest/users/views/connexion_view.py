from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache


# ──────────────────────────────────────────
# VUE : CONNEXION
# ──────────────────────────────────────────

class ConnexionView(View):
    """
    Gère la connexion des utilisateurs (étudiant, propriétaire, admin).
    Méthode GET  → affiche le formulaire de connexion.
    Méthode POST → valide les identifiants et redirige selon le rôle.
    """

    template_name = 'home/authentification/connexion.html'

    def get(self, request):
        # Si l'utilisateur est déjà connecté, on le redirige directement
        if request.user.is_authenticated:
            return self._redirect_selon_role(request.user)

        return render(request, self.template_name, self._context())

    def post(self, request):
        email    = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        # ── Validation basique des champs ──
        errors = {}

        if not email:
            errors['email'] = "L'adresse e-mail est obligatoire."
        if not password:
            errors['password'] = "Le mot de passe est obligatoire."

        if errors:
            return render(request, self.template_name, self._context(
                errors=errors,
                email=email,
            ))

        # ── Authentification ──
        utilisateur = authenticate(request, username=email, password=password)

        if utilisateur is None:
            errors['global'] = "Adresse e-mail ou mot de passe incorrect."
            return render(request, self.template_name, self._context(
                errors=errors,
                email=email,
            ))

        # ── Vérification que le compte est actif ──
        if not utilisateur.is_active:
            errors['global'] = "Votre compte est désactivé. Contactez l'administration."
            return render(request, self.template_name, self._context(
                errors=errors,
                email=email,
            ))

        # ── Connexion réussie ──
        login(request, utilisateur)
        messages.success(request, f"Bienvenue, {utilisateur.first_name or utilisateur.email} !")

        # Redirection vers la page demandée avant la connexion (si elle existe)
        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)

        return self._redirect_selon_role(utilisateur)

    # ── Helpers privés ──────────────────────────────────────────────────────

    def _context(self, errors=None, email=''):
        """Construit le contexte envoyé au template."""
        return {
            'form': {
                'email': type('Field', (), {
                    'value': lambda self=None: email,
                    'errors': [errors.get('email')] if errors and errors.get('email') else [],
                })(),
                'password': type('Field', (), {
                    'errors': [errors.get('password')] if errors and errors.get('password') else [],
                })(),
            },
            'error_global': errors.get('global') if errors else None,
        }

    @staticmethod
    def _redirect_selon_role(utilisateur):
        """Redirige l'utilisateur vers son tableau de bord selon son rôle."""
        if utilisateur.is_admin:
            return redirect('admin:index')
        elif utilisateur.est_proprietaire():
            return redirect('proprietaire:dashboard')
        else:
            # client / étudiant (rôle par défaut)
            return redirect('users:accueil')


# ──────────────────────────────────────────
# VUE : DÉCONNEXION
# ──────────────────────────────────────────

class DeconnexionView(View):
    """
    Déconnecte l'utilisateur et le redirige vers la page de connexion.
    On accepte uniquement POST pour éviter les déconnexions involontaires
    via une simple URL (bonne pratique CSRF).
    """

    def post(self, request):
        logout(request)
        messages.info(request, "Vous avez été déconnecté avec succès.")
        return redirect('users:connexion')

    # Fallback GET (cas d'un lien direct) — moins sécurisé mais pratique en dev
    def get(self, request):
        logout(request)
        return redirect('users:connexion')