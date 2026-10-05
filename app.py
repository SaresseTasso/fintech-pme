import streamlit as st
import pandas as pd
import io
from datetime import date

from database import (
    initialize_database,
    creer_entreprise,
    email_existe,
    creer_administrateur,
    authentifier_utilisateur,
    obtenir_utilisateur,
    obtenir_entreprise_par_defaut,
    ajouter_recette,
    recuperer_recettes,
    obtenir_recette,
    modifier_recette,
    supprimer_recette,
    ajouter_depense,
    recuperer_depenses,
    obtenir_depense,
    modifier_depense,
    supprimer_depense,
    calculer_total_recettes,
    calculer_total_depenses,
    obtenir_solde_initial,
    modifier_solde_initial
)


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="FinTech PME",
    page_icon="💼",
    layout="wide"
)

initialize_database()


# ============================================================
# SESSION
# ============================================================

if "connecte" not in st.session_state:
    st.session_state.connecte = False

if "utilisateur_id" not in st.session_state:
    st.session_state.utilisateur_id = None

if "entreprise_id" not in st.session_state:
    st.session_state.entreprise_id = None

if "nom_utilisateur" not in st.session_state:
    st.session_state.nom_utilisateur = ""

if "email_utilisateur" not in st.session_state:
    st.session_state.email_utilisateur = ""


# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def format_fcfa(montant):
    return f"{montant:,.0f} FCFA".replace(",", " ")


def nettoyer_texte(valeur):
    if valeur is None:
        return ""
    return str(valeur)


# ============================================================
# PAGE D'AUTHENTIFICATION
# ============================================================

def page_authentification():

    st.title("💼 FinTech PME")

    st.markdown(
        "### Plateforme de gestion financière pour les petites et moyennes entreprises"
    )

    st.divider()

    onglet_connexion, onglet_inscription = st.tabs(
        ["🔐 Connexion administrateur", "📝 Créer un compte"]
    )

    # --------------------------------------------------------
    # CONNEXION
    # --------------------------------------------------------

    with onglet_connexion:

        st.subheader("Connexion administrateur")

        with st.form("form_connexion"):

            email = st.text_input(
                "Adresse e-mail",
                placeholder="admin@entreprise.com"
            )

            mot_de_passe = st.text_input(
                "Mot de passe",
                type="password"
            )

            connexion = st.form_submit_button(
                "Se connecter",
                use_container_width=True
            )

        if connexion:

            if not email or not mot_de_passe:
                st.error(
                    "Veuillez renseigner votre adresse e-mail et votre mot de passe."
                )

            else:

                utilisateur = authentifier_utilisateur(
                    email,
                    mot_de_passe
                )

                if utilisateur:

                    st.session_state.connecte = True
                    st.session_state.utilisateur_id = utilisateur[0]
                    st.session_state.nom_utilisateur = utilisateur[1]
                    st.session_state.email_utilisateur = utilisateur[2]
                    st.session_state.entreprise_id = utilisateur[3]

                    st.success("Connexion réussie.")

                    st.rerun()

                else:

                    st.error(
                        "Adresse e-mail ou mot de passe incorrect."
                    )

    # --------------------------------------------------------
    # INSCRIPTION
    # --------------------------------------------------------

    with onglet_inscription:

        st.subheader("Créer un compte administrateur")

        st.info(
            "L'inscription crée automatiquement votre entreprise "
            "et votre compte administrateur."
        )

        with st.form("form_inscription"):

            st.markdown("#### Informations de l'administrateur")

            nom_admin = st.text_input(
                "Nom complet"
            )

            email_admin = st.text_input(
                "Adresse e-mail"
            )

            mot_de_passe_admin = st.text_input(
                "Mot de passe",
                type="password"
            )

            confirmation_mot_de_passe = st.text_input(
                "Confirmer le mot de passe",
                type="password"
            )

            st.markdown("#### Informations de l'entreprise")

            nom_entreprise = st.text_input(
                "Nom de l'entreprise"
            )

            secteur = st.text_input(
                "Secteur d'activité",
                placeholder="Commerce, restauration, services..."
            )

            adresse = st.text_input(
                "Adresse"
            )

            telephone = st.text_input(
                "Téléphone"
            )

            email_entreprise = st.text_input(
                "E-mail de l'entreprise"
            )

            inscription = st.form_submit_button(
                "Créer mon compte",
                use_container_width=True
            )

        if inscription:

            if not nom_admin:
                st.error("Veuillez renseigner votre nom.")

            elif not email_admin:
                st.error("Veuillez renseigner votre adresse e-mail.")

            elif not mot_de_passe_admin:
                st.error("Veuillez créer un mot de passe.")

            elif len(mot_de_passe_admin) < 6:
                st.error(
                    "Le mot de passe doit contenir au moins 6 caractères."
                )

            elif mot_de_passe_admin != confirmation_mot_de_passe:
                st.error(
                    "Les deux mots de passe ne correspondent pas."
                )

            elif not nom_entreprise:
                st.error(
                    "Veuillez renseigner le nom de l'entreprise."
                )

            elif email_existe(email_admin):

                st.error(
                    "Cette adresse e-mail possède déjà un compte."
                )

            else:

                try:

                    entreprise_id = creer_entreprise(
                        nom_entreprise,
                        secteur,
                        adresse,
                        telephone,
                        email_entreprise
                    )

                    utilisateur_id = creer_administrateur(
                        nom_admin,
                        email_admin,
                        mot_de_passe_admin,
                        entreprise_id
                    )

                    st.success(
                        "Compte administrateur créé avec succès."
                    )

                    st.info(
                        "Vous pouvez maintenant vous connecter "
                        "avec votre adresse e-mail et votre mot de passe."
                    )

                except Exception as erreur:

                    st.error(
                        f"Une erreur est survenue : {erreur}"
                    )


