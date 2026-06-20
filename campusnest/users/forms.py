from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Utilisateur


CSS = (
    "w-full px-3 py-2.5 text-base border border-gray-200 rounded-xl bg-gray-50 "
    "focus:outline-none focus:ring-2 focus:ring-secondary/50 "
    "focus:border-secondary transition"
)

# Extensions et taille max autorisées pour les pièces d'identité
EXTENSIONS_PIECE = ["jpg", "jpeg", "png", "pdf"]
TAILLE_MAX_PIECE = 5 * 1024 * 1024  # 5 Mo


def _valider_piece_identite(fichier):
    """Validateur partagé pour recto et verso."""
    if fichier:
        ext = fichier.name.rsplit(".", 1)[-1].lower()
        if ext not in EXTENSIONS_PIECE:
            raise ValidationError("Format non accepté. Utilisez JPG, PNG ou PDF.")
        if fichier.size > TAILLE_MAX_PIECE:
            raise ValidationError("Le fichier dépasse la taille maximale de 5 Mo.")
    return fichier


# ─── Connexion ───────────────────────────────────────────────────────────────

class ConnexionForm(AuthenticationForm):
    username = forms.EmailField(
        label="Adresse email",
        widget=forms.EmailInput(attrs={
            "placeholder": "votre@email.cm", "class": CSS, "autofocus": True,
        }),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••", "class": CSS}),
    )
    error_messages = {
        "invalid_login": "Email ou mot de passe incorrect.",
        "inactive": "Ce compte est désactivé.",
    }


# ─── Inscription étudiant ─────────────────────────────────────────────────────

class InscriptionClientForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••", "class": CSS}),
    )
    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••", "class": CSS}),
    )

    class Meta:
        model  = Utilisateur
        fields = ["email", "telephone"]
        widgets = {
            "email":     forms.EmailInput(attrs={"class": CSS, "placeholder": "votre@email.cm"}),
            "telephone": forms.TextInput(attrs={"class": CSS, "placeholder": "6XX XXX XXX"}),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if Utilisateur.objects.filter(email=email).exists():
            raise ValidationError("Cette adresse email est déjà utilisée.")
        return email

    def clean_password1(self):
        p = self.cleaned_data.get("password1")
        validate_password(p)
        return p

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            self.add_error("password2", "Les mots de passe ne correspondent pas.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = Utilisateur.Role.CLIENT
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


# ─── Inscription propriétaire ─────────────────────────────────────────────────

class InscriptionProprietaireForm(InscriptionClientForm):
    """
    Étend le formulaire étudiant avec l'upload recto + verso de la pièce d'identité.
    Le champ texte `numero_piece` est remplacé par deux ImageField.
    """
    piece_identite_recto = forms.FileField(
        label="Recto de la pièce d'identité",
        required=True,
        error_messages={
            "required": "Veuillez fournir le recto de votre pièce d'identité.",
        },
        widget=forms.FileInput(attrs={"class": "hidden", "accept": "image/jpeg,image/png,application/pdf"}),
    )
    piece_identite_verso = forms.FileField(
        label="Verso de la pièce d'identité",
        required=True,
        error_messages={
            "required": "Veuillez fournir le verso de votre pièce d'identité.",
        },
        widget=forms.FileInput(attrs={"class": "hidden", "accept": "image/jpeg,image/png,application/pdf"}),
    )

    def clean_piece_identite_recto(self):
        return _valider_piece_identite(self.cleaned_data.get("piece_identite_recto"))

    def clean_piece_identite_verso(self):
        return _valider_piece_identite(self.cleaned_data.get("piece_identite_verso"))

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = Utilisateur.Role.PROPRIETAIRE
        if commit:
            user.save()
            # Correction : ProfilProprietaire (et non Proprietaire)
            from .models import ProfilProprietaire
            ProfilProprietaire.objects.update_or_create(
                utilisateur=user,
                defaults={
                    "piece_identite_recto": self.cleaned_data["piece_identite_recto"],
                    "piece_identite_verso": self.cleaned_data["piece_identite_verso"],
                    "est_valide": False,
                },
            )
        return user


# ─── Mot de passe oublié — étape 1 ───────────────────────────────────────────

class MotDePasseOublieForm(forms.Form):
    email = forms.EmailField(
        label="Adresse email",
        widget=forms.EmailInput(attrs={"class": CSS, "placeholder": "votre@email.cm"}),
    )


# ─── Vérification OTP — étape 2 ──────────────────────────────────────────────

class VerifierOTPForm(forms.Form):
    code = forms.CharField(
        label="Code de vérification",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            "class": (
                "w-full px-4 py-4 text-center text-3xl font-mono tracking-[0.5em] "
                "border border-gray-200 rounded-xl bg-gray-50 "
                "focus:outline-none focus:ring-2 focus:ring-secondary/50 "
                "focus:border-secondary transition"
            ),
            "placeholder": "000000",
            "inputmode": "numeric",
            "pattern": "[0-9]{6}",
            "autocomplete": "one-time-code",
            "autofocus": True,
        }),
    )

    def clean_code(self):
        code = self.cleaned_data.get("code", "").strip()
        if not code.isdigit():
            raise ValidationError("Le code doit contenir uniquement des chiffres.")
        if len(code) != 6:
            raise ValidationError("Le code doit contenir exactement 6 chiffres.")
        return code


# ─── Nouveau mot de passe — étape 3 ──────────────────────────────────────────

class NouveauMotDePasseForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={"class": CSS, "placeholder": "••••••••"}),
        help_text="",
    )
    new_password2 = forms.CharField(
        label="Confirmer le nouveau mot de passe",
        widget=forms.PasswordInput(attrs={"class": CSS, "placeholder": "••••••••"}),
    )


# ─── Modifier profil ──────────────────────────────────────────────────────────

class ModifierProfilForm(forms.ModelForm):
    class Meta:
        model  = Utilisateur
        fields = ["nom", "prenom", "telephone"]
        widgets = {
            "nom":       forms.TextInput(attrs={"class": CSS}),
            "prenom":    forms.TextInput(attrs={"class": CSS}),
            "telephone": forms.TextInput(attrs={"class": CSS}),
        }