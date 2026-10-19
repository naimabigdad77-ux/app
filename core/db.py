"""Gestion de la base SQLite locale (schéma + données de démonstration)."""

from __future__ import annotations

import hashlib
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent


def _default_db_dir() -> Path:
    """Dossier de stockage de la base.

    Priorité à la variable d'environnement `EDUDAR_DB_DIR` (utile pour placer la base
    ailleurs, par exemple hors d'un dossier synchronisé) ; sinon `<projet>/data`,
    ce qui fonctionne aussi sur Streamlit Community Cloud.
    """
    override = os.environ.get("EDUDAR_DB_DIR")
    if override:
        return Path(override).expanduser()
    return BASE_DIR / "data"


DATA_DIR = _default_db_dir()
DB_PATH = DATA_DIR / "edudar.db"

# Domaines académiques marocains acceptés pour la vérification du statut étudiant
ACADEMIC_DOMAINS = (
    "ac.ma",
    "ensias.ac.ma",
    "emi.ac.ma",
    "encgk.ac.ma",
    "aui.ma",
    "uii.ac.ma",
    "uca.ac.ma",
)

UNIVERSITIES = [
    # Universités publiques
    "Université Mohammed V - Rabat (UM5)",
    "Université Hassan II - Casablanca (UFC)",
    "Université Cadi Ayyad - Marrakech (UCA)",
    "Université Sidi Mohamed Ben Abdellah - Fès (USMBA)",
    "Université Mohammed I - Oujda (UMI)",
    "Université Ibn Tofail - Kénitra (UIT)",
    "Université Chouaib Doukkali - El Jadida (UCD)",
    "Université Ibn Zohr - Agadir (UIZ)",
    "Université Moulay Ismaïl - Meknès",
    "Université Abdelmalek Essaâdi - Tanger (UAE)",
    "Université Mohammed VI Polytechnique - Benguerir (UM6P)",
    # Grandes écoles publiques
    "ENSIAS - Rabat",
    "EMI - Casablanca",
    "ENCG - Kénitra",
    "ENCG Agadir",
    "ENCG Casablanca",
    "ENCG Fès",
    "ENCG Tanger",
    "ENCG Marrakech",
    "ENCG Oujda",
    "ENCG Mohammedia",
    "ENSA Casablanca",
    "ENSA Mohammedia",
    "ENSA Agadir",
    "ENSA Tanger",
    "ENSA Oujda",
    "ENSA Marrakech",
    "ENSA Béni Mellal",
    "ENIM - Rabat (Mines et Métallurgie)",
    "INPT - Rabat",
    "INSEA - Casablanca",
    "ENSAM - Rabat (Arts et Métiers)",
    "EST Casablanca",
    "EST Rabat",
    "EST Agadir",
    "EST Tanger",
    "EST Fès",
    "EST Kénitra",
    "EST Marrakech",
    "FST Settat",
    "FST Mohammedia",
    "FST Kénitra",
    "FST Oujda",
    "ENI - Marrakech (Informatique)",
    "ISTA - Technologie appliquée",
    "UIR - Casablanca",
    "Al Akhawayn - Ifrane (AUI)",
    "UIP - Université Polytechnique internationale",
    "EAC - École d'Architecture Casablanca",
    "Autre école / université",
]

# Références nommées, utilisées par les données de démo et lisibles ailleurs
U_UM5 = UNIVERSITIES[0]
U_UFC = UNIVERSITIES[1]
U_UCA = UNIVERSITIES[2]
U_USMBA = UNIVERSITIES[3]
U_UMI = UNIVERSITIES[4]
U_UIT = UNIVERSITIES[5]
U_UIZ = UNIVERSITIES[7]
U_UMI_M = UNIVERSITIES[8]
U_ENSIAS = UNIVERSITIES[11]
U_EMI = UNIVERSITIES[12]
U_ENCG_K = UNIVERSITIES[13]
U_ENCG_AG = UNIVERSITIES[14]

