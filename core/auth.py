"""Inscription, connexion et vérification du statut étudiant."""

from __future__ import annotations

import random
import re
from datetime import datetime, timedelta

import streamlit as st

from . import db
from .db import ACADEMIC_DOMAINS
from .i18n import t

CODE_TTL_MINUTES = 15


# --------------------------------------------------------------------------- #
# Utilitaires
# --------------------------------------------------------------------------- #
def current_user() -> dict | None:
    uid = st.session_state.get("user_id")
    if not uid:
        return None
    row = db.get_conn().execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
    return dict(row) if row else None


def is_academic_email(email: str) -> bool:
    email = (email or "").strip().lower()
    return any(email.endswith("@" + d) or email.endswith("." + d) for d in ACADEMIC_DOMAINS)


def _valid_email(email: str) -> bool:
    return re.match(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", (email or "").strip().lower()) is not None


# --------------------------------------------------------------------------- #
# Actions
# --------------------------------------------------------------------------- #
def login(email: str, password: str) -> tuple[bool, str]:
    conn = db.get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE lower(email) = ?", ((email or "").strip().lower(),)
    ).fetchone()
    if not row or not db.check_password(password, row["password_hash"]):
        return False, t("a.err_credentials")
    st.session_state["user_id"] = row["id"]
    return True, t("a.welcome", name=row["full_name"])


def register(
    full_name: str,
    email: str,
    password: str,
    password2: str,
    phone: str,
    university: str,
    city: str,
) -> tuple[bool, str]:
    email = (email or "").strip().lower()
    full_name = (full_name or "").strip()

    if len(full_name) < 3:
        return False, t("a.err_credentials")
    if not _valid_email(email):
        return False, t("a.err_credentials")
    if len(password) < 6:
        return False, t("a.err_short")
    if password != password2:
        return False, t("a.err_match")
    if not is_academic_email(email):
        return False, t("a.err_domain")

    conn = db.get_conn()
    if conn.execute("SELECT 1 FROM users WHERE lower(email) = ?", (email,)).fetchone():
        return False, t("a.err_exists")

    cur = conn.execute(
        """INSERT INTO users (full_name, email, password_hash, phone, university, city,
                              is_verified, created_at)
           VALUES (?,?,?,?,?,?,0,?)""",
        (full_name, email, db.hash_password(password), (phone or "").strip(),
         university, city, db.now()),
    )
    conn.commit()
    st.session_state["user_id"] = cur.lastrowid
    return True, t("a.welcome", name=full_name)


def logout() -> None:
    st.session_state.pop("user_id", None)


def delete_account(user_id: int) -> None:
    conn = db.get_conn()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    logout()


# --------------------------------------------------------------------------- #
# Vérification du statut étudiant
# --------------------------------------------------------------------------- #
def request_verification_code(user_id: int) -> str | None:
    """Génère et stocke un code à 6 chiffres. Retourne le code (mode démo)."""
    if not is_academic_email(current_user()["email"]):
        return None
    code = f"{random.randint(0, 999999):06d}"
    until = (datetime.now() + timedelta(minutes=CODE_TTL_MINUTES)).isoformat(timespec="seconds")
    conn = db.get_conn()
    conn.execute(
        "UPDATE users SET verify_code = ?, verify_until = ? WHERE id = ?", (code, until, user_id)
    )
    conn.commit()
    return code


def confirm_verification_code(user_id: int, code: str) -> bool:
    user = current_user()
    if not user or not user.get("verify_code"):
        return False
    if (code or "").strip() != user["verify_code"]:
        return False
    if datetime.fromisoformat(user["verify_until"]) < datetime.now():
        return False
    conn = db.get_conn()
    conn.execute(
        "UPDATE users SET is_verified = 1, verify_code = NULL, verify_until = NULL WHERE id = ?",
        (user_id,),
    )
    conn.commit()
    return True
