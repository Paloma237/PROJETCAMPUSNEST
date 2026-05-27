from django.db import models


class MessageDeContact(models.Model):
    # Expéditeur — peut être un étudiant ou un utilisateur anonyme
    expediteur   = models.ForeignKey(
        "users.Utilisateur",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="messages_envoyes",
        verbose_name="Expéditeur",
    )
    # Destinataire — propriétaire ou null (message général vers l'admin)
    destinataire = models.ForeignKey(
        "users.Utilisateur",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="messages_recus",
        verbose_name="Destinataire",
    )
    # Champs visibles dans le formulaire
    nom_expediteur = models.CharField("Nom", max_length=150, blank=True)
    telephone      = models.CharField("Téléphone", max_length=20, blank=True)
    email          = models.EmailField("Email", blank=True)
    objet_message  = models.CharField("Objet", max_length=255)
    message        = models.TextField("Message")

    # Réponse de l'admin ou du propriétaire
    reponse_admin   = models.TextField("Réponse", blank=True)

    est_lu         = models.BooleanField("Lu", default=False)
    date_envoi     = models.DateTimeField("Date d'envoi", auto_now_add=True)

    class Meta:
        verbose_name        = "Message de contact"
        verbose_name_plural = "Messages de contact"
        ordering            = ["-date_envoi"]

    def __str__(self):
        return f"Message de {self.nom_expediteur or self.expediteur} — {self.objet_message}"

    def marquer_lu(self):
        self.est_lu = True
        self.save(update_fields=["est_lu"])