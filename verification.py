import re
import secrets
import smtplib
import ssl
from email.message import EmailMessage

import psycopg2.errors
import streamlit as st

from database import connexion, hasher_mot_de_passe, verifier_mot_de_passe
from recuperation import _smtp_configure

DUREE_VALIDITE_MIN = 15
DELAI_RENVOI_SEC = 60
MAX_TENTATIVES = 5
MOT_DE_PASSE_MIN = 8

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MSG_INVALIDE = "Code invalide ou expiré. Vérifiez le code saisi."


# ============================================================
# LOGIQUE
# ============================================================

def _generer_code():
    return f"{secrets.randbelow(10**6):06d}"


def _envoyer(destinataire, nom, code):
    cfg = st.secrets["smtp"]

    message = EmailMessage()
    message["Subject"] = "FinTech PME : code de vérification"
    message["From"] = cfg.get("expediteur", cfg["user"])
    message["To"] = destinataire
    message.set_content(
        f"Bonjour {nom},\n\n"
        f"Votre code de vérification est : {code}\n\n"
        f"Il est valable {DUREE_VALIDITE_MIN} minutes. Saisissez-le dans "
        "l'application pour finaliser la création de votre compte.\n\n"
        "Si vous n'êtes pas à l'origine de cette demande, ignorez ce message : "
        "aucun compte ne sera créé.\n\n"
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


def _supprimer_attente(email):
    with connexion() as conn, conn.cursor() as cur:
        cur.execute(
            "DELETE FROM inscriptions_en_attente WHERE LOWER(email) = %s",
            (email,),
        )


def demander_inscription(
    nom_admin, email, mot_de_passe, nom_entreprise,
    secteur="", adresse="", telephone="", email_entreprise="",
):
    """Enregistre la demande et envoie le code.
    Retourne 'ok', 'email_existant' ou 'trop_tot'."""
    email = email.strip().lower()

    with connexion() as conn, conn.cursor() as cur:
        # Nettoyage des anciennes demandes
        cur.execute(
            "DELETE FROM inscriptions_en_attente "
            "WHERE expire_le < now() - interval '1 day'"
        )

        cur.execute(
            "SELECT 1 FROM utilisateurs WHERE LOWER(email) = %s", (email,)
        )
        if cur.fetchone():
            return "email_existant"

        cur.execute("""
            SELECT 1 FROM inscriptions_en_attente
            WHERE LOWER(email) = %s
              AND date_creation > now() - (%s * interval '1 second')
        """, (email, DELAI_RENVOI_SEC))
        if cur.fetchone():
            return "trop_tot"

        code = _generer_code()

        cur.execute(
            "DELETE FROM inscriptions_en_attente WHERE LOWER(email) = %s",
            (email,),
        )
        cur.execute("""
            INSERT INTO inscriptions_en_attente
                (email, nom_admin, mot_de_passe_hash, nom_entreprise, secteur,
                 adresse, telephone, email_entreprise, code_hash, expire_le)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                    now() + (%s * interval '1 minute'))
        """, (
            email, nom_admin, hasher_mot_de_passe(mot_de_passe), nom_entreprise,
            secteur, adresse, telephone, email_entreprise,
            hasher_mot_de_passe(code), DUREE_VALIDITE_MIN,
        ))

    try:
        _envoyer(email, nom_admin, code)
    except Exception:
        _supprimer_attente(email)
        raise

    return "ok"


def renvoyer_code(email):
    """Retourne 'ok', 'trop_tot' ou 'inconnu'."""
    email = email.strip().lower()

    with connexion() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, nom_admin FROM inscriptions_en_attente "
            "WHERE LOWER(email) = %s",
            (email,),
        )
        ligne = cur.fetchone()
        if ligne is None:
            return "inconnu"

        cur.execute("""
            SELECT 1 FROM inscriptions_en_attente
            WHERE id = %s
              AND date_creation > now() - (%s * interval '1 second')
        """, (ligne[0], DELAI_RENVOI_SEC))
        if cur.fetchone():
            return "trop_tot"

        code = _generer_code()
        cur.execute("""
            UPDATE inscriptions_en_attente
            SET code_hash = %s,
                expire_le = now() + (%s * interval '1 minute'),
                tentatives = 0,
                date_creation = now()
            WHERE id = %s
        """, (hasher_mot_de_passe(code), DUREE_VALIDITE_MIN, ligne[0]))

    _envoyer(email, ligne[1], code)
    return "ok"


