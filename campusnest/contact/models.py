from django.db import models
from django.conf import settings


class MessageContact(models.Model):
    """
    Message envoyé à l'équipe CampusNest.
    Peut venir d'un utilisateur connecté ou d'un anonyme.
    """
    expediteur     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="messages_contact_envoyes",
        verbose_name="Expéditeur",
    )
    nom_expediteur = models.CharField("Nom",       max_length=150, blank=True)
    email          = models.EmailField("Email",    blank=True)
    telephone      = models.CharField("Téléphone", max_length=20,  blank=True)
    objet          = models.CharField("Objet",     max_length=255)
    message        = models.TextField("Message")
    reponse_admin  = models.TextField("Réponse admin", blank=True)
    est_lu         = models.BooleanField("Lu", default=False)
    date_envoi     = models.DateTimeField("Date d'envoi", auto_now_add=True)

    class Meta:
        verbose_name        = "Message de contact"
        verbose_name_plural = "Messages de contact"
        ordering            = ["-date_envoi"]

    def __str__(self):
        return f"{self.nom_expediteur or self.expediteur} — {self.objet}"

    def marquer_lu(self):
        if not self.est_lu:
            self.est_lu = True
            self.save(update_fields=["est_lu"])


class Conversation(models.Model):
    """
    Fil de discussion entre un client et un propriétaire
    à propos d'une chambre précise.
    Une seule conversation par trio (client, propriétaire, chambre).
    """
    client       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_client",
        verbose_name="Client",
    )
    proprietaire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations_proprietaire",
        verbose_name="Propriétaire",
    )
    chambre      = models.ForeignKey(
        "logements.Chambre",
        on_delete=models.CASCADE,
        related_name="conversations",
        verbose_name="Chambre",
    )
    date_creation = models.DateTimeField("Date de création", auto_now_add=True)

    class Meta:
        verbose_name        = "Conversation"
        verbose_name_plural = "Conversations"
        ordering            = ["-date_creation"]
        # Un seul fil par trio
        unique_together     = [("client", "proprietaire", "chambre")]

    def __str__(self):
        return (
            f"Conv. {self.client.get_full_name()} ↔ "
            f"{self.proprietaire.get_full_name()} "
            f"— {self.chambre}"
        )

    def dernier_message(self):
        return self.messages.order_by("-date_envoi").first()

    def non_lus_pour(self, user):
        """Nombre de messages non lus pour un utilisateur donné."""
        return self.messages.filter(est_lu=False).exclude(auteur=user).count()


class MessageConversation(models.Model):
    """
    Un message dans une conversation client ↔ propriétaire.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Conversation",
    )
    auteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages_conversation",
        verbose_name="Auteur",
    )
    contenu    = models.TextField("Message")
    date_envoi = models.DateTimeField("Date d'envoi", auto_now_add=True)
    est_lu     = models.BooleanField("Lu", default=False)

    class Meta:
        verbose_name        = "Message de conversation"
        verbose_name_plural = "Messages de conversation"
        ordering            = ["date_envoi"]

    def __str__(self):
        return f"{self.auteur.get_full_name()} — {self.date_envoi:%d/%m/%Y %H:%M}"