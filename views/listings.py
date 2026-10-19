"""Page des annonces — recherche, filtres, détails et contact direct."""

from __future__ import annotations

import html

import streamlit as st

from core import auth
from core import images as IMG
from core import listings as L
from core import messaging as M
from core import reports as R
from core import ui
from core.db import CITIES, GENDER_PREFS, LISTING_TYPES
from core.i18n import t

st.title(f"🔍 {t('l.title')}")
st.caption(t("l.sub"))

user = auth.current_user()


# --------------------------------------------------------------------------- #
# Dialogue de détail
# --------------------------------------------------------------------------- #
@st.dialog(t("l.details"), width="large")
def open_listing(listing_id: int) -> None:
    l = L.get_listing(listing_id)
    if not l:
        st.error(t("m.listing_gone"))
        st.session_state.pop("open_listing", None)
        return

    open_rep = R.open_reports_count(l["id"])
    score = L.trust_score(l, open_rep)

    offer = t("l.offer_propose") if l["offer"] == "propose" else t("l.offer_cherche")
    ui.render(
        f"""
        <div class="k-top" style="display:flex;gap:.4rem;flex-wrap:wrap">
            <span class="k-pill type">{L.TYPE_ICONS.get(l['listing_type'], '🏠')} {html.escape(l['listing_type'])}</span>
            <span class="k-pill offer">{html.escape(offer)}</span>
            <span class="k-pill furn">🛋 {t('l.furnished') if l['furnished'] else t('l.unfurnished')}</span>
            {'<span class="k-pill charges">💡 ' + t('l.charges_incl') + '</span>' if l['charges_incl'] else '<span class="k-pill warn">⚡ ' + t('l.charges_extra') + '</span>'}
        </div>
        <h2 style="margin:.7rem 0 .2rem">{html.escape(l['title'])}</h2>
        <div class="k-price" style="font-size:1.6rem">{L.fmt_mad(l['price_mad'])}<span> {t('l.per_month')}</span></div>
        """
    )

    loc = f"📍 {l['city']}" + (f" — {l['quartier']}" if l.get("quartier") else "")
    st.markdown(f"{loc} · {t('l.posted', d=L.rel_time(l['created_at']))}")
    if l.get("available_from"):
        st.markdown(f"📅 {t('l.dispo', d=l['available_from'])}")

    if l.get("images"):
        paths = [p for p in (IMG.path_of(n) for n in l["images"]) if p]
        if paths:
            st.write("")
            cells = st.columns(len(paths))
            for cell, p in zip(cells, paths):
                cell.image(str(p), width="stretch")

    if open_rep:
        ui.alert(t("l.open_report", n=open_rep))

    st.write("")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📐 m²", l["surface"] if l["surface"] else "—")
    m2.metric("🚪" if st.session_state.get("lang") != "ary" else "🚪",
              (str(l["rooms"]) if l["rooms"] else "—"))
    m3.metric(t("l.gender"), l["gender_pref"])
    m4.metric("👁", l["views"])

    if l.get("university"):
        st.markdown(f"🎓 **{html.escape(l['university'])}**")

    st.divider()
    st.markdown(f"#### 💬 {t('p.desc')}")
    st.write(l.get("description") or "—")

    st.divider()
    score_html = ui.trust_bar(score)
    verified = ui.owner_badge(l["owner_verified"], l.get("owner_type"))
    n_owner = len(L.my_listings(l["owner_id"]))
    ui.render(
        f"""
        <div class="k-card" style="box-shadow:none;background:#fdfaf4">
            <div class="k-top">
                <div><b>👤 {html.escape(l['owner_name'])}</b> {verified}</div>
                <div class="k-mini">{t('l.owner_listings', n=n_owner)}</div>
            </div>
            <div style="margin-top:.5rem">{score_html}</div>
            {('<div class="k-mini" style="margin-top:.4rem">📞 ' + html.escape(l['contact_phone']) + '</div>') if l.get('contact_phone') else ''}
        </div>
        """
    )

    st.divider()

    # --- Contact direct ----------------------------------------------------- #
    if user is None:
        st.info(t("l.login_needed"))
        if st.button(t("a.login_t"), type="primary", use_container_width=True):
            st.session_state.pop("open_listing", None)
            ui.goto("views/account.py")
    elif user["id"] == l["owner_id"]:
        st.info(t("m.about"))
    else:
        st.markdown(f"#### 💬 {t('l.contact_owner')}")
        ui.info_line(t("l.contact_free"))
        with st.form("contact_form", clear_on_submit=True):
            body = st.text_area(t("l.your_msg"), value=t("l.msg_placeholder"), height=110)
            sent = st.form_submit_button(t("l.send"), type="primary", use_container_width=True)
        if sent and body.strip():
            conv = M.get_or_create_conversation(l["id"], user["id"], l["owner_id"])
            M.send_message(conv, user["id"], body)
            st.session_state["active_conv"] = conv
            st.session_state.pop("open_listing", None)
            ui.flash(t("l.sent"))
            ui.goto("views/inbox.py")

    # --- Signalement -------------------------------------------------------- #
    if user is not None and user["id"] != l["owner_id"]:
        with st.expander(f"🚨 {t('l.report')}"):
            if R.has_reported(user["id"], l["id"]):
                st.caption(t("l.report_done"))
            else:
                with st.form("report_form"):
                    reason = st.selectbox(
                        t("l.report_reason"),
                        R.REASONS_KEYS,
                        format_func=lambda k: t(k),
                    )
                    details = st.text_area(t("l.report_details"), height=80)
                    ok = st.form_submit_button(t("l.report_send"), use_container_width=True)
                if ok:
                    R.add_report(l["id"], user["id"], t(reason), details)
                    st.session_state.pop("open_listing", None)
                    ui.flash(t("r.confirmed"))
                    st.rerun()

    if st.button(t("r.cancel"), use_container_width=True):
        st.session_state.pop("open_listing", None)
        st.rerun()


