"""Recherche, publication et gestion des annonces."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from . import db
from .i18n import t

TYPE_ICONS = {
    "Studio": "🏠",
    "Chambre": "🛏️",
    "Appartement": "🏢",
    "Colocation": "👥",
    "Dortoir": "🛌",
    "Riad / Villa partagée": "🌿",
}

MAX_TRUST_PENALTY = 40


# --------------------------------------------------------------------------- #
# Score de fiabilité
# --------------------------------------------------------------------------- #
def trust_score(listing: dict, open_reports: int | None = None) -> int:
    """0-100. Pénalise les annonces signalées, récompense les comptes vérifiés."""
    conn = db.get_conn()
    if open_reports is None:
        open_reports = conn.execute(
            "SELECT COUNT(*) c FROM reports WHERE listing_id = ? AND status = 'ouvert'",
            (listing["id"],),
        ).fetchone()["c"]

    owner = conn.execute(
        "SELECT is_verified, account_type FROM users WHERE id = ?", (listing["owner_id"],)
    ).fetchone()

    score = 60
    if owner and owner["is_verified"]:
        score += 22          # étudiant vérifié via e-mail universitaire @ac.ma
    elif owner and owner["account_type"] == "proprietaire":
        score += 10          # propriétaire ou agent identifié (téléphone + documents)
    if listing.get("contact_phone"):
        score += 8
    if listing.get("image_url"):
        score += 5
    if (listing.get("description") or "") and len(listing["description"]) > 90:
        score += 5
    score -= min(open_reports * 20, MAX_TRUST_PENALTY)
    return max(5, min(100, score))


def trust_color(score: int) -> str:
    if score >= 75:
        return "#16a34a"
    if score >= 50:
        return "#f59e0b"
    return "#dc2626"


# --------------------------------------------------------------------------- #
# Requêtes
# --------------------------------------------------------------------------- #
def _base_query() -> str:
    return """
        SELECT l.*, u.full_name AS owner_name, u.is_verified AS owner_verified,
               u.account_type AS owner_type, u.university AS owner_university
        FROM listings l
        JOIN users u ON u.id = l.owner_id
    """


def list_listings(
    city: str | None = None,
    listing_type: str | None = None,
    offer: str | None = None,
    max_price: int | None = None,
    gender: str | None = None,
    furnished: bool = False,
    charges: bool = False,
    query: str | None = None,
    sort: str = "new",
    include_inactive: bool = False,
) -> list[dict]:
    sql = [_base_query(), " WHERE 1=1"]
    params: list = []
    if not include_inactive:
        sql.append("AND l.status = 'active'")
    if city:
        sql.append("AND l.city = ?")
        params.append(city)
    if listing_type:
        sql.append("AND l.listing_type = ?")
        params.append(listing_type)
    if offer:
        sql.append("AND l.offer = ?")
        params.append(offer)
    if max_price:
        sql.append("AND l.price_mad <= ?")
        params.append(max_price)
    if gender and gender != "Tous":
        sql.append("AND l.gender_pref IN (?, 'Tous')")
        params.append(gender)
    if furnished:
        sql.append("AND l.furnished = 1")
    if charges:
        sql.append("AND l.charges_incl = 1")
    if query:
        like = f"%{query.strip()}%"
        sql.append("AND (l.title LIKE ? OR l.description LIKE ? OR l.quartier LIKE ? "
                   "OR l.university LIKE ? OR l.city LIKE ?)")
        params += [like] * 5

    order = {
        "new": "l.created_at DESC",
        "price_asc": "l.price_mad ASC",
        "price_desc": "l.price_mad DESC",
        "popular": "l.views DESC",
    }.get(sort, "l.created_at DESC")

    rows = db.get_conn().execute(" ".join(sql) + f" ORDER BY {order}", params).fetchall()
    return [dict(r) for r in rows]


def get_listing(listing_id: int, include_inactive: bool = False) -> dict | None:
    sql = _base_query() + " WHERE l.id = ?"
    if not include_inactive:
        sql += " AND l.status = 'active'"
    row = db.get_conn().execute(sql, (listing_id,)).fetchone()
    return dict(row) if row else None


def count_stats() -> dict:
    conn = db.get_conn()
    return {
        "listings": conn.execute("SELECT COUNT(*) c FROM listings WHERE status='active'").fetchone()["c"],
        "cities": conn.execute("SELECT COUNT(DISTINCT city) c FROM listings").fetchone()["c"],
        "verified": conn.execute("SELECT COUNT(*) c FROM users WHERE is_verified=1").fetchone()["c"],
        "reports": conn.execute("SELECT COUNT(*) c FROM reports").fetchone()["c"],
    }


# --------------------------------------------------------------------------- #
# Écriture
# --------------------------------------------------------------------------- #
def add_listing(owner_id: int, data: dict) -> int:
    conn = db.get_conn()
    cur = conn.execute(
        """INSERT INTO listings (owner_id, title, listing_type, offer, city, quartier, university,
                                 price_mad, charges_incl, surface, rooms, furnished, gender_pref,
                                 available_from, description, contact_phone, image_url, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (owner_id, data["title"], data["listing_type"], data["offer"], data["city"],
         data.get("quartier"), data.get("university"), data["price_mad"],
         int(data.get("charges_incl", True)), data.get("surface"), data.get("rooms"),
         int(data.get("furnished", True)), data.get("gender_pref", "Tous"),
         data.get("available_from"), data["description"], data.get("contact_phone"),
         data.get("image_url"), db.now()),
    )
    conn.commit()
    return cur.lastrowid