CITIES = [
    "Casablanca",
    "Rabat",
    "Fès",
    "Marrakech",
    "Tanger",
    "Agadir",
    "Meknès",
    "Oujda",
    "Kénitra",
    "El Jadida",
    "Mohammedia",
    "Settat",
    "Béni Mellal",
    "Ifrane",
    "Benguerir",
]

QUARTIERS = {
    "Casablanca": ["Maârif", "Ain Diab", "Gauthier", "Oasis", "Hay Hassani", "Sidi Bernoussi", "Derb Ghallef", "Californie"],
    "Rabat": ["Agdal", "Hay Riad", "Hassan", "Souissi", "Hay Salam", "L'Océan"],
    "Fès": ["Ville Nouvelle", "Saïss", "Quartier Noria", "Mechouar", "Atlas"],
    "Marrakech": ["Guéliz", "Hivernage", "Médina", "Targa", "Massira"],
    "Tanger": ["Malabata", "Iberia", "Boukhalef", "Marchan", "Zone Zero"],
    "Agadir": ["Dakhla", "Talborjt", "Founty", "Hay Mohammadi"],
    "Meknès": ["Hamria", "Arrouad", "Khaddouj", "Majdoub"],
    "Oujda": ["Ninghir", "Sidi Yahia", "Annakhil", "Andalous"],
    "Kénitra": ["Hay Essalam", "Maâmora", "Sidi Boulahia", "Centre"],
    "El Jadida": ["Centre", "Sidi Bouzid", "Quartier Er-Rahma", "Littoral"],
    "Mohammedia": ["Centre", "Al Alia", "Kasbah", "Parc"],
    "Settat": ["Centre", "Al Massira", "Sidi El Aidi", "Boulevard Mohammed V"],
    "Béni Mellal": ["Centre", "Al Massira", "Hay Hassani", "Aïn Asserdoun"],
    "Ifrane": ["Centre", "Michlifen", "Route d'Azrou"],
    "Benguerir": ["Centre", "Zone universitaire", "Al Massira"],
}

LISTING_TYPES = ["Studio", "Chambre", "Appartement", "Colocation", "Dortoir", "Riad / Villa partagée"]
GENDER_PREFS = ["Tous", "Filles", "Garçons"]


# --------------------------------------------------------------------------- #
# Connexion
# --------------------------------------------------------------------------- #
def connect(path: Path | str = DB_PATH) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        # Écritures concurrentes sûres entre plusieurs onglets Streamlit
        conn.execute("PRAGMA journal_mode=WAL")
    except sqlite3.Error:
        pass
    return conn


def get_conn() -> sqlite3.Connection:
    """Connexion réutilisée entre les reruns de Streamlit (schéma initialisé à la volée)."""
    if "conn" not in st.session_state:
        st.session_state["conn"] = connect()
        init_db()  # la connexion est déjà en session_state : pas de récursion
    return st.session_state["conn"]


# --------------------------------------------------------------------------- #
# Mots de passe
# --------------------------------------------------------------------------- #
def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"{salt.hex()}${digest.hex()}"


