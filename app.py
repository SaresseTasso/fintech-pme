import streamlit as st
from datetime import date, datetime
from collections import defaultdict

from database import (
    initialize_database,
    obtenir_entreprise_par_defaut,
    ajouter_recette,
    recuperer_recettes,
    ajouter_depense,
    recuperer_depenses,
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

    .metric-card {
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #e6e6e6;
        background-color: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    .metric-title {
        font-size: 13px;
        color: #666666;
        margin-bottom: 6px;
    }

    .metric-value {
        font-size: 25px;
        font-weight: 700;
    }

    .positive {
        color: #16803c;
    }

    .negative {
        color: #c62828;
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
        "Version 1.0 — Prototype"
    )


# ============================================================
# DONNÉES
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

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">
                    Solde actuel
                </div>

                <div class="metric-value">
                    {solde_actuel:,.0f} FCFA
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">
                    Total des recettes
                </div>

                <div class="metric-value positive">
                    {total_recettes:,.0f} FCFA
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">
                    Total des dépenses
                </div>

                <div class="metric-value negative">
                    {total_depenses:,.0f} FCFA
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:

        resultat_class = (
            "positive"
            if resultat >= 0
            else "negative"
        )

        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">
                    Résultat
                </div>

                <div class="metric-value {resultat_class}">
                    {resultat:,.0f} FCFA
                </div>
            </div>
            """,
            unsafe_allow_html=True
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

            mois = str(
                date_transaction
            )[:7]

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

            mois = str(
                date_transaction
            )[:7]

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

            categories_depenses[
                categorie
            ] += montant


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

                if transaction["type"] == "Recette":

                    signe = "+"

                else:

                    signe = "-"


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
        "Enregistrez les revenus de votre entreprise."
    )

    st.divider()

    st.subheader(
        "➕ Ajouter une recette"
    )

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

    st.subheader(
        "📋 Historique des recettes"
    )

    recettes = recuperer_recettes(
        entreprise_id
    )


    if recettes:

        for recette in recettes:

            with st.container(border=True):

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.write(
                        f"**Date :** {recette[1]}"
                    )

                    st.write(
                        f"**Catégorie :** {recette[3]}"
                    )

                with col2:

                    st.write(
                        f"**Montant :** "
                        f"{recette[2]:,.0f} FCFA"
                    )

                    st.write(
                        f"**Source :** "
                        f"{recette[4] or 'Non renseignée'}"
                    )

                with col3:

                    st.write(
                        f"**Paiement :** {recette[5]}"
                    )

                    st.write(
                        f"**Description :** "
                        f"{recette[6] or 'Aucune'}"
                    )

    else:

        st.info(
            "Aucune recette enregistrée pour le moment."
        )


# ============================================================
# DEPENSES
# ============================================================

elif menu == "💸 Dépenses":

    st.title("💸 Gestion des dépenses")

    st.write(
        "Enregistrez et suivez les dépenses "
        "de votre entreprise."
    )

    st.divider()

    st.subheader(
        "➕ Ajouter une dépense"
    )

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

    st.subheader(
        "📋 Historique des dépenses"
    )

    depenses = recuperer_depenses(
        entreprise_id
    )


    if depenses:

        for depense in depenses:

            with st.container(border=True):

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.write(
                        f"**Date :** {depense[1]}"
                    )

                    st.write(
                        f"**Catégorie :** {depense[3]}"
                    )

                with col2:

                    st.write(
                        f"**Montant :** "
                        f"{depense[2]:,.0f} FCFA"
                    )

                    st.write(
                        f"**Bénéficiaire :** "
                        f"{depense[4] or 'Non renseigné'}"
                    )

                with col3:

                    st.write(
                        f"**Paiement :** {depense[5]}"
                    )

                    st.write(
                        f"**Description :** "
                        f"{depense[6] or 'Aucune'}"
                    )

    else:

        st.info(
            "Aucune dépense enregistrée pour le moment."
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
