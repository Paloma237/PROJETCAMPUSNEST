from django.contrib import messages
from django.db.models import Q, Exists, OuterRef, Value, BooleanField
from django.shortcuts import get_object_or_404, redirect, render
from urllib3 import request

from campusnest.users.utils import admin_requis, proprietaire_valide_requis
from .models import Chambre, Cite, PhotoCity, PhotoChambre
from .forms import ChambreForm, CiteForm, DateVisiteFormSet
from campusnest.favoris.models import Favori


# ─────────────────────────────────────────────
#  Vues publiques
# ─────────────────────────────────────────────

def home_view(request):
    chambres = Chambre.objects.filter(est_disponible=True).select_related("cite")
    cites    = Cite.objects.prefetch_related("chambres", "photos_cite").all()

    q = request.GET.get("q", "").strip()
    if q:
        chambres = chambres.filter(
            Q(description__icontains=q) | Q(cite__nom__icontains=q)
        )
        cites = cites.filter(Q(nom__icontains=q) | Q(adresse__icontains=q))

    type_chambre = request.GET.get("type", "")
    if type_chambre:
        chambres = chambres.filter(type=type_chambre)

    prix_max = request.GET.get("prix_max", "")
    if prix_max.isdigit():
        chambres = chambres.filter(loyer__lte=int(prix_max))

    if request.GET.get("meublee"):
        chambres = chambres.filter(meublee=True)
    if request.GET.get("wc"):
        chambres = chambres.filter(wc_interieur=True)
    if request.GET.get("cuisine"):
        chambres = chambres.filter(cuisine=True)

    return render(request, "logements/home.html", {
        "cites":         cites[:6],
        "chambres":      chambres[:20],
        "q":             q,
        "types_chambre": Chambre.Type.choices,
    })

def liste_cites_view(request):
    cites = Cite.objects.prefetch_related("chambres", "photos_cite").all()
    
    # Récupérer le mot-clé de recherche 'q'
    q = request.GET.get("q", "").strip()
    if q:
        # Recherche intelligente multicritère (par nom de la cité ou quartier/adresse)
        cites = cites.filter(
            Q(nom__icontains=q) | 
            Q(adresse__icontains=q) |
            Q(chambres__description__icontains=q)
        ).distinct()

    return render(request, "logements/liste_cites.html", {
        "cites": cites,
        "q": q
    })
    
def liste_chambres_view(request):
    chambres = Chambre.objects.filter(est_disponible=True, est_actif=True)\
                .select_related("cite")\
                .prefetch_related("photos")

    q = request.GET.get("q", "").strip()
    if q:
        chambres = chambres.filter(
            Q(description__icontains=q) | Q(cite__nom__icontains=q)
        )

    type_chambre = request.GET.get("type", "")
    if type_chambre:
        chambres = chambres.filter(type=type_chambre)

    prix_max = request.GET.get("prix_max", "")
    if prix_max.isdigit():
        chambres = chambres.filter(loyer__lte=int(prix_max))

    if request.GET.get("meublee"):
        chambres = chambres.filter(meublee=True)
    if request.GET.get("wc"):
        chambres = chambres.filter(wc_interieur=True)
    if request.GET.get("cuisine"):
        chambres = chambres.filter(cuisine=True)
    if request.user.is_authenticated and request.user.role == "client":
        chambres = chambres.annotate(
            est_favori=Exists(
                Favori.objects.filter(
                    client=request.user,
                    chambre=OuterRef("pk"),
                )
            )
        )
    else:
        chambres = chambres.annotate(
            est_favori=Value(False, output_field=BooleanField())
        )


    return render(request, "logements/liste_chambres.html", {
        "chambres":      chambres,
        "q":             q,
        "types_chambre": Chambre.Type.choices,
    })

def detail_cite_view(request, pk):
    cite     = get_object_or_404(Cite, pk=pk)
    chambres = cite.chambres.filter(est_disponible=True)
    # Photos de la cité
    photos_cite = PhotoCity.objects.filter(city=cite)
    return render(request, "logements/detail_cite.html", {
        "cite":       cite,
        "chambres":   chambres,
        "photos_cite": photos_cite,
    })


def detail_chambre_view(request, pk):
    chambre    = get_object_or_404(Chambre, pk=pk)
    photos     = PhotoChambre.objects.filter(chambre=chambre)
    avis       = chambre.avis.filter(est_visible=True).select_related("client")
    note_moy   = chambre.note_moyenne()
    similaires = Chambre.objects.filter(
        cite=chambre.cite, est_disponible=True
    ).exclude(pk=chambre.pk)[:3]
    est_favori = (
        request.user.is_authenticated
        and request.user.role == "client"
        and Favori.objects.filter(client=request.user, chambre=chambre).exists()
    )


    return render(request, "logements/detail_chambre.html", {
        "chambre":    chambre,
        "photos":     photos,
        "avis":       avis,
        "note_moy":   note_moy,
        "similaires": similaires,
        "est_favori": est_favori,
    })


