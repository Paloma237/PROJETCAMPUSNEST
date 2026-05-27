from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Avis(models.Model):

    chambre = models.ForeignKey(
        "logements.Chambre",
        on_delete=models.CASCADE,
        related_name="avis",
        verbose_name="Chambre",
    )
    client = models.ForeignKey(
        "users.Utilisateur",
        on_delete=models.CASCADE,
        related_name="avis_donnes",
        limit_choices_to={"role": "client"},
        verbose_name="Étudiant",
    )
    note        = models.PositiveSmallIntegerField(
        "Note",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    commentaire   = models.TextField("Commentaire")
    date_creation = models.DateTimeField("Date", auto_now_add=True)
    est_visible   = models.BooleanField("Visible", default=True)

    class Meta:
        verbose_name        = "Avis"
        verbose_name_plural = "Avis"
        ordering            = ["-date_creation"]
        # Un seul avis par étudiant par chambre
        unique_together     = [("chambre", "client")]

    def __str__(self):
        return f"{self.note}/5 — {self.client} sur {self.chambre}"