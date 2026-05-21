
# from typing import ClassVar
# from django.db import models

# from django.contrib.auth.models import AbstractUser
# from django.urls import reverse
# from django.utils.translation import gettext_lazy as _

# from campusnest.global_data.enums import ROLE_CHOICES
# from campusnest.core.models import BaseModel

# from .managers import UserManager

# class User(AbstractUser, BaseModel):
#     """
#     Custom user model with additional fields for CampusNest.
#     """
#     role = models.CharField(
#         max_length=20,
#         choices=ROLE_CHOICES.choices,
#         default=ROLE_CHOICES.CLIENT,
#         verbose_name="Rôle",
#         help_text="Rôle de l'utilisateur dans l'application"
#     )
#     email = models.EmailField(unique=True)
#     telephone = models.CharField(max_length=20, blank=True, null=True)
#     first_name = models.CharField(max_length=200, blank=True, null=True)
#     last_name = models.CharField(max_length=200, blank=True, null=True)
#     photo_profil = models.ImageField(upload_to='profils/', blank=True, null=True)
    
#     objects: ClassVar[UserManager] = UserManager()

#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = []

#     def __str__(self):
#         return f"{self.email} ({self.get_role_display()})"

#     def est_client(self):
#         return self.role == ROLE_CHOICES.CLIENT

#     def est_proprietaire(self):
#         return self.role == ROLE_CHOICES.PROPRIETAIRE
    
#     def save(self, *args, **kwargs):
#         # Les superusers sont toujours admin
#         if self.is_superuser:
#             self.role = 'admin'
#             self.is_staff = True
#         super().save(*args, **kwargs)
    
#     @property
#     def is_admin(self):
#         """Propriété pour vérifier si l'utilisateur est admin"""
#         return self.role == 'admin' or self.is_superuser
    
#     def has_admin_access(self):
#         """Vérifie l'accès à l'interface admin Django"""
#         return self.is_superuser or self.role == 'admin'


# class Client(BaseModel):
#     utilisateur = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil_client')
#     filiere = models.CharField(max_length=100, blank=True, null=True)
#     niveau = models.CharField(max_length=20, blank=True, null=True)
#     universite = models.CharField(max_length=150, default='IUT-FV Bandjoun')

#     def __str__(self):
#         return f"Étudiant : {self.User.email}"


# class Proprietaire(BaseModel):
#     utilisateur = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil_proprietaire')
#     piece_identite = models.FileField(upload_to='pieces_identite/', blank=True, null=True)
#     verifie = models.BooleanField(default=False)

#     def __str__(self):
#         return f"Propriétaire : {self.User.get_full_name()}"

import random
import string
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from datetime import timedelta
 



class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", Utilisateur.Role.ADMIN)
        extra_fields.setdefault("est_actif", True)
        return self.create_user(email, password, **extra_fields)


class Utilisateur(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        ADMIN = "admin", "Administrateur"
        PROPRIETAIRE = "proprietaire", "Propriétaire de cité"
        CLIENT = "client", "Étudiant"

    # Champs de base (diagramme de classes)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENT)
    est_actif = models.BooleanField(default=True)
    date_inscription = models.DateTimeField(default=timezone.now)

    # Champs Django internes
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nom", "prenom"]

    objects = UserManager()

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.prenom} {self.nom} <{self.email}>"

    def get_full_name(self):
        return f"{self.prenom} {self.nom}"

    # Méthodes du diagramme de classes
    def modifier_profil(self, **kwargs):
        for champ, valeur in kwargs.items():
            if hasattr(self, champ):
                setattr(self, champ, valeur)
        self.save()

    @property
    def est_proprietaire(self):
        return self.role == self.Role.PROPRIETAIRE

    @property
    def est_client(self):
        return self.role == self.Role.CLIENT

    @property
    def est_admin(self):
        return self.role == self.Role.ADMIN


class Proprietaire(Utilisateur):
    """Proxy model pour les propriétaires de cité (héritage du diagramme)."""
    numero_piece = models.CharField(max_length=50, blank=True)
    est_valide = models.BooleanField(default=False)          # validation par l'admin
    date_validation = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Propriétaire"
        verbose_name_plural = "Propriétaires"

    def save(self, *args, **kwargs):
        self.role = Utilisateur.Role.PROPRIETAIRE
        super().save(*args, **kwargs)

    # Méthodes du diagramme de classes
    def consulter_reservations(self):
        from campusnest.campusnest.reservations.models import Reservation
        return Reservation.objects.filter(chambre__cite__proprietaire=self)

    def consulter_statistiques(self):
        reservations = self.consulter_reservations()
        return {
            "total_reservations": reservations.count(),
            "reservations_confirmees": reservations.filter(statut="confirmee").count(),
        }

    def programmer_visite(self, reservation, date_visite):
        reservation.date_visite_chambre = date_visite
        reservation.save()


