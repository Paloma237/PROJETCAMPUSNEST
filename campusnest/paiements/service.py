"""
campusnest/paiements/services.py

Couche service Mobile Money.
En production, remplacer simulate_paiement() par l'appel à l'API réelle
(ex: CinetPay, Monetbil, FedaPay, ou SDK MTN MoMo / Orange Money direct).
"""
import logging
import re

logger = logging.getLogger(__name__)


# ── Préfixes valides par opérateur (Cameroun) ────────────────────────────────
PREFIXES_MTN    = ("650", "651", "652", "653", "654", "670", "671", "672",
                   "673", "674", "675", "676", "677", "678", "679", "680",
                   "681", "682", "683", "684", "685", "686", "687", "688", "689")

PREFIXES_ORANGE = ("655", "656", "657", "658", "659", "690", "691", "692",
                   "693", "694", "695", "696", "697", "698", "699")


def nettoyer_numero(numero: str) -> str:
    """Supprime espaces, tirets, préfixe pays (+237 / 237)."""
    numero = re.sub(r"[\s\-]", "", numero)
    if numero.startswith("+237"):
        numero = numero[4:]
    elif numero.startswith("237") and len(numero) == 12:
        numero = numero[3:]
    return numero


def valider_numero(numero: str, operateur: str) -> tuple[bool, str]:
    """
    Vérifie que le numéro est cohérent avec l'opérateur choisi.
    Retourne (ok: bool, message: str).
    """
    numero = nettoyer_numero(numero)

    if not re.fullmatch(r"\d{9}", numero):
        return False, "Le numéro doit contenir 9 chiffres (sans indicatif pays)."

    prefixe = numero[:3]

    if operateur == "mtn" and prefixe not in PREFIXES_MTN:
        return False, f"Le numéro {numero} ne correspond pas à un numéro MTN."

    if operateur == "orange" and prefixe not in PREFIXES_ORANGE:
        return False, f"Le numéro {numero} ne correspond pas à un numéro Orange."

    return True, "Numéro valide."


def simulate_paiement(paiement) -> dict:
    """
    Simule l'appel à l'API Mobile Money.

    Règle de simulation :
      - Numéro se terminant par un chiffre pair  → succès
      - Numéro se terminant par un chiffre impair → échec

    En production, remplacer ce bloc par l'appel HTTP à l'opérateur.

    Retourne :
        {"succes": bool, "reference": str, "message": str}
    """
    numero = nettoyer_numero(paiement.numero_telephone)
    dernier_chiffre = int(numero[-1])

    if dernier_chiffre % 2 == 0:
        logger.info("Simulation paiement RÉUSSI pour %s", numero)
        return {
            "succes":    True,
            "reference": paiement.reference,
            "message":   "Paiement effectué avec succès.",
        }
    else:
        logger.warning("Simulation paiement ÉCHOUÉ pour %s", numero)
        return {
            "succes":  False,
            "reference": paiement.reference,
            "message": "Échec du paiement. Solde insuffisant ou numéro non reconnu.",
        }