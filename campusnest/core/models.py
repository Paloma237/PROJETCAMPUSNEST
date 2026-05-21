# import uuid
# from django.db import models
# from django_extensions.db.models import TimeStampedModel, ActivatorModel

# from campusnest.global_data.enums import STATUT_CHOICES, STATUT_RESERVATION, TYPE_CHOICES

# class BaseModel(TimeStampedModel, ActivatorModel):
#     """Modèle de base avec les champs communs à tous les modèles"""
#     id = models.UUIDField(
#         default=uuid.uuid4,
#         primary_key=True,
#         unique=True,
#         null=False,
#         blank=False,
#         editable=False,
#     )
#     is_deleted = models.BooleanField(default=False)
#     metadata = models.JSONField(default=dict, null=True, blank=True)

#     class Meta:
#         abstract = True


# class PhotoCity(BaseModel):
#     image = models.ImageField(
#         upload_to='chambres/',  
#         verbose_name="Image",
#         help_text="Fichier image de la cité (format JPG, PNG)"
#     )
#     principale = models.BooleanField(
#         default=False,
#         verbose_name="Photo principale",
#         help_text="Cocher si cette photo doit être affichée en premier"
#     )

# class Cite(BaseModel):
#     proprietaire = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='cites')
#     nom          = models.CharField(max_length=200, verbose_name="Nom de la ville", help_text="Nom de la ville")
#     adresse      = models.TextField(verbose_name="Adresse", help_text="Adresse de la ville", null=True, blank=True)
#     quartier     = models.CharField(max_length=100, verbose_name="Quartier", help_text="Quartier de la ville")
#     ville        = models.CharField(max_length=100, default='Bandjoun', verbose_name="Ville", help_text="Ville")
#     description  = models.TextField(blank=True, null=True, verbose_name="Description", help_text="Description de la ville")
#     photo_cite = models.ManyToManyField(PhotoCity, blank=True, null=True)

#     def __str__(self):
#         return f"{self.nom} — {self.quartier}"


# class PhotoChambre(BaseModel):
#     image = models.ImageField(
#         upload_to='chambres/',
#         verbose_name="Image",
#         help_text="Fichier image de la chambre (format JPG, PNG)"
#     )
#     principale = models.BooleanField(
#         default=False,
#         verbose_name="Photo principale",
#         help_text="Cocher si cette photo doit être affichée en premier"
#     )


# class Chambre(BaseModel):
#     cite = models.ForeignKey(
#         Cite,  
#         on_delete=models.CASCADE,
#         related_name='chambres',
#         verbose_name="Cité",
#         help_text="Cité à laquelle appartient la chambre"
#     )
#     titre = models.CharField(
#         max_length=200,
#         verbose_name="Titre",
#         help_text="Titre ou numéro d'identification de la chambre"
#     )
#     type_chambre = models.CharField(
#         max_length=20,
#         choices=TYPE_CHOICES.choices,
#         verbose_name="Type de chambre",
#         help_text="Type de logement (simple, double, studio, appartement)"
#     )
#     description = models.TextField(
#         blank=True, null=True,
#         verbose_name="Description",
#         help_text="Description détaillée de la chambre (optionnelle)"
#     )
#     prix_mensuel = models.DecimalField(
#         max_digits=10, decimal_places=2,
#         verbose_name="Prix mensuel (FCFA)",
#         help_text="Montant du loyer par mois"
#     )
#     superficie = models.FloatField(
#         blank=True, null=True,
#         verbose_name="Superficie (m²)",
#         help_text="Surface au sol en mètres carrés (optionnelle)"
#     )
#     statut = models.CharField(
#         max_length=20,
#         choices=STATUT_CHOICES.choices,
#         default=STATUT_CHOICES.DISPONIBLE,
#         verbose_name="Statut",
#         help_text="État actuel de la chambre (disponible, occupée, suspendue)"
#     )
#     wifi = models.BooleanField(
#         default=False,
#         verbose_name="Wi-Fi inclus",
#         help_text="Cocher si la connexion Wi-Fi est fournie"
#     )
#     electricite = models.BooleanField(
#         default=True,
#         verbose_name="Électricité",
#         help_text="Cocher si l'électricité est disponible"
#     )
#     eau_courante = models.BooleanField(
#         default=True,
#         verbose_name="Eau courante",
#         help_text="Cocher si l'eau courante est disponible"
#     )
#     cuisine = models.BooleanField(
#         default=False,
#         verbose_name="Cuisine équipée",
#         help_text="Cocher si la chambre dispose d'une cuisine"
#     )
#     salle_de_bain = models.BooleanField(
#         default=False,
#         verbose_name="Salle de bain privée",
#         help_text="Cocher si une salle de bain est attenante"
#     )

#     photo_chambre = models.ManyToManyField(PhotoChambre, blank=True, null=True, verbose_name="Photos", help_text="Photos de la chambre")

#     def __str__(self):
#         return f"{self.titre} — {self.cite.nom}"

#     def est_disponible(self):
#         return self.statut == STATUT_CHOICES.DISPONIBLE




# class Reservation(BaseModel):
   
#     etudiant = models.ForeignKey(
#         'users.User',
#         on_delete=models.CASCADE,
#         related_name='reservations',
#         verbose_name="Étudiant",
#         help_text="Utilisateur (étudiant) qui effectue la réservation"
#     )
#     chambre = models.ForeignKey(
#         Chambre,
#         on_delete=models.CASCADE,
#         related_name='reservations',
#         verbose_name="Chambre",
#         help_text="Chambre réservée"
#     )
#     date_debut = models.DateField(
#         verbose_name="Date de début",
#         help_text="Date d'entrée prévue"
#     )
#     date_fin = models.DateField(
#         verbose_name="Date de fin",
#         help_text="Date de sortie prévue"
#     )
#     statut = models.CharField(
#         max_length=20,
#         choices=STATUT_RESERVATION.choices,
#         default=STATUT_RESERVATION.EN_ATTENTE,
#         verbose_name="Statut",
#         help_text="État de la réservation (en attente, confirmée, annulée, terminée)"
#     )
#     message = models.TextField(
#         blank=True,
#         null=True,
#         verbose_name="Message",
#         help_text="Message ou demande particulière (optionnel)"
#     )

#     def __str__(self):
#         return f"{self.etudiant.email} → {self.chambre.titre}"

#     def duree_mois(self):
#         return round((self.date_fin - self.date_debut).days / 30)

#     def montant_total(self):
#         return self.chambre.prix_mensuel * self.duree_mois()


# class Avis(BaseModel):
#     etudiant    = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='avis')
#     chambre     = models.ForeignKey(Chambre, on_delete=models.CASCADE, related_name='avis')
#     note        = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
#     commentaire = models.TextField(blank=True, null=True)

#     class Meta:
#         unique_together = ('etudiant', 'chambre')

#     def __str__(self):
#         return f"{self.note}★ — {self.etudiant.email} sur {self.chambre.titre}"
    