# ============================================================
# SI L'UTILISATEUR N'EST PAS CONNECTÉ
# ============================================================

if not st.session_state.connecte:

    page_authentification()

    st.stop()


# ============================================================
# VÉRIFICATION DE LA SESSION
# ============================================================

utilisateur_actuel = obtenir_utilisateur(
    st.session_state.utilisateur_id
)

if utilisateur_actuel is None:

    st.session_state.connecte = False
    st.session_state.utilisateur_id = None
    st.session_state.entreprise_id = None

    st.rerun()

if utilisateur_actuel[4] != "admin":

    st.error(
        "Accès refusé. Seuls les administrateurs peuvent utiliser la plateforme."
    )

    st.stop()


entreprise_id = st.session_state.entreprise_id


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("💼 FinTech PME")

st.sidebar.write(
    f"**Administrateur :** {st.session_state.nom_utilisateur}"
)

st.sidebar.write(
    f"**E-mail :** {st.session_state.email_utilisateur}"
)

st.sidebar.divider()

menu = st.sidebar.radio(
    "Navigation",
    [
        "📊 Tableau de bord",
        "💰 Recettes",
        "💸 Dépenses",
        "🏦 Trésorerie",
        "📈 Rapports",
        "⚙️ Paramètres"
    ]
)

st.sidebar.divider()

if st.sidebar.button(
    "🚪 Se déconnecter",
    use_container_width=True
):

    st.session_state.connecte = False
    st.session_state.utilisateur_id = None
    st.session_state.entreprise_id = None
    st.session_state.nom_utilisateur = ""
    st.session_state.email_utilisateur = ""

    st.rerun()


# ============================================================
# DONNÉES FINANCIÈRES
# ============================================================

total_recettes = calculer_total_recettes(
    entreprise_id
)

total_depenses = calculer_total_depenses(
    entreprise_id
)

solde_initial = obtenir_solde_initial(
    entreprise_id
)

resultat = total_recettes - total_depenses

solde_actuel = (
    solde_initial
    + total_recettes
    - total_depenses
)


# ============================================================
# TABLEAU DE BORD
# ============================================================

