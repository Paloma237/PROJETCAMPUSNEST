from django.shortcuts import render

# Create your views here.
"""
contact/views.py
Emplacement : campusnest/contact/views.py
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.utils import client_requis, proprietaire_valide_requis, admin_requis
from accounts.models import Utilisateur
from .models import MessageDeContact
from .forms import MessageForm, ReponseForm


# ─────────────────────────────────────────────
#  Vue publique (page contact générale)
# ─────────────────────────────────────────────

def contact_view(request):
    """
    Formulaire de contact général visible par tous.
    Si l'utilisateur est connecté, pre-remplit nom/email.
    Template : contact/templates/contact/contact.html
    """
    initial = {}
    if request.user.is_authenticated:
        initial = {
            "nom_expediteur": request.user.get_full_name(),
            "email":          request.user.email,
            "telephone":      request.user.telephone,
        }

    form = MessageForm(request.POST or None, initial=initial)

    if request.method == "POST" and form.is_valid():
        msg = form.save(commit=False)
        if request.user.is_authenticated:
            msg.expediteur = request.user
        else:
            # Utilisateur anonyme : lier à un compte admin pour le suivi
            admin = Utilisateur.objects.filter(role=Utilisateur.Role.ADMIN).first()
            msg.expediteur = admin  # Fallback
        msg.save()
        messages.success(
            request,
            "Votre message a bien été envoyé. Nous vous répondrons dans les meilleurs délais."
        )
        return redirect("contact:contact")

    return render(request, "contact/contact.html", {"form": form})


# ─────────────────────────────────────────────
#  Vue étudiant — contacter un propriétaire
# ─────────────────────────────────────────────

@client_requis
def contacter_proprietaire_view(request, proprietaire_pk):
    """
    Un étudiant envoie un message directement à un propriétaire.
    Accessible depuis la fiche chambre (bouton "Contacter le propriétaire").
    Template : contact/templates/contact/contacter_proprietaire.html
    """
    proprietaire = get_object_or_404(
        Utilisateur, pk=proprietaire_pk, role=Utilisateur.Role.PROPRIETAIRE
    )
    form = MessageForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        msg = form.save(commit=False)
        msg.expediteur   = request.user
        msg.destinataire = proprietaire
        msg.nom_expediteur = request.user.get_full_name()
        msg.email          = request.user.email
        msg.telephone      = request.user.telephone
        msg.save()
        messages.success(request, f"Message envoyé à {proprietaire.get_full_name()}.")
        return redirect("contact:mes_messages")

    return render(request, "contact/contacter_proprietaire.html", {
        "proprietaire": proprietaire,
        "form":         form,
    })


# ─────────────────────────────────────────────
#  Vue messages reçus (propriétaire & admin)
# ─────────────────────────────────────────────

@login_required
def mes_messages_view(request):
    """
    Messages reçus par l'utilisateur connecté.
    Marque automatiquement les messages comme lus à l'affichage.
    Template : contact/templates/contact/mes_messages.html
    """
    messages_recus = MessageDeContact.objects.filter(
        destinataire=request.user
    ).select_related("expediteur").order_by("-date_envoi")

    # Marquer tous comme lus
    messages_recus.filter(est_lu=False).update(est_lu=True)

    return render(request, "contact/mes_messages.html", {
        "messages_recus": messages_recus,
    })


@login_required
def messages_envoyes_view(request):
    """
    Messages envoyés par l'utilisateur connecté.
    Template : contact/templates/contact/messages_envoyes.html
    """
    messages_envoyes = MessageDeContact.objects.filter(
        expediteur=request.user
    ).select_related("destinataire").order_by("-date_envoi")

    return render(request, "contact/messages_envoyes.html", {
        "messages_envoyes": messages_envoyes,
    })


@login_required
def detail_message_view(request, pk):
    """
    Détail d'un message (expéditeur ou destinataire peuvent le consulter).
    Template : contact/templates/contact/detail_message.html
    """
    msg = get_object_or_404(
        MessageDeContact,
        pk=pk,
        # Accessible par l'expéditeur OU le destinataire
    )
    # Contrôle d'accès manuel
    if msg.expediteur != request.user and msg.destinataire != request.user:
        messages.error(request, "Vous n'avez pas accès à ce message.")
        return redirect("contact:mes_messages")

    if not msg.est_lu and msg.destinataire == request.user:
        msg.marquer_lu()

    return render(request, "contact/detail_message.html", {"msg": msg})


# ─────────────────────────────────────────────
#  Vue admin — répondre à un message
# ─────────────────────────────────────────────

@admin_requis
def repondre_message_view(request, pk):
    """
    L'administrateur répond à un message de contact.
    La réponse est enregistrée dans le champ reponse_admin du message.
    Template : contact/templates/contact/repondre.html
    """
    msg  = get_object_or_404(MessageDeContact, pk=pk)
    form = ReponseForm(request.POST or None, instance=msg)

    if request.method == "POST" and form.is_valid():
        form.save()
        msg.marquer_lu()
        messages.success(request, "Réponse enregistrée.")
        return redirect("contact:mes_messages")

    return render(request, "contact/repondre.html", {
        "msg":  msg,
        "form": form,
    })


@admin_requis
def tous_messages_admin_view(request):
    """
    Vue admin : tous les messages de contact de la plateforme.
    Template : contact/templates/contact/tous_messages.html
    """
    tous = MessageDeContact.objects.select_related(
        "expediteur", "destinataire"
    ).all().order_by("-date_envoi")

    # Filtre non lus
    non_lus = request.GET.get("non_lus")
    if non_lus:
        tous = tous.filter(est_lu=False)

    return render(request, "contact/tous_messages.html", {
        "messages_liste": tous,
    })