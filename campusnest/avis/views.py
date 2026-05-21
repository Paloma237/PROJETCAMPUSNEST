from django.shortcuts import render

# Create your views here.
"""
avis/views.py
Emplacement : campusnest/avis/views.py
"""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.utils import client_requis, admin_requis
from logements.models import Chambre
from reservations.models import Reservation
from .models import Avis
from .forms import AvisForm


# ─────────────────────────────────────────────
#  Vues étudiant (client)
# ─────────────────────────────────────────────

@client_requis
def laisser_avis_view(request, chambre_pk):
    """
    Permet à un étudiant de laisser un avis sur une chambre.
    Condition : il doit avoir eu une réservation confirmée sur cette chambre.
    Template : avis/templates/avis/laisser_avis.html
    """
    chambre = get_object_or_404(Chambre, pk=chambre_pk)

    # Vérifier que l'étudiant a bien séjourné dans cette chambre
    a_reserve = Reservation.objects.filter(
        client=request.user,
        chambre=chambre,
        statut=Reservation.Statut.CONFIRMEE,
    ).exists()

    if not a_reserve:
        messages.error(
            request,
            "Vous ne pouvez laisser un avis que pour une chambre que vous avez réservée."
        )
        return redirect("logements:detail_chambre", pk=chambre_pk)

    # Vérifier qu'il n'a pas déjà laissé un avis
    avis_existant = Avis.objects.filter(
        chambre=chambre, client=request.user
    ).first()

    form = AvisForm(request.POST or None, instance=avis_existant)

    if request.method == "POST" and form.is_valid():
        avis = form.save(commit=False)
        avis.chambre = chambre
        avis.client  = request.user
        avis.save()
        messages.success(request, "Votre avis a été publié.")
        return redirect("logements:detail_chambre", pk=chambre_pk)

    return render(request, "avis/laisser_avis.html", {
        "chambre":        chambre,
        "form":           form,
        "avis_existant":  avis_existant,
    })


@client_requis
def supprimer_avis_view(request, pk):
    """
    Un étudiant supprime son propre avis.
    POST uniquement.
    """
    avis = get_object_or_404(Avis, pk=pk, client=request.user)
    chambre_pk = avis.chambre.pk
    if request.method == "POST":
        avis.delete()
        messages.success(request, "Votre avis a été supprimé.")
    return redirect("logements:detail_chambre", pk=chambre_pk)


# ─────────────────────────────────────────────
#  Vues admin
# ─────────────────────────────────────────────

@admin_requis
def liste_avis_admin_view(request):
    """
    Liste de tous les avis pour l'administrateur, avec modération.
    Template : avis/templates/avis/liste_admin.html
    """
    avis = Avis.objects.select_related("client", "chambre__cite").all()

    # Filtre visibilité
    visible = request.GET.get("visible", "")
    if visible == "1":
        avis = avis.filter(est_visible=True)
    elif visible == "0":
        avis = avis.filter(est_visible=False)

    return render(request, "avis/liste_admin.html", {"avis": avis})


@admin_requis
def moderer_avis_view(request, pk):
    """
    Masque un avis jugé inapproprié (est_visible → False).
    POST uniquement.
    """
    avis = get_object_or_404(Avis, pk=pk)
    if request.method == "POST":
        avis.moderer()
        messages.warning(request, f"Avis #{pk} masqué.")
    return redirect("avis:liste_admin")


@admin_requis
def publier_avis_view(request, pk):
    """
    Rend un avis visible à nouveau après modération.
    POST uniquement.
    """
    avis = get_object_or_404(Avis, pk=pk)
    if request.method == "POST":
        avis.publier()
        messages.success(request, f"Avis #{pk} rendu visible.")
    return redirect("avis:liste_admin")


@admin_requis
def supprimer_avis_admin_view(request, pk):
    """
    Suppression définitive d'un avis par l'admin.
    POST uniquement.
    """
    avis = get_object_or_404(Avis, pk=pk)
    if request.method == "POST":
        avis.delete()
        messages.success(request, f"Avis #{pk} supprimé définitivement.")
    return redirect("avis:liste_admin")