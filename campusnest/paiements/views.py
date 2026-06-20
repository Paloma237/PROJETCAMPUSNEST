"""
campusnest/paiements/views.py
"""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from campusnest.users.utils import client_requis
from campusnest.reservations.models import Reservation
from .forms import PaiementForm
from .models import Paiement
from campusnest.paiements.service import simulate_paiement
from django.conf import settings


@client_requis
def initier_paiement_view(request, reservation_pk):
    """
    Page de paiement Mobile Money affichée juste après la soumission
    du formulaire de réservation.
    L'étudiant choisit son opérateur et saisit son numéro.
    """
    reservation = get_object_or_404(
        Reservation,
        pk=reservation_pk,
        client=request.user,
        statut=Reservation.Statut.EN_ATTENTE,
    )

    # Si un paiement réussi existe déjà → pas de double paiement
    if hasattr(reservation, "paiement") and reservation.paiement.statut == Paiement.Statut.REUSSI:
        messages.info(request, "Cette réservation a déjà été payée.")
        return redirect("reservations:detail", pk=reservation.pk)

    montant = settings.MONTANT_RESERVATION
    form    = PaiementForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        paiement = form.save(commit=False)
        paiement.reservation = reservation
        paiement.montant     = montant

        # Créer ou réutiliser le paiement (en cas de nouvelle tentative)
        if hasattr(reservation, "paiement"):
            ancien = reservation.paiement
            ancien.operateur         = paiement.operateur
            ancien.numero_telephone  = paiement.numero_telephone
            ancien.montant           = montant
            ancien.statut            = Paiement.Statut.EN_ATTENTE
            ancien.reference         = ancien.generer_reference()
            ancien.save()
            paiement = ancien
        else:
            paiement.reference = paiement.generer_reference()
            paiement.save()

        # Appel au service (simulation ou API réelle)
        resultat = simulate_paiement(paiement)

        if resultat["succes"]:
            paiement.marquer_reussi()
            messages.success(
                request,
                f"✅ Paiement de {montant} FCFA reçu ! "
                f"Référence : {paiement.reference}"
            )
            return redirect("paiements:confirmation", pk=paiement.pk)
        else:
            paiement.marquer_echoue()
            messages.error(request, f"❌ {resultat['message']}")
            # On reste sur la page pour réessayer

    return render(request, "paiements/initier_paiement.html", {
        "reservation": reservation,
        "montant":     montant,
        "form":        form,
    })


@client_requis
def confirmation_paiement_view(request, pk):
    """
    Page de confirmation affichée après un paiement réussi.
    Sert de reçu récapitulatif.
    """
    paiement = get_object_or_404(
        Paiement,
        pk=pk,
        reservation__client=request.user,
        statut=Paiement.Statut.REUSSI,
    )
    return render(request, "paiements/confirmation_paiement.html", {
        "paiement": paiement,
    })