if menu == "📊 Tableau de bord":

    st.title("📊 Tableau de bord")

    st.write(
        "Bienvenue dans votre espace de gestion financière."
    )

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Solde actuel",
            format_fcfa(solde_actuel)
        )

    with col2:

        st.metric(
            "Total recettes",
            format_fcfa(total_recettes)
        )

    with col3:

        st.metric(
            "Total dépenses",
            format_fcfa(total_depenses)
        )

    with col4:

        st.metric(
            "Résultat",
            format_fcfa(resultat)
        )

    st.divider()

    # --------------------------------------------------------
    # INDICATEURS
    # --------------------------------------------------------

    st.subheader("📌 Indicateurs financiers")

    col1, col2, col3 = st.columns(3)

    nombre_recettes = len(
        recuperer_recettes(entreprise_id)
    )

    nombre_depenses = len(
        recuperer_depenses(entreprise_id)
    )

    nombre_transactions = (
        nombre_recettes + nombre_depenses
    )

    with col1:

        st.metric(
            "Nombre de transactions",
            nombre_transactions
        )

    with col2:

        if total_recettes > 0:

            marge = (
                resultat / total_recettes
            ) * 100

        else:

            marge = 0

        st.metric(
            "Marge financière",
            f"{marge:.1f} %"
        )

    with col3:

        if nombre_recettes > 0:

            moyenne_recettes = (
                total_recettes / nombre_recettes
            )

        else:

            moyenne_recettes = 0

        st.metric(
            "Recette moyenne",
            format_fcfa(moyenne_recettes)
        )

    st.divider()

    # --------------------------------------------------------
    # GRAPHIQUE
    # --------------------------------------------------------

    st.subheader("📈 Évolution financière")

    recettes = recuperer_recettes(
        entreprise_id
    )

    depenses = recuperer_depenses(
        entreprise_id
    )

    donnees_graphique = {}

    for recette in recettes:

        mois = recette[1][:7]

        if mois not in donnees_graphique:

            donnees_graphique[mois] = {
                "Recettes": 0,
                "Dépenses": 0
            }

        donnees_graphique[mois]["Recettes"] += recette[2]

    for depense in depenses:

        mois = depense[1][:7]

        if mois not in donnees_graphique:

            donnees_graphique[mois] = {
                "Recettes": 0,
                "Dépenses": 0
            }

        donnees_graphique[mois]["Dépenses"] += depense[2]

    if donnees_graphique:

        graphique = pd.DataFrame.from_dict(
            donnees_graphique,
            orient="index"
        )

        graphique.index.name = "Mois"

        graphique = graphique.sort_index()

        st.line_chart(
            graphique
        )

    else:

        st.info(
            "Aucune donnée financière disponible pour afficher le graphique."
        )

    st.divider()

    # --------------------------------------------------------
    # DERNIÈRES TRANSACTIONS
    # --------------------------------------------------------

    st.subheader("🧾 Dernières transactions")

    transactions = []

    for recette in recettes:

        transactions.append({
            "Date": recette[1],
            "Type": "Recette",
            "Catégorie": recette[3],
            "Montant": recette[2],
            "Description": recette[6]
        })

    for depense in depenses:

        transactions.append({
            "Date": depense[1],
            "Type": "Dépense",
            "Catégorie": depense[3],
            "Montant": depense[2],
            "Description": depense[6]
        })

    if transactions:

        df_transactions = pd.DataFrame(
            transactions
        )

        df_transactions = (
            df_transactions
            .sort_values("Date", ascending=False)
            .head(10)
        )

        st.dataframe(
            df_transactions,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "Aucune transaction enregistrée."
        )


# ============================================================
# RECETTES
# ============================================================

