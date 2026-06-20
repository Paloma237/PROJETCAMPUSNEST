import random
import string
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Utilisateur(AbstractUser):
    """
    Hérite d'AbstractUser (cookiecutter-django default).
    allauth gère la connexion via email.
    On désactive username, on ajoute rôle + téléphone.
    """
    class Role(models.TextChoices):
        ADMIN        = "admin",        "Administrateur"
        PROPRIETAIRE = "proprietaire", "Propriétaire de cité"
        CLIENT       = "client",       "Étudiant"

    # AbstractUser a déjà : first_name, last_name, email, is_active, is_staff...
    # On ajoute :
    nom       = models.CharField("Nom", max_length=100, blank=True, default="")
    prenom    = models.CharField("Prénom", max_length=100, blank=True)
    telephone = models.CharField("Téléphone", max_length=20, blank=True)
    role      = models.CharField(
        "Rôle", max_length=20,
        choices=Role.choices,
        default=Role.CLIENT,
    )

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}>"

    def get_full_name(self):
        if self.prenom and self.nom:
            return f"{self.prenom} {self.nom}"
        return super().get_full_name() or self.email

    def get_initials(self):
        """
        Retourne les initiales selon la logique:
        - Si prénom ET nom: 1ère lettre du prénom (maj) + 1ère lettre du nom (maj)
        - Si seulement nom: 1ère lettre du nom (maj) + 2ème lettre du nom (min)
        - Sinon: 1ère lettre de l'email (maj)
        """
        if self.prenom and self.nom:
            return f"{self.prenom[0].upper()}{self.nom[0].upper()}"
        elif self.nom:
            name = self.nom.strip()
            if len(name) >= 2:
                return f"{name[0].upper()}{name[1].lower()}"
            return name[0].upper()
        return self.email[0].upper() if self.email else "?"

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"pk": self.pk})

    @property
    def est_proprietaire(self): return self.role == self.Role.PROPRIETAIRE
    @property
    def est_client(self):       return self.role == self.Role.CLIENT
    @property
    def est_admin(self):        return self.role == self.Role.ADMIN


class ProfilProprietaire(models.Model):
    """Informations complémentaires du propriétaire. Créé via signal post_save."""
    utilisateur = models.OneToOneField(
        Utilisateur, on_delete=models.CASCADE,
        related_name="profil_proprietaire",
    )
    # ── Pièce d'identité (recto + verso) ──────────────────────────
    # Remplace l'ancien champ texte `numero_piece`.
    # Les fichiers sont stockés dans media/pieces_identite/recto/ et /verso/
    piece_identite_recto = models.ImageField(
        "Recto pièce d'identité",
        upload_to="pieces_identite/recto/",
        blank=True,
    )
    piece_identite_verso = models.ImageField(
        "Verso pièce d'identité",
        upload_to="pieces_identite/verso/",
        blank=True,
    )
    # ──────────────────────────────────────────────────────────────
    est_valide      = models.BooleanField("Validé par l'admin", default=False)
    date_validation = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name        = "Profil propriétaire"
        verbose_name_plural = "Profils propriétaires"

    def __str__(self):
        return f"Profil — {self.utilisateur.get_full_name()}"

    def valider(self):
        self.est_valide      = True
        self.date_validation = timezone.now()
        self.save(update_fields=["est_valide", "date_validation"])

    def suspendre(self):
        self.est_valide            = False
        self.utilisateur.is_active = False
        self.utilisateur.save(update_fields=["is_active"])
        self.save(update_fields=["est_valide"])


class OTPCode(models.Model):
    """Code à 6 chiffres pour le reset mot de passe."""
    OTP_EXPIRY_MINUTES = 10

    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, related_name="otp_codes",
    )
    code    = models.CharField(max_length=6)
    cree_le = models.DateTimeField(auto_now_add=True)
    utilise = models.BooleanField(default=False)

    class Meta:
        verbose_name        = "Code OTP"
        verbose_name_plural = "Codes OTP"
        ordering            = ["-cree_le"]

    def __str__(self):
        return f"OTP {self.code} — {self.utilisateur.email}"

    @property
    def est_expire(self):
        return timezone.now() > self.cree_le + timedelta(minutes=self.OTP_EXPIRY_MINUTES)

    @property
    def est_valide(self):
        return not self.utilise and not self.est_expire

    def marquer_utilise(self):
        self.utilise = True
        self.save(update_fields=["utilise"])

    @classmethod
    def generer_pour(cls, utilisateur):
        cls.objects.filter(utilisateur=utilisateur, utilise=False).update(utilise=True)
        code = "".join(random.choices(string.digits, k=6))
        return cls.objects.create(utilisateur=utilisateur, code=code)


class LogActivite(models.Model):
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="logs",
    )
    action     = models.CharField(max_length=255)
    detail     = models.TextField(blank=True)
    adresse_ip = models.GenericIPAddressField(null=True, blank=True)
    date       = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Log d'activité"
        verbose_name_plural = "Logs d'activité"
        ordering            = ["-date"]

    def __str__(self):
        u = str(self.utilisateur) if self.utilisateur else "Anonyme"
        return f"[{self.date:%d/%m/%Y %H:%M}] {u} — {self.action}"