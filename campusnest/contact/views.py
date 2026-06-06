from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render

from campusnest.users.utils import client_requis, proprietaire_valide_requis, admin_requis
from campusnest.users.models import Utilisateur
from campusnest.logements.models import Chambre
from .models import MessageContact, Conversation, MessageConversation
from .forms import MessageContactForm, ReponseAdminForm, MessageConversationForm


# ─────────────────────────────────────────────
#  Utilitaire email
# ─────────────────────────────────────────────

def envoyer_email(sujet, corps, destinataire_email):
    try:
        send_mail(
            subject=sujet,
            message=corps,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destinataire_email],
            fail_silently=True,
        )
    except Exception:
        pass


# ─────────────────────────────────────────────
#  Contact général → équipe CampusNest
# ─────────────────────────────────────────────

def contact_view(request):
    initial = {}
    if request.user.is_authenticated:
        initial = {
            "nom_expediteur": request.user.get_full_name(),
            "email":          request.user.email,
            "telephone":      getattr(request.user, "telephone", ""),
        }

    form = MessageContactForm(request.POST or None, initial=initial)

    if request.method == "POST" and form.is_valid():
        msg = form.save(commit=False)
        if request.user.is_authenticated:
            msg.expediteur = request.user
        msg.save()

        admins = Utilisateur.objects.filter(role=Utilisateur.Role.ADMIN)
        for admin in admins:
            envoyer_email(
                sujet=f"[CampusNest] Nouveau message : {msg.objet}",
                corps=(
                    f"Nouveau message de contact.\n\n"
                    f"De : {msg.nom_expediteur} ({msg.email})\n"
                    f"Objet : {msg.objet}\n\n"
                    f"Message :\n{msg.message}"
                ),
                destinataire_email=admin.email,
            )

        messages.success(
            request,
            "Votre message a bien été envoyé. Nous vous répondrons dans les meilleurs délais."
        )
        return redirect("contact:contact")

    return render(request, "contact/contact.html", {"form": form})

# ─────────────────────────────────────────────
#  Client → contacter un propriétaire
# ─────────────────────────────────────────────

@client_requis
def contacter_proprietaire_view(request, proprietaire_pk, chambre_pk):
    proprietaire = get_object_or_404(
        Utilisateur, pk=proprietaire_pk, role=Utilisateur.Role.PROPRIETAIRE
    )
    chambre = get_object_or_404(Chambre, pk=chambre_pk)

    # Si une conversation existe déjà → on y redirige directement
    conversation_existante = Conversation.objects.filter(
        client=request.user,
        proprietaire=proprietaire,
        chambre=chambre,
    ).first()

    if conversation_existante:
        return redirect("contact:conversation", pk=conversation_existante.pk)

    form = MessageConversationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        # Créer la conversation
        conversation = Conversation.objects.create(
            client=request.user,
            proprietaire=proprietaire,
            chambre=chambre,
        )
        # Créer le premier message
        MessageConversation.objects.create(
            conversation=conversation,
            auteur=request.user,
            contenu=form.cleaned_data["contenu"],
        )
        # Email au propriétaire
        envoyer_email(
            sujet=f"[CampusNest] Nouveau message à propos de votre chambre",
            corps=(
                f"{request.user.get_full_name()} vous a envoyé un message "
                f"à propos de la chambre : {chambre}\n\n"
                f"Message :\n{form.cleaned_data['contenu']}\n\n"
                f"Connectez-vous à votre espace pour répondre."
            ),
            destinataire_email=proprietaire.email,
        )
        messages.success(request, "Votre message a bien été envoyé.")
        return redirect("contact:conversation", pk=conversation.pk)

    return render(request, "contact/contacter_proprietaire.html", {
        "proprietaire": proprietaire,
        "chambre":      chambre,
        "form":         form,
    })


# ─────────────────────────────────────────────
#  Fil de conversation (style chat)
# ─────────────────────────────────────────────