elif menu == "💰 Recettes":

    st.title("💰 Gestion des recettes")

    onglet_ajout, onglet_liste = st.tabs(
        [
            "➕ Ajouter une recette",
            "📋 Gérer les recettes"
        ]
    )

    # --------------------------------------------------------
    # AJOUT
    # --------------------------------------------------------

    with onglet_ajout:

        st.subheader("Nouvelle recette")

        with st.form("form_recette"):

            date_recette = st.date_input(
                "Date",
                value=date.today()
            )

            montant = st.number_input(
                "Montant (FCFA)",
                min_value=0.0,
                step=100.0
            )

            categorie = st.text_input(
                "Catégorie",
                placeholder="Vente, prestation, etc."
            )

            source = st.text_input(
                "Source"
            )

            moyen_paiement = st.selectbox(
                "Moyen de paiement",
                [
                    "Espèces",
                    "Mobile Money",
                    "Virement bancaire",
                    "Carte bancaire",
                    "Chèque",
                    "Autre"
                ]
            )

            description = st.text_area(
                "Description"
            )

            enregistrer = st.form_submit_button(
                "Enregistrer la recette",
                use_container_width=True
            )

        if enregistrer:

            if montant <= 0:

                st.error(
                    "Le montant doit être supérieur à zéro."
                )

            elif not categorie:

                st.error(
                    "Veuillez renseigner la catégorie."
                )

            else:

                ajouter_recette(
                    entreprise_id,
                    date_recette.strftime("%Y-%m-%d"),
                    montant,
                    categorie,
                    source,
                    moyen_paiement,
                    description
                )

                st.success(
                    "Recette enregistrée avec succès."
                )

                st.rerun()

    # --------------------------------------------------------
    # GESTION
    # --------------------------------------------------------

    with onglet_liste:

        st.subheader("Liste des recettes")

        recettes = recuperer_recettes(
            entreprise_id
        )

        if recettes:

            recherche = st.text_input(
                "🔎 Rechercher",
                placeholder="Catégorie, source ou description..."
            )

            categories = sorted(
                list(
                    set(
                        [r[3] for r in recettes]
                    )
                )
            )

            filtre_categorie = st.selectbox(
                "Filtrer par catégorie",
                ["Toutes"] + categories
            )

            recettes_filtrees = []

            for recette in recettes:

                texte = " ".join(
                    [
                        nettoyer_texte(recette[3]),
                        nettoyer_texte(recette[4]),
                        nettoyer_texte(recette[6])
                    ]
                ).lower()

                if recherche.lower() not in texte:
                    continue

                if (
                    filtre_categorie != "Toutes"
                    and recette[3] != filtre_categorie
                ):
                    continue

                recettes_filtrees.append(recette)

            donnees = []

            for recette in recettes_filtrees:

                donnees.append({
                    "ID": recette[0],
                    "Date": recette[1],
                    "Montant": recette[2],
                    "Catégorie": recette[3],
                    "Source": recette[4],
                    "Paiement": recette[5],
                    "Description": recette[6]
                })

            if donnees:

                df = pd.DataFrame(donnees)

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

                st.divider()

                st.subheader("Modifier ou supprimer une recette")

                ids = [
                    recette[0]
                    for recette in recettes_filtrees
                ]

                recette_selectionnee = st.selectbox(
                    "Sélectionner une recette",
                    ids
                )

                recette = obtenir_recette(
                    recette_selectionnee,
                    entreprise_id
                )

                if recette:

                    col1, col2 = st.columns(2)

                    with col1:

                        nouvelle_date = st.date_input(
                            "Date",
                            value=pd.to_datetime(
                                recette[1]
                            ).date()
                        )

                        nouveau_montant = st.number_input(
                            "Montant",
                            value=float(recette[2]),
                            min_value=0.0,
                            step=100.0
                        )

                        nouvelle_categorie = st.text_input(
                            "Catégorie",
                            value=nettoyer_texte(recette[3])
                        )

                    with col2:

                        nouvelle_source = st.text_input(
                            "Source",
                            value=nettoyer_texte(recette[4])
                        )

                        nouveaux_paiement = st.selectbox(
                            "Moyen de paiement",
                            [
                                "Espèces",
                                "Mobile Money",
                                "Virement bancaire",
                                "Carte bancaire",
                                "Chèque",
                                "Autre"
                            ],
                            index=(
                                [
                                    "Espèces",
                                    "Mobile Money",
                                    "Virement bancaire",
                                    "Carte bancaire",
                                    "Chèque",
                                    "Autre"
                                ].index(recette[5])
                                if recette[5] in [
                                    "Espèces",
                                    "Mobile Money",
                                    "Virement bancaire",
                                    "Carte bancaire",
                                    "Chèque",
                                    "Autre"
                                ]
                                else 0
                            )
                        )

                        nouvelle_description = st.text_area(
                            "Description",
                            value=nettoyer_texte(recette[6])
                        )

                    col_modif, col_suppr = st.columns(2)

                    with col_modif:

                        if st.button(
                            "💾 Enregistrer les modifications",
                            use_container_width=True
                        ):

                            modifier_recette(
                                recette_selectionnee,
                                entreprise_id,
                                nouvelle_date.strftime("%Y-%m-%d"),
                                nouveau_montant,
                                nouvelle_categorie,
                                nouvelle_source,
                                nouveaux_paiement,
                                nouvelle_description
                            )

                            st.success(
                                "Recette modifiée avec succès."
                            )

                            st.rerun()

                    with col_suppr:

                        if st.button(
                            "🗑️ Supprimer cette recette",
                            use_container_width=True
                        ):

                            supprimer_recette(
                                recette_selectionnee,
                                entreprise_id
                            )

                            st.success(
                                "Recette supprimée."
                            )

                            st.rerun()

                # ------------------------------------------------
                # EXPORT EXCEL
                # ------------------------------------------------

                st.divider()

                st.subheader("📥 Export Excel")

                df_export = pd.DataFrame(
                    donnees
                )

                buffer = io.BytesIO()

                with pd.ExcelWriter(
                    buffer,
                    engine="openpyxl"
                ) as writer:

                    df_export.to_excel(
                        writer,
                        index=False,
                        sheet_name="Recettes",
                        startrow=4
                    )

                    feuille = writer.sheets["Recettes"]

                    feuille["A1"] = "FINTECH PME"
                    feuille["A2"] = "Rapport des recettes"
                    feuille["A3"] = (
                        f"Administrateur : "
                        f"{st.session_state.nom_utilisateur}"
                    )

                    for colonne in feuille.columns:

                        longueur = 0

                        for cellule in colonne:

                            if cellule.value is not None:

                                longueur = max(
                                    longueur,
                                    len(str(cellule.value))
                                )

                        feuille.column_dimensions[
                            colonne[0].column_letter
                        ].width = min(
                            longueur + 3,
                            40
                        )

                    feuille.freeze_panes = "A6"
                    feuille.auto_filter.ref = (
                        feuille.dimensions
                    )

                st.download_button(
                    "📥 Télécharger les recettes en Excel",
                    data=buffer.getvalue(),
                    file_name="rapport_recettes.xlsx",
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),
                    use_container_width=True
                )

            else:

                st.info(
                    "Aucune recette ne correspond aux critères."
                )

        else:

            st.info(
                "Aucune recette enregistrée."
            )