class Client(Utilisateur):
    """Proxy model pour les étudiants (héritage du diagramme)."""

    class Meta:
        verbose_name = "Étudiant"
        verbose_name_plural = "Étudiants"

    def save(self, *args, **kwargs):
        self.role = Utilisateur.Role.CLIENT
        super().save(*args, **kwargs)

    # Méthodes du diagramme de classes
    def rechercher_logement(self, **filtres):
        from logements.models import Chambre
        return Chambre.objects.filter(est_disponible=True, **filtres)

    def consulter_reservations(self):
        from campusnest.campusnest.reservations.models import Reservation
        return Reservation.objects.filter(client=self)

    def laisser_avis(self, chambre, note, commentaire):
        from campusnest.campusnest.avis.models import Avis
        return Avis.objects.create(
            client=self,
            chambre=chambre,
            note=note,
            commentaire=commentaire,
        )

    def signaler_logement(self, chambre, motif, description):
        from campusnest.campusnest.signalements.models import Signalement
        return Signalement.objects.create(
            client=self,
            chambre=chambre,
            motif=motif,
            description=description,
        )

    def contacter_proprietaire(self, proprietaire, sujet, message):
        from logements.models import MessageDeContact
        return MessageDeContact.objects.create(
            expediteur=self,
            destinataire=proprietaire,
            sujet=sujet,
            message=message,
        )


class Administrateur(Utilisateur):
    class Meta:
        verbose_name = "Administrateur"
        verbose_name_plural = "Administrateurs"

    def save(self, *args, **kwargs):
        self.role = Utilisateur.Role.ADMIN
        self.is_staff = True
        super().save(*args, **kwargs)

    # Méthodes du diagramme de classes
    def gerer_comptes(self):
        return Utilisateur.objects.all()

    def consulter_log_activite(self):
        from accounts.models import LogActivite
        return LogActivite.objects.all().order_by("-date")

    def gerer_signalements(self):
        from campusnest.campusnest.signalements.models import Signalement
        return Signalement.objects.filter(statut="ouvert")

    def configurer_plateforme(self, **params):
        pass  # Géré via le panneau admin Django

    def consulter_statistiques(self):
        from logements.models import Chambre, Cite
        return {
            "total_etudiants": Client.objects.count(),
            "total_proprietaires": Proprietaire.objects.count(),
            "total_cites": Cite.objects.count(),
            "total_chambres": Chambre.objects.count(),
            "chambres_disponibles": Chambre.objects.filter(est_disponible=True).count(),
        }
        
# ─────────────────────────────────────────────
#  OTP
# ───────────────────────────────────────────
 
class OTPCode(models.Model):
    """
    Code à 6 chiffres envoyé par email pour réinitialiser le mot de passe.
    Un seul code actif par utilisateur à la fois.
    Expire après OTP_EXPIRY_MINUTES minutes.
    """
    OTP_EXPIRY_MINUTES = 10   #  durée d'expiration du code
 
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name="otp_codes",
    )
    code       = models.CharField(max_length=6)
    cree_le    = models.DateTimeField(auto_now_add=True)
    utilise    = models.BooleanField(default=False)
 
    class Meta:
        verbose_name         = "Code OTP"
        verbose_name_plural  = "Codes OTP"
        ordering             = ["-cree_le"]
 
    def __str__(self):
        return f"OTP {self.code} — {self.utilisateur.email}"
 
    # ── helpers ──────────────────────────────
 
    @property
    def est_expire(self):
        return timezone.now() > self.cree_le + timedelta(minutes=self.OTP_EXPIRY_MINUTES)
 
    @property
    def est_valide(self):
        return not self.utilise and not self.est_expire
 
    def marquer_utilise(self):
        self.utilise = True
        self.save(update_fields=["utilise"])
 
    # ── factory ──────────────────────────────
 
    @classmethod
    def generer_pour(cls, utilisateur):
        """
        Invalide les anciens codes de l'utilisateur,
        génère un nouveau code à 6 chiffres et le retourne.
        """
        # Invalider tous les codes précédents
        cls.objects.filter(utilisateur=utilisateur, utilise=False).update(utilise=True)
 
        code = "".join(random.choices(string.digits, k=6))
        return cls.objects.create(utilisateur=utilisateur, code=code)
 



class LogActivite(models.Model):
    """Journal des actions effectuées sur la plateforme."""
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logs",
    )
    action = models.CharField(max_length=255)
    detail = models.TextField(blank=True)
    adresse_ip = models.GenericIPAddressField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log d'activité"
        verbose_name_plural = "Logs d'activité"
        ordering = ["-date"]

    def __str__(self):
        user = str(self.utilisateur) if self.utilisateur else "Anonyme"
        return f"[{self.date:%d/%m/%Y %H:%M}] {user} — {self.action}"