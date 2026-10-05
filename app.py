import streamlit as st
from datetime import date

from database import (
    initialize_database,
    obtenir_entreprise_par_defaut,
    ajouter_recette,
    recuperer_recettes,
    ajouter_depense,
    recuperer_depenses
)

# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="FinTech PME",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# INITIALISATION
# --------------------------------------------------

initialize_database()

entreprise_id = obtenir_entreprise_par_defaut()

# --------------------------------------------------
# STYLE
# --------------------------------------------------

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
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #e6e6e6;
            background-color: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }

        .metric-title {
            font-size: 14px;
            color: #666666;
            margin-bottom: 8px;
        }

        .metric-value {
            font-size: 28px;
            font-weight: 700;
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

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.title("💼 FinTech PME")

    st.caption("Gestion financière simplifiée")

    st.divider()

    menu = st.radio(
        "Navigation",
        [
            "📊 Tableau de bord",
            "💰 Recettes",
            "💸 Dépenses",
            "🏦 Trésorerie",
            "📈 Rapports"
        ]
    )

    st.divider()

    st.caption("Version 1.0 — Prototype")


# --------------------------------------------------
# TABLEAU DE BORD
# --------------------------------------------------

if menu == "📊 Tableau de bord":

    st.title("Tableau de bord")

    st.markdown(
        """
        <div class="welcome">
            <h2>Bienvenue sur FinTech PME</h2>
            <p>
                Pilotez simplement les finances de votre entreprise
                depuis un seul espace.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-title">Solde actuel</div>
                <div class="metric-value">0 FCFA</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-title">Recettes</div>
                <div class="metric-value">0 FCFA</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col3:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-title">Dépenses</div>
                <div class="metric-value">0 FCFA</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col4:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-title">Résultat</div>
                <div class="metric-value">0 FCFA</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        '<div class="section-title">Évolution financière</div>',
        unsafe_allow_html=True
    )

    chart_data = {
        "Mois": [
            "Mai",
            "Juin",
            "Juillet",
            "Août",
            "Septembre",
            "Octobre"
        ],
        "Recettes": [0, 0, 0, 0, 0, 0],
        "Dépenses": [0, 0, 0, 0, 0, 0]
    }

    st.line_chart(
        chart_data,
        x="Mois",
        y=["Recettes", "Dépenses"]
    )

    st.markdown(
        '<div class="section-title">Dernières transactions</div>',
        unsafe_allow_html=True
    )

    st.info(
        "Aucune transaction enregistrée pour le moment."
    )


# --------------------------------------------------
# RECETTES
# --------------------------------------------------

elif menu == "💰 Recettes":

    st.title("💰 Gestion des recettes")

    st.write(
        "Enregistrez les revenus de votre entreprise."
    )

    st.divider()

    # FORMULAIRE

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

    # LISTE DES RECETTES

    st.divider()

    st.subheader("📋 Historique des recettes")

    recettes = recuperer_recettes(entreprise_id)

    if recettes:

        for recette in recettes:

            recette_id = recette[0]
            date_r = recette[1]
            montant_r = recette[2]
            categorie_r = recette[3]
            source_r = recette[4]
            paiement_r = recette[5]
            description_r = recette[6]

            with st.container(border=True):

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(f"**Date :** {date_r}")
                    st.write(f"**Catégorie :** {categorie_r}")

                with col2:
                    st.write(
                        f"**Montant :** {montant_r:,.0f} FCFA"
                    )
                    st.write(
                        f"**Source :** {source_r or 'Non renseignée'}"
                    )

                with col3:
                    st.write(
                        f"**Paiement :** {paiement_r}"
                    )
                    st.write(
                        f"**Description :** "
                        f"{description_r or 'Aucune'}"
                    )

    else:

        st.info(
            "Aucune recette enregistrée pour le moment."
        )


# --------------------------------------------------
# DÉPENSES
# --------------------------------------------------

elif menu == "💸 Dépenses":

    st.title("💸 Gestion des dépenses")

    st.write(
        "Enregistrez et suivez les dépenses de votre entreprise."
    )

    st.divider()

    # FORMULAIRE

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

    # HISTORIQUE

    st.divider()

    st.subheader("📋 Historique des dépenses")

    depenses = recuperer_depenses(entreprise_id)

    if depenses:

        for depense in depenses:

            depense_id = depense[0]
            date_d = depense[1]
            montant_d = depense[2]
            categorie_d = depense[3]
            beneficiaire_d = depense[4]
            paiement_d = depense[5]
            description_d = depense[6]

            with st.container(border=True):

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(f"**Date :** {date_d}")
                    st.write(f"**Catégorie :** {categorie_d}")

                with col2:
                    st.write(
                        f"**Montant :** {montant_d:,.0f} FCFA"
                    )
                    st.write(
                        f"**Bénéficiaire :** "
                        f"{beneficiaire_d or 'Non renseigné'}"
                    )

                with col3:
                    st.write(
                        f"**Paiement :** {paiement_d}"
                    )
                    st.write(
                        f"**Description :** "
                        f"{description_d or 'Aucune'}"
                    )

    else:

        st.info(
            "Aucune dépense enregistrée pour le moment."
        )

# --------------------------------------------------
# TRÉSORERIE
# --------------------------------------------------

elif menu == "🏦 Trésorerie":

    st.title("🏦 Trésorerie")

    st.info(
        "Le module de suivi de la trésorerie sera développé prochainement."
    )


# --------------------------------------------------
# RAPPORTS
# --------------------------------------------------

elif menu == "📈 Rapports":

    st.title("📈 Rapports")

    st.info(
        "Le module de rapports financiers sera développé prochainement."
    )
