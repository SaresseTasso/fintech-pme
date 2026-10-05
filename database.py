import sqlite3
import hashlib
from datetime import datetime


DATABASE_NAME = "fintech_pme.db"


# ============================================================
# CONNEXION
# ============================================================

def get_connection():
    return sqlite3.connect(DATABASE_NAME)


# ============================================================
# INITIALISATION DE LA BASE
# ============================================================

def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------------------------
    # ENTREPRISES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entreprises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            secteur TEXT,
            adresse TEXT,
            telephone TEXT,
            email TEXT,
            devise TEXT DEFAULT 'FCFA'
        )
    """)

    try:

        cursor.execute("""
            ALTER TABLE entreprises
            ADD COLUMN solde_initial REAL DEFAULT 0
        """)

    except sqlite3.OperationalError:

        pass

    # --------------------------------------------------------
    # UTILISATEURS / ADMINISTRATEURS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            mot_de_passe TEXT NOT NULL,
            entreprise_id INTEGER,
            role TEXT DEFAULT 'admin',
            actif INTEGER DEFAULT 1,
            date_creation TEXT,
            FOREIGN KEY (entreprise_id)
            REFERENCES entreprises(id)
        )
    """)

    # Ajouter les nouvelles colonnes aux anciennes bases

    try:

        cursor.execute("""
            ALTER TABLE utilisateurs
            ADD COLUMN role TEXT DEFAULT 'admin'
        """)

    except sqlite3.OperationalError:

        pass

    try:

        cursor.execute("""
            ALTER TABLE utilisateurs
            ADD COLUMN actif INTEGER DEFAULT 1
        """)

    except sqlite3.OperationalError:

        pass

    try:

        cursor.execute("""
            ALTER TABLE utilisateurs
            ADD COLUMN date_creation TEXT
        """)

    except sqlite3.OperationalError:

        pass

    # --------------------------------------------------------
    # RECETTES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recettes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entreprise_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            montant REAL NOT NULL,
            categorie TEXT NOT NULL,
            source TEXT,
            moyen_paiement TEXT,
            description TEXT,
            FOREIGN KEY (entreprise_id)
            REFERENCES entreprises(id)
        )
    """)

    # --------------------------------------------------------
    # DEPENSES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS depenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entreprise_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            montant REAL NOT NULL,
            categorie TEXT NOT NULL,
            beneficiaire TEXT,
            moyen_paiement TEXT,
            description TEXT,
            FOREIGN KEY (entreprise_id)
            REFERENCES entreprises(id)
        )
    """)

    connection.commit()
    connection.close()


# ============================================================
# SECURITE MOT DE PASSE
# ============================================================

def hasher_mot_de_passe(mot_de_passe):

    return hashlib.sha256(
        mot_de_passe.encode("utf-8")
    ).hexdigest()


# ============================================================
# ENTREPRISE
# ============================================================

def creer_entreprise(
    nom,
    secteur,
    adresse,
    telephone,
    email,
    devise="FCFA"
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO entreprises (
            nom,
            secteur,
            adresse,
            telephone,
            email,
            devise,
            solde_initial
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        nom,
        secteur,
        adresse,
        telephone,
        email,
        devise,
        0
    ))

    entreprise_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return entreprise_id


# ============================================================
# ADMINISTRATEUR
# ============================================================

def email_existe(email):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM utilisateurs
        WHERE LOWER(email) = LOWER(?)
    """, (email.strip(),))

    resultat = cursor.fetchone()

    connection.close()

    return resultat is not None


def creer_administrateur(
    nom,
    email,
    mot_de_passe,
    entreprise_id
):

    connection = get_connection()
    cursor = connection.cursor()

    mot_de_passe_hash = hasher_mot_de_passe(
        mot_de_passe
    )

    date_creation = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute("""
        INSERT INTO utilisateurs (
            nom,
            email,
            mot_de_passe,
            entreprise_id,
            role,
            actif,
            date_creation
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        nom,
        email.strip().lower(),
        mot_de_passe_hash,
        entreprise_id,
        "admin",
        1,
        date_creation
    ))

    utilisateur_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return utilisateur_id


def authentifier_utilisateur(
    email,
    mot_de_passe
):

    connection = get_connection()
    cursor = connection.cursor()

    mot_de_passe_hash = hasher_mot_de_passe(
        mot_de_passe
    )

    cursor.execute("""
        SELECT
            id,
            nom,
            email,
            entreprise_id,
            role
        FROM utilisateurs
        WHERE LOWER(email) = LOWER(?)
        AND mot_de_passe = ?
        AND actif = 1
    """, (
        email.strip(),
        mot_de_passe_hash
    ))

    utilisateur = cursor.fetchone()

    connection.close()

    return utilisateur


def obtenir_utilisateur(
    utilisateur_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            nom,
            email,
            entreprise_id,
            role,
            actif,
            date_creation
        FROM utilisateurs
        WHERE id = ?
    """, (utilisateur_id,))

    utilisateur = cursor.fetchone()

    connection.close()

    return utilisateur


# ============================================================
# ENTREPRISE PAR DEFAUT
# ============================================================

def obtenir_entreprise_par_defaut():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM entreprises
        ORDER BY id
        LIMIT 1
    """)

    entreprise = cursor.fetchone()

    if entreprise:

        connection.close()

        return entreprise[0]

    cursor.execute("""
        INSERT INTO entreprises (
            nom,
            secteur,
            devise,
            solde_initial
        )
        VALUES (?, ?, ?, ?)
    """, (
        "Mon entreprise",
        "À définir",
        "FCFA",
        0
    ))

    entreprise_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return entreprise_id


