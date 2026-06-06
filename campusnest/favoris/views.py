from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from campusnest.users.utils import client_requis
from campusnest.logements.models import Chambre
from campusnest.favoris.models import Favori


# ─────────────────────────────────────────────
#  Toggle favori (ajouter / retirer)
# ─────────────────────────────────────────────

@client_requis
def toggle_favori_view(request, chambre_pk):
    """
    Ajoute la chambre aux favoris si elle n'y est pas encore,
    la retire sinon. POST uniquement.
    Redirige vers la page précédente (HTTP_REFERER) ou la liste des favoris.
    """
    if request.method != "POST":
        return redirect("favoris:mes_favoris")

    chambre = get_object_or_404(Chambre, pk=chambre_pk)
    favori, created = Favori.objects.get_or_create(
        client=request.user,
        chambre=chambre,
    )

    if created:
        messages.success(request, f"« {chambre} » ajoutée à vos favoris.")
    else:
        favori.delete()
        messages.info(request, f"« {chambre} » retirée de vos favoris.")

    # Retourne à la page d'où vient le clic (détail chambre, listing, etc.)
    retour = request.META.get("HTTP_REFERER", "")
    return redirect(retour or "favoris:mes_favoris")


# ─────────────────────────────────────────────
#  Liste des favoris du client connecté
# ─────────────────────────────────────────────

@client_requis
def mes_favoris_view(request):
    """
    Affiche toutes les chambres mises en favori par le client connecté.
    Template : favoris/templates/favoris/mes_favoris.html
    """
    favoris = (
        Favori.objects
        .filter(client=request.user)
        .select_related("chambre__cite")
        .order_by("-date_ajout")
    )

    return render(request, "favoris/mes_favoris.html", {
        "favoris": favoris,
    })