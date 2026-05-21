from django.shortcuts import render

# Create your views here.
"""
signalements/views.py
Emplacement : campusnest/signalements/views.py
"""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.utils import client_requis, admin_requis
from logements.models import Chambre
from .models import Signalement
from .forms import SignalementForm


# ─────────────────────────────────────────────
#  Vues étudiant (client)
# ─────────────────────────────────────────────

@client_requis
def signaler_logement_view(request, chambre_pk):
    """
    Un étudiant signale un problème sur une chambre (photos incorrectes,
    prix trompeur, chambre inexistante, etc.).
    Template : signalements/templates/signalements/signaler.html
    """
    chambre = get_object_or_404(Chambre, pk=chambre_pk)

    # Empêcher les doublons : un seul signalement ouvert par étudiant et par chambre
    signalement_existant = Signalement.objects.filter(
        chambre=chambre,
        client=request.user,
        statut__in=[Signalement.Statut.OUVERT, Signalement.Statut.EN_COURS],
    ).first()

    if signalement_existant:
        messages.info(
            request,
            "Vous avez déjà un signalement en cours pour cette chambre."
        )
        return redirect("logements:detail_chambre", pk=chambre_pk)

    form = SignalementForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        signalement = form.save(commit=False)
        signalement.chambre = chambre
        signalement.client  = request.user
        signalement.save()
        messages.success(
            request,
            "Votre signalement a été transmis à l'équipe d'administration."
        )
        return redirect("logements:detail_chambre", pk=chambre_pk)

    return render(request, "signalements/signaler.html", {
        "chambre": chambre,
        "form":    form,
    })


@client_requis
def mes_signalements_view(request):
    """
    Liste des signalements soumis par l'étudiant connecté.
    Template : signalements/templates/signalements/mes_signalements.html
    """
    signalements = Signalement.objects.filter(
        client=request.user
    ).select_related("chambre__cite").order_by("-date_signalement")

    return render(request, "signalements/mes_signalements.html", {
        "signalements": signalements,
    })


# ─────────────────────────────────────────────
#  Vues admin
# ─────────────────────────────────────────────

@admin_requis
def liste_signalements_view(request):
    """
    Liste de tous les signalements pour l'administrateur.
    Filtrables par statut.
    Template : signalements/templates/signalements/liste.html
    """
    signalements = Signalement.objects.select_related(
        "client", "chambre__cite"
    ).all().order_by("-date_signalement")

    statut_filtre = request.GET.get("statut", "")
    if statut_filtre:
        signalements = signalements.filter(statut=statut_filtre)

    return render(request, "signalements/liste.html", {
        "signalements":  signalements,
        "statut_filtre": statut_filtre,
        "statuts":       Signalement.Statut.choices,
    })


@admin_requis
def detail_signalement_view(request, pk):
    """
    Détail d'un signalement pour l'administrateur.
    Template : signalements/templates/signalements/detail.html
    """
    signalement = get_object_or_404(Signalement, pk=pk)
    return render(request, "signalements/detail.html", {"signalement": signalement})


@admin_requis
def traiter_signalement_view(request, pk):
    """
    Passe un signalement en statut 'en_cours' (prise en charge par l'admin).
    POST uniquement.
    """
    signalement = get_object_or_404(Signalement, pk=pk, statut=Signalement.Statut.OUVERT)
    if request.method == "POST":
        signalement.traiter()
        messages.info(request, f"Signalement #{pk} pris en charge.")
    return redirect("signalements:liste")


@admin_requis
def cloturer_signalement_view(request, pk):
    """
    Clôture un signalement après traitement.
    POST uniquement.
    """
    signalement = get_object_or_404(
        Signalement, pk=pk,
        statut__in=[Signalement.Statut.OUVERT, Signalement.Statut.EN_COURS]
    )
    if request.method == "POST":
        signalement.cloturer()
        messages.success(request, f"Signalement #{pk} clôturé.")
    return redirect("signalements:liste")