from django.shortcuts import render

# Create your views here.
"""
avis/views.py
Emplacement : campusnest/avis/views.py
"""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from campusnest.users.utils import client_requis, admin_requis, proprietaire_valide_requis
from campusnest.logements.models import Chambre
from campusnest.reservations.models import Reservation
from campusnest.avis.models import Avis
from campusnest.avis.forms import AvisForm
from django.db.models import Avg, Count
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


"""
avis/views_proprietaire.py
Emplacement : campusnest/avis/views_proprietaire.py

Vues réservées au propriétaire pour consulter et modérer les avis
laissés sur ses chambres.
"""
# ─────────────────────────────────────────────────────────────
#  Liste globale des avis reçus sur toutes les chambres du proprio
# ─────────────────────────────────────────────────────────────

@proprietaire_valide_requis 
def liste_avis_proprietaire_view(request):
    """
    Affiche tous les avis publiés (est_visible=True) sur les chambres
    appartenant au propriétaire connecté, avec filtres optionnels.

    Contexte transmis au template :
        avis        – QuerySet filtré et annoté
        note_filtre – valeur du filtre note (int ou None)
        cite_filtre – pk de la cité filtrée (int ou None)
        cites       – liste des cités du propriétaire (pour le <select>)
        note_moy    – note moyenne globale (float ou None)
        total_avis  – nombre total d'avis visibles
    """
    # Toutes les chambres du proprio
    chambres_proprio = Chambre.objects.filter(cite__proprietaire=request.user)

    # Base queryset : avis visibles sur ces chambres
    avis_qs = (
        Avis.objects
        .filter(chambre__in=chambres_proprio, est_visible=True)
        .select_related("client", "chambre__cite")
        .order_by("-date_creation")
    )

    # ── Filtres GET ──
    note_filtre = request.GET.get("note", "")
    cite_filtre = request.GET.get("cite", "")

    if note_filtre.isdigit() and 1 <= int(note_filtre) <= 5:
        avis_qs = avis_qs.filter(note=int(note_filtre))
        note_filtre = int(note_filtre)
    else:
        note_filtre = None

    if cite_filtre.isdigit():
        avis_qs = avis_qs.filter(chambre__cite__pk=int(cite_filtre))
        cite_filtre = int(cite_filtre)
    else:
        cite_filtre = None

    # ── Statistiques rapides ──
    stats = avis_qs.aggregate(note_moy=Avg("note"), total=Count("pk"))

    # Liste des cités pour le filtre
    from campusnest.logements.models import Cite
    cites = Cite.objects.filter(proprietaire=request.user).order_by("nom")

    return render(request, "avis/liste_proprietaire.html", {
        "avis":         avis_qs,
        "note_filtre":  note_filtre,
        "cite_filtre":  cite_filtre,
        "cites":        cites,
        "note_moy":     stats["note_moy"],
        "total_avis":   stats["total"],
    })


# ─────────────────────────────────────────────────────────────
#  Signaler un avis inapproprié (le proprio demande une modération)
# ─────────────────────────────────────────────────────────────

@proprietaire_valide_requis
def signaler_avis_view(request, pk):
    """
    Le propriétaire signale un avis qu'il juge inapproprié.
    Cela masque l'avis (est_visible → False) en attendant une décision admin.
    POST uniquement.

    Note : dans une version plus élaborée, on pourrait créer un modèle
    « Signalement » plutôt que de masquer directement.
    """
    avis = get_object_or_404(
        Avis,
        pk=pk,
        chambre__cite__proprietaire=request.user,   # sécurité ownership
    )
    if request.method == "POST":
        avis.est_visible = False
        avis.save(update_fields=["est_visible"])
        messages.warning(
            request,
            f"L'avis a été signalé et masqué temporairement. "
            f"Un administrateur en prendra connaissance."
        )
    return redirect("avis:liste_proprietaire")