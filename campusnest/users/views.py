from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import redirect, render
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
from .models import LogActivite, OTPCode, Utilisateur
from .utils import enregistrer_log, admin_requis, proprietaire_valide_requis

# ─────────────────────────────────────────────
#  Connexion / Déconnexion
# ─────────────────────────────────────────────
# Extraire la partie avant le @ de l'email

def connexion_view(request):
    if request.user.is_authenticated:
        return redirect("users:dashboard")

    form = ConnexionForm(request, data=request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            enregistrer_log(request, user, "Connexion réussie")

            # Redirection selon le rôle
            next_url = request.POST.get("next") or request.GET.get("next")
            if next_url:
                return redirect(next_url)
            return redirect(_redirection_par_role(user))
        else:
            enregistrer_log(
                request,
                None,
                f"Tentative connexion échouée — {request.POST.get('username', '?')}",
            )

    return render(request, "accounts/connexion.html", {"form": form})


def deconnexion_view(request):
    if request.user.is_authenticated:
        enregistrer_log(request, request.user, "Déconnexion")
    logout(request)
    messages.success(request, "Vous avez été déconnecté.")
    return redirect("users:connexion")


def _redirection_par_role(user):
    """Retourne l'URL du tableau de bord selon le rôle."""
    if user.role == Utilisateur.Role.ADMIN:
        return "admin_dashboard"
    if user.role == Utilisateur.Role.PROPRIETAIRE:
        # Vérifier si le compte propriétaire est validé
        try:
            if not user.proprietaire.est_valide:
                return "users:validation_en_attente"
        except Exception:
            pass
        return "users:proprietaire_dashboard"
    return "users:dashboard"


# ─────────────────────────────────────────────
#  Inscription
# ─────────────────────────────────────────────
def inscription_view(request):
    if request.user.is_authenticated:
        return redirect("users:dashboard")

    type_compte = request.POST.get("type_compte") or request.GET.get("type", "client")

    if type_compte == "proprietaire":
        form = InscriptionProprietaireForm(request.POST or None)
    else:
        form = InscriptionClientForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.est_actif = False  # ← inactif jusqu'à vérification email
        user.save()
        enregistrer_log(request, user, f"Inscription — rôle : {user.role}")

        # Générer et envoyer le code OTP
        otp = OTPCode.generer_pour(user)
        send_mail(
            subject="CampusNest — Vérifiez votre adresse email",
            message=(
                f"Bonjour {user.nom_email},\n\n"
                f"Merci de vous être inscrit sur CampusNest.\n"
                f"Votre code de vérification est : {otp.code}\n\n"
                f"Il est valide pendant {OTPCode.OTP_EXPIRY_MINUTES} minutes.\n"
                f"Si vous n'avez pas créé ce compte, ignorez cet email.\n\n"
                f"L'équipe CampusNest IUT-FV"
            ),
            from_email="noreply@campusnest.iutfv.cm",
            recipient_list=[user.email],
            fail_silently=False,
        )

        # Stocker l'email en session pour la vérification
        request.session["inscription_otp_email"] = user.email
        request.session["inscription_type_compte"] = user.role

        messages.success(
            request,
            "Un code de vérification a été envoyé à votre adresse email."
        )
        return redirect("users:verifier_otp_inscription")

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
            user = Utilisateur.objects.get(email=email, est_actif=False)
            otp = OTPCode.objects.filter(
                utilisateur=user,
                code=code,
                utilise=False,
            ).order_by("-cree_le").first()

            if otp and otp.est_valide:
                otp.marquer_utilise()

                # Activer le compte
                user.est_actif = True
                user.save(update_fields=["est_actif"])

                request.session.pop("inscription_otp_email", None)
                enregistrer_log(request, user, "Email vérifié — compte activé")

                if user.role == Utilisateur.Role.PROPRIETAIRE:
                    messages.info(
                        request,
                        "Email vérifié ! Votre compte attend la validation par l'administrateur.",
                    )
                    return redirect("users:validation_en_attente")

                # Auto-connexion pour les clients
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                messages.success(request, f"Bienvenue, {user.prenom} ! Votre compte est activé.")
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
        user = Utilisateur.objects.get(email=email, est_actif=False)
        otp = OTPCode.generer_pour(user)
        send_mail(
            subject="CampusNest — Nouveau code de vérification",
            message=(
                f"Bonjour {user.email},\n\n"
                f"Votre nouveau code est : {otp.code}\n\n"
                f"Il est valide {OTPCode.OTP_EXPIRY_MINUTES} minutes.\n\n"
                f"L'équipe CampusNest IUT-FV"
            ),
            from_email="noreply@campusnest.iutfv.cm",
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Utilisateur.DoesNotExist:
        pass

    messages.info(request, "Un nouveau code vous a été envoyé.")
    return redirect("users:verifier_otp_inscription")

# ─────────────────────────────────────────────
#  En attente de validation (propriétaire)
# ─────────────────────────────────────────────

def validation_en_attente_view(request):
    return render(request, "accounts/validation_en_attente.html")



# ─────────────────────────────────────────────
#  Réinitialisation mot de passe — FLUX OTP
#
#  Étape 1 : /comptes/mot-de-passe-oublie/
#            → saisie email → génère OTP → redirige vers étape 2
#
#  Étape 2 : /comptes/verifier-otp/
#            → saisie du code à 6 chiffres → stocke user_id en session
#            → redirige vers étape 3
#
#  Étape 3 : /comptes/nouveau-mot-de-passe/
#            → saisie nouveau mot de passe → connexion auto
# ─────────────────────────────────────────────
 
def mot_de_passe_oublie_view(request):
    """
    Étape 1 — L'utilisateur entre son email.
    Un code OTP à 6 chiffres est généré et affiché dans la console (dev).
    En production, il est envoyé par email SMTP.
    Template : templates/accounts/mot_de_passe_oublie.html
    """
    form = MotDePasseOublieForm(request.POST or None)
 
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
 
        try:
            user = Utilisateur.objects.get(email=email, est_actif=True)
            otp  = OTPCode.generer_pour(user)
 
            # ── Envoi du code ────────────────────────────────────────────
            # EMAIL_BACKEND = console → le code s'affiche dans le terminal.
            # Passe à smtp.EmailBackend en production.
            send_mail(
                subject="CampusNest — Votre code de vérification",
                message=(
                    f"Bonjour {user.email},\n\n"
                    f"Votre code de vérification est : {otp.code}\n\n"
                    f"Il est valide pendant {OTPCode.OTP_EXPIRY_MINUTES} minutes.\n"
                    f"Si vous n'avez pas fait cette demande, ignorez cet email.\n\n"
                    f"L'équipe CampusNest IUT-FV"
                ),
                from_email="noreply@campusnest.iutfv.cm",
                recipient_list=[user.email],
                fail_silently=False,
            )
            enregistrer_log(request, user, "OTP généré pour reset mot de passe")
 
        except Utilisateur.DoesNotExist:
            pass  # Ne pas révéler si l'email existe
 
        # Stocker l'email en session pour l'étape 2
        # (même si l'email n'existe pas → même comportement visible)
        request.session["otp_email"] = email
 
        messages.success(request,
            "Si cet email est associé à un compte, un code à 6 chiffres "
            "vous a été envoyé. Vérifiez votre boîte mail (et les spams).")
        return redirect("users:verifier_otp")
 
    return render(request, "accounts/mot_de_passe_oublie.html", {"form": form})


#vérifier opt

def verifier_otp_view(request):
    """
    Étape 2 — L'utilisateur saisit le code à 6 chiffres reçu par email.
    En cas de succès, l'ID de l'utilisateur est stocké en session et on
    redirige vers le formulaire de nouveau mot de passe.
    Template : templates/accounts/otp_verification.html
    """
    email = request.session.get("otp_email")
    if not email:
        messages.error(request, "Session expirée. Recommencez.")
        return redirect("users:mot_de_passe_oublie")
 
    form = VerifierOTPForm(request.POST or None)
 
    if request.method == "POST" and form.is_valid():
        code = form.cleaned_data["code"]
 
        try:
            user = Utilisateur.objects.get(email=email, est_actif=True)
            otp  = OTPCode.objects.filter(
                utilisateur=user,
                code=code,
                utilise=False,
            ).order_by("-cree_le").first()
 
            if otp and otp.est_valide:
                otp.marquer_utilise()
                # Stocker l'accès autorisé en session
                request.session["reset_user_id"] = user.pk
                request.session.pop("otp_email", None)
                enregistrer_log(request, user, "OTP vérifié — accès reset accordé")
                return redirect("users:nouveau_mot_de_passe")
            else:
                form.add_error("code",
                    "Code incorrect ou expiré. Vérifiez le code ou demandez-en un nouveau.")
 
        except Utilisateur.DoesNotExist:
            form.add_error("code", "Une erreur est survenue. Recommencez.")
 
    tentatives_restantes = _otp_tentatives_restantes(request)
 
    return render(request, "accounts/otp_verification.html", {
        "form":                form,
        "email_masque":        _masquer_email(email),
        "expiry_minutes":      OTPCode.OTP_EXPIRY_MINUTES,
        "titre": "Vérification",
        "renvoyer_url": "users:renvoyer_otp",
        "retour_url": "users:mot_de_passe_oublie",
        "retour_texte": "← Changer d'email",
        "tentatives_restantes": tentatives_restantes,
    })



#nouveau mot de passe

def nouveau_mot_de_passe_view(request):
    """
    Étape 3 — L'utilisateur saisit son nouveau mot de passe.
    Accessible uniquement si reset_user_id est en session (OTP validé).
    Template : templates/accounts/reinitialiser_mot_de_passe.html
    """
    user_id = request.session.get("reset_user_id")
    if not user_id:
        messages.error(request, "Accès refusé. Vérifiez d'abord votre code OTP.")
        return redirect("users:mot_de_passe_oublie")
 
    try:
        user = Utilisateur.objects.get(pk=user_id)
    except Utilisateur.DoesNotExist:
        messages.error(request, "Utilisateur introuvable.")
        return redirect("users:mot_de_passe_oublie")
 
    form = NouveauMotDePasseForm(user, request.POST or None)
 
    if request.method == "POST" and form.is_valid():
        form.save()
        update_session_auth_hash(request, user)
        request.session.pop("reset_user_id", None)
        enregistrer_log(request, user, "Mot de passe réinitialisé via OTP")
        messages.success(request,
            "Votre mot de passe a été mis à jour. Vous pouvez maintenant vous connecter.")
        return redirect("users:connexion")
 
    return render(request, "accounts/reinitialiser_mot_de_passe.html", {"form": form})


def renvoyer_otp_view(request):
    """
    Renvoie un nouveau code OTP si l'ancien a expiré.
    Accessible uniquement si otp_email est en session.
    """
    email = request.session.get("otp_email")
    if not email:
        return redirect("users:mot_de_passe_oublie")

    try:
        user = Utilisateur.objects.get(email=email, est_actif=True)
        otp  = OTPCode.generer_pour(user)
        send_mail(
            subject="CampusNest — Nouveau code de vérification",
            message=(
                f"Bonjour {user.email},\n\n"
                f"Votre nouveau code est : {otp.code}\n\n"
                f"Il est valide {OTPCode.OTP_EXPIRY_MINUTES} minutes.\n\n"
                f"L'équipe CampusNest IUT-FV"
            ),
            from_email="noreply@campusnest.iutfv.cm",
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Utilisateur.DoesNotExist:
        pass

    messages.info(request, "Un nouveau code vous a été envoyé.")
    return redirect("users:verifier_otp")





def _envoyer_email_reinitialisation(request, user):
    site = get_current_site(request)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    sujet = "CampusNest — Réinitialisation de votre mot de passe"
    corps = render_to_string("accounts/email/reinitialisation.txt", {
        "user": user,
        "domain": site.domain,
        "uid": uid,
        "token": token,
        "protocol": "https" if request.is_secure() else "http",
    })
    send_mail(sujet, corps, "noreply@campusnest.iutfv.cm", [user.email])


def reinitialiser_mot_de_passe_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Utilisateur.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Utilisateur.DoesNotExist):
        user = None

    token_valide = user and default_token_generator.check_token(user, token)

    if not token_valide:
        messages.error(request, "Ce lien de réinitialisation est invalide ou a expiré.")
        return redirect("mot_de_passe_oublie")

    form = NouveauMotDePasseForm(user, request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        update_session_auth_hash(request, user)
        enregistrer_log(request, user, "Mot de passe réinitialisé")
        messages.success(request, "Votre mot de passe a été mis à jour. Connectez-vous.")
        return redirect("connexion")

    return render(request, "accounts/reinitialiser_mot_de_passe.html", {
        "form": form,
        "uidb64": uidb64,
        "token": token,
    })


# ─────────────────────────────────────────────
#  Profil utilisateur
# ─────────────────────────────────────────────

@login_required
def profil_view(request):
    form = ModifierProfilForm(request.POST or None, instance=request.user)

    if request.method == "POST" and form.is_valid():
        form.save()
        enregistrer_log(request, request.user, "Profil modifié")
        messages.success(request, "Votre profil a été mis à jour.")
        return redirect("users:profil")

    return render(request, "accounts/profil.html", {"form": form})


# ─────────────────────────────────────────────
#  Dashboard générique (redirige vers le bon)
# ─────────────────────────────────────────────

@login_required
def dashboard_view(request):
    return redirect(_redirection_par_role(request.user))

@login_required
def client_dashboard_view(request):
    from logements.models import Chambre, Cite
    from reservations.models import Reservation
    cites    = Cite.objects.all()[:6]
    chambres = Chambre.objects.filter(est_disponible=True)[:8]
    mes_reservations = Reservation.objects.filter(
        client=request.user).select_related("chambre__cite")[:3]
    return render(request, "logements/home.html", {
        "cites": cites, "chambres": chambres,
        "mes_reservations": mes_reservations,
    })
 
 
from campusnest.users.utils import proprietaire_valide_requis, admin_requis
 
@proprietaire_valide_requis
def proprietaire_dashboard_view(request):
    from logements.models import Chambre, Cite
    from reservations.models import Reservation
    cites     = Cite.objects.filter(proprietaire=request.user)
    chambres  = Chambre.objects.filter(cite__proprietaire=request.user)
    resa_rece = Reservation.objects.filter(
        chambre__cite__proprietaire=request.user
    ).select_related("client", "chambre")[:5]
    stats = {
        "total_chambres":       chambres.count(),
        "chambres_disponibles": chambres.filter(est_disponible=True).count(),
        "reservations_attente": resa_rece.filter(statut="en_attente").count(),
        "total_cites":          cites.count(),
    }
    return render(request, "accounts/proprietaire_dashboard.html", {
        "cites": cites, "chambres": chambres[:8],
        "reservations_recentes": resa_rece, "stats": stats,
    })
 
 
@admin_requis
def admin_dashboard_view(request):
    from logements.models import Chambre, Cite
    from reservations.models import Reservation
    from signalements.models import Signalement
    props_attente     = Utilisateur.objects.filter(
        role=Utilisateur.Role.PROPRIETAIRE, proprietaire__est_valide=False)
    signalements      = Signalement.objects.filter(statut="ouvert")[:5]
    logs_recents      = LogActivite.objects.all()[:10]
    stats = {
        "total_etudiants":       Utilisateur.objects.filter(role=Utilisateur.Role.CLIENT).count(),
        "total_proprietaires":   Utilisateur.objects.filter(role=Utilisateur.Role.PROPRIETAIRE).count(),
        "total_cites":           Cite.objects.count(),
        "total_chambres":        Chambre.objects.count(),
        "chambres_disponibles":  Chambre.objects.filter(est_disponible=True).count(),
        "proprietaires_attente": props_attente.count(),
        "signalements_ouverts":  signalements.count(),
    }
    return render(request, "accounts/admin_dashboard.html", {
        "proprietaires_en_attente": props_attente,
        "signalements_ouverts": signalements,
        "logs_recents": logs_recents,
        "stats": stats,
    })
 
 
@admin_requis
def valider_proprietaire_view(request, pk):
    from users.models import Proprietaire
    p = Proprietaire.objects.get(pk=pk)
    p.est_valide = True; p.date_validation = timezone.now(); p.save()
    enregistrer_log(request, request.user, f"Propriétaire validé : {p.email}")
    messages.success(request, f"Compte de {p.get_full_name()} validé.")
    return redirect("users:admin_dashboard")
 
 
@admin_requis
def suspendre_compte_view(request, pk):
    user = Utilisateur.objects.get(pk=pk)
    user.est_actif = False; user.save(update_fields=["est_actif"])
    enregistrer_log(request, request.user, f"Compte suspendu : {user.email}")
    messages.warning(request, f"Compte de {user.get_full_name()} suspendu.")
    return redirect("users:admin_dashboard")
 
 
# ─────────────────────────────────────────────
#  Helpers privés
# ─────────────────────────────
# ────────────────
 
def _masquer_email(email: str) -> str:
    """ex: jean.mbarga@cm  →  j***@cm"""
    try:
        local, domain = email.split("@")
        return f"{local[0]}***@{domain}"
    except Exception:
        return email
 
 
def _otp_tentatives_restantes(request) -> int:
    """Limite basique anti-brute-force côté session (max 5 essais)."""
    key  = "otp_attempts"
    nb   = request.session.get(key, 0)
    return max(0, 5 - nb)
 
