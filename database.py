import sqlite3

DATABASE_NAME = "fintech_pme.db"


def get_connection():
    return sqlite3.connect(DATABASE_NAME)


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            mot_de_passe TEXT NOT NULL,
            entreprise_id INTEGER,
            FOREIGN KEY (entreprise_id)
            REFERENCES entreprises(id)
        )
    """)

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
# ENTREPRISE
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
