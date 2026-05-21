from django.shortcuts import render

# Create your views here.
"""
reservations/views.py
Emplacement : campusnest/reservations/views.py
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.utils import client_requis, proprietaire_valide_requis, admin_requis
from logements.models import Chambre
from .models import Reservation
from .forms import ReservationForm, DateVisiteForm


# ─────────────────────────────────────────────
#  Vues étudiant (client)
# ─────────────────────────────────────────────

@client_requis
def reserver_view(request, chambre_pk):
    """
    Formulaire de réservation d'une chambre par un étudiant.
    Vérifie que la chambre est disponible avant d'afficher le formulaire.
    Template : reservations/templates/reservations/reserver.html
    """
    chambre = get_object_or_404(Chambre, pk=chambre_pk, est_disponible=True)

    # Empêcher une double réservation active sur la même chambre
    deja_reserve = Reservation.objects.filter(
        client=request.user,
        chambre=chambre,
        statut__in=["en_attente", "confirmee"],
    ).exists()
    if deja_reserve:
        messages.warning(request, "Vous avez déjà une réservation active pour cette chambre.")
        return redirect("logements:detail_chambre", pk=chambre_pk)

    form = ReservationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        reservation = form.save(commit=False)
        reservation.chambre = chambre
        reservation.client  = request.user
        reservation.statut  = Reservation.Statut.EN_ATTENTE
        reservation.save()
        messages.success(
            request,
            "Votre demande de réservation a été envoyée au propriétaire."
        )
        return redirect("reservations:mes_reservations")

    return render(request, "reservations/reserver.html", {
        "chambre": chambre,
        "form":    form,
    })


@client_requis
def mes_reservations_view(request):
    """
    Liste de toutes les réservations de l'étudiant connecté.
    Triées par date de demande décroissante.
    Template : reservations/templates/reservations/mes_reservations.html
    """
    reservations = Reservation.objects.filter(
        client=request.user
    ).select_related("chambre__cite").order_by("-date_demande")

    return render(request, "reservations/mes_reservations.html", {
        "reservations": reservations,
    })


@client_requis
def detail_reservation_view(request, pk):
    """
    Détail d'une réservation de l'étudiant : statut, dates, montant total.
    Template : reservations/templates/reservations/detail_reservation.html
    """
    reservation = get_object_or_404(
        Reservation, pk=pk, client=request.user
    )
    return render(request, "reservations/detail_reservation.html", {
        "reservation": reservation,
        "montant_total": reservation.get_montant_total(),
    })


@client_requis
def annuler_reservation_client_view(request, pk):
    """
    Annulation d'une réservation par l'étudiant (uniquement si statut = en_attente).
    POST uniquement.
    """
    reservation = get_object_or_404(
        Reservation, pk=pk, client=request.user, statut=Reservation.Statut.EN_ATTENTE
    )
    if request.method == "POST":
        reservation.annuler(motif="Annulée par l'étudiant")
        messages.success(request, "Réservation annulée.")
    return redirect("reservations:mes_reservations")


@client_requis
def demander_nouvelle_date_view(request, pk):
    """
    L'étudiant peut proposer une nouvelle date de visite au propriétaire.
    Template : reservations/templates/reservations/demander_date.html
    """
    reservation = get_object_or_404(
        Reservation, pk=pk, client=request.user
    )
    form = DateVisiteForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        reservation.date_visite_chambre = form.cleaned_data["date_visite"]
        reservation.save(update_fields=["date_visite_chambre"])
        messages.success(request, "Nouvelle date de visite proposée au propriétaire.")
        return redirect("reservations:detail_reservation", pk=pk)

    return render(request, "reservations/demander_date.html", {
        "reservation": reservation,
        "form": form,
    })


# ─────────────────────────────────────────────
#  Vues propriétaire
# ─────────────────────────────────────────────

@proprietaire_valide_requis
def reservations_recues_view(request):
    """
    Liste de toutes les réservations reçues par le propriétaire connecté.
    Filtrables par statut.
    Template : reservations/templates/reservations/reservations_recues.html
    """
    reservations = Reservation.objects.filter(
        chambre__cite__proprietaire=request.user
    ).select_related("client", "chambre__cite").order_by("-date_demande")

    statut_filtre = request.GET.get("statut", "")
    if statut_filtre:
        reservations = reservations.filter(statut=statut_filtre)

    return render(request, "reservations/reservations_recues.html", {
        "reservations":   reservations,
        "statut_filtre":  statut_filtre,
        "statuts":        Reservation.Statut.choices,
    })


@proprietaire_valide_requis
def confirmer_reservation_view(request, pk):
    """
    Le propriétaire confirme une réservation (statut → confirmée).
    La chambre est automatiquement marquée comme indisponible.
    POST uniquement.
    """
    reservation = get_object_or_404(
        Reservation,
        pk=pk,
        chambre__cite__proprietaire=request.user,
        statut=Reservation.Statut.EN_ATTENTE,
    )
    if request.method == "POST":
        reservation.confirmer()
        messages.success(
            request,
            f"Réservation de {reservation.client.get_full_name()} confirmée."
        )
    return redirect("reservations:recues")


@proprietaire_valide_requis
def annuler_reservation_proprio_view(request, pk):
    """
    Le propriétaire annule une réservation avec un motif.
    La chambre est remise à disponible.
    POST uniquement.
    """
    reservation = get_object_or_404(
        Reservation,
        pk=pk,
        chambre__cite__proprietaire=request.user,
        statut__in=[Reservation.Statut.EN_ATTENTE, Reservation.Statut.CONFIRMEE],
    )
    if request.method == "POST":
        motif = request.POST.get("motif", "Annulée par le propriétaire")
        reservation.annuler(motif=motif)
        messages.warning(request, "Réservation annulée.")
    return redirect("reservations:recues")


@proprietaire_valide_requis
def programmer_visite_view(request, pk):
    """
    Le propriétaire fixe ou modifie la date de visite d'une réservation.
    Template : reservations/templates/reservations/programmer_visite.html
    """
    reservation = get_object_or_404(
        Reservation, pk=pk, chambre__cite__proprietaire=request.user
    )
    form = DateVisiteForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        reservation.programmer_visite(form.cleaned_data["date_visite"])
        messages.success(request, "Date de visite enregistrée.")
        return redirect("reservations:recues")

    return render(request, "reservations/programmer_visite.html", {
        "reservation": reservation,
        "form": form,
    })


@proprietaire_valide_requis
def historique_reservations_view(request):
    """
    Historique complet des réservations du propriétaire (confirmées + annulées + archivées).
    Template : reservations/templates/reservations/historique.html
    """
    reservations = Reservation.objects.filter(
        chambre__cite__proprietaire=request.user,
        statut__in=[
            Reservation.Statut.CONFIRMEE,
            Reservation.Statut.ANNULEE,
            Reservation.Statut.ARCHIVEE,
        ],
    ).select_related("client", "chambre__cite").order_by("-date_demande")

    return render(request, "reservations/historique.html", {
        "reservations": reservations,
    })


# ─────────────────────────────────────────────
#  Vues admin
# ─────────────────────────────────────────────

@admin_requis
def toutes_reservations_view(request):
    """
    Vue admin : toutes les réservations de la plateforme avec filtres.
    Template : reservations/templates/reservations/toutes_reservations.html
    """
    reservations = Reservation.objects.select_related(
        "client", "chambre__cite__proprietaire"
    ).all().order_by("-date_demande")

    statut = request.GET.get("statut", "")
    if statut:
        reservations = reservations.filter(statut=statut)

    return render(request, "reservations/toutes_reservations.html", {
        "reservations": reservations,
        "statuts":      Reservation.Statut.choices,
        "statut":       statut,
    })