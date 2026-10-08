import secrets
import smtplib
import ssl
from email.message import EmailMessage

import streamlit as st

from database import connexion, hasher_mot_de_passe, verifier_mot_de_passe

DUREE_VALIDITE_MIN = 15
DELAI_RENVOI_SEC = 60
MAX_TENTATIVES = 5
MOT_DE_PASSE_MIN = 8

MSG_INVALIDE = "Code invalide ou expiré. Vérifiez l'adresse e-mail et le code."


# ============================================================
# LOGIQUE
# ============================================================

def _smtp_configure():
    try:
        return "smtp" in st.secrets
    except Exception:
        return False


def _envoyer_email(destinataire, nom, code):
    cfg = st.secrets["smtp"]

    message = EmailMessage()
    message["Subject"] = "FinTech PME : code de réinitialisation"
    message["From"] = cfg.get("expediteur", cfg["user"])
    message["To"] = destinataire
    message.set_content(
        f"Bonjour {nom},\n\n"
        f"Votre code de réinitialisation est : {code}\n\n"
        f"Il est valable {DUREE_VALIDITE_MIN} minutes et ne peut servir "
        f"qu'une seule fois.\n\n"
        "Si vous n'êtes pas à l'origine de cette demande, ignorez ce message : "
        "votre mot de passe n'a pas été modifié.\n\n"
        "FinTech PME"
    )

    port = int(cfg.get("port", 465))
    contexte = ssl.create_default_context()

    if port == 465:
        with smtplib.SMTP_SSL(cfg["host"], port, context=contexte, timeout=15) as s:
            s.login(cfg["user"], cfg["password"])
            s.send_message(message)
    else:
        with smtplib.SMTP(cfg["host"], port, timeout=15) as s:
            s.starttls(context=contexte)
            s.login(cfg["user"], cfg["password"])
            s.send_message(message)


def _creer_code(email):
    """Crée un code en base. Retourne (nom, code) ou None (compte inconnu
    ou demande trop rapprochée)."""
    email = email.strip().lower()

    with connexion() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, nom FROM utilisateurs "
            "WHERE LOWER(email) = %s AND actif = TRUE",
            (email,),
        )
        utilisateur = cur.fetchone()
        if utilisateur is None:
            return None

        cur.execute("""
            SELECT 1 FROM reinitialisations_mdp
            WHERE utilisateur_id = %s
              AND date_creation > now() - (%s * interval '1 second')
        """, (utilisateur[0], DELAI_RENVOI_SEC))
        if cur.fetchone():
            return None

        code = f"{secrets.randbelow(10**6):06d}"

        cur.execute(
            "UPDATE reinitialisations_mdp SET utilise = TRUE "
            "WHERE utilisateur_id = %s AND utilise = FALSE",
            (utilisateur[0],),
        )
        cur.execute("""
            INSERT INTO reinitialisations_mdp (utilisateur_id, code_hash, expire_le)
            VALUES (%s, %s, now() + (%s * interval '1 minute'))
        """, (utilisateur[0], hasher_mot_de_passe(code), DUREE_VALIDITE_MIN))

        return utilisateur[1], code


def demander_code(email):
    resultat = _creer_code(email)
    if resultat:
        _envoyer_email(email.strip().lower(), resultat[0], resultat[1])


def reinitialiser(email, code, nouveau_mot_de_passe):
    """Retourne (ok, message)."""
    email = email.strip().lower()

    with connexion() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM utilisateurs WHERE LOWER(email) = %s AND actif = TRUE",
            (email,),
        )
        utilisateur = cur.fetchone()
        if utilisateur is None:
            return False, MSG_INVALIDE

        cur.execute("""
            SELECT id, code_hash, tentatives
            FROM reinitialisations_mdp
            WHERE utilisateur_id = %s AND utilise = FALSE AND expire_le > now()
            ORDER BY date_creation DESC
            LIMIT 1
            FOR UPDATE
        """, (utilisateur[0],))
        demande = cur.fetchone()
        if demande is None:
            return False, MSG_INVALIDE

        demande_id, code_hash, tentatives = demande

        if tentatives >= MAX_TENTATIVES:
            return False, "Trop d'essais. Demandez un nouveau code."

        if not verifier_mot_de_passe(code.strip(), code_hash):
            cur.execute(
                "UPDATE reinitialisations_mdp SET tentatives = tentatives + 1 "
                "WHERE id = %s",
                (demande_id,),
            )
            return False, MSG_INVALIDE

        cur.execute(
            "UPDATE utilisateurs SET mot_de_passe = %s WHERE id = %s",
            (hasher_mot_de_passe(nouveau_mot_de_passe), utilisateur[0]),
        )
        cur.execute(
            "UPDATE reinitialisations_mdp SET utilise = TRUE WHERE id = %s",
            (demande_id,),
        )

    return True, "Mot de passe modifié. Vous pouvez vous connecter."


# ============================================================
# INTERFACE (onglet de la page de connexion)
# ============================================================

def interface_mot_de_passe_oublie():

    st.subheader("Mot de passe oublié")

    if not _smtp_configure():
        st.warning(
            "La récupération par e-mail n'est pas encore configurée. "
            "Contactez l'administrateur de la plateforme."
        )
        return

    st.markdown("**1. Recevoir un code par e-mail**")

    with st.form("form_oubli_demande"):
        email = st.text_input("Adresse e-mail du compte")
        envoyer = st.form_submit_button("Envoyer le code", use_container_width=True)

    if envoyer:
        if "@" not in email or "." not in email:
            st.error("Veuillez saisir une adresse e-mail valide.")
        else:
            try:
                demander_code(email)
            except Exception:
                st.error("Envoi impossible pour le moment. Réessayez plus tard.")
            else:
                st.success(
                    "Si cette adresse correspond à un compte, un code vient "
                    f"d'être envoyé (valable {DUREE_VALIDITE_MIN} minutes, "
                    "un envoi par minute maximum). Pensez à vérifier les spams."
                )

    st.divider()
    st.markdown("**2. Choisir un nouveau mot de passe**")

    with st.form("form_oubli_reset"):
        email_reset = st.text_input("Adresse e-mail du compte", key="oubli_email_reset")
        code = st.text_input("Code reçu par e-mail (6 chiffres)", max_chars=6)
        nouveau = st.text_input("Nouveau mot de passe", type="password")
        confirmation = st.text_input("Confirmer le mot de passe", type="password")
        valider = st.form_submit_button(
            "Réinitialiser le mot de passe", use_container_width=True
        )

    if valider:
        if not email_reset or not code or not nouveau:
            st.error("Veuillez remplir tous les champs.")
        elif len(nouveau) < MOT_DE_PASSE_MIN:
            st.error(
                f"Le mot de passe doit contenir au moins {MOT_DE_PASSE_MIN} caractères."
            )
        elif nouveau != confirmation:
            st.error("Les deux mots de passe ne correspondent pas.")
        else:
            ok, message = reinitialiser(email_reset, code, nouveau)
            if ok:
                st.success(message)
            else:
                st.error(message)
