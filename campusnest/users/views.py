# campusnest/users/views.py
# VERSION CORRIGÉE COMPLÈTE
# Corrections apportées :
#   1. _redirection_par_role → user.proprietaire → ProfilProprietaire.objects.filter()
#   2. admin_dashboard_view  → proprietaire__est_valide → profil_proprietaire__est_valide
#   3. valider_proprietaire_view → Proprietaire → ProfilProprietaire

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

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

def devenir_proprietaire(request):
    return render(request, "accounts/devenir_proprietaire.html")


# ─────────────────────────────────────────────
#  Helper — redirection par rôle  ← CORRIGÉ
# ────────────────────────────────────────────

def _redirection_par_role(user):
    if user.role == Utilisateur.Role.ADMIN:
        return "users:admin_dashboard"

    if user.role == Utilisateur.Role.PROPRIETAIRE:
        # ✅ Correction : on utilise ProfilProprietaire.objects.filter()
        # au lieu de user.proprietaire qui n'existe pas
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
    FormClass = InscriptionProprietaireForm if type_compte == "proprietaire" else InscriptionClientForm
    form = FormClass(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.is_active = False
        user.username = user.email
        user.save()
        enregistrer_log(request, user, f"Inscription — rôle : {user.role}")

        otp = OTPCode.generer_pour(user)
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

    return render(request, "accounts/inscription.html", {
        "form": form, "type_compte": type_compte,
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
            otp = OTPCode.objects.filter(
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
                messages.success(request, f"Bienvenue ! Votre compte est activé.")
                return redirect("users:dashboard")
            else:
                form.add_error("code", "Code incorrect ou expiré.")

        except Utilisateur.DoesNotExist:
            form.add_error("code", "Une erreur est survenue. Recommencez.")

    return render(request, "accounts/otp_verification.html", {
        "form": form,
        "email_masque": _masquer_email(email),
        "expiry_minutes": OTPCode.OTP_EXPIRY_MINUTES,
        "titre": "Vérification de votre adresse email",
        "renvoyer_url": "users:renvoyer_otp_inscription",
        "retour_url": "users:inscription",
        "retour_texte": "← Retour à l'inscription",
    })


def renvoyer_otp_inscription_view(request):
    email = request.session.get("inscription_otp_email")
    if not email:
        return redirect("users:inscription")
    try:
        user = Utilisateur.objects.get(email=email, is_active=False)
        otp = OTPCode.generer_pour(user)
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
            otp = OTPCode.generer_pour(user)
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
            otp = OTPCode.objects.filter(
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
        "email_masque": _masquer_email(email),
        "expiry_minutes": OTPCode.OTP_EXPIRY_MINUTES,
        "titre": "Réinitialisation du mot de passe",
        "renvoyer_url": "users:renvoyer_otp",
        "retour_url": "users:mot_de_passe_oublie",
        "retour_texte": "← Changer d'email",
        "tentatives_restantes": _otp_tentatives_restantes(request),
    })


def renvoyer_otp_view(request):
    email = request.session.get("otp_email")
    if not email:
        return redirect("users:mot_de_passe_oublie")
    try:
        user = Utilisateur.objects.get(email=email, is_active=True)
        otp = OTPCode.generer_pour(user)
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
    from campusnest.logements.models import Chambre, Cite
    from campusnest.reservations.models import Reservation
    return render(request, "accounts/client_dashboard.html", {
        "cites":            Cite.objects.all()[:6],
        "chambres":         Chambre.objects.filter(est_disponible=True)[:8],
        "mes_reservations": Reservation.objects.filter(
            client=request.user).select_related("chambre__cite")[:3],
    })


@proprietaire_valide_requis
def proprietaire_dashboard_view(request):
    from campusnest.logements.models import Chambre, Cite
    from campusnest.reservations.models import Reservation
    
    cites    = Cite.objects.filter(proprietaire=request.user)
    chambres = Chambre.objects.filter(cite__proprietaire=request.user)
    
    # 1. On ne met PAS de [:5] ici pour pouvoir filtrer et compter librement ensuite
    toutes_les_reservations = Reservation.objects.filter(
        chambre__cite__proprietaire=request.user
    ).select_related("client", "chambre")
    
    return render(request, "accounts/proprietaire_dashboard.html", {
        "cites": cites,
        "chambres": chambres[:8],
        # 2. On applique le découpage ici, juste pour l'affichage du tableau
        "reservations_recentes": toutes_les_reservations[:5],
        "stats": {
            "total_cites":          cites.count(),
            "total_chambres":       chambres.count(),
            "chambres_disponibles": chambres.filter(est_disponible=True).count(),
            # 3. Fonctionne parfaitement maintenant car la requête de base n'est pas bridée
            "reservations_attente": toutes_les_reservations.filter(statut="en_attente").count(),
        },
    })


@admin_requis
def admin_dashboard_view(request):
    from campusnest.logements.models import Chambre, Cite
    from campusnest.signalements.models import Signalement

    props_attente = Utilisateur.objects.filter(
        role=Utilisateur.Role.PROPRIETAIRE,
        profil_proprietaire__est_valide=False,
    )
    
    # Requête complète pour le comptage global
    tous_les_signalements = Signalement.objects.filter(statut="ouvert")
    logs = LogActivite.objects.all()[:10]

    return render(request, "accounts/admin_dashboard.html", {
        "proprietaires_en_attente": props_attente,
        "signalements_ouverts":     tous_les_signalements[:5], # Découpage pour l'affichage
        "logs_recents":             logs,
        "stats": {
            "total_etudiants":       Utilisateur.objects.filter(role="client").count(),
            "total_proprietaires":   Utilisateur.objects.filter(role="proprietaire").count(),
            "total_cites":           Cite.objects.count(),
            "total_chambres":        Chambre.objects.count(),
            "chambres_disponibles":  Chambre.objects.filter(est_disponible=True).count(),
            "proprietaires_attente": props_attente.count(),
            "signalements_ouverts":  tous_les_signalements.count(), # Compte réel de la BDD
        },
    })


@admin_requis
def valider_proprietaire_view(request, pk):
    # ✅ Correction : ProfilProprietaire (pas Proprietaire)
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