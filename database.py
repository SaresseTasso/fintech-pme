import hashlib
import hmac
import secrets
from contextlib import contextmanager

import psycopg2
import psycopg2.errors
import streamlit as st

PBKDF2_ITERATIONS = 200_000

# Noms utilisés par l'application -> valeur du champ "type" en base
TYPES = {
    "recettes": "recette",
    "depenses": "depense",
}


# ============================================================
# CONNEXION
# ============================================================

def _url():
    try:
        return st.secrets["database"]["url"]
    except Exception:
        raise RuntimeError(
            "Secret introuvable : ajoutez [database] url = \"...\" "
            "dans les Secrets Streamlit."
        )


@contextmanager
def connexion():
    """Ouvre une connexion, commit si tout va bien, rollback sinon."""
    conn = psycopg2.connect(_url(), connect_timeout=10)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _type(table):
    if table not in TYPES:
        raise ValueError(f"Table inconnue : {table}")
    return TYPES[table]


@st.cache_resource(show_spinner=False)
def initialize_database():
    """Vérifie que la base répond (les tables sont créées par le script SQL)."""
    with connexion() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1")
    return True


def tester_connexion():
    """Retourne (ok, message) pour diagnostiquer la connexion."""
    try:
        with connexion() as conn, conn.cursor() as cur:
            cur.execute("SELECT current_database()")
            base = cur.fetchone()[0]

            cur.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            presentes = {r[0] for r in cur.fetchall()}
            attendues = {
                "entreprises", "utilisateurs", "categories",
                "moyens_paiement", "transactions",
            }
            manquantes = attendues - presentes
            if manquantes:
                return False, f"Tables manquantes : {', '.join(sorted(manquantes))}"

            cur.execute("SELECT COUNT(*) FROM categories")
            nb_cat = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM moyens_paiement")
            nb_moy = cur.fetchone()[0]

        return True, (
            f"Connexion réussie à « {base} » · "
            f"{nb_cat} catégories · {nb_moy} moyens de paiement"
        )
    except Exception as erreur:
        return False, f"Échec de connexion : {type(erreur).__name__}"


# ============================================================
# MOTS DE PASSE (PBKDF2 + sel aléatoire)
# ============================================================

def hasher_mot_de_passe(mot_de_passe):
    sel = secrets.token_bytes(16)
    empreinte = hashlib.pbkdf2_hmac(
        "sha256", mot_de_passe.encode("utf-8"), sel, PBKDF2_ITERATIONS
    )
    return f"pbkdf2${PBKDF2_ITERATIONS}${sel.hex()}${empreinte.hex()}"


def verifier_mot_de_passe(mot_de_passe, stocke):
    try:
        _, iterations, sel, empreinte = stocke.split("$")
        calcule = hashlib.pbkdf2_hmac(
            "sha256",
            mot_de_passe.encode("utf-8"),
            bytes.fromhex(sel),
            int(iterations),
        )
        return hmac.compare_digest(calcule.hex(), empreinte)
    except (ValueError, TypeError, AttributeError):
        return False


# ============================================================
# UTILISATEURS / INSCRIPTION
# ============================================================

def email_existe(email):
    with connexion() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM utilisateurs WHERE LOWER(email) = LOWER(%s)",
            (email.strip(),),
        )
        return cur.fetchone() is not None


def inscrire_administrateur(
    nom_admin,
    email_admin,
    mot_de_passe,
    nom_entreprise,
    secteur="",
    adresse="",
    telephone="",
    email_entreprise="",
):
    """Crée l'entreprise ET l'administrateur dans une seule transaction.
    Lève ValueError si l'e-mail existe déjà."""
    email_admin = email_admin.strip().lower()

    try:
        with connexion() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM utilisateurs WHERE LOWER(email) = %s",
                (email_admin,),
            )
            if cur.fetchone():
                raise ValueError("email_existant")

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
                RETURNING id
            """, (
                entreprise_id,
                nom_admin,
                email_admin,
                hasher_mot_de_passe(mot_de_passe),
            ))
            return cur.fetchone()[0]
    except psycopg2.errors.UniqueViolation:
        raise ValueError("email_existant")


def authentifier_utilisateur(email, mot_de_passe):
    """Retourne (id, nom, email, entreprise_id, role) ou None."""
    with connexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT id, nom, email, entreprise_id, role, mot_de_passe
            FROM utilisateurs
            WHERE LOWER(email) = LOWER(%s) AND actif = TRUE
        """, (email.strip(),))
        ligne = cur.fetchone()

    if ligne is None or not verifier_mot_de_passe(mot_de_passe, ligne[5]):
        return None

    return ligne[:5]