def valider_inscription(email, code):
    """Vérifie le code puis crée l'entreprise et l'administrateur.
    Retourne (ok, message)."""
    email = email.strip().lower()

    try:
        with connexion() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT id, nom_admin, mot_de_passe_hash, nom_entreprise,
                       secteur, adresse, telephone, email_entreprise,
                       code_hash, tentatives
                FROM inscriptions_en_attente
                WHERE LOWER(email) = %s AND expire_le > now()
                FOR UPDATE
            """, (email,))
            demande = cur.fetchone()
            if demande is None:
                return False, MSG_INVALIDE

            (demande_id, nom_admin, mdp_hash, nom_entreprise, secteur,
             adresse, telephone, email_entreprise, code_hash, tentatives) = demande

            if tentatives >= MAX_TENTATIVES:
                return False, (
                    "Trop d'essais. Demandez un nouveau code "
                    "ou recommencez l'inscription."
                )

            if not verifier_mot_de_passe(code.strip(), code_hash):
                cur.execute(
                    "UPDATE inscriptions_en_attente "
                    "SET tentatives = tentatives + 1 WHERE id = %s",
                    (demande_id,),
                )
                return False, MSG_INVALIDE

            cur.execute(
                "SELECT 1 FROM utilisateurs WHERE LOWER(email) = %s", (email,)
            )
            if cur.fetchone():
                cur.execute(
                    "DELETE FROM inscriptions_en_attente WHERE id = %s",
                    (demande_id,),
                )
                return False, "Cette adresse e-mail possède déjà un compte."

            cur.execute("""
                INSERT INTO entreprises
                    (nom, secteur, adresse, telephone, email, devise, solde_initial)
                VALUES (%s, %s, %s, %s, %s, 'FCFA', 0)
                RETURNING id
            """, (nom_entreprise, secteur, adresse, telephone, email_entreprise))
            entreprise_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO utilisateurs
                    (entreprise_id, nom, email, mot_de_passe, role, actif)
                VALUES (%s, %s, %s, %s, 'admin', TRUE)
            """, (entreprise_id, nom_admin, email, mdp_hash))

            cur.execute(
                "DELETE FROM inscriptions_en_attente WHERE id = %s",
                (demande_id,),
            )
    except psycopg2.errors.UniqueViolation:
        return False, "Cette adresse e-mail possède déjà un compte."

    return True, "Adresse e-mail confirmée. Votre compte a été créé avec succès."


# ============================================================
# INTERFACE (onglet « Créer un compte »)
# ============================================================