# ============================================================
# DÉPENSES
# ============================================================

elif menu == "💸 Dépenses":

    st.title("💸 Gestion des dépenses")

    onglet_ajout, onglet_liste = st.tabs(
        [
            "➕ Ajouter une dépense",
            "📋 Gérer les dépenses"
        ]
    )

    # --------------------------------------------------------
    # AJOUT
    # --------------------------------------------------------

    with onglet_ajout:

        st.subheader("Nouvelle dépense")

        with st.form("form_depense"):

            date_depense = st.date_input(
                "Date",
                value=date.today()
            )

            montant = st.number_input(
                "Montant (FCFA)",
                min_value=0.0,
                step=100.0
            )

            categorie = st.text_input(
                "Catégorie",
                placeholder="Loyer, salaire, achat, etc."
            )

            beneficiaire = st.text_input(
                "Bénéficiaire"
            )

            moyen_paiement = st.selectbox(
                "Moyen de paiement",
                [
                    "Espèces",
                    "Mobile Money",
                    "Virement bancaire",
                    "Carte bancaire",
                    "Chèque",
                    "Autre"
                ]
            )

            description = st.text_area(
                "Description"
            )

            enregistrer = st.form_submit_button(
                "Enregistrer la dépense",
                use_container_width=True
            )

        if enregistrer:

            if montant <= 0:

                st.error(
                    "Le montant doit être supérieur à zéro."
                )

            elif not categorie:

                st.error(
                    "Veuillez renseigner la catégorie."
                )

            else:

                ajouter_depense(
                    entreprise_id,
                    date_depense.strftime("%Y-%m-%d"),
                    montant,
                    categorie,
                    beneficiaire,
                    moyen_paiement,
                    description
                )

                st.success(
                    "Dépense enregistrée avec succès."
                )

                st.rerun()

    # --------------------------------------------------------
    # GESTION
    # --------------------------------------------------------

    with onglet_liste:

        st.subheader("Liste des dépenses")

        depenses = recuperer_depenses(
            entreprise_id
        )

        if depenses:

            recherche = st.text_input(
                "🔎 Rechercher",
                placeholder="Catégorie, bénéficiaire ou description..."
            )

            categories = sorted(
                list(
                    set(
                        [d[3] for d in depenses]
                    )
                )
            )

            filtre_categorie = st.selectbox(
                "Filtrer par catégorie",
                ["Toutes"] + categories
            )

            depenses_filtrees = []

            for depense in depenses:

                texte = " ".join(
                    [
                        nettoyer_texte(depense[3]),
                        nettoyer_texte(depense[4]),
                        nettoyer_texte(depense[6])
                    ]
                ).lower()

                if recherche.lower() not in texte:
                    continue

                if (
                    filtre_categorie != "Toutes"
                    and depense[3] != filtre_categorie
                ):
                    continue

                depenses_filtrees.append(depense)

            donnees = []

            for depense in depenses_filtrees:

                donnees.append({
                    "ID": depense[0],
                    "Date": depense[1],
                    "Montant": depense[2],
                    "Catégorie": depense[3],
                    "Bénéficiaire": depense[4],
                    "Paiement": depense[5],
                    "Description": depense[6]
                })

            if donnees:

                df = pd.DataFrame(
                    donnees
                )

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

                st.divider()

                st.subheader("Modifier ou supprimer une dépense")

                ids = [
                    depense[0]
                    for depense in depenses_filtrees
                ]

                depense_selectionnee = st.selectbox(
                    "Sélectionner une dépense",
                    ids
                )

                depense = obtenir_depense(
                    depense_selectionnee,
                    entreprise_id
                )

                if depense:

                    col1, col2 = st.columns(2)

                    with col1:

                        nouvelle_date = st.date_input(
                            "Date",
                            value=pd.to_datetime(
                                depense[1]
                            ).date()
                        )

                        nouveau_montant = st.number_input(
                            "Montant",
                            value=float(depense[2]),
                            min_value=0.0,
                            step=100.0
                        )

                        nouvelle_categorie = st.text_input(
                            "Catégorie",
                            value=nettoyer_texte(depense[3])
                        )

                    with col2:

                        nouveau_beneficiaire = st.text_input(
                            "Bénéficiaire",
                            value=nettoyer_texte(depense[4])
                        )

                        nouveau_paiement = st.selectbox(
                            "Moyen de paiement",
                            [
                                "Espèces",
                                "Mobile Money",
                                "Virement bancaire",
                                "Carte bancaire",
                                "Chèque",
                                "Autre"
                            ],
                            index=(
                                [
                                    "Espèces",
                                    "Mobile Money",
                                    "Virement bancaire",
                                    "Carte bancaire",
                                    "Chèque",
                                    "Autre"
                                ].index(depense[5])
                                if depense[5] in [
                                    "Espèces",
                                    "Mobile Money",
                                    "Virement bancaire",
                                    "Carte bancaire",
                                    "Chèque",
                                    "Autre"
                                ]
                                else 0
                            )
                        )

                        nouvelle_description = st.text_area(
                            "Description",
                            value=nettoyer_texte(depense[6])
                        )

                    col_modif, col_suppr = st.columns(2)

                    with col_modif:

                        if st.button(
                            "💾 Enregistrer les modifications",
                            use_container_width=True
                        ):

                            modifier_depense(
                                depense_selectionnee,
                                entreprise_id,
                                nouvelle_date.strftime("%Y-%m-%d"),
                                nouveau_montant,
                                nouvelle_categorie,
                                nouveau_beneficiaire,
                                nouveau_paiement,
                                nouvelle_description
                            )

                            st.success(
                                "Dépense modifiée avec succès."
                            )

                            st.rerun()

                    with col_suppr:

                        if st.button(
                            "🗑️ Supprimer cette dépense",
                            use_container_width=True
                        ):

                            supprimer_depense(
                                depense_selectionnee,
                                entreprise_id
                            )

                            st.success(
                                "Dépense supprimée."
                            )

                            st.rerun()

                # ------------------------------------------------
                # EXPORT EXCEL
                # ------------------------------------------------

                st.divider()

                st.subheader("📥 Export Excel")

                df_export = pd.DataFrame(
                    donnees
                )

                buffer = io.BytesIO()

                with pd.ExcelWriter(
                    buffer,
                    engine="openpyxl"
                ) as writer:

                    df_export.to_excel(
                        writer,
                        index=False,
                        sheet_name="Depenses",
                        startrow=4
                    )

                    feuille = writer.sheets["Depenses"]

                    feuille["A1"] = "FINTECH PME"
                    feuille["A2"] = "Rapport des dépenses"
                    feuille["A3"] = (
                        f"Administrateur : "
                        f"{st.session_state.nom_utilisateur}"
                    )

                    for colonne in feuille.columns:

                        longueur = 0

                        for cellule in colonne:

                            if cellule.value is not None:

                                longueur = max(
                                    longueur,
                                    len(str(cellule.value))
                                )

                        feuille.column_dimensions[
                            colonne[0].column_letter
                        ].width = min(
                            longueur + 3,
                            40
                        )

                    feuille.freeze_panes = "A6"
                    feuille.auto_filter.ref = (
                        feuille.dimensions
                    )

                st.download_button(
                    "📥 Télécharger les dépenses en Excel",
                    data=buffer.getvalue(),
                    file_name="rapport_depenses.xlsx",
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),
                    use_container_width=True
                )

            else:

                st.info(
                    "Aucune dépense ne correspond aux critères."
                )

        else:

            st.info(
                "Aucune dépense enregistrée."
            )


