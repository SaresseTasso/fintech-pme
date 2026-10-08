import calendar
import io
from datetime import date, timedelta
from xml.sax.saxutils import escape

import pandas as pd
import streamlit as st
from openpyxl.utils import get_column_letter

from database import connexion, obtenir_solde_initial

MOIS = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]


# ============================================================
# DONNÉES
# ============================================================

def fcfa(montant):
    return f"{montant:,.0f} FCFA".replace(",", " ")


def _charger(entreprise_id, debut, fin):
    with connexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT t.id, t.date_operation, t.type, t.montant::float8,
                   c.nom, t.tiers, m.nom, t.description
            FROM transactions t
            JOIN categories c ON c.id = t.categorie_id
            LEFT JOIN moyens_paiement m ON m.id = t.moyen_paiement_id
            WHERE t.entreprise_id = %s
              AND t.date_operation BETWEEN %s AND %s
            ORDER BY t.date_operation, t.id
        """, (entreprise_id, debut, fin))
        lignes = cur.fetchall()

    df = pd.DataFrame(
        lignes,
        columns=["ID", "Date", "Type", "Montant", "Catégorie",
                 "Tiers", "Paiement", "Description"],
    )
    df["Date"] = pd.to_datetime(df["Date"])
    df["Type"] = df["Type"].map({"recette": "Recette", "depense": "Dépense"})
    for col in ["Tiers", "Paiement", "Description"]:
        df[col] = df[col].fillna("")
    return df


def _net_avant(entreprise_id, debut):
    """Recettes - dépenses de toutes les opérations avant la période."""
    with connexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT COALESCE(SUM(
                CASE WHEN type = 'recette' THEN montant ELSE -montant END
            ), 0)::float8
            FROM transactions
            WHERE entreprise_id = %s AND date_operation < %s
        """, (entreprise_id, debut))
        return cur.fetchone()[0]


def _nom_entreprise(entreprise_id):
    with connexion() as conn, conn.cursor() as cur:
        cur.execute("SELECT nom FROM entreprises WHERE id = %s", (entreprise_id,))
        ligne = cur.fetchone()
    return ligne[0] if ligne else ""


def _evolution(df, debut, fin, ouverture):
    """Recettes, dépenses, résultat et trésorerie par jour, semaine ou mois."""
    jours = (fin - debut).days + 1

    if jours <= 31:
        granularite = "Jour"
        cle = df["Date"].dt.strftime("%Y-%m-%d")
    elif jours <= 100:
        granularite = "Semaine (lundi)"
        lundi = df["Date"] - pd.to_timedelta(df["Date"].dt.weekday, unit="D")
        cle = lundi.dt.strftime("%Y-%m-%d")
    else:
        granularite = "Mois"
        cle = df["Date"].dt.strftime("%Y-%m")

    tableau = (
        df.assign(P=cle)
        .pivot_table(index="P", columns="Type", values="Montant",
                     aggfunc="sum", fill_value=0)
        .reindex(columns=["Recette", "Dépense"], fill_value=0)
        .sort_index()
    )
    tableau.columns = ["Recettes", "Dépenses"]
    tableau["Résultat"] = tableau["Recettes"] - tableau["Dépenses"]
    tableau["Trésorerie"] = ouverture + tableau["Résultat"].cumsum()
    tableau.index.name = granularite
    return tableau


def _formater_index(evolution):
    """Copie avec des libellés lisibles (l'original reste trié en ISO)."""
    copie = evolution.copy()
    g = evolution.index.name

    if g == "Jour":
        libs = [pd.to_datetime(i).strftime("%d/%m/%Y") for i in copie.index]
    elif g.startswith("Semaine"):
        libs = ["Sem. du " + pd.to_datetime(i).strftime("%d/%m/%Y")
                for i in copie.index]
    else:
        libs = [pd.to_datetime(i + "-01").strftime("%m/%Y") for i in copie.index]

    copie.index = pd.Index(libs, name=g)
    return copie


