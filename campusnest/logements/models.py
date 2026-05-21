"""
logements/models.py
Emplacement : campusnest/logements/models.py
"""
from django.db import models
from django.utils import timezone


class Cite(models.Model):
    """
    Correspond à la classe Cité du diagramme de classes.
    Une cité appartient à un propriétaire et contient des chambres.
    """
    proprietaire = models.ForeignKey(
        "users.Utilisateur",
        on_delete=models.CASCADE,
        related_name="cites",
        limit_choices_to={"role": "proprietaire"},
    )
    nom         = models.CharField(max_length=150)
    adresse     = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    latitude    = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude   = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    date_creation = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Cité"
        verbose_name_plural = "Cités"
        ordering = ["-date_creation"]

    def __str__(self):
        return self.nom

    # Méthodes du diagramme de classes
    def ajouter(self):
        self.save()

    def modifier(self, **kwargs):
        for champ, valeur in kwargs.items():
            setattr(self, champ, valeur)
        self.save()

    def supprimer(self):
        self.delete()

    def get_chambres_disponibles(self):
        return self.chambres.filter(est_disponible=True)


class Chambre(models.Model):
    """
    Correspond à la classe Chambre du diagramme de classes.
    Une chambre appartient à une cité.
    """
    class Type(models.TextChoices):
        SIMPLE  = "simple",  "Simple"
        DOUBLE  = "double",  "Double"
        STUDIO  = "studio",  "Studio"
        APPARTEMENT = "appartement", "Appartement"

    class Etat(models.TextChoices):
        BON      = "bon",      "Bon état"
        MOYEN    = "moyen",    "État moyen"
        RENOVATION = "renovation", "En rénovation"

    cite          = models.ForeignKey(Cite, on_delete=models.CASCADE, related_name="chambres")
    description   = models.TextField()
    superficie    = models.PositiveIntegerField(help_text="En m²")
    loyer         = models.PositiveIntegerField(help_text="En FCFA par mois")
    type          = models.CharField(max_length=20, choices=Type.choices, default=Type.SIMPLE)
    etat          = models.CharField(max_length=20, choices=Etat.choices, default=Etat.BON)
    est_disponible = models.BooleanField(default=True)
    date_ajout    = models.DateTimeField(default=timezone.now)

    # Équipements (champs booléens simples — pas de table séparée)
    meublee       = models.BooleanField(default=False)
    salle_de_bain  = models.BooleanField(default=False)
    cuisine       = models.BooleanField(default=False)
    internet      = models.BooleanField(default=False)
    eau_courante  = models.BooleanField(default=True)
    electricite   = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Chambre"
        verbose_name_plural = "Chambres"
        ordering = ["-date_ajout"]

    def __str__(self):
        return f"{self.cite.nom} — {self.get_type_display()} ({self.superficie} m²)"

    # Méthodes du diagramme de classes
    def ajouter(self):
        self.save()

    def modifier(self, **kwargs):
        for champ, valeur in kwargs.items():
            setattr(self, champ, valeur)
        self.save()

    def supprimer(self):
        self.delete()

    def set_disponibilite(self, disponible: bool):
        self.est_disponible = disponible
        self.save(update_fields=["est_disponible"])

    def get_avis_moyenne(self):
        avis = self.avis.filter(est_visible=True)
        if not avis.exists():
            return None
        total = sum(a.note for a in avis)
        return round(total / avis.count(), 1)

    def get_photo_principale(self):
        return self.photos.filter(est_principale=True).first() or self.photos.first()


class Photo(models.Model):
    """
    Correspond à la classe Photo du diagramme de classes.
    Photos associées à une chambre.
    """
    chambre      = models.ForeignKey(Chambre, on_delete=models.CASCADE, related_name="photos")
    url          = models.ImageField(upload_to="chambres/")  # stocké dans media/chambres/
    legende      = models.CharField(max_length=200, blank=True)
    est_principale = models.BooleanField(default=False)
    date_upload  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Photo"
        verbose_name_plural = "Photos"
        ordering = ["-est_principale", "date_upload"]

    def __str__(self):
        return f"Photo de {self.chambre} ({'principale' if self.est_principale else 'secondaire'})"

    def telecharger(self):
        """Retourne l'URL publique de la photo."""
        return self.url.url

    def supprimer(self):
        self.url.delete(save=False)  # supprime le fichier physique
        self.delete()