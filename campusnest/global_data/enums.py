from django.db import models

class TYPE_CHOICES(models.TextChoices):
    SIMPLE = 'simple', 'Chambre simple'
    DOUBLE = 'double', 'Chambre double'
    STUDIO = 'studio', 'Studio'
    APPARTEMENT = 'appartement', 'Appartement'

class STATUT_CHOICES(models.TextChoices):
    DISPONIBLE = 'disponible', 'Disponible'
    OCCUPEE = 'occupee', 'Occupée'
    SUSPENDUE = 'suspendue', 'Suspendue'


class STATUT_RESERVATION(models.TextChoices):
    EN_ATTENTE = 'en_attente', 'En attente'
    CONFIRMEE = 'confirmee', 'Confirmée'
    ANNULEE = 'annulee', 'Annulée'
    TERMINEE = 'terminee', 'Terminée'


class ROLE_CHOICES(models.TextChoices):
    CLIENT = 'client', 'Étudiant'
    PROPRIETAIRE = 'proprietaire', 'Propriétaire'
    ADMIN = 'admin', 'Administrateur'