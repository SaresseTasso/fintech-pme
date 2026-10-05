import streamlit as st

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

    # Indicateurs principaux

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

    # Section graphique

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
        "Recettes": [
            0,
            0,
            0,
            0,
            0,
            0
        ],
        "Dépenses": [
            0,
            0,
            0,
            0,
            0,
            0
        ]
    }

    st.line_chart(
        chart_data,
        x="Mois",
        y=["Recettes", "Dépenses"]
    )

    # Dernières transactions

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

    st.title("💰 Recettes")

    st.info(
        "Le module de gestion des recettes sera développé dans la prochaine étape."
    )


# --------------------------------------------------
# DÉPENSES
# --------------------------------------------------

elif menu == "💸 Dépenses":

    st.title("💸 Dépenses")

    st.info(
        "Le module de gestion des dépenses sera développé dans la prochaine étape."
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