def _repartition(df, type_label):
    sous = df[df["Type"] == type_label]
    if sous.empty:
        return pd.DataFrame(columns=["Catégorie", "Montant", "Part (%)"])

    r = (
        sous.groupby("Catégorie", as_index=False)["Montant"].sum()
        .sort_values("Montant", ascending=False)
        .reset_index(drop=True)
    )
    r["Part (%)"] = (r["Montant"] / r["Montant"].sum() * 100).round(1)
    return r


# ============================================================
# EXPORTS
# ============================================================

def _excel(resume, evolution, depenses_cat, recettes_cat, detail):
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame(resume, columns=["Indicateur", "Valeur"]).to_excel(
            writer, sheet_name="Résumé", index=False)
        _formater_index(evolution).to_excel(writer, sheet_name="Évolution")
        depenses_cat.to_excel(
            writer, sheet_name="Dépenses par catégorie", index=False)
        recettes_cat.to_excel(
            writer, sheet_name="Recettes par catégorie", index=False)
        detail.to_excel(writer, sheet_name="Transactions", index=False)

        for feuille in writer.book.worksheets:
            for index, colonne in enumerate(feuille.columns, start=1):
                longueur = max(
                    (len(str(c.value)) for c in colonne if c.value is not None),
                    default=0,
                )
                feuille.column_dimensions[get_column_letter(index)].width = (
                    min(longueur + 3, 40)
                )
            feuille.freeze_panes = "A2"

    return buffer.getvalue()


def _pdf(nom_entreprise, administrateur, libelle, resume, evolution,
         depenses_cat, recettes_cat, detail):
    # Imports ici : si reportlab manque, le reste de l'application fonctionne
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
    )

    styles = getSampleStyleSheet()
    petit = ParagraphStyle("petit", parent=styles["Normal"], fontSize=7.5, leading=9)

    def tableau(donnees, largeurs=None, droite=()):
        t = Table(donnees, colWidths=largeurs, repeatRows=1)
        style = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3A5F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F2F5F9")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        for c in droite:
            style.append(("ALIGN", (c, 0), (c, -1), "RIGHT"))
        t.setStyle(TableStyle(style))
        return t

    def cellule(texte):
        return Paragraph(escape(str(texte)), petit)

    def pied(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawString(1.5 * cm, 1 * cm, "FinTech PME - Rapport financier")
        canvas.drawRightString(A4[0] - 1.5 * cm, 1 * cm, f"Page {doc.page}")
        canvas.restoreState()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4, title="Rapport financier",
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.5 * cm, bottomMargin=1.8 * cm,
    )

    el = [
        Paragraph("Rapport financier", styles["Title"]),
        Paragraph(f"<b>Entreprise :</b> {escape(nom_entreprise)}", styles["Normal"]),
        Paragraph(f"<b>Période :</b> {escape(libelle)}", styles["Normal"]),
        Paragraph(
            f"<b>Édité par :</b> {escape(administrateur)} "
            f"le {date.today():%d/%m/%Y}", styles["Normal"]),
        Spacer(1, 0.4 * cm),
        Paragraph("Synthèse", styles["Heading2"]),
    ]

    lignes = [["Indicateur", "Valeur"]]
    for nom, valeur in resume[1:]:  # la 1re ligne est la période
        lignes.append([nom, valeur if isinstance(valeur, str) else fcfa(valeur)])
    el.append(tableau(lignes, [8 * cm, 6 * cm], droite=(1,)))

    # Évolution
    ev = _formater_index(evolution)
    lignes = [[ev.index.name, "Recettes", "Dépenses", "Résultat", "Trésorerie"]]
    for libelle_p, r in ev.iterrows():
        lignes.append([libelle_p, fcfa(r["Recettes"]), fcfa(r["Dépenses"]),
                       fcfa(r["Résultat"]), fcfa(r["Trésorerie"])])
    el += [Spacer(1, 0.4 * cm), Paragraph("Évolution", styles["Heading2"]),
           tableau(lignes, [3.6 * cm, 3.5 * cm, 3.5 * cm, 3.5 * cm, 3.8 * cm],
                   droite=(1, 2, 3, 4))]

    # Répartitions
    for titre, rep, vide in [
        ("Répartition des dépenses", depenses_cat, "Aucune dépense sur la période."),
        ("Répartition des recettes", recettes_cat, "Aucune recette sur la période."),
    ]:
        el += [Spacer(1, 0.4 * cm), Paragraph(titre, styles["Heading2"])]
        if rep.empty:
            el.append(Paragraph(vide, styles["Normal"]))
        else:
            lignes = [["Catégorie", "Montant", "Part (%)"]]
            for _, r in rep.iterrows():
                lignes.append([cellule(r["Catégorie"]), fcfa(r["Montant"]),
                               f"{r['Part (%)']:.1f}"])
            el.append(tableau(lignes, [8 * cm, 4.5 * cm, 2.5 * cm], droite=(1, 2)))

    # Détail
    el += [Spacer(1, 0.4 * cm), Paragraph("Détail des transactions", styles["Heading2"])]
    lignes = [["Date", "Type", "Catégorie", "Tiers", "Montant", "Description"]]
    for _, r in detail.iterrows():
        lignes.append([r["Date"], r["Type"], cellule(r["Catégorie"]),
                       cellule(r["Tiers"]), fcfa(r["Montant"]),
                       cellule(r["Description"])])
    el.append(tableau(
        lignes, [2.1 * cm, 1.7 * cm, 3.2 * cm, 3 * cm, 2.9 * cm, 5.1 * cm],
        droite=(4,)))

    doc.build(el, onFirstPage=pied, onLaterPages=pied)
    return buffer.getvalue()


