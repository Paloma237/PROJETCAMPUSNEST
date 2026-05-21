from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from campusnest.global_data.enums import ROLE_CHOICES
from campusnest.users.models import Client, Proprietaire

# Récupérer le modèle User
User = get_user_model()

# ══════════════════════════════════════════════════════════════════
#  VUE D'INSCRIPTION UNIQUE  (étudiant + propriétaire)
# ══════════════════════════════════════════════════════════════════
class InscriptionView(View):
    """
    GET  → affiche le formulaire vide.
    POST → valide manuellement les données POST, crée User
           + Client ou Proprietaire selon le rôle.
    """

    template_name = 'home/authentification/inscription.html'

    # ──────────────────────────────────────────────
    # GET
    # ──────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'role_initial': 'client',
        })

    # ──────────────────────────────────────────────
    # POST
    # ──────────────────────────────────────────────
    def post(self, request):
        data = request.POST

        # ── 1. Récupération des champs ───────────
        role        = data.get('role', 'client').strip()
        username    = data.get('username', '').strip()
        email       = data.get('email', '').strip()
        telephone   = data.get('telephone', '').strip()
        password1   = data.get('password1', '')
        password2   = data.get('password2', '')
        first_name  = data.get('first_name', '').strip()   # prénom (propriétaire)
        last_name   = data.get('last_name', '').strip()    # nom (propriétaire)
        filiere     = data.get('filiere', '').strip()      # étudiant
        niveau      = data.get('niveau', '').strip()       # étudiant

        errors       = []
        field_errors = {}

        # ── 2. Validations communes ──────────────

        if role not in (ROLE_CHOICES.CLIENT, ROLE_CHOICES.PROPRIETAIRE):
            errors.append("Rôle invalide.")

        # Nom d'utilisateur
        if not username:
            field_errors['username'] = "Le nom d'utilisateur est obligatoire."
        elif User.objects.filter(username=username).exists():
            field_errors['username'] = "Ce nom d'utilisateur est déjà pris."

        # Email
        if not email:
            field_errors['email'] = "L'adresse e-mail est obligatoire."
        else:
            try:
                validate_email(email)
            except ValidationError:
                field_errors['email'] = "Adresse e-mail invalide."
            else:
                if User.objects.filter(email=email).exists():
                    field_errors['email'] = "Un compte existe déjà avec cet e-mail."

        # Mots de passe
        if not password1:
            field_errors['password1'] = "Le mot de passe est obligatoire."
        elif password1 != password2:
            field_errors['password2'] = "Les mots de passe ne correspondent pas."
        else:
            try:
                validate_password(password1)
            except ValidationError as exc:
                field_errors['password1'] = exc.messages[0]

        # ── 3. Validations spécifiques au rôle ───
        if role == 'proprietaire':
            if not first_name:
                field_errors['first_name'] = "Le prénom est obligatoire."
            if not last_name:
                field_errors['last_name'] = "Le nom est obligatoire."

        # ── 4. Erreurs → ré-afficher le formulaire
        if errors or field_errors:
            return render(request, self.template_name, {
                'errors'      : errors,
                'field_errors': field_errors,
                'form_data'   : data,
            })

        # ── 5. Création de l'utilisateur ─────────
        utilisateur = User.objects.create_user(
            username   = username,
            email      = email,
            password   = password1,
            role       = role,
            telephone  = telephone or None,
            first_name = first_name or None,
            last_name  = last_name or None,
        )

        # ── 6. Création du profil selon le rôle ──
        if role == 'client':
            Client.objects.create(
                utilisateur = utilisateur,  # ← champ correct : utilisateur
                filiere = filiere or None,
                niveau = niveau or None,
            )
        else:  # proprietaire
            Proprietaire.objects.create(
                utilisateur = utilisateur,  # ← champ correct : utilisateur
                # piece_identite sera ajouté plus tard si nécessaire
                # verifie est False par défaut
            )

        # ── 7. Succès → redirection ───────────────
        messages.success(
            request,
            f"Compte créé avec succès ! Bienvenue, {username}. "
            "Vous pouvez maintenant vous connecter."
        )
        return redirect('users:connexion')
    