# ============================================================
# TRÉSORERIE
# ============================================================

elif menu == "🏦 Trésorerie":

    st.title("🏦 Gestion de la trésorerie")

    st.subheader("Situation financière")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Solde initial",
            format_fcfa(solde_initial)
        )

    with col2:

        st.metric(
            "Entrées nettes",
            format_fcfa(
                total_recettes - total_depenses
            )
        )

    with col3:

        st.metric(
            "Solde actuel",
            format_fcfa(solde_actuel)
        )

    st.divider()

    st.subheader("Modifier le solde initial")

    with st.form("form_solde_initial"):

        nouveau_solde = st.number_input(
            "Solde initial (FCFA)",
            min_value=0.0,
            value=float(solde_initial),
            step=1000.0
        )

        modifier = st.form_submit_button(
            "💾 Enregistrer",
            use_container_width=True
        )

    if modifier:

        modifier_solde_initial(
            entreprise_id,
            nouveau_solde
        )

        st.success(
            "Solde initial mis à jour."
        )

        st.rerun()

    st.divider()

    st.subheader("Résumé")

    st.write(
        f"Solde initial : **{format_fcfa(solde_initial)}**"
    )

    st.write(
        f"Total des recettes : **{format_fcfa(total_recettes)}**"
    )

    st.write(
        f"Total des dépenses : **{format_fcfa(total_depenses)}**"
    )

    st.write(
        f"Résultat : **{format_fcfa(resultat)}**"
    )

    st.write(
        f"Solde actuel : **{format_fcfa(solde_actuel)}**"
    )