def interface_inscription():

    st.subheader("Créer un compte administrateur")

    if not _smtp_configure():
        st.warning(
            "L'inscription nécessite l'envoi d'un code par e-mail, qui "
            "n'est pas encore configuré. Contactez l'administrateur de "
            "la plateforme."
        )
        return

    email_attente = st.session_state.get("insc_attente")

    # ---------------- Étape 2 : saisie du code ----------------
    if email_attente:

        st.info(
            f"Un code à 6 chiffres a été envoyé à **{email_attente}**. "
            f"Saisissez-le pour finaliser votre inscription "
            f"(valable {DUREE_VALIDITE_MIN} minutes). "
            "Pensez à vérifier les spams."
        )

        with st.form("form_insc_code"):
            code = st.text_input("Code reçu par e-mail", max_chars=6)
            valider = st.form_submit_button(
                "Valider mon inscription", use_container_width=True
            )

        if valider:
            if not code.strip():
                st.error("Veuillez saisir le code reçu.")
            else:
                ok, message = valider_inscription(email_attente, code)
                if ok:
                    st.session_state.pop("insc_attente", None)
                    st.success(message)
                    st.info(
                        "Vous pouvez maintenant vous connecter dans l'onglet "
                        "« Connexion administrateur »."
                    )
                    return
                st.error(message)

        col1, col2 = st.columns(2)

        if col1.button("📧 Renvoyer le code", use_container_width=True):
            try:
                statut = renvoyer_code(email_attente)
            except Exception:
                st.error("Envoi impossible pour le moment. Réessayez plus tard.")
            else:
                if statut == "ok":
                    st.success("Un nouveau code vient d'être envoyé.")
                elif statut == "trop_tot":
                    st.warning("Patientez une minute avant de redemander un code.")
                else:
                    st.session_state.pop("insc_attente", None)
                    st.error("Demande expirée. Recommencez l'inscription.")

        if col2.button("✏️ Modifier mes informations", use_container_width=True):
            st.session_state.pop("insc_attente", None)
            st.rerun()

        return

    # ---------------- Étape 1 : formulaire ----------------
    st.info(
        "Un code de vérification sera envoyé à votre adresse e-mail. "
        "Votre compte et votre entreprise seront créés après sa saisie."
    )

    with st.form("form_inscription"):
        st.markdown("#### Informations de l'administrateur")
        nom_admin = st.text_input("Nom complet")
        email_admin = st.text_input("Adresse e-mail")
        mot_de_passe = st.text_input("Mot de passe", type="password")
        confirmation = st.text_input("Confirmer le mot de passe", type="password")

        st.markdown("#### Informations de l'entreprise")
        nom_entreprise = st.text_input("Nom de l'entreprise")
        secteur = st.text_input(
            "Secteur d'activité",
            placeholder="Commerce, restauration, services...",
        )
        adresse = st.text_input("Adresse")
        telephone = st.text_input("Téléphone")
        email_entreprise = st.text_input("E-mail de l'entreprise")

        envoyer = st.form_submit_button("Recevoir mon code", use_container_width=True)

    if not envoyer:
        return

    if not nom_admin.strip():
        st.error("Veuillez renseigner votre nom.")
    elif not EMAIL_REGEX.match(email_admin.strip()):
        st.error("Veuillez renseigner une adresse e-mail valide.")
    elif len(mot_de_passe) < MOT_DE_PASSE_MIN:
        st.error(
            f"Le mot de passe doit contenir au moins {MOT_DE_PASSE_MIN} caractères."
        )
    elif mot_de_passe != confirmation:
        st.error("Les deux mots de passe ne correspondent pas.")
    elif not nom_entreprise.strip():
        st.error("Veuillez renseigner le nom de l'entreprise.")
    elif email_entreprise.strip() and not EMAIL_REGEX.match(email_entreprise.strip()):
        st.error("L'adresse e-mail de l'entreprise n'est pas valide.")
    else:
        try:
            statut = demander_inscription(
                nom_admin.strip(), email_admin, mot_de_passe,
                nom_entreprise.strip(), secteur.strip(), adresse.strip(),
                telephone.strip(), email_entreprise.strip(),
            )
        except Exception:
            st.error("Envoi du code impossible pour le moment. Réessayez plus tard.")
            return

        if statut == "email_existant":
            st.error("Cette adresse e-mail possède déjà un compte.")
        elif statut == "trop_tot":
            st.warning(
                "Un code vient d'être envoyé à cette adresse. "
                "Patientez une minute avant de recommencer."
            )
        else:
            st.session_state["insc_attente"] = email_admin.strip().lower()
            st.rerun()
