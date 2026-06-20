"""
campusnest/reservations/models.py
"""
from django.db import models
from dateutil.relativedelta import relativedelta
from django.utils import timezone


class Reservation(models.Model):

    class Statut(models.TextChoices):
        EN_ATTENTE = "en_attente", "En attente"
        CONFIRMEE  = "confirmee",  "Confirmée"
        ANNULEE    = "annulee",    "Annulée"
        ARCHIVEE   = "archivee",   "Archivée"

    chambre = models.ForeignKey(
        "logements.Chambre",
        on_delete=models.CASCADE,
        related_name="reservations",
        verbose_name="Chambre",
    )
    client = models.ForeignKey(
        "users.Utilisateur",
        on_delete=models.CASCADE,
        related_name="reservations",
        limit_choices_to={"role": "client"},
        verbose_name="Étudiant",
    )
    date_debut = models.DateField("Date d'entrée")
    date_fin   = models.DateField("Date de sortie")

    # Date de visite choisie par le CLIENT lors de la réservation
    date_visite = models.DateField("Date de visite choisie", null=True, blank=True)

    # Informations de visite complétées par le PROPRIÉTAIRE lors de l'acceptation
    lieu_visite  = models.CharField("Lieu de la visite", max_length=255, blank=True)
    heure_visite = models.TimeField("Heure de la visite", null=True, blank=True)

    statut = models.CharField(
        "Statut", max_length=20,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE,
    )
    date_demande      = models.DateTimeField("Date de demande", default=timezone.now)
    date_confirmation = models.DateTimeField("Date de confirmation", null=True, blank=True)
    motif_annulation  = models.TextField("Motif d'annulation", blank=True)

    class Meta:
        verbose_name        = "Réservation"
        verbose_name_plural = "Réservations"
        ordering            = ["-date_demande"]

    def __str__(self):
        return f"Réservation #{self.pk} — {self.client} → {self.chambre}"

    # ── Actions métier ──────────────────────────────────────

    def confirmer(self, lieu_visite="", heure_visite=None):
        """Accepte la réservation et enregistre les infos de visite fournies par le proprio."""
        self.statut            = self.Statut.CONFIRMEE
        self.date_confirmation = timezone.now()
        self.lieu_visite       = lieu_visite
        self.heure_visite      = heure_visite
        self.chambre.est_disponible = False
        self.chambre.save(update_fields=["est_disponible"])
        self.save()

    def annuler(self, motif=""):
        self.statut           = self.Statut.ANNULEE
        self.motif_annulation = motif
        self.chambre.est_disponible = True
        self.chambre.save(update_fields=["est_disponible"])
        self.save()

    def duree_jours(self):
        return (self.date_fin - self.date_debut).days
    def nombre_mois(self):
    #Nombre de mois complets entre date_debut et date_fin.
        delta = relativedelta(self.date_fin, self.date_debut)
        return delta.months + (delta.years * 12)

    def montant_total(self):
    #Loyer mensuel × nombre de mois complets.
        mois = self.nombre_mois()
        if mois == 0:
            mois = 1  # minimum 1 mois facturé si la durée est inférieure à un mois
        return self.chambre.loyer * mois