# ─────────────────────────────────────────────
#  Vues propriétaire — Cités
# ─────────────────────────────────────────────

@proprietaire_valide_requis
def mes_cites_view(request):
    cites = Cite.objects.filter(
        proprietaire=request.user
    ).prefetch_related("chambres")
    return render(request, "logements/mes_cites.html", {"cites": cites})


@proprietaire_valide_requis
def ajouter_cite_view(request):
    # ✅ Correction : On ajoute request.FILES ici pour récupérer l'input HTML "photos"
    form = CiteForm(request.POST or None, request.FILES or None)
    
    if request.method == "POST" and form.is_valid():
        cite = form.save(commit=False)
        cite.proprietaire = request.user
        cite.save()

        # Cette boucle va maintenant parfaitement s'exécuter !
        for i, fichier in enumerate(request.FILES.getlist("photos")):
            PhotoCity.objects.create(
                city=cite,
                image=fichier,
                est_principale=(i == 0),
            )

        messages.success(request, f"Cité « {cite.nom} » créée avec succès.")
        return redirect("logements:mes_cites")

    return render(request, "logements/ajouter_cite.html", {"form": form})


@proprietaire_valide_requis
def modifier_cite_view(request, pk):
    cite = get_object_or_404(Cite, pk=pk, proprietaire=request.user)
    form = CiteForm(request.POST or None, instance=cite)

    if request.method == "POST" and form.is_valid():
        form.save()

        # ✅ Nouvelles photos de la cité
        for fichier in request.FILES.getlist("photos"):
            PhotoCity.objects.create(city=cite, image=fichier)

        messages.success(request, "Cité mise à jour.")
        return redirect("logements:mes_cites")

    photos_cite = PhotoCity.objects.filter(city=cite)
    return render(request, "logements/modifier_cite.html", {
        "form": form, "cite": cite, "photos_cite": photos_cite,
    })
@proprietaire_valide_requis
def supprimer_photo_view(request, pk):
    """Supprime une photo de chambre appartenant au propriétaire connecté."""
    photo = get_object_or_404(
        PhotoChambre, pk=pk, chambre__cite__proprietaire=request.user
    )
    chambre_pk = photo.chambre.pk
    if request.method == "POST":
        photo.image.delete(save=False)  # supprime le fichier disque
        photo.delete()
        messages.success(request, "Photo supprimée.")
    return redirect("logements:modifier_chambre", pk=chambre_pk)

@proprietaire_valide_requis
def supprimer_cite_view(request, pk):
    cite = get_object_or_404(Cite, pk=pk, proprietaire=request.user)
    if request.method == "POST":
        nom = cite.nom
        cite.delete()
        messages.success(request, f"Cité « {nom} » supprimée.")
    return redirect("logements:mes_cites")


@proprietaire_valide_requis
def supprimer_photo_cite_view(request, pk):
    """Suppression d'une photo de cité."""
    photo = get_object_or_404(PhotoCity, pk=pk, city__proprietaire=request.user)
    cite_pk = photo.city.pk
    if request.method == "POST":
        photo.image.delete(save=False)
        photo.delete()
        messages.success(request, "Photo supprimée.")
    return redirect("logements:modifier_cite", pk=cite_pk)


# ─────────────────────────────────────────────
#  Vues propriétaire — Chambres
# ─────────────────────────────────────────────

@proprietaire_valide_requis
def ajouter_chambre_view(request, cite_pk):
    cite = get_object_or_404(Cite, pk=cite_pk, proprietaire=request.user)

    form        = ChambreForm(request.POST or None, request.FILES or None)  # pas d'instance = création
    date_formset = DateVisiteFormSet(request.POST or None)  # pas d'instance = création

    if request.method == "POST":
        if form.is_valid() and date_formset.is_valid():
            # 1. Sauvegarder la chambre
            chambre      = form.save(commit=False)
            chambre.cite = cite
            chambre.save()

            # 2. Sauvegarder les dates de visite liées
            date_formset.instance = chambre
            date_formset.save()

            # 3. Sauvegarder les photos (jusqu'à 4)
            photos = request.FILES.getlist("photos")
            for i, photo_file in enumerate(request.FILES.getlist("photos")[:4]):
                PhotoChambre.objects.create(
                    chambre=chambre,
                    image=photo_file,
                    est_principale=(i == 0),
                )

            messages.success(request, "Chambre ajoutée avec succès.")
            return redirect("logements:mes_cites")
        else:
            # Afficher les erreurs dans la console pour debug
            print("Erreurs form:", form.errors)
            print("Erreurs formset:", date_formset.errors)
            print("Erreurs non_form:", date_formset.non_form_errors())
        
    # ── Préparer les 4 slots pour le template ──
    photo_slots = [None, None, None, None]

    return render(request, "logements/ajouter_chambre.html", {
        "form":         form,
        "date_formset": date_formset,
        "cite":         cite,
        "chambre":      None,
        "photos":       [],
        "photo_slots":  photo_slots,
    })


