"""
campusnest/signalements/models.py
"""
from django.db import models
from django.utils import timezone


class Signalement(models.Model):

    class Statut(models.TextChoices):
        OUVERT   = "ouvert",   "Ouvert"
        EN_COURS = "en_cours", "En cours"
        CLOTURE  = "cloture",  "Clôturé"

    class Motif(models.TextChoices):
        PHOTOS_INCORRECTES  = "photos",     "Photos incorrectes"
        PRIX_TROMPEUR       = "prix",       "Prix trompeur"
        CHAMBRE_INEXISTANTE = "inexistante","Chambre inexistante"
        MAUVAIS_ETAT        = "etat",       "Mauvais état"
        AUTRE               = "autre",      "Autre"

    chambre  = models.ForeignKey(
        "logements.Chambre",
        on_delete=models.CASCADE,
        related_name="signalements",
        verbose_name="Chambre",
    )
    client   = models.ForeignKey(
        "users.Utilisateur",
        on_delete=models.CASCADE,
        related_name="signalements_soumis",
        limit_choices_to={"role": "client"},
        verbose_name="Étudiant",
    )
    motif           = models.CharField("Motif", max_length=20, choices=Motif.choices)
    description     = models.TextField("Description")
    statut          = models.CharField(
        "Statut", max_length=20,
        choices=Statut.choices,
        default=Statut.OUVERT,
    )
    date_signalement = models.DateTimeField("Date du signalement", default=timezone.now)
    date_traitement  = models.DateTimeField("Date de traitement", null=True, blank=True)

    class Meta:
        verbose_name        = "Signalement"
        verbose_name_plural = "Signalements"
        ordering            = ["-date_signalement"]

    def __str__(self):
        return f"Signalement #{self.pk} — {self.get_motif_display()} ({self.statut})"

    def traiter(self):
        self.statut = self.Statut.EN_COURS
        self.save(update_fields=["statut"])

    def cloturer(self):
        self.statut          = self.Statut.CLOTURE
        self.date_traitement = timezone.now()
        self.save(update_fields=["statut", "date_traitement"])