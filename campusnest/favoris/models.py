from django.db import models


class Favori(models.Model):
    client = models.ForeignKey(
        "users.Utilisateur",
        on_delete=models.CASCADE,
        related_name="favoris",
        limit_choices_to={"role": "client"},
        verbose_name="Étudiant",
    )
    chambre = models.ForeignKey(
        "logements.Chambre",
        on_delete=models.CASCADE,
        related_name="mis_en_favori_par",
        verbose_name="Chambre",
    )
    date_ajout = models.DateTimeField("Ajouté le", auto_now_add=True)

    class Meta:
        verbose_name        = "Favori"
        verbose_name_plural = "Favoris"
        ordering            = ["-date_ajout"]
        unique_together     = [("client", "chambre")]   # un seul favori par (client, chambre)

    def __str__(self):
        return f"{self.client} ♥ {self.chambre}"