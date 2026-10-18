"""Signalement des annonces suspectes (protection contre les arnaques)."""

from __future__ import annotations

from . import db

REASONS_KEYS = ["r.arnaque", "r.faux", "r.dup", "r.contact", "r.logement", "r.other"]

# Au-delà de ce nombre de signalements ouverts, l'annonce est masquée automatiquement.
AUTO_HIDE_THRESHOLD = 3


def add_report(listing_id: int, reporter_id: int, reason: str, details: str = "") -> None:
    conn = db.get_conn()
    conn.execute(
        """INSERT INTO reports (listing_id, reporter_id, reason, details, status, created_at)
           VALUES (?,?,?,?,?,?)""",
        (listing_id, reporter_id, reason, (details or "").strip(), "ouvert", db.now()),
    )
    conn.commit()
    _auto_moderate(listing_id)


def _auto_moderate(listing_id: int) -> None:
    conn = db.get_conn()
    n = open_reports_count(listing_id)
    if n >= AUTO_HIDE_THRESHOLD:
        conn.execute("UPDATE listings SET status = 'retire' WHERE id = ?", (listing_id,))
        conn.commit()


def open_reports_count(listing_id: int) -> int:
    return db.get_conn().execute(
        "SELECT COUNT(*) c FROM reports WHERE listing_id = ? AND status = 'ouvert'",
        (listing_id,),
    ).fetchone()["c"]


def has_reported(reporter_id: int, listing_id: int) -> bool:
    return db.get_conn().execute(
        "SELECT 1 FROM reports WHERE reporter_id = ? AND listing_id = ?", (reporter_id, listing_id)
    ).fetchone() is not None


def my_reports(reporter_id: int) -> list[dict]:
    rows = db.get_conn().execute(
        """SELECT r.*, l.title AS listing_title, l.city AS listing_city
           FROM reports r JOIN listings l ON l.id = r.listing_id
           WHERE r.reporter_id = ? ORDER BY r.created_at DESC""",
        (reporter_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def global_open_reports() -> int:
    return db.get_conn().execute(
        "SELECT COUNT(*) c FROM reports WHERE status = 'ouvert'"
    ).fetchone()["c"]