# ============================================================
# PAGE
# ============================================================

def _choisir_periode():
    """Retourne (debut, fin, libelle) ou None si la sélection est incomplète."""
    mode = st.radio(
        "Type de période",
        ["Jour", "Semaine", "Mois", "Année", "Période personnalisée"],
        horizontal=True,
    )
    aujourdhui = date.today()
    annees = list(range(aujourdhui.year - 5, aujourdhui.year + 1))

    if mode == "Jour":
        jour = st.date_input("Jour", value=aujourdhui, format="DD/MM/YYYY",
                             key="rap_jour")
        debut = fin = jour

    elif mode == "Semaine":
        ref = st.date_input("Un jour de la semaine voulue", value=aujourdhui,
                            format="DD/MM/YYYY", key="rap_semaine")
        debut = ref - timedelta(days=ref.weekday())
        fin = debut + timedelta(days=6)

    elif mode == "Mois":
        c1, c2 = st.columns(2)
        annee = c1.selectbox("Année", annees, index=len(annees) - 1,
                             key="rap_mois_annee")
        mois = c2.selectbox("Mois", list(range(1, 13)),
                            index=aujourdhui.month - 1,
                            format_func=lambda m: MOIS[m - 1], key="rap_mois_mois")
        debut = date(annee, mois, 1)
        fin = date(annee, mois, calendar.monthrange(annee, mois)[1])

    elif mode == "Année":
        annee = st.selectbox("Année", annees, index=len(annees) - 1,
                             key="rap_annee")
        debut, fin = date(annee, 1, 1), date(annee, 12, 31)

    else:
        choix = st.date_input(
            "Période (date de début puis date de fin)",
            value=(aujourdhui.replace(day=1), aujourdhui),
            format="DD/MM/YYYY", key="rap_perso",
        )
        if not isinstance(choix, (tuple, list)) or len(choix) != 2:
            st.info("Sélectionnez une date de début et une date de fin.")
            return None
        debut, fin = choix

    libelle = f"Du {debut:%d/%m/%Y} au {fin:%d/%m/%Y}"
    return debut, fin, libelle