@proprietaire_valide_requis
def modifier_chambre_view(request, pk):
    chambre = get_object_or_404(Chambre, pk=pk, cite__proprietaire=request.user)
    cite    = chambre.cite

    form         = ChambreForm(request.POST or None, request.FILES or None, instance=chambre)
    date_formset = DateVisiteFormSet(request.POST or None, instance=chambre)

    if request.method == "POST":
        if form.is_valid() and date_formset.is_valid():
            form.save()
            date_formset.save()
            photos_existantes = chambre.photos.all()
            a_une_principale  = photos_existantes.filter(est_principale=True).exists()
            for i, photo_file in enumerate(request.FILES.getlist("photos")[:4]):
                PhotoChambre.objects.create(
                    chambre=chambre,
                    image=photo_file,
                    est_principale=(i == 0 and not a_une_principale),
                )
            messages.success(request, "Chambre modifiée avec succès.")
            return redirect("logements:mes_cites")
        else:
            print("Erreurs form:", form.errors)
            print("Erreurs formset:", date_formset.errors)

    # ── Préparer les 4 slots pour le template ──
    photos_qs = list(chambre.photos.all()[:4])
    # On complète avec None jusqu'à 4 éléments
    photo_slots = photos_qs + [None] * (4 - len(photos_qs))

    return render(request, "logements/ajouter_chambre.html", {
        "form":         form,
        "date_formset": date_formset,
        "cite":         cite,
        "chambre":      chambre,
        "photos":       photos_qs,
        "photo_slots":  photo_slots,
    })

@proprietaire_valide_requis
def supprimer_chambre_view(request, pk):
    chambre = get_object_or_404(Chambre, pk=pk, cite__proprietaire=request.user)
    if request.method == "POST":
        chambre.delete()
        messages.success(request, "Chambre supprimée.")
    return redirect("logements:mes_cites")


@proprietaire_valide_requis
def supprimer_photo_chambre_view(request, pk):
    """Suppression d'une photo de chambre."""
    photo   = get_object_or_404(PhotoChambre, pk=pk,
                                chambre__cite__proprietaire=request.user)
    chambre_pk = photo.chambre.pk
    if request.method == "POST":
        photo.image.delete(save=False)
        photo.delete()
        messages.success(request, "Photo supprimée.")
    return redirect("logements:modifier_chambre", pk=chambre_pk)


@proprietaire_valide_requis
def toggle_disponibilite_view(request, pk):
    chambre = get_object_or_404(Chambre, pk=pk, cite__proprietaire=request.user)
    if request.method == "POST":
        chambre.est_disponible = not chambre.est_disponible
        chambre.save(update_fields=["est_disponible"])
        etat = "disponible" if chambre.est_disponible else "indisponible"
        messages.success(request, f"Chambre marquée comme {etat}.")
    return redirect("logements:mes_cites")


# ─────────────────────────────────────────────
#  Vues admin
# ─────────────────────────────────────────────

@admin_requis
def liste_admin_view(request):
    chambres = Chambre.objects.select_related("cite", "cite__proprietaire").all()

    proprio_id = request.GET.get("proprietaire")
    if proprio_id:
        chambres = chambres.filter(cite__proprietaire_id=proprio_id)

    dispo = request.GET.get("disponible")
    if dispo == "1":
        chambres = chambres.filter(est_disponible=True)
    elif dispo == "0":
        chambres = chambres.filter(est_disponible=False)

    return render(request, "logements/liste_admin.html", {"chambres": chambres})


@admin_requis
def supprimer_logement_admin_view(request, pk):
    chambre = get_object_or_404(Chambre, pk=pk)
    if request.method == "POST":
        chambre.delete()
        messages.success(request, "Logement supprimé.")
    return redirect("logements:liste_admin")