# ============================================================
# RAPPORTS
# ============================================================

elif menu == "📈 Rapports":

    st.title("📈 Rapports financiers")

    st.info(
        "Le module de rapports avancés sera développé "
        "dans la prochaine étape."
    )

    st.subheader("Résumé financier")

    donnees_resume = pd.DataFrame(
        {
            "Indicateur": [
                "Solde initial",
                "Total recettes",
                "Total dépenses",
                "Résultat",
                "Solde actuel"
            ],
            "Montant (FCFA)": [
                solde_initial,
                total_recettes,
                total_depenses,
                resultat,
                solde_actuel
            ]
        }
    )

    st.dataframe(
        donnees_resume,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# PARAMÈTRES
# ============================================================

elif menu == "⚙️ Paramètres":

    st.title("⚙️ Paramètres")

    st.subheader("👤 Administrateur")

    st.write(
        f"**Nom :** {st.session_state.nom_utilisateur}"
    )

    st.write(
        f"**E-mail :** {st.session_state.email_utilisateur}"
    )

    st.write(
        "**Rôle :** Administrateur"
    )

    st.divider()

    st.subheader("🔐 Sécurité")

    st.info(
        "L'accès à la plateforme est actuellement réservé "
        "aux administrateurs."
    )

    st.divider()

    st.subheader("🏢 Entreprise")

    st.info(
        "Les informations détaillées de l'entreprise seront "
        "configurables dans une prochaine version."
    )
