import sqlite3
import hashlib
import hmac
import secrets
from contextlib import contextmanager
from datetime import datetime

DATABASE_NAME = "fintech_pme.db"
PBKDF2_ITERATIONS = 200_000

# Table -> nom de la colonne "tiers" (liste blanche, évite toute injection)
TABLES = {
    "recettes": "source",
    "depenses": "beneficiaire",
}


# ============================================================
# CONNEXION
# ============================================================

@contextmanager
def connexion():
    """Ouvre une connexion, commit si tout va bien, rollback sinon."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _verifier_table(table):
    if table not in TABLES:
        raise ValueError(f"Table inconnue : {table}")
    return TABLES[table]


def _ajouter_colonne(cur, table, colonne, definition):
    colonnes = [r[1] for r in cur.execute(f"PRAGMA table_info({table})")]
    if colonne not in colonnes:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {colonne} {definition}")


# ============================================================
# INITIALISATION
# ============================================================

def initialize_database():
    with connexion() as conn:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS entreprises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                secteur TEXT,
                adresse TEXT,
                telephone TEXT,
                email TEXT,
                devise TEXT DEFAULT 'FCFA',
                solde_initial REAL DEFAULT 0
            )
        """)
        _ajouter_colonne(cur, "entreprises", "solde_initial", "REAL DEFAULT 0")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS utilisateurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                mot_de_passe TEXT NOT NULL,
                entreprise_id INTEGER,
                role TEXT DEFAULT 'admin',
                actif INTEGER DEFAULT 1,
                date_creation TEXT,
                FOREIGN KEY (entreprise_id) REFERENCES entreprises(id)
            )
        """)
        _ajouter_colonne(cur, "utilisateurs", "role", "TEXT DEFAULT 'admin'")
        _ajouter_colonne(cur, "utilisateurs", "actif", "INTEGER DEFAULT 1")
        _ajouter_colonne(cur, "utilisateurs", "date_creation", "TEXT")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS recettes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entreprise_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                montant REAL NOT NULL CHECK (montant > 0),
                categorie TEXT NOT NULL,
                source TEXT,
                moyen_paiement TEXT,
                description TEXT,
                FOREIGN KEY (entreprise_id) REFERENCES entreprises(id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS depenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entreprise_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                montant REAL NOT NULL CHECK (montant > 0),
                categorie TEXT NOT NULL,
                beneficiaire TEXT,
                moyen_paiement TEXT,
                description TEXT,
                FOREIGN KEY (entreprise_id) REFERENCES entreprises(id)
            )
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_recettes_ent_date
            ON recettes (entreprise_id, date)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_depenses_ent_date
            ON depenses (entreprise_id, date)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_utilisateurs_email
            ON utilisateurs (LOWER(email))
        """)


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
    """Vérifie le nouveau format et l'ancien SHA-256 (migration)."""
    if stocke.startswith("pbkdf2$"):
        try:
            _, iterations, sel, empreinte = stocke.split("$")
            calcule = hashlib.pbkdf2_hmac(
                "sha256",
                mot_de_passe.encode("utf-8"),
                bytes.fromhex(sel),
                int(iterations),
            )
            return hmac.compare_digest(calcule.hex(), empreinte)
        except (ValueError, TypeError):
            return False

    ancien = hashlib.sha256(mot_de_passe.encode("utf-8")).hexdigest()
    return hmac.compare_digest(ancien, stocke)


# ============================================================
# UTILISATEURS / INSCRIPTION
# ============================================================

def email_existe(email):
    with connexion() as conn:
        resultat = conn.execute(
            "SELECT id FROM utilisateurs WHERE LOWER(email) = LOWER(?)",
            (email.strip(),),
        ).fetchone()
    return resultat is not None


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
    date_creation = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with connexion() as conn:
            cur = conn.cursor()

            cur.execute(
                "SELECT id FROM utilisateurs WHERE LOWER(email) = ?",
                (email_admin,),
            )
            if cur.fetchone():
                raise ValueError("email_existant")

            cur.execute("""
                INSERT INTO entreprises
                    (nom, secteur, adresse, telephone, email, devise, solde_initial)
                VALUES (?, ?, ?, ?, ?, 'FCFA', 0)
            """, (nom_entreprise, secteur, adresse, telephone, email_entreprise))
            entreprise_id = cur.lastrowid

            cur.execute("""
                INSERT INTO utilisateurs
                    (nom, email, mot_de_passe, entreprise_id, role, actif, date_creation)
                VALUES (?, ?, ?, ?, 'admin', 1, ?)
            """, (
                nom_admin,
                email_admin,
                hasher_mot_de_passe(mot_de_passe),
                entreprise_id,
                date_creation,
            ))
            return cur.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError("email_existant")


