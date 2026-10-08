import re

import streamlit as st

from database import changer_mot_de_passe, connexion

MOT_DE_PASSE_MIN = 8
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
TEL_REGEX = re.compile(r"^[0-9+()\-\s]{6,20}$")


def _charger_entreprise(entreprise_id):
    with connexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT nom, secteur, adresse, telephone, email, devise
            FROM entreprises WHERE id = %s
        """, (entreprise_id,))
        ligne = cur.fetchone()
    if ligne is None:
        return {}
    cles = ["nom", "secteur", "adresse", "telephone", "email", "devise"]
    return {k: (v or "") for k, v in zip(cles, ligne)}


def _enregistrer_entreprise(entreprise_id, nom, secteur, adresse, telephone, email):
    with connexion() as conn, conn.cursor() as cur:
        cur.execute("""
            UPDATE entreprises
            SET nom = %s, secteur = %s, adresse = %s, telephone = %s, email = %s
            WHERE id = %s
        """, (nom, secteur, adresse, telephone, email, entreprise_id))
        return cur.rowcount > 0


def page_parametres_avances(eid):

    st.title("⚙️ Paramètres")

    # ---------------- Administrateur ----------------
    st.subheader("👤 Administrateur")
    st.write(f"**Nom :** {st.session_state.nom_utilisateur}")
    st.write(f"**E-mail :** {st.session_state.email_utilisateur}")
    st.write("**Rôle :** Administrateur")

    # ---------------- Entreprise ----------------
    st.divider()
    st.subheader("🏢 Entreprise")

    infos = _charger_entreprise(eid)

    with st.form("form_entreprise"):
        nom = st.text_input("Nom de l'entreprise", value=infos.get("nom", ""))
        secteur = st.text_input("Secteur d'activité", value=infos.get("secteur", ""))
        adresse = st.text_input("Adresse", value=infos.get("adresse", ""))
        telephone = st.text_input("Téléphone", value=infos.get("telephone", ""))
        email = st.text_input("E-mail de l'entreprise", value=infos.get("email", ""))
        st.text_input("Devise", value=infos.get("devise", "FCFA"), disabled=True)
        st.caption("La version actuelle fonctionne uniquement en FCFA.")
        enregistrer = st.form_submit_button(
            "💾 Enregistrer les informations", use_container_width=True
        )

    if enregistrer:
        if not nom.strip():
            st.error("Le nom de l'entreprise est obligatoire.")
        elif email.strip() and not EMAIL_REGEX.match(email.strip()):
            st.error("L'adresse e-mail de l'entreprise n'est pas valide.")
        elif telephone.strip() and not TEL_REGEX.match(telephone.strip()):
            st.error("Le numéro de téléphone n'est pas valide.")
        elif _enregistrer_entreprise(
            eid, nom.strip(), secteur.strip(), adresse.strip(),
            telephone.strip(), email.strip(),
        ):
            st.session_state["flash"] = "Informations de l'entreprise mises à jour."
            st.rerun()
        else:
            st.error("Mise à jour impossible : entreprise introuvable.")

    # ---------------- Sécurité ----------------
    st.divider()
    st.subheader("🔐 Sécurité")

    with st.form("form_mot_de_passe", clear_on_submit=True):
        ancien = st.text_input("Mot de passe actuel", type="password")
        nouveau = st.text_input("Nouveau mot de passe", type="password")
        confirmation = st.text_input("Confirmer le nouveau mot de passe", type="password")
        valider = st.form_submit_button(
            "Changer le mot de passe", use_container_width=True
        )

    if valider:
        if not ancien or not nouveau:
            st.error("Veuillez remplir tous les champs.")
        elif len(nouveau) < MOT_DE_PASSE_MIN:
            st.error(
                f"Le mot de passe doit contenir au moins {MOT_DE_PASSE_MIN} caractères."
            )
        elif nouveau != confirmation:
            st.error("Les deux mots de passe ne correspondent pas.")
        elif changer_mot_de_passe(st.session_state.utilisateur_id, ancien, nouveau):
            st.success("Mot de passe modifié avec succès.")
        else:
            st.error("Le mot de passe actuel est incorrect.")