@login_required
def conversation_view(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk)

    # ✅ Comparaison par ID plus fiable
    user_ids_autorises = [conversation.client_id, conversation.proprietaire_id]
    if request.user.pk not in user_ids_autorises:
        messages.error(request, "Vous n'avez pas accès à cette conversation.")
        return redirect("contact:mes_messages")

    # Marquer les messages de l'autre comme lus
    conversation.messages.exclude(auteur=request.user).update(est_lu=True)

    form = MessageConversationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        MessageConversation.objects.create(
            conversation=conversation,
            auteur=request.user,
            contenu=form.cleaned_data["contenu"],
        )
        if request.user == conversation.client:
            destinataire_email = conversation.proprietaire.email
            destinataire_nom   = conversation.proprietaire.get_full_name()
        else:
            destinataire_email = conversation.client.email
            destinataire_nom   = conversation.client.get_full_name()

        envoyer_email(
            sujet="[CampusNest] Nouveau message dans votre conversation",
            corps=(
                f"Bonjour {destinataire_nom},\n\n"
                f"{request.user.get_full_name()} vous a envoyé un message "
                f"à propos de la chambre : {conversation.chambre}\n\n"
                f"Message :\n{form.cleaned_data['contenu']}\n\n"
                f"Connectez-vous à votre espace pour répondre."
            ),
            destinataire_email=destinataire_email,
        )
        return redirect("contact:conversation", pk=pk)

    tous_messages = conversation.messages.select_related("auteur").all()

    return render(request, "contact/conversation.html", {
        "conversation":  conversation,
        "tous_messages": tous_messages,
        "form":          form,
    })


# ─────────────────────────────────────────────
#  Liste des messages (client & propriétaire)
# ─────────────────────────────────────────────

@login_required
def mes_messages_view(request):
    user = request.user

    if user.role == Utilisateur.Role.CLIENT:
        conversations_qs = Conversation.objects.filter(
            client=user
        ).select_related("proprietaire", "chambre__cite").prefetch_related("messages")

        # Calcul des non lus et dernier message dans la vue
        conversations = []
        for conv in conversations_qs:
            conversations.append({
                "obj":        conv,
                "dernier":    conv.dernier_message(),
                "non_lus":    conv.non_lus_pour(user),
            })

        contacts = MessageContact.objects.filter(
            expediteur=user
        ).order_by("-date_envoi")

        return render(request, "contact/mes_messages_client.html", {
            "conversations": conversations,
            "contacts":      contacts,
        })

    elif user.role == Utilisateur.Role.PROPRIETAIRE:
        conversations_qs = Conversation.objects.filter(
            proprietaire=user
        ).select_related("client", "chambre__cite").prefetch_related("messages")

        conversations = []
        for conv in conversations_qs:
            conversations.append({
                "obj":     conv,
                "dernier": conv.dernier_message(),
                "non_lus": conv.non_lus_pour(user),
            })

        return render(request, "contact/mes_messages_proprietaire.html", {
            "conversations": conversations,
        })

    return redirect("contact:tous_messages_admin")

# ─────────────────────────────────────────────
#  Admin — tous les messages de contact
# ─────────────────────────────────────────────

@admin_requis
def tous_messages_admin_view(request):
    tous = MessageContact.objects.select_related("expediteur").order_by("-date_envoi")

    if request.GET.get("non_lus"):
        tous = tous.filter(est_lu=False)

    return render(request, "contact/tous_messages.html", {
        "messages_liste": tous,
    })


@admin_requis
def repondre_message_view(request, pk):
    msg  = get_object_or_404(MessageContact, pk=pk)
    form = ReponseAdminForm(request.POST or None, instance=msg)

    if request.method == "POST" and form.is_valid():
        form.save()
        msg.marquer_lu()

        # Email à l'expéditeur si on a son email
        if msg.email:
            envoyer_email(
                sujet="[CampusNest] Réponse à votre message",
                corps=(
                    f"Bonjour {msg.nom_expediteur},\n\n"
                    f"L'équipe CampusNest a répondu à votre message "
                    f"« {msg.objet} » :\n\n"
                    f"{msg.reponse_admin}\n\n"
                    f"Cordialement,\nL'équipe CampusNest"
                ),
                destinataire_email=msg.email,
            )

        messages.success(request, "Réponse enregistrée et envoyée.")
        return redirect("contact:tous_messages_admin")

    return render(request, "contact/repondre.html", {
        "msg":  msg,
        "form": form,
    })