def page_rapports_avances(eid):

    st.title("📈 Rapports financiers")

    periode = _choisir_periode()
    if periode is None:
        return
    debut, fin, libelle = periode

    st.caption(libelle)
    st.divider()

    df = _charger(eid, debut, fin)
    ouverture = obtenir_solde_initial(eid) + _net_avant(eid, debut)

    recettes = float(df.loc[df["Type"] == "Recette", "Montant"].sum())
    depenses = float(df.loc[df["Type"] == "Dépense", "Montant"].sum())
    resultat = recettes - depenses
    cloture = ouverture + resultat
    marge = (resultat / recettes * 100) if recettes > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Solde d'ouverture", fcfa(ouverture))
    c2.metric("Total recettes", fcfa(recettes))
    c3.metric("Total dépenses", fcfa(depenses))
    c4.metric("Solde de clôture", fcfa(cloture))

    c1, c2, c3 = st.columns(3)
    c1.metric("Résultat", fcfa(resultat))
    c2.metric("Nombre de transactions", len(df))
    c3.metric("Marge", f"{marge:.1f} %")

    if df.empty:
        st.info("Aucune transaction sur cette période.")
        return

    resume = [
        ("Période", libelle),
        ("Solde d'ouverture", ouverture),
        ("Total recettes", recettes),
        ("Total dépenses", depenses),
        ("Résultat", resultat),
        ("Solde de clôture", cloture),
        ("Nombre de transactions", str(len(df))),
        ("Marge", f"{marge:.1f} %"),
    ]

    evolution = _evolution(df, debut, fin, ouverture)
    depenses_cat = _repartition(df, "Dépense")
    recettes_cat = _repartition(df, "Recette")

    # ---------------- Évolution ----------------
    st.divider()
    st.subheader(f"Évolution par {evolution.index.name.lower().split(' ')[0]}")

    col_a, col_b = st.columns(2)
    with col_a:
        st.caption("Recettes et dépenses")
        st.bar_chart(evolution[["Recettes", "Dépenses"]])
    with col_b:
        st.caption("Trésorerie")
        st.line_chart(evolution[["Trésorerie"]])

    st.dataframe(_formater_index(evolution), use_container_width=True)

    # ---------------- Répartitions ----------------
    st.divider()
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Répartition des dépenses")
        if depenses_cat.empty:
            st.info("Aucune dépense sur la période.")
        else:
            st.bar_chart(depenses_cat.set_index("Catégorie")["Montant"])
            st.dataframe(depenses_cat, use_container_width=True, hide_index=True)

    with col_b:
        st.subheader("Répartition des recettes")
        if recettes_cat.empty:
            st.info("Aucune recette sur la période.")
        else:
            st.bar_chart(recettes_cat.set_index("Catégorie")["Montant"])
            st.dataframe(recettes_cat, use_container_width=True, hide_index=True)

    # ---------------- Détail ----------------
    st.divider()
    st.subheader("Détail des transactions")

    detail = df.assign(Date=df["Date"].dt.strftime("%d/%m/%Y"))[
        ["Date", "Type", "Catégorie", "Tiers", "Paiement", "Montant", "Description"]
    ]
    st.dataframe(detail, use_container_width=True, hide_index=True)

    # ---------------- Exports ----------------
    st.divider()
    st.subheader("📥 Exports")

    nom_fichier = f"rapport_{debut:%Y%m%d}_{fin:%Y%m%d}"
    col_x, col_p = st.columns(2)

    with col_x:
        st.download_button(
            "📊 Télécharger en Excel",
            data=_excel(resume, evolution, depenses_cat, recettes_cat, detail),
            file_name=f"{nom_fichier}.xlsx",
            mime=("application/vnd.openxmlformats-officedocument."
                  "spreadsheetml.sheet"),
            use_container_width=True,
        )

    with col_p:
        try:
            pdf = _pdf(
                _nom_entreprise(eid),
                st.session_state.nom_utilisateur,
                libelle, resume, evolution,
                depenses_cat, recettes_cat, detail,
            )
            st.download_button(
                "📄 Télécharger en PDF",
                data=pdf,
                file_name=f"{nom_fichier}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except ImportError:
            st.warning(
                "Export PDF indisponible : ajoutez `reportlab` "
                "dans requirements.txt."
            )
