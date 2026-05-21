from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
 
from .models import Utilisateur
 
 
CSS = (
    "w-full px-3 py-2.5 text-sm border border-gray-200 rounded-xl bg-gray-50 "
    "focus:outline-none focus:ring-2 focus:ring-secondary/50 "
    "focus:border-secondary transition"
)
 
 
# ─── Connexion ───────────────────────────────
 
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
 
 
# ─── Inscription étudiant ────────────────────
 
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
 
 
# ─── Inscription propriétaire ────────────────
 
class InscriptionProprietaireForm(InscriptionClientForm):
    numero_piece = forms.CharField(
        label="Numéro de pièce d'identité", max_length=50,
        widget=forms.TextInput(attrs={"class": CSS, "placeholder": "CNI / Passeport"}),
    )
 
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = Utilisateur.Role.PROPRIETAIRE
        if commit:
            user.save()
            from .models import Proprietaire
            Proprietaire.objects.update_or_create(
                pk=user.pk,
                defaults={"numero_piece": self.cleaned_data["numero_piece"], "est_valide": False},
            )
        return user
 
 
# ─── Mot de passe oublié — étape 1 ──────────
 
class MotDePasseOublieForm(forms.Form):
    email = forms.EmailField(
        label="Adresse email",
        widget=forms.EmailInput(attrs={"class": CSS, "placeholder": "votre@email.cm"}),
    )
 
 
# ─── Vérification OTP — étape 2  ← NOUVEAU ──
 
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
 
 
# ─── Nouveau mot de passe — étape 3 ─────────
 
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
 
 
# ─── Modifier profil ─────────────────────────
 
class ModifierProfilForm(forms.ModelForm):
    class Meta:
        model  = Utilisateur
        fields = ["nom", "prenom", "telephone"]
        widgets = {
            "nom":       forms.TextInput(attrs={"class": CSS}),
            "prenom":    forms.TextInput(attrs={"class": CSS}),
            "telephone": forms.TextInput(attrs={"class": CSS}),
        }