def obtenir_utilisateur(utilisateur_id):
    """Retourne (id, nom, email, entreprise_id, role, actif, date_creation)."""
    with connexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT id, nom, email, entreprise_id, role,
                   CASE WHEN actif THEN 1 ELSE 0 END,
                   to_char(date_creation, 'YYYY-MM-DD HH24:MI:SS')
            FROM utilisateurs
            WHERE id = %s
        """, (utilisateur_id,))
        return cur.fetchone()


def changer_mot_de_passe(utilisateur_id, ancien, nouveau):
    with connexion() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT mot_de_passe FROM utilisateurs WHERE id = %s",
            (utilisateur_id,),
        )
        ligne = cur.fetchone()

        if ligne is None or not verifier_mot_de_passe(ancien, ligne[0]):
            return False

        cur.execute(
            "UPDATE utilisateurs SET mot_de_passe = %s WHERE id = %s",
            (hasher_mot_de_passe(nouveau), utilisateur_id),
        )
    return True


# ============================================================
# CATÉGORIES ET MOYENS DE PAIEMENT
# (prédéfinis : entreprise_id NULL ; propres à l'entreprise sinon)
# ============================================================

def _id_categorie(cur, entreprise_id, type_op, nom):
    nom = (nom or "").strip()
    cur.execute("""
        SELECT id FROM categories
        WHERE type = %s AND LOWER(nom) = LOWER(%s)
          AND (entreprise_id IS NULL OR entreprise_id = %s)
        ORDER BY entreprise_id NULLS FIRST
        LIMIT 1
    """, (type_op, nom, entreprise_id))
    ligne = cur.fetchone()
    if ligne:
        return ligne[0]

    cur.execute(
        "INSERT INTO categories (entreprise_id, type, nom) "
        "VALUES (%s, %s, %s) RETURNING id",
        (entreprise_id, type_op, nom),
    )
    return cur.fetchone()[0]


def _id_moyen_paiement(cur, entreprise_id, nom):
    nom = (nom or "").strip()
    if not nom:
        return None

    cur.execute("""
        SELECT id FROM moyens_paiement
        WHERE LOWER(nom) = LOWER(%s)
          AND (entreprise_id IS NULL OR entreprise_id = %s)
        ORDER BY entreprise_id NULLS FIRST
        LIMIT 1
    """, (nom, entreprise_id))
    ligne = cur.fetchone()
    if ligne:
        return ligne[0]

    cur.execute(
        "INSERT INTO moyens_paiement (entreprise_id, nom) "
        "VALUES (%s, %s) RETURNING id",
        (entreprise_id, nom),
    )
    return cur.fetchone()[0]


def lister_categories(table, entreprise_id):
    type_op = _type(table)
    with connexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT nom FROM categories
            WHERE type = %s AND (entreprise_id IS NULL OR entreprise_id = %s)
            ORDER BY nom
        """, (type_op, entreprise_id))
        return [r[0] for r in cur.fetchall()]


def lister_moyens_paiement(entreprise_id):
    with connexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT nom FROM moyens_paiement
            WHERE entreprise_id IS NULL OR entreprise_id = %s
            ORDER BY id
        """, (entreprise_id,))
        return [r[0] for r in cur.fetchall()]


# ============================================================
# TRANSACTIONS (recettes / dépenses)
# Lignes retournées : id, date, montant, categorie, tiers,
#                     moyen_paiement, description
# ============================================================

_SELECT_TRANSACTION = """
    SELECT t.id,
           to_char(t.date_operation, 'YYYY-MM-DD'),
           t.montant::float8,
           c.nom,
           t.tiers,
           m.nom,
           t.description
    FROM transactions t
    JOIN categories c ON c.id = t.categorie_id
    LEFT JOIN moyens_paiement m ON m.id = t.moyen_paiement_id
