from django.db import models
from django.utils import timezone


class Cite(models.Model):
    proprietaire = models.ForeignKey(
        "users.Utilisateur",
        on_delete=models.CASCADE,
        related_name="cites",
        limit_choices_to={"role": "proprietaire"},
        verbose_name="Propriétaire",
    )
    nom           = models.CharField("Nom", max_length=150)
    adresse       = models.CharField("Adresse", max_length=255)
    description   = models.TextField("Description", blank=True)
    est_actif = models.BooleanField("Visible sur le site", default=True)
    motif_suppression = models.TextField("Raison de la suppression/rejet", blank=True)
    date_creation = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name        = "Cité"
        verbose_name_plural = "Cités"
        ordering            = ["-date_creation"]

    def __str__(self):
        return self.nom
    
    def image_principale_url(self):
        """Retourne l'URL de la photo principale ou None s'il n'y en a pas."""
        # On cherche d'abord s'il y a une photo marquée 'est_principale=True'
        photo = self.photos_cite.filter(est_principale=True).first()
        if not photo:
            # Sinon, on prend la toute première photo associée
            photo = self.photos_cite.first()
        
        if photo and photo.image:
            return photo.image.url
        return None
    
    def chambres_disponibles(self):
        return self.chambres.filter(est_disponible=True)


class Chambre(models.Model):

    class Type(models.TextChoices):
        SIMPLE      = "simple",      "Simple"
        MODERNE     = "moderne",     "Moderne"
        STUDIO      = "studio",      "Studio"
        APPARTEMENT = "appartement", "Appartement"

    class Etat(models.TextChoices):
        BON        = "bon",        "Bon état"
        MOYEN      = "moyen",      "État moyen"
        RENOVATION = "renovation", "En rénovation"

    cite          = models.ForeignKey(Cite, on_delete=models.CASCADE, related_name="chambres", verbose_name="Cité")
    description   = models.TextField("Description")
    superficie    = models.PositiveIntegerField("Superficie (m²)")
    loyer         = models.PositiveIntegerField("Loyer mensuel (FCFA)")
    type          = models.CharField("Type", max_length=20, choices=Type.choices, default=Type.SIMPLE)
    etat          = models.CharField("État", max_length=20, choices=Etat.choices, default=Etat.BON)
    est_disponible = models.BooleanField("Disponible", default=True)
    date_ajout    = models.DateTimeField(default=timezone.now)
    est_actif = models.BooleanField("Visible sur le site", default=True)
    motif_suppression = models.TextField("Raison de la désactivation/suppression", blank=True, help_text="Expliquez ici au propriétaire pourquoi sa chambre n'est plus visible.")

    # Équipements
    meublee      = models.BooleanField("Meublée", default=False)
    wc_interieur = models.BooleanField("WC intérieur", default=False)
    cuisine      = models.BooleanField("Cuisine", default=False)
    internet     = models.BooleanField("Internet", default=False)
    eau_courante = models.BooleanField("Eau courante", default=True)
    electricite  = models.BooleanField("Électricité", default=True)
    armoire       = models.BooleanField("Armoire", default=False)
    

    class Meta:
        verbose_name        = "Chambre"
        verbose_name_plural = "Chambres"
        ordering            = ["-date_ajout"]

    def __str__(self):
        return f"{self.cite.nom} — {self.get_type_display()} {self.superficie}m²"
    def note_moyenne(self):
        avis = self.avis.filter(est_visible=True)
        if not avis.exists():
            return None
        return round(sum(a.note for a in avis) / avis.count(), 1)

    def photo_principale(self):
        return self.photos.filter(est_principale=True).first() or self.photos.first()


class PhotoChambre(models.Model):
    chambre       = models.ForeignKey(Chambre, on_delete=models.CASCADE, related_name="photos", verbose_name="Chambre")
    image         = models.ImageField("Image", upload_to="chambres/%Y/%m/")
    legende       = models.CharField("Légende", max_length=200, blank=True)
    est_principale = models.BooleanField("Photo principale", default=False)
    date_upload   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Photo"
        verbose_name_plural = "Photos"
        ordering            = ["-est_principale", "date_upload"]

    def __str__(self):
        return f"Photo {'principale' if self.est_principale else 'secondaire'} — {self.chambre}"
    

class PhotoCity(models.Model):
    city= models.ForeignKey(Cite, on_delete=models.CASCADE, related_name="photos_cite", verbose_name="Cite")
    image         = models.ImageField("Image", upload_to="cites/%Y/%m/")
    legende       = models.CharField("Légende", max_length=200, blank=True)
    est_principale = models.BooleanField("Photo principale", default=False)
    date_upload   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Photo Cité"
        verbose_name_plural = "Photos Cités"
        ordering            = ["-est_principale", "date_upload"]

    def __str__(self):
        return f"Photo {'principale' if self.est_principale else 'secondaire'} — {self.city}"