def update_status(listing_id: int, owner_id: int, status: str) -> None:
    conn = db.get_conn()
    conn.execute("UPDATE listings SET status = ? WHERE id = ? AND owner_id = ?",
                 (status, listing_id, owner_id))
    conn.commit()


def delete_listing(listing_id: int, owner_id: int) -> None:
    conn = db.get_conn()
    conn.execute("DELETE FROM listings WHERE id = ? AND owner_id = ?", (listing_id, owner_id))
    conn.commit()


def my_listings(owner_id: int) -> list[dict]:
    rows = db.get_conn().execute(
        _base_query() + " WHERE l.owner_id = ? ORDER BY l.created_at DESC", (owner_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def increment_views(listing_id: int) -> None:
    conn = db.get_conn()
    conn.execute("UPDATE listings SET views = views + 1 WHERE id = ?", (listing_id,))
    conn.commit()


# --------------------------------------------------------------------------- #
# Favoris
# --------------------------------------------------------------------------- #
def is_favorite(user_id: int, listing_id: int) -> bool:
    return db.get_conn().execute(
        "SELECT 1 FROM favorites WHERE user_id = ? AND listing_id = ?", (user_id, listing_id)
    ).fetchone() is not None


def toggle_favorite(user_id: int, listing_id: int) -> bool:
    """Retourne True si l'annonce est maintenant en favori."""
    conn = db.get_conn()
    if is_favorite(user_id, listing_id):
        conn.execute("DELETE FROM favorites WHERE user_id = ? AND listing_id = ?",
                     (user_id, listing_id))
        saved = False
    else:
        conn.execute("INSERT OR IGNORE INTO favorites (user_id, listing_id, created_at) VALUES (?,?,?)",
                     (user_id, listing_id, db.now()))
        saved = True
    conn.commit()
    return saved


def my_favorites(user_id: int) -> list[dict]:
    rows = db.get_conn().execute(
        _base_query() + " JOIN favorites f ON f.listing_id = l.id WHERE f.user_id = ? "
        "ORDER BY f.created_at DESC",
        (user_id,),
    ).fetchall()
    return [dict(r) for r in rows]


# --------------------------------------------------------------------------- #
# Affichage
# --------------------------------------------------------------------------- #
def rel_days(iso: str | None) -> int:
    if not iso:
        return 0
    try:
        return max(0, (datetime.now() - datetime.fromisoformat(iso)).days)
    except ValueError:
        return 0


def rel_time(iso: str | None) -> str:
    days = rel_days(iso)
    if st.session_state.get("lang") == "ary":
        if days == 0:
            return "اليوم"
        if days == 1:
            return "البارح"
        if days < 30:
            return f"منذ {days} يوم"
        return f"منذ {days // 30} شهر"
    if days == 0:
        return "aujourd'hui"
    if days == 1:
        return "hier"
    if days < 30:
        return f"il y a {days} jours"
    return f"il y a {days // 30} mois"


def fmt_mad(value: float | int) -> str:
    return f"{value:,.0f}".replace(",", " ") + " DH"