def check_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 120_000
        )
        return candidate.hex() == digest_hex
    except Exception:
        return False


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _days_ago(days: int) -> str:
    return (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")


# --------------------------------------------------------------------------- #
# Schéma
# --------------------------------------------------------------------------- #
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    phone         TEXT,
    university    TEXT,
    city          TEXT,
    bio           TEXT,
    account_type  TEXT    NOT NULL DEFAULT 'etudiant',   -- 'etudiant' | 'proprietaire'
    is_verified   INTEGER NOT NULL DEFAULT 0,
    verify_code   TEXT,
    verify_until  TEXT,
    created_at    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS listings (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title          TEXT    NOT NULL,
    listing_type   TEXT    NOT NULL,
    offer          TEXT    NOT NULL DEFAULT 'propose',   -- 'propose' | 'cherche'
    city           TEXT    NOT NULL,
    quartier       TEXT,
    university     TEXT,
    price_mad      INTEGER NOT NULL,
    charges_incl   INTEGER NOT NULL DEFAULT 1,
    surface        INTEGER,
    rooms          INTEGER,
    furnished      INTEGER NOT NULL DEFAULT 1,
    gender_pref    TEXT    NOT NULL DEFAULT 'Tous',
    available_from TEXT,
    description    TEXT,
    image_url      TEXT,
    images         TEXT    NOT NULL DEFAULT '[]',          -- JSON : noms de fichiers photo
    contact_phone  TEXT,
    status         TEXT    NOT NULL DEFAULT 'active',    -- 'active' | 'loue' | 'retire'
    views          INTEGER NOT NULL DEFAULT 0,
    created_at     TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id  INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    reporter_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reason      TEXT    NOT NULL,
    details     TEXT,
    status      TEXT    NOT NULL DEFAULT 'ouvert',
    created_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    user1_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user2_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TEXT    NOT NULL,
    UNIQUE (listing_id, user1_id, user2_id)
);

CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body            TEXT    NOT NULL,
    is_read         INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS favorites (
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    created_at TEXT    NOT NULL,
    PRIMARY KEY (user_id, listing_id)
);
"""


# --------------------------------------------------------------------------- #
# Données de démonstration
# --------------------------------------------------------------------------- #
SEED_USERS = [
    # (nom, email, ville, université, tél, bio, vérifié, type de compte)
    ("Salma Benali", "salma.benali@um5.ac.ma", "Rabat", U_UM5,
     "0661-245187", "Étudiante en 2e année droit, je cherche une coloc calme et studieuse.", 1, "etudiant"),
    ("Youssef El Amrani", "youssef.amrani@ufc.ac.ma", "Casablanca", U_UFC,
     "0662-883410", "Étudiant en gestion, je loue moi-même mon studio sans agence.", 1, "etudiant"),
    ("Imane Chraibi", "imane.chraibi@ensias.ac.ma", "Rabat", U_ENSIAS,
     "0670-112233", "Élève ingénieure ENSIAS, je libère ma chambre en colocation.", 1, "etudiant"),
    ("Mehdi Ouazzani", "mehdi.ouazzani@uca.ac.ma", "Marrakech", U_UCA,
     "0655-778899", "Cherche une chambre proche de la fac, budget serré mais sérieux.", 1, "etudiant"),
    ("Nour Ait Baha", "nour.aitbaha@usmba.ac.ma", "Fès", U_USMBA,
     "0677-456123", "En médecine, je cherche colocataire fille pour appartement partagé.", 1, "etudiant"),
    ("Anas Berrada", "anas.berrada@emi.ac.ma", "Casablanca", U_EMI,
     "0663-990011", "Élève ingénieur EMI, je propose une chambre dans mon appart.", 1, "etudiant"),
    ("Khadija Mernissi", "khadija.mernissi@gmail.com", "Agadir", U_UIZ,
     "0658-221100", "Étudiante indépendante — profil de démonstration non vérifié.", 0, "etudiant"),
    ("Hamza Tazi", "hamza.tazi@ump.ac.ma", "Oujda", U_UMI,
     "0669-341278", "Recherche studio pas cher à Oujda pour la rentrée.", 1, "etudiant"),
    # --- Propriétaires et agents : pas nécessairement des étudiants ---
    ("Fatima Zahra El Idrissi", "fatimazahra.elidrissi@gmail.com", "Casablanca", None,
     "0661-775544", "Propriétaire directe : je loue mes studios à des étudiants, "
     "sans agence et sans commission cachée.", 0, "proprietaire"),
    ("Nour Immobilier — agent", "contact@nour-immobilier.ma", "Tanger", None,
     "0539-448822", "Agent immobilier agréé à Tanger. Je représente des propriétaires "
     "particuliers : honoraires annoncés à l'avance et contrat conforme.", 0, "proprietaire"),
]

SEED_LISTINGS = [
    # (titre, type, offre, ville, quartier, université, prix, charges, surface,
    #  chambres, meublé, genre, dispo, description, téléphone, jours, vues, image)
    ("Studio meublé près de la fac, sans agence", "Studio", "propose", "Casablanca",
     "Maârif", U_UFC, 3800, 1, 28, 1, 1, "Tous", "2026-09-01",
     "Studio entièrement meublé et lumineux, 5 min à pied de la faculté. Électricité et eau comprises, "
     "internet fibre disponible. Propriétaire direct, aucune commission d'agence.", "0662-883410", 12, 214,
     "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800"),

    ("Colocation fille, chambre calme et lumineuse", "Colocation", "propose", "Rabat",
     "Agdal", U_ENSIAS, 2100, 1, 16, 1, 1, "Filles", "2026-09-05",
     "Chambre dans une colocation de 3 étudiantes ENSIAS. Cuisine équipée, salon, wifi, local sécurisé. "
     "Ambiance studieuse, on partage les courses.", "0670-112233", 8, 168,
     "https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?w=800"),

    ("Chambre dans appartement partagé - Maârif", "Chambre", "propose", "Casablanca",
     "Derb Ghallef", U_UFC, 1750, 0, 14, 1, 1, "Garçons", "2026-08-20",
     "Chambre à louer dans un appartement de 2 colocataires (ENSA + EMI). Charges (eau, électricité, "
     "wifi) en sus selon consommation, environ 200 DH/mois. Quartier animé et bien desservi.", "0663-990011",
     20, 341, "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800"),

    ("Appartement 2 chambres - je cherche un colocataire", "Appartement", "cherche", "Casablanca",
     "Gauthier", U_UFC, 2600, 1, 62, 2, 1, "Garçons", "2026-09-01",
     "J'ai déjà l'appartement et je cherche un colocataire sérieux pour partager le loyer (1300 DH chacun). "
     "Meublé, climatisation, immeuble avec gardien, proche tramway.", "0662-441122", 5, 97,
     "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800"),

    ("Studio proche Université Cadi Ayyad", "Studio", "propose", "Marrakech",
     "Guéliz", U_UCA, 3200, 1, 30, 1, 1, "Tous", "2026-10-01",
     "Studio rénové dans une résidence calme de Guéliz. Proche café, market et arrêt de bus pour la fac. "
     "Bail direct avec le propriétaire, pas de frais d'agence.", "0655-778899", 15, 122,
     "https://images.unsplash.com/photo-1554995207-c18c203602cb?w=800"),

    ("Colocation mixte près de la fac des sciences", "Colocation", "propose", "Fès",
     "Ville Nouvelle", U_USMBA, 1350, 1, 18, 1, 1, "Tous", "2026-09-15",
     "Chambre disponible dans une colocation de 4 étudiants. Loyer tout compris : eau, électricité, internet. "
     "Cuisine commune équipée, machine à laver.", "0677-456123", 3, 88,
     "https://images.unsplash.com/photo-1540518614846-7eded433c457?w=800"),

    ("Chambre étudiante meublée à Tanger", "Chambre", "propose", "Tanger",
     "Malabata", "Autre école / université", 2400, 1, 17, 1, 1, "Tous", "2026-09-01",
     "Chambre meublée dans une résidence étudiante sécurisée. Parking, ascenseur, gardien 24h/24. "
     "Contrat direct, la propriétaire habite l'immeuble.", "0668-554433", 27, 402,
     "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800"),

    ("Studio pas cher au centre de Oujda", "Studio", "propose", "Oujda",
     "Ninghir", U_UMI, 1500, 0, 22, 1, 0, "Tous", "2026-09-10",
     "Studio non meublé, idéal pour étudiant avec peu de budget. Charges (eau + électricité) en sus. "
     "Proche des cafés et du bus pour l'université Mohammed I.", "0669-341278", 6, 76,
     "https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=800"),

    ("Cherche colocataire pour T2 - Hay Riad", "Appartement", "cherche", "Rabat",
     "Hay Riad", U_UM5, 3000, 1, 74, 2, 1, "Filles", "2026-09-01",
     "Je loue un T2 et je cherche une colocataire pour la rentrée. Chambre 2 avec placard, salon spacieux, "
     "terrasse. Quartier calme et sécurisé, bus direct pour Agdal.", "0661-245187", 9, 133,
     "https://images.unsplash.com/photo-1484154218962-a197022b5858?w=800"),

    ("Colocation garçons - proche ENCG Kénitra", "Colocation", "propose", "Kénitra",
     "Maâmora", U_ENCG_K, 1200, 1, 15, 1, 1, "Garçons", "2026-09-20",
     "Chambre dans une grande maison avec jardin, 10 min à vélo de l'ENCG. Tout est compris, "
     "on partage les corvées. Ambiance sympa entre jeunes.", "0672-119988", 4, 61,
     "https://images.unsplash.com/photo-1519710164239-da123dc03ef4?w=800"),

    ("Studio avec terrasse - Agadir", "Studio", "propose", "Agadir",
     "Talborjt", "Autre école / université", 2700, 1, 26, 1, 1, "Tous", "2026-09-01",
     "Studio avec petite terrasse et vue sur la mer à 10 min. Meublé, cuisine équipée, clim. "
     "Bail direct avec le propriétaire, documents en règle.", "0656-771122", 33, 508,
     "https://images.unsplash.com/photo-1522771930-78848d9293e8?w=800"),

    ("Chambre libre dans T2 - Ville Nouvelle Fès", "Chambre", "propose", "Fès",
     "Saïss", U_USMBA, 1600, 0, 15, 1, 0, "Tous", "2026-09-05",
     "Chambre libre dans un T2 partagé avec un étudiant en licence. Non meublée mais placard fourni. "
     "Charges à part (environ 250 DH/mois). Très proche des écoles de commerce.", "0677-998877", 11, 145,
     None),

    ("Appartement entier pas cher à Meknès", "Appartement", "propose", "Meknès",
     "Hamria", U_UMI_M, 2200, 0, 55, 2, 0, "Tous", "2026-10-15",
     "Appartement 2 chambres à louer en direct. Idéal pour 2 étudiants qui veulent se partager. "
     "Non meublé, proprio disponible et flexible sur la caution.", "0667-223344", 24, 267,
     "https://images.unsplash.com/photo-1560185007-cde436f6a4d0?w=800"),

    ("Colocation fille - Hivernage Marrakech", "Colocation", "propose", "Marrakech",
     "Hivernage", U_UCA, 1900, 1, 20, 1, 1, "Filles", "2026-09-12",
     "Chambre dans une villa partagée avec piscine et jardin. 3 colocataires étudiantes. "
     "Tout compris : ménage commun, wifi, électricité. Quartier Hivernage, bus pour la fac.", "0655-334455",
     7, 198, "https://images.unsplash.com/photo-1560448075-bb485b067938?w=800"),

    ("Chambre à 10 min de l'ENCG Agadir", "Chambre", "propose", "Agadir",
     "Dakhla", U_ENCG_AG, 1700, 1, 16, 1, 1, "Filles", "2026-09-15",
     "Chambre meublée dans une colocation de 3 étudiantes de l'ENCG Agadir, à 10 minutes à pied. "
     "Tout compris (eau, électricité, wifi), cuisine équipée. Bail direct, sans agence.", "0658-221100",
     2, 57, "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800"),
]

SEED_REPORTS = [
    # (index annonce, index user, motif, détails)
    (11, 1, "Téléphone incorrect / injoignable",
     "Le numéro affiché ne correspond pas à celui du propriétaire, j'ai essayé 3 fois."),
    (7, 3, "Annonce dupliquée", "La même annonce apparaît 4 fois avec des prix différents."),
]

SEED_CONVERSATIONS = [
    # (annonce_idx, user_a_idx, user_b_idx, [(sender_idx, texte, lu), ...])
    (0, 7, 1, [
        (7, "Bonjour, le studio est toujours disponible pour la rentrée ?", 1),
        (1, "Bonjour Hamza, oui toujours disponible. Vous êtes étudiant à quelle faculté ?", 1),
        (7, "À la faculté des sciences d'Oujda, licence info. Je peux visiter samedi ?", 0),
    ]),
    (1, 4, 2, [
        (4, "Salam, la chambre est toujours libre ? Je suis en médecine à Fès.", 1),
        (2, "Salam Nour, oui elle est libre. La colocation est 100% filles.", 1),
    ]),
]


# --------------------------------------------------------------------------- #
# Initialisation
# --------------------------------------------------------------------------- #
def demo_mode() -> bool:
    """Données de démonstration activées ? (EDUDAR_DEMO=1, hors production)."""
    return os.environ.get("EDUDAR_DEMO", "").strip().lower() in ("1", "true", "yes", "on")


def init_db(force_reseed: bool = False) -> None:
    conn = get_conn()
    conn.executescript(SCHEMA)
    _migrate(conn)

    # L'application démarre vide : les données de démonstration ne sont créées
    # que sur demande (EDUDAR_DEMO=1), jamais dans une vraie utilisation.
    if not (demo_mode() or force_reseed):
        return

    has_users = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
    if has_users and not force_reseed:
        return

    if has_users:
        # force_reseed : on repart d'une base propre avant de réinsérer la démo
        for table in ("messages", "conversations", "favorites", "reports", "listings"):
            conn.execute(f"DELETE FROM {table}")
        conn.execute("DELETE FROM users")
        # Les ids doivent repartir de 1 : les données de démo s'y réfèrent
        try:
            conn.execute(
                "DELETE FROM sqlite_sequence WHERE name IN "
                "('users','listings','reports','conversations','messages','favorites')"
            )
        except sqlite3.Error:
            pass

    _seed(conn)
    conn.commit()


def _migrate(conn: sqlite3.Connection) -> None:
    """Ajoute les colonnes manquantes aux bases créées par une version antérieure."""
    users_cols = {row["name"] for row in conn.execute("PRAGMA table_info(users)")}
    if "account_type" not in users_cols:
        conn.execute(
            "ALTER TABLE users ADD COLUMN account_type TEXT NOT NULL DEFAULT 'etudiant'"
        )
        conn.commit()

    listings_cols = {row["name"] for row in conn.execute("PRAGMA table_info(listings)")}
    if "images" not in listings_cols:
        conn.execute("ALTER TABLE listings ADD COLUMN images TEXT NOT NULL DEFAULT '[]'")
        conn.commit()


def _seed(conn: sqlite3.Connection) -> None:
    for name, email, city, uni, phone, bio, verified, account_type in SEED_USERS:
        conn.execute(
            """INSERT INTO users (full_name, email, password_hash, phone, university,
                                  city, bio, account_type, is_verified, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (name, email, hash_password("etudiant2026"), phone, uni, city, bio,
             account_type, verified, _days_ago(40)),
        )

    for row in SEED_LISTINGS:
        (title, ltype, offer, city, quartier, uni, price, charges, surface, rooms,
         furnished, gender, dispo, desc, phone, days, views, image) = row
        owner_id = (days % len(SEED_USERS)) + 1
        conn.execute(
            """INSERT INTO listings (owner_id, title, listing_type, offer, city, quartier, university,
                                     price_mad, charges_incl, surface, rooms, furnished, gender_pref,
                                     available_from, description, contact_phone, image_url, views, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (owner_id, title, ltype, offer, city, quartier, uni, price, charges, surface, rooms,
             furnished, gender, dispo, desc, phone, image, views, _days_ago(days)),
        )

    for listing_idx, reporter_idx, reason, details in SEED_REPORTS:
        conn.execute(
            """INSERT INTO reports (listing_id, reporter_id, reason, details, status, created_at)
               VALUES (?,?,?,?,?,?)""",
            (listing_idx + 1, reporter_idx + 1, reason, details, "ouvert", _days_ago(4)),
        )

    for listing_idx, a, b, msgs in SEED_CONVERSATIONS:
        u1, u2 = sorted([a + 1, b + 1])
        cur = conn.execute(
            "INSERT INTO conversations (listing_id, user1_id, user2_id, created_at) VALUES (?,?,?,?)",
            (listing_idx + 1, u1, u2, _days_ago(6)),
        )
        for sender_idx, body, is_read in msgs:
            conn.execute(
                """INSERT INTO messages (conversation_id, sender_id, body, is_read, created_at)
                   VALUES (?,?,?,?,?)""",
                (cur.lastrowid, sender_idx + 1, body, is_read, _days_ago(5)),
            )
