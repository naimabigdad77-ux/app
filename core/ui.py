"""Composants visuels partagés (cartes, barres de fiabilité, titres de section)."""

from __future__ import annotations

import html
from pathlib import Path

import streamlit as st

from . import listings as L
from .i18n import brand, t

CSS_PATH = Path(__file__).resolve().parent.parent / "assets" / "style.css"


def load_css() -> None:
    st.markdown(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def goto(page_path: str) -> None:
    """Navigation programmatique vers une page de st.navigation."""
    try:
        st.switch_page(page_path)
    except Exception:
        st.rerun()


def flash(message: str) -> None:
    st.session_state["flash"] = message


# --------------------------------------------------------------------------- #
# En-têtes
# --------------------------------------------------------------------------- #
def brand_block() -> None:
    st.markdown(
        f"""
        <div class="k-brand">
            <div class="logo">🏠</div>
            <div>
                <div class="name">{brand()}</div>
                <div class="sub">{t('brand.sub')}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero() -> None:
    st.markdown(
        f"""
        <div class="k-hero">
            <h1>{t('home.title')}</h1>
            <p>{t('home.sub')}</p>
            <div class="k-tags">
                <span class="k-tag">🏠 {t('home.tag1')}</span>
                <span class="k-tag">🎓 {t('home.tag2')}</span>
                <span class="k-tag">🛡️ {t('home.tag3')}</span>
                <span class="k-tag">💬 {t('home.tag4')}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(title: str, hint: str = "") -> None:
    right = f'<span class="hint">{html.escape(hint)}</span>' if hint else ""
    st.markdown(
        f'<div class="k-section"><div class="bar"></div><h2>{html.escape(title)}</h2>{right}</div>',
        unsafe_allow_html=True,
    )


def stat_tiles(stats: dict[str, str]) -> None:
    tiles = "".join(
        f'<div class="k-stat"><div class="v">{html.escape(str(v))}</div>'
        f'<div class="l">{html.escape(str(k))}</div></div>'
        for k, v in stats.items()
    )
    st.markdown(f'<div class="k-stats">{tiles}</div>', unsafe_allow_html=True)


def trust_bar(score: int, label: str = "") -> str:
    color = L.trust_color(score)
    name = html.escape(label or t("l.trust"))
    return (
        f'<div class="k-trust"><span title="{name}">🛡️</span>'
        f'<div class="track"><div class="fill" style="width:{score}%;background:{color}"></div></div>'
        f'<b style="color:{color}">{score}</b></div>'
    )


def owner_badge(is_verified: bool, account_type: str | None) -> str:
    """Badge d'un propriétaire d'annonce : étudiant vérifié, propriétaire/agent, ou non vérifié."""
    if account_type == "proprietaire":
        return (f'<span class="k-pill" style="background:#e0e7ff;color:#3730a3">'
                f'🏠 {t("l.owner_badge")}</span>')
    if is_verified:
        return f'<span class="k-pill ok">✅ {t("l.verified_badge")}</span>'
    return f'<span class="k-pill warn">⚠️ {t("l.unverified_badge")}</span>'


def alert(message: str, kind: str = "") -> None:
    st.markdown(
        f'<div class="k-alert {kind}">{message}</div>',
        unsafe_allow_html=True,
    )


def info_line(message: str, icon: str = "ℹ️") -> None:
    st.markdown(f'<div class="k-mini">{icon} {message}</div>', unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Carte d'annonce
# --------------------------------------------------------------------------- #
def listing_card(l: dict) -> str:
    """Rendu HTML d'une annonce (à placer dans une colonne)."""
    icon = L.TYPE_ICONS.get(l["listing_type"], "🏠")
    offer = t("l.offer_propose") if l["offer"] == "propose" else t("l.offer_cherche")
    charges = (
        f'<span class="k-pill charges">💡 {t("l.charges_incl")}</span>'
        if l["charges_incl"]
        else f'<span class="k-pill warn">⚡ {t("l.charges_extra")}</span>'
    )
    furn = t("l.furnished") if l["furnished"] else t("l.unfurnished")
    quartier = f' — {html.escape(l["quartier"])}' if l.get("quartier") else ""
    desc = html.escape((l.get("description") or "")[:220])
    score = L.trust_score(l)

    status_badge = ""
    if l.get("status") == "loue":
        status_badge = f'<span class="k-pill warn">{t("l.status_loue")}</span>'

    return f"""
    <div class="k-card">
        <div class="k-top">
            <div>
                <span class="k-pill type">{icon} {html.escape(l['listing_type'])}</span>
                <span class="k-pill offer">{html.escape(offer)}</span>
            </div>
            {status_badge}
        </div>
        <h3>{html.escape(l['title'])}</h3>
        <div class="k-loc">📍 {html.escape(l['city'])}{quartier} · {t('l.posted', d=L.rel_time(l['created_at']))}</div>
        <div class="k-desc">{desc}</div>
        <div style="display:flex;align-items:center;gap:.5rem;flex-wrap:wrap;margin-top:.45rem">
            <div class="k-price">{L.fmt_mad(l['price_mad'])}<span> {t('l.per_month')}</span></div>
            <span class="k-pill" style="background:#f5f5f4;color:#57534e">🛋 {html.escape(furn)}</span>
            {charges}
        </div>
        <div class="k-foot">
            {trust_bar(score)}
            <div class="k-mini">👁 {l['views']}</div>
        </div>
    </div>
    """
