"""
campusnest/reservations/views.py
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from campusnest.users.utils import client_requis, proprietaire_valide_requis, admin_requis
from campusnest.logements.models import Chambre
from campusnest.reservations.models import Reservation
from .forms import ReservationForm, AccepterReservationForm


# ─────────────────────────────────────────────
#  Vues étudiant (client)
# ─────────────────────────────────────────────

@client_requis
def reserver_view(request, chambre_pk):
    """
    Formulaire de réservation d'une chambre par un étudiant.
    Le client choisit ses dates de séjour ET une date de visite parmi
    celles proposées par le propriétaire pour cette chambre.
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

    # Vérifier qu'il existe au moins une date de visite disponible
    dates_disponibles = chambre.dates_visites_disponibles()
    if not dates_disponibles.exists():
        messages.warning(
            request,
            "Ce propriétaire n'a pas encore renseigné de dates de visite disponibles pour cette chambre."
        )
        return redirect("logements:detail_chambre", pk=chambre_pk)

    form = ReservationForm(request.POST or None, chambre=chambre)

    if request.method == "POST" and form.is_valid():
        reservation = form.save(commit=False)
        reservation.chambre = chambre
        reservation.client  = request.user
        reservation.statut  = Reservation.Statut.EN_ATTENTE
        reservation.save()
        messages.info(
            request,
            "Réservation créée. Veuillez procéder au paiement pour la confirmer."
        )
        return redirect("paiements:initier", reservation_pk=reservation.pk)
    return render(request, "reservations/reserver.html", {
        "chambre":            chambre,
        "form":               form,
        "dates_disponibles":  dates_disponibles,
    })


@client_requis
def mes_reservations_view(request):
    """
    Liste de toutes les réservations de l'étudiant connecté.
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
    Détail d'une réservation de l'étudiant.
    """
    reservation = get_object_or_404(Reservation, pk=pk, client=request.user)
    return render(request, "reservations/detail_reservation.html", {
        "reservation": reservation,
    })


@client_requis
def annuler_reservation_client_view(request, pk):
    """
    Annulation d'une réservation par l'étudiant (uniquement si statut = en_attente).
    """
    reservation = get_object_or_404(
        Reservation, pk=pk, client=request.user, statut=Reservation.Statut.EN_ATTENTE
    )
    if request.method == "POST":
        reservation.annuler(motif="Annulée par l'étudiant")
        messages.success(request, "Réservation annulée.")
    return redirect("reservations:mes_reservations")


# ─────────────────────────────────────────────
#  Vues propriétaire
# ─────────────────────────────────────────────

@proprietaire_valide_requis
def reservations_recues_view(request):
    """
    Liste des réservations reçues par le propriétaire.
    Chaque carte affiche les infos essentielles + un bouton "Traiter" unique.
    """
    reservations = Reservation.objects.filter(
        chambre__cite__proprietaire=request.user
    ).select_related("client", "chambre__cite").order_by("-date_demande")

    statut_filtre = request.GET.get("statut", "")
    if statut_filtre:
        reservations = reservations.filter(statut=statut_filtre)

    return render(request, "reservations/reservations_recues.html", {
        "reservations":  reservations,
        "statut_filtre": statut_filtre,
        "statuts":       Reservation.Statut.choices,
    })


@proprietaire_valide_requis
def traiter_reservation_view(request, pk):
    """
    Page de traitement d'une réservation par le propriétaire.
    Affiche tous les détails de la chambre + du client.
    Permet d'accepter (avec lieu + heure de visite) ou de refuser.
    """
    reservation = get_object_or_404(
        Reservation,
        pk=pk,
        chambre__cite__proprietaire=request.user,
    )
    form = AccepterReservationForm(request.POST or None)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "accepter":
            if form.is_valid():
                reservation.confirmer(
            lieu_visite=form.cleaned_data["lieu_visite"],
            heure_visite=form.cleaned_data["heure_visite"],
        )
        # Construire le message en gérant le cas où date_visite est None
        if reservation.date_visite:
            date_str = reservation.date_visite.strftime('%d/%m/%Y')
            msg = (
                f"Réservation de {reservation.client.get_full_name()} acceptée. "
                f"La visite est fixée le {date_str} "
                f"à {reservation.heure_visite.strftime('%H:%M')} — {reservation.lieu_visite}."
            )
        else:
            msg = (
                f"Réservation de {reservation.client.get_full_name()} acceptée. "
                f"Visite à {reservation.heure_visite.strftime('%H:%M')} — {reservation.lieu_visite}."
            )
        messages.success(request, msg)
        return redirect("reservations:recues")

    return render(request, "reservations/traiter_reservation.html", {
        "reservation": reservation,
        "form":        form,
    })


@proprietaire_valide_requis
def annuler_reservation_proprio_view(request, pk):
    """
    Le propriétaire annule une réservation déjà confirmée.
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
def historique_reservations_view(request):
    """
    Historique complet : confirmées + annulées + archivées.
    """
    reservations = Reservation.objects.filter(
        chambre__cite__proprietaire=request.user,
        statut__in=[
            Reservation.Statut.CONFIRMEE,
            Reservation.Statut.ANNULEE,
            Reservation.Statut.ARCHIVEE,
        ],
    ).select_related("client", "chambre__cite").order_by("-date_demande")

    return render(request, "reservations/historique_reservations.html", {
        "reservations": reservations,
    })


# ─────────────────────────────────────────────
#  Vues admin
# ─────────────────────────────────────────────

@admin_requis
def toutes_reservations_view(request):
    """
    Vue admin : toutes les réservations de la plateforme.
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