# ============================================================
# RECETTES
# ============================================================

def ajouter_recette(
    entreprise_id,
    date,
    montant,
    categorie,
    source,
    moyen_paiement,
    description
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO recettes (
            entreprise_id,
            date,
            montant,
            categorie,
            source,
            moyen_paiement,
            description
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        entreprise_id,
        date,
        montant,
        categorie,
        source,
        moyen_paiement,
        description
    ))

    connection.commit()
    connection.close()


def recuperer_recettes(entreprise_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            date,
            montant,
            categorie,
            source,
            moyen_paiement,
            description
        FROM recettes
        WHERE entreprise_id = ?
        ORDER BY date DESC, id DESC
    """, (entreprise_id,))

    recettes = cursor.fetchall()

    connection.close()

    return recettes


def obtenir_recette(
    recette_id,
    entreprise_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            date,
            montant,
            categorie,
            source,
            moyen_paiement,
            description
        FROM recettes
        WHERE id = ?
        AND entreprise_id = ?
    """, (
        recette_id,
        entreprise_id
    ))

    recette = cursor.fetchone()

    connection.close()

    return recette


def modifier_recette(
    recette_id,
    entreprise_id,
    date,
    montant,
    categorie,
    source,
    moyen_paiement,
    description
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE recettes
        SET
            date = ?,
            montant = ?,
            categorie = ?,
            source = ?,
            moyen_paiement = ?,
            description = ?
        WHERE id = ?
        AND entreprise_id = ?
    """, (
        date,
        montant,
        categorie,
        source,
        moyen_paiement,
        description,
        recette_id,
        entreprise_id
    ))

    connection.commit()
    connection.close()


def supprimer_recette(
    recette_id,
    entreprise_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM recettes
        WHERE id = ?
        AND entreprise_id = ?
    """, (
        recette_id,
        entreprise_id
    ))

    connection.commit()
    connection.close()


# ============================================================
# DEPENSES
# ============================================================

def ajouter_depense(
    entreprise_id,
    date,
    montant,
    categorie,
    beneficiaire,
    moyen_paiement,
    description
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO depenses (
            entreprise_id,
            date,
            montant,
            categorie,
            beneficiaire,
            moyen_paiement,
            description
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        entreprise_id,
        date,
        montant,
        categorie,
        beneficiaire,
        moyen_paiement,
        description
    ))

    connection.commit()
    connection.close()


def recuperer_depenses(entreprise_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            date,
            montant,
            categorie,
            beneficiaire,
            moyen_paiement,
            description
        FROM depenses
        WHERE entreprise_id = ?
        ORDER BY date DESC, id DESC
    """, (entreprise_id,))

    depenses = cursor.fetchall()

    connection.close()

    return depenses


def obtenir_depense(
    depense_id,
    entreprise_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            date,
            montant,
            categorie,
            beneficiaire,
            moyen_paiement,
            description
        FROM depenses
        WHERE id = ?
        AND entreprise_id = ?
    """, (
        depense_id,
        entreprise_id
    ))

    depense = cursor.fetchone()

    connection.close()

    return depense


def modifier_depense(
    depense_id,
    entreprise_id,
    date,
    montant,
    categorie,
    beneficiaire,
    moyen_paiement,
    description
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE depenses
        SET
            date = ?,
            montant = ?,
            categorie = ?,
            beneficiaire = ?,
            moyen_paiement = ?,
            description = ?
        WHERE id = ?
        AND entreprise_id = ?
    """, (
        date,
        montant,
        categorie,
        beneficiaire,
        moyen_paiement,
        description,
        depense_id,
        entreprise_id
    ))

    connection.commit()
    connection.close()


def supprimer_depense(
    depense_id,
    entreprise_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM depenses
        WHERE id = ?
        AND entreprise_id = ?
    """, (
        depense_id,
        entreprise_id
    ))

    connection.commit()
    connection.close()


# ============================================================
# CALCULS
# ============================================================

def calculer_total_recettes(entreprise_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(montant), 0)
        FROM recettes
        WHERE entreprise_id = ?
    """, (entreprise_id,))

    total = cursor.fetchone()[0]

    connection.close()

    return total


def calculer_total_depenses(entreprise_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(montant), 0)
        FROM depenses
        WHERE entreprise_id = ?
    """, (entreprise_id,))

    total = cursor.fetchone()[0]

    connection.close()

    return total


def obtenir_solde_initial(entreprise_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT solde_initial
        FROM entreprises
        WHERE id = ?
    """, (entreprise_id,))

    resultat = cursor.fetchone()

    connection.close()

    if resultat and resultat[0] is not None:

        return resultat[0]

    return 0


def modifier_solde_initial(
    entreprise_id,
    montant
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE entreprises
        SET solde_initial = ?
        WHERE id = ?
    """, (
        montant,
        entreprise_id
    ))

    connection.commit()
    connection.close()
