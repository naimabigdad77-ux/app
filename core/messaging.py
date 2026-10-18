"""Messagerie directe étudiant ↔ étudiant (aucun intermédiaire)."""

from __future__ import annotations

import streamlit as st

from . import db


def _pair(a: int, b: int) -> tuple[int, int]:
    return (a, b) if a < b else (b, a)


def get_or_create_conversation(listing_id: int, me_id: int, other_id: int) -> int:
    u1, u2 = _pair(me_id, other_id)
    conn = db.get_conn()
    row = conn.execute(
        "SELECT id FROM conversations WHERE listing_id = ? AND user1_id = ? AND user2_id = ?",
        (listing_id, u1, u2),
    ).fetchone()
    if row:
        return row["id"]
    cur = conn.execute(
        "INSERT INTO conversations (listing_id, user1_id, user2_id, created_at) VALUES (?,?,?,?)",
        (listing_id, u1, u2, db.now()),
    )
    conn.commit()
    return cur.lastrowid


def can_access(conversation_id: int, user_id: int) -> bool:
    row = db.get_conn().execute(
        "SELECT user1_id, user2_id FROM conversations WHERE id = ?", (conversation_id,)
    ).fetchone()
    return bool(row) and user_id in (row["user1_id"], row["user2_id"])


def send_message(conversation_id: int, sender_id: int, body: str) -> None:
    body = (body or "").strip()
    if not body:
        return
    conn = db.get_conn()
    conn.execute(
        "INSERT INTO messages (conversation_id, sender_id, body, is_read, created_at) "
        "VALUES (?,?,?,?,?)",
        (conversation_id, sender_id, body, 0, db.now()),
    )
    conn.commit()


def messages_of(conversation_id: int) -> list[dict]:
    rows = db.get_conn().execute(
        """SELECT m.*, u.full_name AS sender_name
           FROM messages m JOIN users u ON u.id = m.sender_id
           WHERE m.conversation_id = ? ORDER BY m.created_at ASC, m.id ASC""",
        (conversation_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def mark_read(conversation_id: int, user_id: int) -> None:
    conn = db.get_conn()
    conn.execute(
        "UPDATE messages SET is_read = 1 WHERE conversation_id = ? AND sender_id != ?",
        (conversation_id, user_id),
    )
    conn.commit()


def list_conversations(user_id: int) -> list[dict]:
    rows = db.get_conn().execute(
        """SELECT c.*, l.title AS listing_title, l.city AS listing_city, l.status AS listing_status,
                  u.full_name AS other_name, u.id AS other_id, u.is_verified AS other_verified,
                  u.account_type AS other_type,
                  (SELECT body FROM messages m WHERE m.conversation_id = c.id
                     ORDER BY m.created_at DESC, m.id DESC LIMIT 1) AS last_body,
                  (SELECT created_at FROM messages m WHERE m.conversation_id = c.id
                     ORDER BY m.created_at DESC, m.id DESC LIMIT 1) AS last_at,
                  (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id
                     AND m.sender_id != ? AND m.is_read = 0) AS unread
           FROM conversations c
           JOIN users   u ON u.id = CASE WHEN c.user1_id = ? THEN c.user2_id ELSE c.user1_id END
           JOIN listings l ON l.id = c.listing_id
           WHERE c.user1_id = ? OR c.user2_id = ?
           ORDER BY COALESCE(last_at, c.created_at) DESC""",
        (user_id, user_id, user_id, user_id),
    ).fetchall()
    return [dict(r) for r in rows]


def unread_total(user_id: int) -> int:
    return sum(c["unread"] for c in list_conversations(user_id))