"""


def ajouter_transaction(
    table, entreprise_id, date, montant, categorie,
    tiers, moyen_paiement, description
):
    type_op = _type(table)
    with connexion() as conn, conn.cursor() as cur:
        categorie_id = _id_categorie(cur, entreprise_id, type_op, categorie)
        moyen_id = _id_moyen_paiement(cur, entreprise_id, moyen_paiement)
        cur.execute("""
            INSERT INTO transactions
                (entreprise_id, type, date_operation, montant,
                 categorie_id, moyen_paiement_id, tiers, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (entreprise_id, type_op, date, montant,
              categorie_id, moyen_id, tiers, description))


def lister_transactions(table, entreprise_id):
    type_op = _type(table)
    with connexion() as conn, conn.cursor() as cur:
        cur.execute(
            _SELECT_TRANSACTION + """
            WHERE t.entreprise_id = %s AND t.type = %s
            ORDER BY t.date_operation DESC, t.id DESC
            """,
            (entreprise_id, type_op),
        )
        return cur.fetchall()


def obtenir_transaction(table, transaction_id, entreprise_id):
    type_op = _type(table)
    with connexion() as conn, conn.cursor() as cur:
        cur.execute(
            _SELECT_TRANSACTION + """
            WHERE t.id = %s AND t.entreprise_id = %s AND t.type = %s
            """,
            (transaction_id, entreprise_id, type_op),
        )
        return cur.fetchone()


def modifier_transaction(
    table, transaction_id, entreprise_id, date, montant,
    categorie, tiers, moyen_paiement, description
):
    """Retourne True si une ligne a été modifiée."""
    type_op = _type(table)
    with connexion() as conn, conn.cursor() as cur:
        categorie_id = _id_categorie(cur, entreprise_id, type_op, categorie)
        moyen_id = _id_moyen_paiement(cur, entreprise_id, moyen_paiement)
        cur.execute("""
            UPDATE transactions
            SET date_operation = %s, montant = %s, categorie_id = %s,
                moyen_paiement_id = %s, tiers = %s, description = %s
            WHERE id = %s AND entreprise_id = %s AND type = %s
        """, (date, montant, categorie_id, moyen_id, tiers, description,
              transaction_id, entreprise_id, type_op))
        return cur.rowcount > 0


def supprimer_transaction(table, transaction_id, entreprise_id):
    """Retourne True si une ligne a été supprimée."""
    type_op = _type(table)
    with connexion() as conn, conn.cursor() as cur:
        cur.execute(
            "DELETE FROM transactions "
            "WHERE id = %s AND entreprise_id = %s AND type = %s",
            (transaction_id, entreprise_id, type_op),
        )
        return cur.rowcount > 0


def calculer_total(table, entreprise_id):
    type_op = _type(table)
    with connexion() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT COALESCE(SUM(montant), 0)::float8
            FROM transactions
            WHERE entreprise_id = %s AND type = %s
        """, (entreprise_id, type_op))
        return cur.fetchone()[0]


# ============================================================
# TRÉSORERIE
# ============================================================

def obtenir_solde_initial(entreprise_id):
    with connexion() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT solde_initial::float8 FROM entreprises WHERE id = %s",
            (entreprise_id,),
        )
        ligne = cur.fetchone()
    return ligne[0] if ligne and ligne[0] is not None else 0.0


def modifier_solde_initial(entreprise_id, montant):
    with connexion() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE entreprises SET solde_initial = %s WHERE id = %s",
            (montant, entreprise_id),
        )


def calculer_solde(entreprise_id):
    """Solde initial + recettes - dépenses."""
    return (
        obtenir_solde_initial(entreprise_id)
        + calculer_total("recettes", entreprise_id)
        - calculer_total("depenses", entreprise_id)
    )