def authentifier_utilisateur(email, mot_de_passe):
    """Retourne (id, nom, email, entreprise_id, role) ou None."""
    with connexion() as conn:
        ligne = conn.execute("""
            SELECT id, nom, email, entreprise_id, role, mot_de_passe
            FROM utilisateurs
            WHERE LOWER(email) = LOWER(?) AND actif = 1
        """, (email.strip(),)).fetchone()

        if ligne is None:
            return None

        stocke = ligne[5]
        if not verifier_mot_de_passe(mot_de_passe, stocke):
            return None

        # Migration automatique des anciens hachages SHA-256
        if not stocke.startswith("pbkdf2$"):
            conn.execute(
                "UPDATE utilisateurs SET mot_de_passe = ? WHERE id = ?",
                (hasher_mot_de_passe(mot_de_passe), ligne[0]),
            )

    return ligne[:5]


def obtenir_utilisateur(utilisateur_id):
    """Retourne (id, nom, email, entreprise_id, role, actif, date_creation)."""
    with connexion() as conn:
        return conn.execute("""
            SELECT id, nom, email, entreprise_id, role, actif, date_creation
            FROM utilisateurs
            WHERE id = ?
        """, (utilisateur_id,)).fetchone()


def changer_mot_de_passe(utilisateur_id, ancien, nouveau):
    with connexion() as conn:
        ligne = conn.execute(
            "SELECT mot_de_passe FROM utilisateurs WHERE id = ?",
            (utilisateur_id,),
        ).fetchone()

        if ligne is None or not verifier_mot_de_passe(ancien, ligne[0]):
            return False

        conn.execute(
            "UPDATE utilisateurs SET mot_de_passe = ? WHERE id = ?",
            (hasher_mot_de_passe(nouveau), utilisateur_id),
        )
    return True


# ============================================================
# TRANSACTIONS (recettes / dépenses)
# Colonnes retournées : id, date, montant, categorie, tiers,
#                       moyen_paiement, description
# ============================================================

def ajouter_transaction(
    table, entreprise_id, date, montant, categorie,
    tiers, moyen_paiement, description
):
    col = _verifier_table(table)
    with connexion() as conn:
        conn.execute(f"""
            INSERT INTO {table}
                (entreprise_id, date, montant, categorie, {col},
                 moyen_paiement, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (entreprise_id, date, montant, categorie,
              tiers, moyen_paiement, description))


def lister_transactions(table, entreprise_id):
    col = _verifier_table(table)
    with connexion() as conn:
        return conn.execute(f"""
            SELECT id, date, montant, categorie, {col},
                   moyen_paiement, description
            FROM {table}
            WHERE entreprise_id = ?
            ORDER BY date DESC, id DESC
        """, (entreprise_id,)).fetchall()


def obtenir_transaction(table, transaction_id, entreprise_id):
    col = _verifier_table(table)
    with connexion() as conn:
        return conn.execute(f"""
            SELECT id, date, montant, categorie, {col},
                   moyen_paiement, description
            FROM {table}
            WHERE id = ? AND entreprise_id = ?
        """, (transaction_id, entreprise_id)).fetchone()


def modifier_transaction(
    table, transaction_id, entreprise_id, date, montant,
    categorie, tiers, moyen_paiement, description
):
    """Retourne True si une ligne a été modifiée."""
    col = _verifier_table(table)
    with connexion() as conn:
        cur = conn.execute(f"""
            UPDATE {table}
            SET date = ?, montant = ?, categorie = ?, {col} = ?,
                moyen_paiement = ?, description = ?
            WHERE id = ? AND entreprise_id = ?
        """, (date, montant, categorie, tiers, moyen_paiement,
              description, transaction_id, entreprise_id))
        return cur.rowcount > 0


def supprimer_transaction(table, transaction_id, entreprise_id):
    """Retourne True si une ligne a été supprimée."""
    _verifier_table(table)
    with connexion() as conn:
        cur = conn.execute(
            f"DELETE FROM {table} WHERE id = ? AND entreprise_id = ?",
            (transaction_id, entreprise_id),
        )
        return cur.rowcount > 0


def calculer_total(table, entreprise_id):
    _verifier_table(table)
    with connexion() as conn:
        return conn.execute(
            f"SELECT COALESCE(SUM(montant), 0) FROM {table} WHERE entreprise_id = ?",
            (entreprise_id,),
        ).fetchone()[0]


# ============================================================
# TRÉSORERIE
# ============================================================

def obtenir_solde_initial(entreprise_id):
    with connexion() as conn:
        resultat = conn.execute(
            "SELECT solde_initial FROM entreprises WHERE id = ?",
            (entreprise_id,),
        ).fetchone()
    if resultat and resultat[0] is not None:
        return resultat[0]
    return 0


def modifier_solde_initial(entreprise_id, montant):
    with connexion() as conn:
        conn.execute(
            "UPDATE entreprises SET solde_initial = ? WHERE id = ?",
            (montant, entreprise_id),
        )


def calculer_solde(entreprise_id):
    """Solde initial + recettes - dépenses."""
    return (
        obtenir_solde_initial(entreprise_id)
        + calculer_total("recettes", entreprise_id)
        - calculer_total("depenses", entreprise_id)
    )
