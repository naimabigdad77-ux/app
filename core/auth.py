"""Inscription, connexion et vérification du statut étudiant."""

from __future__ import annotations

import random
import re
from datetime import datetime, timedelta
from time import time

import streamlit as st

from . import db
from .db import ACADEMIC_DOMAINS
from .i18n import t

CODE_TTL_MINUTES = 15

_CACHE = {}


def cached_get_conn():
    """Utilise la connexion en session_state (déjà mise en cache par db.get_conn)."""
    return db.get_conn()


def _get_cache(key: str):
    item = _CACHE.get(key)
    if not item:
        return None
    val, ts = item
    if time() - ts > 120:
        _CACHE.pop(key, None)
        return None
    return val


def _set_cache(key: str, val):
    _CACHE[key] = (val, time())
    return val


def clear_cache(prefix: str | None = None):
    if prefix is None:
        _CACHE.clear()
        return
    for k in list(_CACHE.keys()):
        if k.startswith(prefix):
            _CACHE.pop(k, None)


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
    account_type: str = "etudiant",
) -> tuple[bool, str]:
    email = (email or "").strip().lower()
    full_name = (full_name or "").strip()
    account_type = account_type if account_type in ("etudiant", "proprietaire") else "etudiant"

    if len(full_name) < 3:
        return False, t("a.err_credentials")
    if not _valid_email(email):
        return False, t("a.err_credentials")
    if len(password) < 6:
        return False, t("a.err_short")
    if password != password2:
        return False, t("a.err_match")
    # Seuls les comptes « étudiant » doivent prouver leur statut via un e-mail @ac.ma.
    # Les propriétaires et agents s'inscrivent avec n'importe quelle adresse valide.
    if account_type == "etudiant" and not is_academic_email(email):
        return False, t("a.err_domain")

    conn = db.get_conn()
    if conn.execute("SELECT 1 FROM users WHERE lower(email) = ?", (email,)).fetchone():
        return False, t("a.err_exists")

    cur = conn.execute(
        """INSERT INTO users (full_name, email, password_hash, phone, university, city,
                              account_type, is_verified, created_at)
           VALUES (?,?,?,?,?,?,?,0,?)""",
        (full_name, email, db.hash_password(password), (phone or "").strip(),
         university if account_type == "etudiant" else None, city, account_type, db.now()),
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
    user = current_user()
    if not user or user.get("id") != user_id:
        conn = db.get_conn()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        user = dict(row) if row else None
    if not user or not is_academic_email(user["email"]):
        return None
    if user.get("account_type") == "proprietaire":
        return None
    if user.get("is_verified"):
        return None
    code = f"{random.randint(0, 999999):06d}"
    until = (datetime.now() + timedelta(minutes=CODE_TTL_MINUTES)).isoformat(timespec="seconds")
    conn = db.get_conn()
    conn.execute(
        "UPDATE users SET verify_code = ?, verify_until = ? WHERE id = ?", (code, until, user_id)
    )
    conn.commit()
    return code


    # Si l'e-mail est modifié, s'assurer que la vérification est cohérente
    conn = db.get_conn()
    row = conn.execute("SELECT account_type, is_verified, email FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        return False
    if row["account_type"] == "proprietaire" or row["is_verified"]:
        return False
    if not is_academic_email(row["email"]):
        return False
    if not user or not user.get("verify_code"):
        return False
    if (code or "").strip() != user["verify_code"]:
        return False
    if datetime.fromisoformat(user["verify_until"]) < datetime.now():
        return False
    conn.execute(
        "UPDATE users SET is_verified = 1, verify_code = NULL, verify_until = NULL WHERE id = ?",
        (user_id,),
    )
    conn.commit()
    return True
