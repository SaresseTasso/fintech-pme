import sqlite3


DATABASE_NAME = "fintech_pme.db"


def get_connection():
    """Créer une connexion à la base de données."""
    return sqlite3.connect(DATABASE_NAME)


def initialize_database():
    """Créer les tables nécessaires à l'application."""

    connection = get_connection()
    cursor = connection.cursor()

    # Table des entreprises
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

    # Table des utilisateurs
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

    # Table des recettes
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

    # Table des dépenses
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
