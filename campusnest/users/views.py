from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Count, Q, Sum
import datetime


from .forms import (
    ConnexionForm,
    InscriptionClientForm,
    InscriptionProprietaireForm,
    ModifierProfilForm,
    MotDePasseOublieForm,
    VerifierOTPForm,
    NouveauMotDePasseForm,
)
from .models import LogActivite, OTPCode, ProfilProprietaire, Utilisateur
from .utils import enregistrer_log, admin_requis, proprietaire_valide_requis
from campusnest.contact.models import MessageContact
from campusnest.logements.models import Chambre, Cite
from campusnest.signalements.models import Signalement
from campusnest.reservations.models import Reservation
from campusnest.avis.models import Avis
from campusnest.favoris.models import Favori


def devenir_proprietaire(request):
    return render(request, "accounts/devenir_proprietaire.html")


# ─────────────────────────────────────────────
#  Helper — redirection par rôle
# ─────────────────────────────────────────────

def _redirection_par_role(user):
    if user.role == Utilisateur.Role.ADMIN:
        return "users:admin_dashboard"

    if user.role == Utilisateur.Role.PROPRIETAIRE:
        valide = ProfilProprietaire.objects.filter(
            utilisateur=user, est_valide=True
        ).exists()
        if valide:
            return "users:proprietaire_dashboard"
        return "users:validation_en_attente"

    return "users:client_dashboard"


# ─────────────────────────────────────────────
#  Connexion / Déconnexion
# ─────────────────────────────────────────────

