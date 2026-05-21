from django.shortcuts import render

# Create your views here.
"""
logements/views.py
Emplacement : campusnest/logements/views.py
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from campusnest.users.utils import admin_requis, proprietaire_valide_requis
from .models import Cite, Chambre, Photo


# ─────────────────────────────────────────────
#  Vues publiques (accessibles à tous)
# ─────────────────────────────────────────────

def home_view(request):
    """
    Page d'accueil = dashboard étudiant (maquette 'Dashboard étudiant').
    Affiche les cités et chambres disponibles avec recherche et filtres.
    Template : logements/templates/logements/home.html
    """
    cites    = Cite.objects.all()[:6]
    chambres = Chambre.objects.filter(est_disponible=True)

    # Recherche textuelle
    q = request.GET.get("q", "")
    if q:
        chambres = chambres.filter(
            Q(description__icontains=q) | Q(cite__nom__icontains=q)
        )

    # Filtres
    type_chambre = request.GET.get("type")
    if type_chambre:
        chambres = chambres.filter(type=type_chambre)

    prix_max = request.GET.get("prix_max")
    if prix_max:
        chambres = chambres.filter(loyer__lte=prix_max)

    meublee = request.GET.get("meublee")
    if meublee:
        chambres = chambres.filter(meublee=True)

    return render(request, "logements/home.html", {
        "cites":    cites,
        "chambres": chambres[:20],
        "q":        q,
    })


def liste_cites_view(request):
    """
    Liste complète des cités.
    Template : logements/templates/logements/liste_cites.html
    """
    cites = Cite.objects.prefetch_related("chambres")
    return render(request, "logements/liste_cites.html", {"cites": cites})


def detail_cite_view(request, pk):
    """
    Fiche d'une cité avec ses chambres.
    Template : logements/templates/logements/detail_cite.html
    """
    cite     = get_object_or_404(Cite, pk=pk)
    chambres = cite.chambres.filter(est_disponible=True)
    return render(request, "logements/detail_cite.html", {
        "cite": cite, "chambres": chambres
    })


def detail_chambre_view(request, pk):
    """
    Fiche complète d'une chambre : photos, prix, avis.
    Template : logements/templates/logements/detail_chambre.html
    """
    chambre = get_object_or_404(Chambre, pk=pk)
    photos  = chambre.photos.all()
    avis    = chambre.avis.filter(est_visible=True)
    note_moy = chambre.get_avis_moyenne()
    return render(request, "logements/detail_chambre.html", {
        "chambre":  chambre,
        "photos":   photos,
        "avis":     avis,
        "note_moy": note_moy,
    })


# ─────────────────────────────────────────────
#  Vues propriétaire
# ─────────────────────────────────────────────

@proprietaire_valide_requis
def mes_cites_view(request):
    """
    Dashboard propriétaire — liste de ses cités.
    Template : logements/templates/logements/mes_cites.html
    """
    cites = Cite.objects.filter(proprietaire=request.user).prefetch_related("chambres")
    return render(request, "logements/mes_cites.html", {"cites": cites})


@proprietaire_valide_requis
def ajouter_cite_view(request):
    """
    Formulaire d'ajout d'une nouvelle cité.
    Template : logements/templates/logements/ajouter_cite.html
    """
    from .forms import CiteForm
    form = CiteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        cite = form.save(commit=False)
        cite.proprietaire = request.user
        cite.save()
        messages.success(request, f"Cité « {cite.nom} » créée avec succès.")
        return redirect("logements:mes_cites")
    return render(request, "logements/ajouter_cite.html", {"form": form})


@proprietaire_valide_requis
def modifier_cite_view(request, pk):
    """
    Modification d'une cité existante.
    Template : logements/templates/logements/modifier_cite.html
    """
    from .forms import CiteForm
    cite = get_object_or_404(Cite, pk=pk, proprietaire=request.user)
    form = CiteForm(request.POST or None, instance=cite)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Cité mise à jour.")
        return redirect("logements:mes_cites")
    return render(request, "logements/modifier_cite.html", {"form": form, "cite": cite})


@proprietaire_valide_requis
def supprimer_cite_view(request, pk):
    cite = get_object_or_404(Cite, pk=pk, proprietaire=request.user)
    if request.method == "POST":
        cite.delete()
        messages.success(request, "Cité supprimée.")
    return redirect("logements:mes_cites")


@proprietaire_valide_requis
def ajouter_chambre_view(request, cite_pk):
    """
    Ajout d'une chambre dans une cité du propriétaire.
    Template : logements/templates/logements/ajouter_chambre.html
    """
    from .forms import ChambreForm
    cite = get_object_or_404(Cite, pk=cite_pk, proprietaire=request.user)
    form = ChambreForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        chambre = form.save(commit=False)
        chambre.cite = cite
        chambre.save()
        # Gestion des photos uploadées
        for fichier in request.FILES.getlist("photos"):
            Photo.objects.create(chambre=chambre, url=fichier)
        messages.success(request, "Chambre ajoutée.")
        return redirect("logements:mes_cites")
    return render(request, "logements/ajouter_chambre.html", {"form": form, "cite": cite})


@proprietaire_valide_requis
def modifier_chambre_view(request, pk):
    from .forms import ChambreForm
    chambre = get_object_or_404(Chambre, pk=pk, cite__proprietaire=request.user)
    form    = ChambreForm(request.POST or None, instance=chambre)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Chambre mise à jour.")
        return redirect("logements:mes_cites")
    return render(request, "logements/modifier_chambre.html", {"form": form, "chambre": chambre})


@proprietaire_valide_requis
def supprimer_chambre_view(request, pk):
    chambre = get_object_or_404(Chambre, pk=pk, cite__proprietaire=request.user)
    if request.method == "POST":
        chambre.delete()
        messages.success(request, "Chambre supprimée.")
    return redirect("logements:mes_cites")


# ─────────────────────────────────────────────
#  Vue admin
# ─────────────────────────────────────────────

@admin_requis
def liste_admin_view(request):
    """
    Liste de tous les logements pour l'administrateur.
    Template :logements/liste_admin.html
    """
    chambres = Chambre.objects.select_related("cite", "cite__proprietaire").all()
    return render(request, "logements/liste_admin.html", {"chambres": chambres})