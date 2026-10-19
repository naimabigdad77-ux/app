"""Téléversement et affichage des photos d'annonces.

Les fichiers sont stockés dans `data/images/` avec une miniature générée par
Pillow ; l'affichage se fait en data-URI base64 (aucun serveur de fichiers).
"""

from __future__ import annotations

import base64
import io
import re
import secrets
from pathlib import Path

import streamlit as st

from .db import DATA_DIR

IMG_DIR = DATA_DIR / "images"
MAX_IMAGES = 4
MAX_SIZE = 5 * 1024 * 1024
THUMB_WIDTH = 900
ALLOWED = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
_NAME = re.compile(r"^[a-f0-9]{16}\.(jpg|png|webp)$")


def _thumb(uploaded) -> bytes:
    """Réduit la photo à THUMB_WIDTH de large (JPEG compressé)."""
    from PIL import Image

    img = Image.open(io.BytesIO(uploaded.getvalue()))
    img = img.convert("RGB")
    if img.width > THUMB_WIDTH:
        img = img.resize((THUMB_WIDTH, int(img.height * THUMB_WIDTH / img.width)),
                         Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=78, optimize=True)
    return out.getvalue()


def save(files) -> tuple[list[str], list[str]]:
    """Enregistre les fichiers valides. Retourne (noms valides, erreurs)."""
    names: list[str] = []
    errors: list[str] = []
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    for f in (files or [])[:MAX_IMAGES]:
        if not getattr(f, "type", None) or f.type not in ALLOWED:
            errors.append(f.name)
            continue
        if len(f.getvalue()) > MAX_SIZE:
            errors.append(f.name)
            continue
        name = secrets.token_hex(8) + ALLOWED[f.type]
        (IMG_DIR / name).write_bytes(f.getvalue())
        (IMG_DIR / ("thumb_" + name)).write_bytes(_thumb(f))
        names.append(name)
    return names, errors


def path_of(name: str) -> Path | None:
    if not name or not _NAME.match(name):
        return None
    p = IMG_DIR / name
    return p if p.exists() else None


def delete(names) -> None:
    for name in names or []:
        p = path_of(name)
        if p:
            for target in (p, IMG_DIR / ("thumb_" + p.name)):
                target.unlink(missing_ok=True)


def data_uri(name: str, thumb: bool = True) -> str | None:
    """data-URI base64 d'une photo ( miniature par défaut)."""
    p = path_of(name)
    if not p:
        return None
    target = IMG_DIR / ("thumb_" + p.name) if thumb else p
    if not target.exists():
        target = p
    return "data:image/jpeg;base64," + base64.b64encode(target.read_bytes()).decode()