def connexion_view(request):
    if request.user.is_authenticated:
        return redirect("users:dashboard")

    form = ConnexionForm(request, data=request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            enregistrer_log(request, user, "Connexion réussie")
            next_url = request.POST.get("next") or request.GET.get("next")
            return redirect(next_url or _redirection_par_role(user))
        else:
            enregistrer_log(request, None,
                f"Tentative connexion échouée — {request.POST.get('username', '?')}")

    return render(request, "accounts/connexion.html", {"form": form})


def deconnexion_view(request):
    if request.user.is_authenticated:
        enregistrer_log(request, request.user, "Déconnexion")
    logout(request)
    messages.success(request, "Vous avez été déconnecté.")
    return redirect("users:connexion")


# ─────────────────────────────────────────────
#  Inscription + vérification OTP email
# ─────────────────────────────────────────────

def inscription_view(request):
    if request.user.is_authenticated:
        return redirect("users:dashboard")

    type_compte = request.POST.get("type_compte") or request.GET.get("type", "client")
    FormClass   = InscriptionProprietaireForm if type_compte == "proprietaire" else InscriptionClientForm

    if request.method == "POST":
        # ⚠️ request.FILES est indispensable pour récupérer recto + verso
        form = FormClass(request.POST, request.FILES)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.username  = user.email
            user.save()

            # Le ProfilProprietaire est créé/mis à jour par form.save(commit=True)
            # via update_or_create dans InscriptionProprietaireForm.save().
            # On appelle donc save() à nouveau avec commit=True pour déclencher cette logique.
            if user.role == Utilisateur.Role.PROPRIETAIRE:
                # On relie les fichiers uploadés au profil via le formulaire
                form.instance = user
                form.save(commit=True)
            else:
                # Pour le client, un simple get_or_create n'est pas nécessaire
                # mais on s'assure que le user est bien sauvegardé
                pass

            otp = OTPCode.generer_pour(user)
            enregistrer_log(request, user, f"Inscription — rôle : {user.role}")

            send_mail(
                subject="CampusNest — Vérifiez votre adresse email",
                message=(
                    f"Bonjour {user.email},\n\n"
                    f"Votre code de vérification est : {otp.code}\n\n"
                    f"Valide {OTPCode.OTP_EXPIRY_MINUTES} minutes.\n\n"
                    f"L'équipe CampusNest IUT-FV"
                ),
                from_email=None,
                recipient_list=[user.email],
                fail_silently=False,
            )
            request.session["inscription_otp_email"] = user.email
            messages.success(request, "Un code de vérification a été envoyé à votre email.")
            return redirect("users:verifier_otp_inscription")

    else:
        form = FormClass()

    return render(request, "accounts/inscription.html", {
        "form": form,
        "type_compte": type_compte,
    })


def verifier_otp_inscription_view(request):
    email = request.session.get("inscription_otp_email")
    if not email:
        messages.error(request, "Session expirée. Recommencez l'inscription.")
        return redirect("users:inscription")

    form = VerifierOTPForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        code = form.cleaned_data["code"]
        try:
            user = Utilisateur.objects.get(email=email, is_active=False)
            otp  = OTPCode.objects.filter(
                utilisateur=user, code=code, utilise=False
            ).order_by("-cree_le").first()

            if otp and otp.est_valide:
                otp.marquer_utilise()
                user.is_active = True
                user.save(update_fields=["is_active"])
                request.session.pop("inscription_otp_email", None)
                enregistrer_log(request, user, "Email vérifié — compte activé")

                if user.role == Utilisateur.Role.PROPRIETAIRE:
                    messages.info(request,
                        "Email vérifié ! Votre compte attend la validation de l'administrateur.")
                    return redirect("users:validation_en_attente")

                login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                messages.success(request, "Bienvenue ! Votre compte est activé.")
                return redirect("users:dashboard")
            else:
                form.add_error("code", "Code incorrect ou expiré.")

        except Utilisateur.DoesNotExist:
            form.add_error("code", "Une erreur est survenue. Recommencez.")

    return render(request, "accounts/otp_verification.html", {
        "form": form,
        "email_masque":    _masquer_email(email),
        "expiry_minutes":  OTPCode.OTP_EXPIRY_MINUTES,
        "titre":           "Vérification de votre adresse email",
        "renvoyer_url":    "users:renvoyer_otp_inscription",
        "retour_url":      "users:inscription",
        "retour_texte":    "← Retour à l'inscription",
    })


def renvoyer_otp_inscription_view(request):
    email = request.session.get("inscription_otp_email")
    if not email:
        return redirect("users:inscription")
    try:
        user = Utilisateur.objects.get(email=email, is_active=False)
        otp  = OTPCode.generer_pour(user)
        send_mail(
            subject="CampusNest — Nouveau code de vérification",
            message=f"Votre nouveau code : {otp.code}\nValide {OTPCode.OTP_EXPIRY_MINUTES} min.",
            from_email=None,
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Utilisateur.DoesNotExist:
        pass
    messages.info(request, "Un nouveau code vous a été envoyé.")
    return redirect("users:verifier_otp_inscription")


def validation_en_attente_view(request):
    return render(request, "accounts/validation_en_attente.html")


# ─────────────────────────────────────────────
#  Reset mot de passe — OTP 3 étapes
# ─────────────────────────────────────────────

def mot_de_passe_oublie_view(request):
    form = MotDePasseOublieForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        try:
            user = Utilisateur.objects.get(email=email, is_active=True)
            otp  = OTPCode.generer_pour(user)
            send_mail(
                subject="CampusNest — Votre code de vérification",
                message=(
                    f"Bonjour {user.email},\n\n"
                    f"Votre code : {otp.code}\n"
                    f"Valide {OTPCode.OTP_EXPIRY_MINUTES} minutes.\n\n"
                    f"L'équipe CampusNest IUT-FV"
                ),
                from_email=None,
                recipient_list=[user.email],
                fail_silently=False,
            )
            enregistrer_log(request, user, "OTP généré — reset mot de passe")
        except Utilisateur.DoesNotExist:
            pass

        request.session["otp_email"] = email
        messages.success(request,
            "Si cet email est associé à un compte, un code vous a été envoyé.")
        return redirect("users:verifier_otp")

    return render(request, "accounts/mot_de_passe_oublie.html", {"form": form})


def verifier_otp_view(request):
    email = request.session.get("otp_email")
    if not email:
        messages.error(request, "Session expirée. Recommencez.")
        return redirect("users:mot_de_passe_oublie")

    form = VerifierOTPForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        code = form.cleaned_data["code"]
        try:
            user = Utilisateur.objects.get(email=email, is_active=True)
            otp  = OTPCode.objects.filter(
                utilisateur=user, code=code, utilise=False
            ).order_by("-cree_le").first()

            if otp and otp.est_valide:
                otp.marquer_utilise()
                request.session["reset_user_id"] = user.pk
                request.session.pop("otp_email", None)
                enregistrer_log(request, user, "OTP vérifié — reset accordé")
                return redirect("users:nouveau_mot_de_passe")
            else:
                form.add_error("code", "Code incorrect ou expiré.")
        except Utilisateur.DoesNotExist:
            form.add_error("code", "Une erreur est survenue.")

    return render(request, "accounts/otp_verification.html", {
        "form": form,
        "email_masque":        _masquer_email(email),
        "expiry_minutes":      OTPCode.OTP_EXPIRY_MINUTES,
        "titre":               "Réinitialisation du mot de passe",
        "renvoyer_url":        "users:renvoyer_otp",
        "retour_url":          "users:mot_de_passe_oublie",
        "retour_texte":        "← Changer d'email",
        "tentatives_restantes": _otp_tentatives_restantes(request),
    })


def renvoyer_otp_view(request):
    email = request.session.get("otp_email")
    if not email:
        return redirect("users:mot_de_passe_oublie")
    try:
        user = Utilisateur.objects.get(email=email, is_active=True)
        otp  = OTPCode.generer_pour(user)
        send_mail(
            subject="CampusNest — Nouveau code",
            message=f"Votre nouveau code : {otp.code}\nValide {OTPCode.OTP_EXPIRY_MINUTES} min.",
            from_email=None,
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Utilisateur.DoesNotExist:
        pass
    messages.info(request, "Un nouveau code vous a été envoyé.")
    return redirect("users:verifier_otp")


def nouveau_mot_de_passe_view(request):
    user_id = request.session.get("reset_user_id")
    if not user_id:
        messages.error(request, "Accès refusé. Vérifiez d'abord votre code.")
        return redirect("users:mot_de_passe_oublie")

    user = get_object_or_404(Utilisateur, pk=user_id)
    form = NouveauMotDePasseForm(user, request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        update_session_auth_hash(request, user)
        request.session.pop("reset_user_id", None)
        enregistrer_log(request, user, "Mot de passe réinitialisé via OTP")
        messages.success(request, "Mot de passe mis à jour. Connectez-vous.")
        return redirect("users:connexion")

    return render(request, "accounts/reinitialiser_mot_de_passe.html", {"form": form})


# ─────────────────────────────────────────────
#  Profil
# ─────────────────────────────────────────────

@login_required
def profil_view(request):
    form = ModifierProfilForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        enregistrer_log(request, request.user, "Profil modifié")
        messages.success(request, "Profil mis à jour.")
        return redirect("users:profil")
    return render(request, "accounts/profil.html", {"form": form})


# ─────────────────────────────────────────────
#  Dashboards
# ─────────────────────────────────────────────

@login_required
def dashboard_view(request):
    return redirect(_redirection_par_role(request.user))


@login_required
def client_dashboard_view(request):
    from campusnest.contact.models import Conversation

    aujourd_hui = timezone.now().date()

    toutes_reservations = Reservation.objects.filter(
        client=request.user
    ).select_related("chambre__cite")

    res_attente  = toutes_reservations.filter(statut="en_attente").count()
    res_validees = toutes_reservations.filter(statut="confirmee").count()
    res_annulees = toutes_reservations.filter(statut="annulee").count()

    reservation_active = toutes_reservations.filter(
        statut="confirmee",
        date_debut__lte=aujourd_hui,
        date_fin__gte=aujourd_hui,
    ).first()

    six_mois = []
    for i in range(5, -1, -1):
        d       = aujourd_hui - datetime.timedelta(days=30 * i)
        m_debut = d.replace(day=1)
        m_fin   = (m_debut + datetime.timedelta(days=32)).replace(day=1)
        count   = toutes_reservations.filter(
            date_demande__date__gte=m_debut,
            date_demande__date__lt=m_fin,
        ).count()
        six_mois.append({"mois": m_debut.strftime("%b"), "count": count})

    favoris_qs = (
        Favori.objects
        .filter(client=request.user)
        .select_related("chambre__cite")
        .prefetch_related("chambre__photos")
        .order_by("-date_ajout")
    )

    mes_messages_recents = MessageContact.objects.filter(
        expediteur=request.user
    ).order_by("-date_envoi")[:4]

    nb_signalements      = Signalement.objects.filter(client=request.user).count()
    chambres_disponibles = Chambre.objects.filter(est_disponible=True).count()

    return render(request, "accounts/client_dashboard.html", {
        "reservation_active":   reservation_active,
        "mes_reservations":     toutes_reservations.order_by("-date_demande")[:4],
        "mes_favoris_recents":  favoris_qs[:4],
        "mes_messages_recents": mes_messages_recents,
        "stats": {
            "attente":              res_attente,
            "validees":             res_validees,
            "annulees":             res_annulees,
            "total_reservations":   toutes_reservations.count(),
            "signalements":         nb_signalements,
            "nb_favoris":           favoris_qs.count(),
            "chambres_disponibles": chambres_disponibles,
            "six_mois_labels":      [m["mois"]  for m in six_mois],
            "six_mois_data":        [m["count"] for m in six_mois],
        },
    })


# ─────────────────────────────────────────────
#  Dashboard Propriétaire
# ─────────────────────────────────────────────

@proprietaire_valide_requis
def proprietaire_dashboard_view(request):
    cites    = Cite.objects.filter(proprietaire=request.user)
    chambres = Chambre.objects.filter(cite__proprietaire=request.user)

    q = request.GET.get("q", "").strip()
    if q:
        chambres = chambres.filter(
            Q(cite__nom__icontains=q) |
            Q(cite__adresse__icontains=q) |
            Q(description__icontains=q) |
            Q(type__icontains=q)
        )

    toutes_reservations = Reservation.objects.filter(
        chambre__cite__proprietaire=request.user
    ).select_related("client", "chambre__cite")

    total_chambres       = chambres.count()
    chambres_disponibles = chambres.filter(est_disponible=True).count()
    chambres_occupees    = total_chambres - chambres_disponibles
    taux_occupation      = round((chambres_occupees / total_chambres * 100) if total_chambres else 0)

    revenus_potentiels = chambres.filter(est_disponible=False).aggregate(
        total=Sum("loyer")
    )["total"] or 0

    aujourd_hui = timezone.now().date()
    debut_mois  = aujourd_hui.replace(day=1)
    reservations_actives_mois = toutes_reservations.filter(
        statut=Reservation.Statut.CONFIRMEE,
        date_debut__lte=aujourd_hui,
        date_fin__gte=debut_mois,
    )
    revenus_mois = sum(r.montant_total() for r in reservations_actives_mois)

    res_en_attente = toutes_reservations.filter(statut="en_attente").count()
    res_confirmees = toutes_reservations.filter(statut="confirmee").count()
    res_annulees   = toutes_reservations.filter(statut="annulee").count()

    six_mois = []
    for i in range(5, -1, -1):
        d          = aujourd_hui - datetime.timedelta(days=30 * i)
        mois_debut = d.replace(day=1)
        mois_fin   = (mois_debut + datetime.timedelta(days=32)).replace(day=1)
        count      = toutes_reservations.filter(
            date_demande__date__gte=mois_debut,
            date_demande__date__lt=mois_fin,
        ).count()
        six_mois.append({"mois": mois_debut.strftime("%b"), "count": count})

    repartition_types = list(
        chambres.values("type").annotate(nb=Count("id")).order_by("-nb")
    )

    avis_recents = (
        Avis.objects
        .filter(chambre__in=chambres, est_visible=True)
        .select_related("client", "chambre__cite")
        .order_by("-date_creation")[:4]
    )

    top_chambres = list(
        chambres.annotate(nb_res=Count("reservations"))
                .order_by("-nb_res")[:3]
    )

    return render(request, "accounts/proprietaire_dashboard.html", {
        "cites":    cites,
        "chambres": chambres[:8],
        "q":        q,
        "reservations_recentes": toutes_reservations[:5],
        "avis_recents":          avis_recents,
        "stats": {
            "total_cites":              cites.count(),
            "total_chambres":           total_chambres,
            "chambres_disponibles":     chambres_disponibles,
            "chambres_occupees":        chambres_occupees,
            "taux_occupation":          taux_occupation,
            "revenus_potentiels":       revenus_potentiels,
            "revenus_mois":             revenus_mois,
            "reservations_attente":     res_en_attente,
            "reservations_confirmees":  res_confirmees,
            "reservations_annulees":    res_annulees,
            "six_mois_labels":          [m["mois"]  for m in six_mois],
            "six_mois_data":            [m["count"] for m in six_mois],
            "repartition_types":        repartition_types,
            "top_chambres":             top_chambres,
        },
    })


# ─────────────────────────────────────────────
#  Dashboard Admin
# ─────────────────────────────────────────────

@admin_requis
def admin_dashboard_view(request):
    aujourd_hui = timezone.now().date()
    debut_mois  = aujourd_hui.replace(day=1)

    props_attente = Utilisateur.objects.filter(
        role=Utilisateur.Role.PROPRIETAIRE,
        profil_proprietaire__est_valide=False,
    )
    total_clients       = Utilisateur.objects.filter(role="client").count()
    total_proprietaires = Utilisateur.objects.filter(role="proprietaire").count()
    nouveaux_ce_mois    = Utilisateur.objects.filter(
        date_joined__date__gte=debut_mois
    ).count()

    total_cites       = Cite.objects.count()
    total_chambres    = Chambre.objects.count()
    chambres_dispo    = Chambre.objects.filter(est_disponible=True).count()
    chambres_occupees = total_chambres - chambres_dispo
    taux_occupation   = round((chambres_occupees / total_chambres * 100) if total_chambres else 0)

    toutes_res     = Reservation.objects.all()
    res_en_attente = toutes_res.filter(statut="en_attente").count()
    res_confirmees = toutes_res.filter(statut="confirmee").count()
    res_annulees   = toutes_res.filter(statut="annulee").count()
    res_ce_mois    = toutes_res.filter(date_demande__date__gte=debut_mois).count()

    tous_signalements = Signalement.objects.filter(statut="ouvert")
    sig_en_cours      = Signalement.objects.filter(statut="en_cours").count()
    sig_clotures      = Signalement.objects.filter(statut="cloture").count()

    repartition_sig = list(
        Signalement.objects.values("motif")
                           .annotate(nb=Count("id"))
                           .order_by("-nb")[:5]
    )

    six_mois_inscriptions = []
    six_mois_reservations = []
    for i in range(5, -1, -1):
        d       = aujourd_hui - datetime.timedelta(days=30 * i)
        m_debut = d.replace(day=1)
        m_fin   = (m_debut + datetime.timedelta(days=32)).replace(day=1)
        six_mois_inscriptions.append({
            "mois":  m_debut.strftime("%b"),
            "count": Utilisateur.objects.filter(
                date_joined__date__gte=m_debut,
                date_joined__date__lt=m_fin,
            ).count(),
        })
        six_mois_reservations.append({
            "mois":  m_debut.strftime("%b"),
            "count": toutes_res.filter(
                date_demande__date__gte=m_debut,
                date_demande__date__lt=m_fin,
            ).count(),
        })

    top_proprietaires = list(
        Utilisateur.objects.filter(role="proprietaire")
                           .annotate(nb_chambres=Count("cites__chambres"))
                           .order_by("-nb_chambres")[:5]
    )

    logs = LogActivite.objects.all()[:10]

    return render(request, "accounts/admin_dashboard.html", {
        "proprietaires_en_attente": props_attente,
        "signalements_ouverts":     tous_signalements[:5],
        "logs_recents":             logs,
        "top_proprietaires":        top_proprietaires,
        "stats": {
            "total_etudiants":           total_clients,
            "total_proprietaires":       total_proprietaires,
            "nouveaux_ce_mois":          nouveaux_ce_mois,
            "proprietaires_attente":     props_attente.count(),
            "total_cites":               total_cites,
            "total_chambres":            total_chambres,
            "chambres_disponibles":      chambres_dispo,
            "chambres_occupees":         chambres_occupees,
            "taux_occupation":           taux_occupation,
            "total_reservations":        toutes_res.count(),
            "reservations_attente":      res_en_attente,
            "reservations_confirmees":   res_confirmees,
            "reservations_annulees":     res_annulees,
            "reservations_ce_mois":      res_ce_mois,
            "signalements_ouverts":      tous_signalements.count(),
            "signalements_en_cours":     sig_en_cours,
            "signalements_clotures":     sig_clotures,
            "repartition_signalements":  repartition_sig,
            "six_mois_labels":           [m["mois"]  for m in six_mois_inscriptions],
            "six_mois_inscriptions":     [m["count"] for m in six_mois_inscriptions],
            "six_mois_reservations":     [m["count"] for m in six_mois_reservations],
        },
    })


@admin_requis
def valider_proprietaire_view(request, pk):
    profil = get_object_or_404(ProfilProprietaire, utilisateur__pk=pk)
    if request.method == "POST":
        profil.est_valide      = True
        profil.date_validation = timezone.now()
        profil.save()
        enregistrer_log(request, request.user,
            f"Propriétaire validé : {profil.utilisateur.email}")
        messages.success(request,
            f"Compte de {profil.utilisateur.get_full_name()} validé.")
    return redirect("users:admin_dashboard")


@admin_requis
def suspendre_compte_view(request, pk):
    user = get_object_or_404(Utilisateur, pk=pk)
    if request.method == "POST":
        user.is_active = False
        user.save(update_fields=["is_active"])
        enregistrer_log(request, request.user, f"Compte suspendu : {user.email}")
        messages.warning(request, f"Compte de {user.get_full_name()} suspendu.")
    return redirect("users:admin_dashboard")


@admin_requis
def gerer_proprietaire_view(request, pk):
    profil = get_object_or_404(ProfilProprietaire, utilisateur__pk=pk)
    user   = profil.utilisateur

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "valider":
            profil.est_valide      = True
            profil.date_validation = timezone.now()
            profil.save()
            user.is_active = True
            user.save(update_fields=["is_active"])
            enregistrer_log(request, request.user, f"Propriétaire validé : {user.email}")
            messages.success(request, f"Le compte de {user.get_full_name()} a été validé.")

        elif action == "suspendre":
            user.is_active = False
            user.save(update_fields=["is_active"])
            enregistrer_log(request, request.user, f"Compte suspendu : {user.email}")
            messages.warning(request, f"Le compte de {user.get_full_name()} a été suspendu.")

        return redirect("users:admin_dashboard")

    cites        = Cite.objects.filter(proprietaire=user)
    chambres     = Chambre.objects.filter(cite__proprietaire=user)
    reservations = Reservation.objects.filter(chambre__cite__proprietaire=user).count()

    return render(request, "accounts/gerer_proprietaire.html", {
        "profil":          profil,
        "proprietaire":    user,
        "nb_cites":        cites.count(),
        "nb_chambres":     chambres.count(),
        "nb_reservations": reservations,
    })


@admin_requis
def liste_proprietaires_view(request):
    proprietaires = Utilisateur.objects.filter(
        role=Utilisateur.Role.PROPRIETAIRE
    ).select_related("profil_proprietaire").order_by("profil_proprietaire__est_valide", "nom")

    return render(request, "accounts/liste_proprietaires.html", {
        "proprietaires": proprietaires,
    })


# ─────────────────────────────────────────────
#  Helpers privés
# ─────────────────────────────────────────────

def _masquer_email(email: str) -> str:
    try:
        local, domain = email.split("@")
        return f"{local[0]}***@{domain}"
    except Exception:
        return email


def _otp_tentatives_restantes(request) -> int:
    return max(0, 5 - request.session.get("otp_attempts", 0))