"""
campusnest/paiements/models.py
"""
from django.db import models
from django.utils import timezone
import uuid


class Paiement(models.Model):

    class Operateur(models.TextChoices):
        MTN    = "mtn",    "MTN Mobile Money"
        ORANGE = "orange", "Orange Money"

    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente"
        REUSSI     = "reussi",     "Réussi"
        ECHOUE     = "echoue",     "Échoué"

    reservation = models.OneToOneField(
        "reservations.Reservation",
        on_delete=models.CASCADE,
        related_name="paiement",
        verbose_name="Réservation",
    )
    montant = models.DecimalField(
        "Montant (FCFA)", max_digits=10, decimal_places=0
    )
    operateur = models.CharField(
        "Opérateur", max_length=10, choices=Operateur.choices
    )
    numero_telephone = models.CharField(
        "Numéro Mobile Money", max_length=20
    )
    statut = models.CharField(
        "Statut", max_length=20,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE,
    )
    reference = models.CharField(
        "Référence transaction", max_length=100,
        unique=True, blank=True,
    )
    date_creation   = models.DateTimeField("Date de création", default=timezone.now)
    date_paiement   = models.DateTimeField("Date de paiement", null=True, blank=True)

    class Meta:
        verbose_name        = "Paiement"
        verbose_name_plural = "Paiements"
        ordering            = ["-date_creation"]

    def __str__(self):
        return f"Paiement #{self.pk} — {self.get_statut_display()} — {self.montant} FCFA"

    def generer_reference(self):
        """Génère une référence unique pour la transaction."""
        return f"CN-{uuid.uuid4().hex[:10].upper()}"

    def marquer_reussi(self):
        self.statut        = self.Statut.REUSSI
        self.date_paiement = timezone.now()
        self.save(update_fields=["statut", "date_paiement"])

    def marquer_echoue(self):
        self.statut = self.Statut.ECHOUE
        self.save(update_fields=["statut"])