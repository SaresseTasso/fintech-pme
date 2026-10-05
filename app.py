import streamlit as st
from datetime import date, datetime
from collections import defaultdict
import csv
import io

from database import (
    initialize_database,
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
    layout="wide",
    initial_sidebar_state="expanded"
)

initialize_database()

entreprise_id = obtenir_entreprise_par_defaut()


# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
    <style>

    .main {
        padding-top: 1rem;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .section-title {
        font-size: 20px;
        font-weight: 700;
        margin-top: 25px;
        margin-bottom: 15px;
    }

    .welcome {
        padding: 25px;
        border-radius: 15px;
        background-color: #f5f7fa;
        margin-bottom: 25px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("💼 FinTech PME")

    st.caption(
        "Gestion financière simplifiée"
    )

    st.divider()

    menu = st.radio(
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

    st.divider()

    st.caption(
        "Version 1.1 — Prototype"
    )


# ============================================================
# DONNÉES FINANCIÈRES
# ============================================================

solde_initial = obtenir_solde_initial(
    entreprise_id
)

total_recettes = calculer_total_recettes(
    entreprise_id
)

total_depenses = calculer_total_depenses(
    entreprise_id
)

resultat = (
    total_recettes
    - total_depenses
)

solde_actuel = (
    solde_initial
    + total_recettes
    - total_depenses
)

recettes = recuperer_recettes(
    entreprise_id
)

depenses = recuperer_depenses(
    entreprise_id
)

nombre_recettes = len(recettes)
nombre_depenses = len(depenses)

nombre_transactions = (
    nombre_recettes
    + nombre_depenses
)

if total_recettes > 0:

    marge_financiere = (
        resultat / total_recettes
    ) * 100

else:

    marge_financiere = 0


# ============================================================
# TABLEAU DE BORD
# ============================================================

if menu == "📊 Tableau de bord":

    st.title("📊 Tableau de bord")

    st.markdown(
        """
        <div class="welcome">
            <h2>Bienvenue sur FinTech PME</h2>
            <p>
                Pilotez les finances de votre entreprise
                depuis un seul espace.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # INDICATEURS PRINCIPAUX
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Solde actuel",
            f"{solde_actuel:,.0f} FCFA"
        )

    with col2:
        st.metric(
            "Total des recettes",
            f"{total_recettes:,.0f} FCFA"
        )

    with col3:
        st.metric(
            "Total des dépenses",
            f"{total_depenses:,.0f} FCFA"
        )

    with col4:
        st.metric(
            "Résultat",
            f"{resultat:,.0f} FCFA"
        )

    # --------------------------------------------------------
    # INDICATEURS SECONDAIRES
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        'Indicateurs financiers'
        '</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Nombre de transactions",
            nombre_transactions
        )

    with col2:
        st.metric(
            "Marge financière",
            f"{marge_financiere:.1f}%"
        )

    with col3:

        moyenne_recette = (
            total_recettes / nombre_recettes
            if nombre_recettes > 0
            else 0
        )

        st.metric(
            "Recette moyenne",
            f"{moyenne_recette:,.0f} FCFA"
        )

    # --------------------------------------------------------
    # ÉVOLUTION MENSUELLE
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        'Évolution des recettes et dépenses'
        '</div>',
        unsafe_allow_html=True
    )

    evolution = defaultdict(
        lambda: {
            "Recettes": 0,
            "Dépenses": 0
        }
    )

    for recette in recettes:

        date_transaction = recette[1]
        montant = recette[2]

        try:
            mois = datetime.strptime(
                date_transaction,
                "%Y-%m-%d"
            ).strftime("%Y-%m")

        except ValueError:
            mois = str(date_transaction)[:7]

        evolution[mois]["Recettes"] += montant

    for depense in depenses:

        date_transaction = depense[1]
        montant = depense[2]

        try:
            mois = datetime.strptime(
                date_transaction,
                "%Y-%m-%d"
            ).strftime("%Y-%m")

        except ValueError:
            mois = str(date_transaction)[:7]

        evolution[mois]["Dépenses"] += montant

    if evolution:

        mois_tries = sorted(
            evolution.keys()
        )

        graphique = []

        for mois in mois_tries:

            graphique.append(
                {
                    "Mois": mois,
                    "Recettes": evolution[mois]["Recettes"],
                    "Dépenses": evolution[mois]["Dépenses"]
                }
            )

        st.line_chart(
            graphique,
            x="Mois",
            y=["Recettes", "Dépenses"]
        )

    else:

        st.info(
            "Ajoutez des recettes et des dépenses "
            "pour afficher l'évolution financière."
        )

    # --------------------------------------------------------
    # ANALYSE DES DÉPENSES
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            '<div class="section-title">'
            'Répartition des dépenses'
            '</div>',
            unsafe_allow_html=True
        )

        categories_depenses = defaultdict(float)

        for depense in depenses:

            categorie = depense[3]
            montant = depense[2]

            categories_depenses[categorie] += montant

        if categories_depenses:

            categories_tries = sorted(
                categories_depenses.items(),
                key=lambda x: x[1],
                reverse=True
            )

            graphique_depenses = []

            for categorie, montant in categories_tries:

                graphique_depenses.append(
                    {
                        "Catégorie": categorie,
                        "Montant": montant
                    }
                )

            st.bar_chart(
                graphique_depenses,
                x="Catégorie",
                y="Montant"
            )

        else:

            st.info(
                "Aucune dépense enregistrée."
            )

    # --------------------------------------------------------
    # DERNIÈRES TRANSACTIONS
    # --------------------------------------------------------

    with col2:

        st.markdown(
            '<div class="section-title">'
            'Dernières transactions'
            '</div>',
            unsafe_allow_html=True
        )

        transactions = []

        for recette in recettes:

            transactions.append(
                {
                    "date": recette[1],
                    "type": "Recette",
                    "categorie": recette[3],
                    "montant": recette[2]
                }
            )

        for depense in depenses:

            transactions.append(
                {
                    "date": depense[1],
                    "type": "Dépense",
                    "categorie": depense[3],
                    "montant": depense[2]
                }
            )

        transactions.sort(
            key=lambda x: x["date"],
            reverse=True
        )

        if transactions:

            for transaction in transactions[:5]:

                signe = (
                    "+"
                    if transaction["type"] == "Recette"
                    else "-"
                )

                st.write(
                    f"**{transaction['date']}** — "
                    f"{transaction['type']} — "
                    f"{transaction['categorie']} : "
                    f"{signe}"
                    f"{transaction['montant']:,.0f} FCFA"
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

    st.write(
        "Enregistrez, recherchez, modifiez et supprimez "
        "les recettes de votre entreprise."
    )

    st.divider()

    # --------------------------------------------------------
    # AJOUT
    # --------------------------------------------------------

    st.subheader("➕ Ajouter une recette")

    with st.form("form_recette"):

        col1, col2 = st.columns(2)

        with col1:

            date_recette = st.date_input(
                "Date",
                value=date.today()
            )

            montant = st.number_input(
                "Montant (FCFA)",
                min_value=0.0,
                step=100.0,
                format="%.0f"
            )

            categorie = st.selectbox(
                "Catégorie",
                [
                    "Vente",
                    "Prestation de service",
                    "Subvention",
                    "Commission",
                    "Autre"
                ]
            )

        with col2:

            source = st.text_input(
                "Source / Client",
                placeholder="Exemple : Client ABC"
            )

            moyen_paiement = st.selectbox(
                "Moyen de paiement",
                [
                    "Espèces",
                    "Mobile Money",
                    "Virement bancaire",
                    "Carte bancaire",
                    "Autre"
                ]
            )

            description = st.text_input(
                "Description",
                placeholder="Description de la recette"
            )

        submitted = st.form_submit_button(
            "💾 Enregistrer la recette",
            use_container_width=True
        )

        if submitted:

            if montant <= 0:

                st.error(
                    "Le montant doit être supérieur à zéro."
                )

            else:

                ajouter_recette(
                    entreprise_id,
                    str(date_recette),
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

    st.divider()

    # --------------------------------------------------------
    # FILTRES
    # --------------------------------------------------------

    st.subheader("🔎 Rechercher et filtrer")

    col1, col2, col3 = st.columns(3)

    with col1:

        recherche_recette = st.text_input(
            "Recherche",
            placeholder="Client, description..."
        )

    with col2:

        filtre_categorie = st.selectbox(
            "Catégorie",
            [
                "Toutes",
                "Vente",
                "Prestation de service",
                "Subvention",
                "Commission",
                "Autre"
            ]
        )

    with col3:

        filtre_date = st.date_input(
            "Période",
            value=(date.today().replace(day=1), date.today()),
            key="periode_recettes"
        )

    recettes = recuperer_recettes(
        entreprise_id
    )

    recettes_filtrees = []

    for recette in recettes:

        date_recette_obj = datetime.strptime(
            recette[1],
            "%Y-%m-%d"
        ).date()

        correspond_recherche = (
            not recherche_recette
            or recherche_recette.lower()
            in (
                f"{recette[4] or ''} "
                f"{recette[6] or ''} "
                f"{recette[3]}"
            ).lower()
        )

        correspond_categorie = (
            filtre_categorie == "Toutes"
            or recette[3] == filtre_categorie
        )

        correspond_date = True

        if isinstance(filtre_date, tuple) and len(filtre_date) == 2:

            date_debut, date_fin = filtre_date

            correspond_date = (
                date_debut
                <= date_recette_obj
                <= date_fin
            )

        if (
            correspond_recherche
            and correspond_categorie
            and correspond_date
        ):

            recettes_filtrees.append(recette)

    # --------------------------------------------------------
    # EXPORT
    # --------------------------------------------------------

    st.subheader("📥 Exporter")

    sortie = io.StringIO()

    writer = csv.writer(
        sortie
    )

    writer.writerow(
        [
            "Date",
            "Montant",
            "Catégorie",
            "Source / Client",
            "Moyen de paiement",
            "Description"
        ]
    )

    for recette in recettes_filtrees:

        writer.writerow(
            [
                recette[1],
                recette[2],
                recette[3],
                recette[4] or "",
                recette[5] or "",
                recette[6] or ""
            ]
        )

    st.download_button(
        "📥 Télécharger les recettes en CSV",
        data=sortie.getvalue(),
        file_name="recettes_fintech_pme.csv",
        mime="text/csv",
        use_container_width=True
    )

    # --------------------------------------------------------
    # HISTORIQUE
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        f"📋 Historique ({len(recettes_filtrees)})"
    )

    if recettes_filtrees:

        for recette in recettes_filtrees:

            with st.container(border=True):

                col1, col2, col3, col4 = st.columns(
                    [1.2, 1.5, 2, 1.5]
                )

                with col1:

                    st.write(
                        f"**Date**\n\n{recette[1]}"
                    )

                with col2:

                    st.write(
                        f"**Montant**\n\n"
                        f"{recette[2]:,.0f} FCFA"
                    )

                    st.write(
                        f"**Catégorie**\n\n"
                        f"{recette[3]}"
                    )

                with col3:

                    st.write(
                        f"**Source**\n\n"
                        f"{recette[4] or 'Non renseignée'}"
                    )

                    st.write(
                        f"**Paiement**\n\n"
                        f"{recette[5]}"
                    )

                with col4:

                    if st.button(
                        "✏️ Modifier",
                        key=f"modifier_recette_{recette[0]}",
                        use_container_width=True
                    ):

                        st.session_state[
                            "recette_a_modifier"
                        ] = recette[0]

                        st.rerun()

                    if st.button(
                        "🗑️ Supprimer",
                        key=f"supprimer_recette_{recette[0]}",
                        use_container_width=True
                    ):

                        st.session_state[
                            "recette_a_supprimer"
                        ] = recette[0]

                        st.rerun()

                if st.session_state.get(
                    "recette_a_supprimer"
                ) == recette[0]:

                    st.warning(
                        "Voulez-vous vraiment supprimer cette recette ?"
                    )

                    col_a, col_b = st.columns(2)

                    with col_a:

                        if st.button(
                            "Oui, supprimer",
                            key=f"confirmer_sup_recette_{recette[0]}",
                            use_container_width=True
                        ):

                            supprimer_recette(
                                recette[0],
                                entreprise_id
                            )

                            del st.session_state[
                                "recette_a_supprimer"
                            ]

                            st.success(
                                "Recette supprimée."
                            )

                            st.rerun()

                    with col_b:

                        if st.button(
                            "Annuler",
                            key=f"annuler_sup_recette_{recette[0]}",
                            use_container_width=True
                        ):

                            del st.session_state[
                                "recette_a_supprimer"
                            ]

                            st.rerun()

                if st.session_state.get(
                    "recette_a_modifier"
                ) == recette[0]:

                    st.divider()

                    st.write("### ✏️ Modifier la recette")

                    with st.form(
                        f"edit_recette_{recette[0]}"
                    ):

                        nouvelle_date = st.date_input(
                            "Date",
                            value=datetime.strptime(
                                recette[1],
                                "%Y-%m-%d"
                            ).date()
                        )

                        nouveau_montant = st.number_input(
                            "Montant (FCFA)",
                            min_value=0.0,
                            value=float(recette[2]),
                            step=100.0,
                            format="%.0f"
                        )

                        nouvelles_categories = [
                            "Vente",
                            "Prestation de service",
                            "Subvention",
                            "Commission",
                            "Autre"
                        ]

                        index_categorie = (
                            nouvelles_categories.index(recette[3])
                            if recette[3]
                            in nouvelles_categories
                            else 0
                        )

                        nouvelle_categorie = st.selectbox(
                            "Catégorie",
                            nouvelles_categories,
                            index=index_categorie
                        )

                        nouvelle_source = st.text_input(
                            "Source / Client",
                            value=recette[4] or ""
                        )

                        moyens = [
                            "Espèces",
                            "Mobile Money",
                            "Virement bancaire",
                            "Carte bancaire",
                            "Autre"
                        ]

                        index_paiement = (
                            moyens.index(recette[5])
                            if recette[5] in moyens
                            else 0
                        )

                        nouveau_paiement = st.selectbox(
                            "Moyen de paiement",
                            moyens,
                            index=index_paiement
                        )

                        nouvelle_description = st.text_input(
                            "Description",
                            value=recette[6] or ""
                        )

                        enregistrer_modification = st.form_submit_button(
                            "💾 Enregistrer les modifications",
                            use_container_width=True
                        )

                        if enregistrer_modification:

                            if nouveau_montant <= 0:

                                st.error(
                                    "Le montant doit être supérieur à zéro."
                                )

                            else:

                                modifier_recette(
                                    recette[0],
                                    entreprise_id,
                                    str(nouvelle_date),
                                    nouveau_montant,
                                    nouvelle_categorie,
                                    nouvelle_source,
                                    nouveau_paiement,
                                    nouvelle_description
                                )

                                del st.session_state[
                                    "recette_a_modifier"
                                ]

                                st.success(
                                    "Recette modifiée avec succès."
                                )

                                st.rerun()

    else:

        st.info(
            "Aucune recette ne correspond aux critères."
        )


# ============================================================
# DEPENSES
# ============================================================

elif menu == "💸 Dépenses":

    st.title("💸 Gestion des dépenses")

    st.write(
        "Enregistrez, recherchez, modifiez et supprimez "
        "les dépenses de votre entreprise."
    )

    st.divider()

    # --------------------------------------------------------
    # AJOUT
    # --------------------------------------------------------

    st.subheader("➕ Ajouter une dépense")

    with st.form("form_depense"):

        col1, col2 = st.columns(2)

        with col1:

            date_depense = st.date_input(
                "Date",
                value=date.today()
            )

            montant = st.number_input(
                "Montant (FCFA)",
                min_value=0.0,
                step=100.0,
                format="%.0f"
            )

            categorie = st.selectbox(
                "Catégorie",
                [
                    "Achat de marchandises",
                    "Transport",
                    "Salaires",
                    "Loyer",
                    "Électricité",
                    "Eau",
                    "Téléphone / Internet",
                    "Fournitures",
                    "Marketing",
                    "Autre"
                ]
            )

        with col2:

            beneficiaire = st.text_input(
                "Bénéficiaire / Fournisseur",
                placeholder="Exemple : Fournisseur ABC"
            )

            moyen_paiement = st.selectbox(
                "Moyen de paiement",
                [
                    "Espèces",
                    "Mobile Money",
                    "Virement bancaire",
                    "Carte bancaire",
                    "Autre"
                ]
            )

            description = st.text_input(
                "Description",
                placeholder="Description de la dépense"
            )

        submitted = st.form_submit_button(
            "💾 Enregistrer la dépense",
            use_container_width=True
        )

        if submitted:

            if montant <= 0:

                st.error(
                    "Le montant doit être supérieur à zéro."
                )

            else:

                ajouter_depense(
                    entreprise_id,
                    str(date_depense),
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

    st.divider()

    # --------------------------------------------------------
    # FILTRES
    # --------------------------------------------------------

    st.subheader("🔎 Rechercher et filtrer")

    col1, col2, col3 = st.columns(3)

    with col1:

        recherche_depense = st.text_input(
            "Recherche",
            placeholder="Fournisseur, description..."
        )

    with col2:

        categories_depense_filtre = [
            "Toutes",
            "Achat de marchandises",
            "Transport",
            "Salaires",
            "Loyer",
            "Électricité",
            "Eau",
            "Téléphone / Internet",
            "Fournitures",
            "Marketing",
            "Autre"
        ]

        filtre_categorie_depense = st.selectbox(
            "Catégorie",
            categories_depense_filtre
        )

    with col3:

        filtre_date_depense = st.date_input(
            "Période",
            value=(date.today().replace(day=1), date.today()),
            key="periode_depenses"
        )

    depenses = recuperer_depenses(
        entreprise_id
    )

    depenses_filtrees = []

    for depense in depenses:

        date_depense_obj = datetime.strptime(
            depense[1],
            "%Y-%m-%d"
        ).date()

        correspond_recherche = (
            not recherche_depense
            or recherche_depense.lower()
            in (
                f"{depense[4] or ''} "
                f"{depense[6] or ''} "
                f"{depense[3]}"
            ).lower()
        )

        correspond_categorie = (
            filtre_categorie_depense == "Toutes"
            or depense[3] == filtre_categorie_depense
        )

        correspond_date = True

        if (
            isinstance(
                filtre_date_depense,
                tuple
            )
            and len(filtre_date_depense) == 2
        ):

            date_debut, date_fin = filtre_date_depense

            correspond_date = (
                date_debut
                <= date_depense_obj
                <= date_fin
            )

        if (
            correspond_recherche
            and correspond_categorie
            and correspond_date
        ):

            depenses_filtrees.append(depense)

    # --------------------------------------------------------
    # EXPORT
    # --------------------------------------------------------

    st.subheader("📥 Exporter")

    sortie = io.StringIO()

    writer = csv.writer(
        sortie
    )

    writer.writerow(
        [
            "Date",
            "Montant",
            "Catégorie",
            "Bénéficiaire / Fournisseur",
            "Moyen de paiement",
            "Description"
        ]
    )

    for depense in depenses_filtrees:

        writer.writerow(
            [
                depense[1],
                depense[2],
                depense[3],
                depense[4] or "",
                depense[5] or "",
                depense[6] or ""
            ]
        )

    st.download_button(
        "📥 Télécharger les dépenses en CSV",
        data=sortie.getvalue(),
        file_name="depenses_fintech_pme.csv",
        mime="text/csv",
        use_container_width=True
    )

    # --------------------------------------------------------
    # HISTORIQUE
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        f"📋 Historique ({len(depenses_filtrees)})"
    )

    if depenses_filtrees:

        for depense in depenses_filtrees:

            with st.container(border=True):

                col1, col2, col3, col4 = st.columns(
                    [1.2, 1.5, 2, 1.5]
                )

                with col1:

                    st.write(
                        f"**Date**\n\n{depense[1]}"
                    )

                with col2:

                    st.write(
                        f"**Montant**\n\n"
                        f"{depense[2]:,.0f} FCFA"
                    )

                    st.write(
                        f"**Catégorie**\n\n"
                        f"{depense[3]}"
                    )

                with col3:

                    st.write(
                        f"**Bénéficiaire**\n\n"
                        f"{depense[4] or 'Non renseigné'}"
                    )

                    st.write(
                        f"**Paiement**\n\n"
                        f"{depense[5]}"
                    )

                with col4:

                    if st.button(
                        "✏️ Modifier",
                        key=f"modifier_depense_{depense[0]}",
                        use_container_width=True
                    ):

                        st.session_state[
                            "depense_a_modifier"
                        ] = depense[0]

                        st.rerun()

                    if st.button(
                        "🗑️ Supprimer",
                        key=f"supprimer_depense_{depense[0]}",
                        use_container_width=True
                    ):

                        st.session_state[
                            "depense_a_supprimer"
                        ] = depense[0]

                        st.rerun()

                if st.session_state.get(
                    "depense_a_supprimer"
                ) == depense[0]:

                    st.warning(
                        "Voulez-vous vraiment supprimer cette dépense ?"
                    )

                    col_a, col_b = st.columns(2)

                    with col_a:

                        if st.button(
                            "Oui, supprimer",
                            key=f"confirmer_sup_depense_{depense[0]}",
                            use_container_width=True
                        ):

                            supprimer_depense(
                                depense[0],
                                entreprise_id
                            )

                            del st.session_state[
                                "depense_a_supprimer"
                            ]

                            st.success(
                                "Dépense supprimée."
                            )

                            st.rerun()

                    with col_b:

                        if st.button(
                            "Annuler",
                            key=f"annuler_sup_depense_{depense[0]}",
                            use_container_width=True
                        ):

                            del st.session_state[
                                "depense_a_supprimer"
                            ]

                            st.rerun()

                if st.session_state.get(
                    "depense_a_modifier"
                ) == depense[0]:

                    st.divider()

                    st.write("### ✏️ Modifier la dépense")

                    with st.form(
                        f"edit_depense_{depense[0]}"
                    ):

                        nouvelle_date = st.date_input(
                            "Date",
                            value=datetime.strptime(
                                depense[1],
                                "%Y-%m-%d"
                            ).date()
                        )

                        nouveau_montant = st.number_input(
                            "Montant (FCFA)",
                            min_value=0.0,
                            value=float(depense[2]),
                            step=100.0,
                            format="%.0f"
                        )

                        categories = [
                            "Achat de marchandises",
                            "Transport",
                            "Salaires",
                            "Loyer",
                            "Électricité",
                            "Eau",
                            "Téléphone / Internet",
                            "Fournitures",
                            "Marketing",
                            "Autre"
                        ]

                        index_categorie = (
                            categories.index(depense[3])
                            if depense[3] in categories
                            else 0
                        )

                        nouvelle_categorie = st.selectbox(
                            "Catégorie",
                            categories,
                            index=index_categorie
                        )

                        nouveau_beneficiaire = st.text_input(
                            "Bénéficiaire / Fournisseur",
                            value=depense[4] or ""
                        )

                        moyens = [
                            "Espèces",
                            "Mobile Money",
                            "Virement bancaire",
                            "Carte bancaire",
                            "Autre"
                        ]

                        index_paiement = (
                            moyens.index(depense[5])
                            if depense[5] in moyens
                            else 0
                        )

                        nouveau_paiement = st.selectbox(
                            "Moyen de paiement",
                            moyens,
                            index=index_paiement
                        )

                        nouvelle_description = st.text_input(
                            "Description",
                            value=depense[6] or ""
                        )

                        enregistrer_modification = st.form_submit_button(
                            "💾 Enregistrer les modifications",
                            use_container_width=True
                        )

                        if enregistrer_modification:

                            if nouveau_montant <= 0:

                                st.error(
                                    "Le montant doit être supérieur à zéro."
                                )

                            else:

                                modifier_depense(
                                    depense[0],
                                    entreprise_id,
                                    str(nouvelle_date),
                                    nouveau_montant,
                                    nouvelle_categorie,
                                    nouveau_beneficiaire,
                                    nouveau_paiement,
                                    nouvelle_description
                                )

                                del st.session_state[
                                    "depense_a_modifier"
                                ]

                                st.success(
                                    "Dépense modifiée avec succès."
                                )

                                st.rerun()

    else:

        st.info(
            "Aucune dépense ne correspond aux critères."
        )


# ============================================================
# TRESORERIE
# ============================================================

elif menu == "🏦 Trésorerie":

    st.title("🏦 Trésorerie")

    st.subheader(
        "Situation de trésorerie"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Solde initial",
            f"{solde_initial:,.0f} FCFA"
        )

    with col2:

        st.metric(
            "Entrées",
            f"{total_recettes:,.0f} FCFA"
        )

    with col3:

        st.metric(
            "Sorties",
            f"{total_depenses:,.0f} FCFA"
        )

    st.divider()

    st.metric(
        "Solde actuel",
        f"{solde_actuel:,.0f} FCFA"
    )


# ============================================================
# RAPPORTS
# ============================================================

elif menu == "📈 Rapports":

    st.title("📈 Rapports")

    st.info(
        "Le module de rapports financiers sera développé "
        "dans une prochaine étape."
    )


# ============================================================
# PARAMETRES
# ============================================================

elif menu == "⚙️ Paramètres":

    st.title("⚙️ Paramètres")

    st.subheader(
        "💰 Solde initial"
    )

    st.write(
        "Indiquez le montant disponible dans la caisse "
        "ou les comptes de l'entreprise au début du suivi."
    )

    nouveau_solde = st.number_input(
        "Solde initial (FCFA)",
        min_value=0.0,
        value=float(solde_initial),
        step=1000.0,
        format="%.0f"
    )

    if st.button(
        "💾 Enregistrer le solde initial",
        use_container_width=True
    ):

        modifier_solde_initial(
            entreprise_id,
            nouveau_solde
        )

        st.success(
            "Solde initial enregistré avec succès."
        )

        st.rerun()