# --------------------------------------------------------------------------- #
# Filtres
# --------------------------------------------------------------------------- #
st.write("")
with st.container(border=True):
    r1 = st.columns([2.2, 1, 1, 1.3])
    with r1[0]:
        q = st.text_input("🔎 " + t("l.search"), key="f_q")
    with r1[1]:
        city = st.selectbox(t("l.city"), [""] + CITIES, key="f_city",
                            format_func=lambda v: "🌍" if v == "" else v)
    with r1[2]:
        ltype = st.selectbox(t("l.type"), [""] + LISTING_TYPES, key="f_type",
                             format_func=lambda v: "🏠" if v == "" else v)
    with r1[3]:
        offer = st.selectbox(
            t("l.offer"), ["", "propose", "cherche"], key="f_offer",
            format_func=lambda v: {"": t("l.offer_all"), "propose": t("l.offer_propose"),
                                   "cherche": t("l.offer_cherche")}[v],
        )

    r2 = st.columns([1.6, 1, 1, 1, 1.4])
    with r2[0]:
        max_price = st.slider(t("l.max_price"), 500, 8000, 8000, step=100, key="f_price")
    with r2[1]:
        gender = st.selectbox(t("l.gender"), GENDER_PREFS, key="f_gender")
    with r2[2]:
        furnished = st.checkbox(t("l.furnished"), key="f_furn")
    with r2[3]:
        charges = st.checkbox(t("l.charges"), key="f_charges")
    with r2[4]:
        sort = st.selectbox(
            t("l.sort"), ["new", "price_asc", "price_desc", "popular"], key="f_sort",
            format_func=lambda v: {"new": t("l.sort_new"), "price_asc": t("l.sort_price_asc"),
                                   "price_desc": t("l.sort_price_desc"),
                                   "popular": t("l.sort_popular")}[v],
        )

# --------------------------------------------------------------------------- #
# Résultats
# --------------------------------------------------------------------------- #
results = L.list_listings(
    city=city or None,
    listing_type=ltype or None,
    offer=offer or None,
    max_price=max_price if max_price < 8000 else None,
    gender=gender,
    furnished=furnished,
    charges=charges,
    query=q or None,
    sort=sort,
)

st.write("")
ui.section(t("l.results", n=len(results)))

if not results:
    st.info(t("l.none"))
    st.caption(t("l.none_hint"))
else:
    for i in range(0, len(results), 3):
        row = results[i:i + 3]
        cols = st.columns(len(row))
        for col, l in zip(cols, row):
            with col:
                ui.render(ui.listing_card(l))
                bc1, bc2 = st.columns([1.4, 1])
                with bc1:
                    if st.button(f"👁 {t('l.details')}", key=f"det_{l['id']}",
                                 use_container_width=True):
                        L.increment_views(l["id"])
                        st.session_state["open_listing"] = l["id"]
                        st.rerun()
                with bc2:
                    if user is None:
                        fav_label = f"🤍 {t('l.save')}"
                        fav_on = False
                    else:
                        fav_on = L.is_favorite(user["id"], l["id"])
                        fav_label = (f"❤️ {t('l.saved')}" if fav_on else f"🤍 {t('l.save')}")
                    if st.button(fav_label, key=f"fav_{l['id']}", use_container_width=True):
                        if user is None:
                            ui.flash(t("l.login_needed"))
                            ui.goto("views/account.py")
                        else:
                            now_on = L.toggle_favorite(user["id"], l["id"])
                            ui.flash(t("l.saved") if now_on else t("p.updated"))
                            st.rerun()

# Ouverture automatique d'une annonce demandée depuis l'accueil
if st.session_state.get("open_listing"):
    open_listing(int(st.session_state["open_listing"]))
