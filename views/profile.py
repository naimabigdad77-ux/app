"""Profil — informations, vérification du statut étudiant, annonces et favoris."""

import html

import streamlit as st

from core import auth
from core import db
from core import listings as L
from core import messaging as M
from core import reports as R
from core import ui
from core.db import CITIES, UNIVERSITIES
from core.i18n import t

st.title(f"👤 {t('pr.title')}")

user = auth.current_user()
if user is None:
    st.warning(t("m.need_login"))
    if st.button(t("a.login_t"), type="primary"):
        ui.goto("views/account.py")
    st.stop()

ui.render(
    f"""
    <div class="k-card" style="box-shadow:none;background:#fdfaf4">
        <div class="k-top">
            <div><b style="font-size:1.15rem">👤 {html.escape(user['full_name'])}</b><br>
                 <span class="k-mini">✉️ {html.escape(user['email'])}</span></div>
            <div>{ui.owner_badge(user['is_verified'], user.get('account_type'))}</div>
        </div>
    </div>
    """
)
st.write("")

# --------------------------------------------------------------------------- #
# Vérification du statut étudiant
# --------------------------------------------------------------------------- #
ui.section(t("v.title"), hint=t("v.sub"))

if user["is_verified"]:
    ui.alert(t("v.ok"), kind="ok")
elif user.get("account_type") == "proprietaire":
    ui.alert(t("v.owner_info"), kind="info")
else:
    if st.session_state.get("vcode") is None:
        st.session_state["vcode"] = auth.request_verification_code(user["id"])
        st.rerun()
    with st.container(border=True):
        st.markdown(f"**{t('v.pending', email=user['email'])}**")
        st.caption(t("v.demo"))
        code = st.session_state.get("vcode")
        if code:
            st.code(code, language=None)
            cpy1, cpy2 = st.columns([1, 1])
            with cpy1:
                if st.button(f"📋 {t('v.copy')}", use_container_width=True):
                    st.session_state["vcode_copied"] = True
                    st.toast(t("v.copied"))
            with cpy2:
                if st.button(f"🔁 {t('v.resend')}", use_container_width=True):
                    st.session_state["vcode"] = auth.request_verification_code(user["id"])
                    st.session_state.pop("vcode_copied", None)
                    st.rerun()
        cc1, cc2 = st.columns([2, 1])
        with cc1:
            typed = st.text_input(t("v.code"), key="v_input", placeholder=t("v.code_ph"))
        with cc2:
            st.write("")
            if st.button(t("v.verify"), type="primary", use_container_width=True):
                if auth.confirm_verification_code(user["id"], typed):
                    st.session_state.pop("vcode", None)
                    st.session_state.pop("vcode_copied", None)
                    ui.flash(t("v.verified"))
                    st.rerun()
                else:
                    st.error(t("v.wrong"))

# --------------------------------------------------------------------------- #
# Informations
# --------------------------------------------------------------------------- #
ui.section(t("pr.my"))
with st.form("profile_form"):
    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input(t("a.name"), value=user["full_name"], key="pf_name")
        phone = st.text_input(t("a.phone"), value=user.get("phone") or "", key="pf_phone")
        university = st.selectbox(
            t("a.university"), UNIVERSITIES,
            index=UNIVERSITIES.index(user["university"]) if user.get("university") in UNIVERSITIES
            else len(UNIVERSITIES) - 1,
            key="pf_uni",
        )
    with c2:
        city = st.selectbox(
            t("a.city"), CITIES,
            index=CITIES.index(user["city"]) if user.get("city") in CITIES else 0, key="pf_city",
        )
        bio = st.text_area(t("pr.bio"), value=user.get("bio") or "", key="pf_bio",
                           placeholder=t("pr.bio_ph"), height=100)
    saved = st.form_submit_button(t("pr.save"), type="primary", use_container_width=True)

if saved:
    conn = db.get_conn()
    conn.execute(
        "UPDATE users SET full_name=?, phone=?, university=?, city=?, bio=? WHERE id=?",
        (name.strip(), phone.strip(), university, city, bio.strip(), user["id"]),
    )
    conn.commit()
    ui.flash(t("pr.saved"))
    st.rerun()

# --------------------------------------------------------------------------- #
# Statistiques + onglets
# --------------------------------------------------------------------------- #
my_listings = L.my_listings(user["id"])
favorites = L.my_favorites(user["id"])
my_reports = R.my_reports(user["id"])

ui.section(t("pr.stats"))
ui.stat_tiles({
    str(len(my_listings)): t("pr.listings"),
    str(len(M.list_conversations(user["id"]))): t("pr.messages"),
    str(len(favorites)): t("pr.favorites"),
    str(len(my_reports)): t("pr.reports"),
})

st.write("")
tab1, tab2, tab3 = st.tabs([
    f"🏠 {t('pr.listings')} ({len(my_listings)})",
    f"❤️ {t('pr.favorites')} ({len(favorites)})",
    f"🚨 {t('pr.reports')} ({len(my_reports)})",
])

with tab1:
    if not my_listings:
        st.info(t("p.none_yet"))
        if st.button(f"➕ {t('p.title')}"):
            ui.goto("views/publish.py")
    for l in my_listings:
        ui.render(ui.listing_card(l))
        bc1, bc2, bc3 = st.columns([1.3, 1.3, 1])
        with bc1:
            label = t("p.mark_active") if l["status"] != "active" else t("p.mark_loue")
            new_status = "active" if l["status"] != "active" else "loue"
            if st.button(label, key=f"st_{l['id']}", use_container_width=True):
                L.update_status(l["id"], user["id"], new_status)
                ui.flash(t("p.updated"))
                st.rerun()
        with bc2:
            if st.button(f"👁 {t('l.details')}", key=f"myd_{l['id']}", use_container_width=True):
                st.session_state["open_listing"] = l["id"]
                ui.goto("views/listings.py")
        with bc3:
            if st.button(f"🗑 {t('p.delete')}", key=f"del_{l['id']}", use_container_width=True):
                L.delete_listing(l["id"], user["id"])
                ui.flash(t("p.deleted"))
                st.rerun()
        st.write("")

with tab2:
    if not favorites:
        st.info(t("pr.fav_none"))
        if st.button(f"🔍 {t('home.cta')}"):
            ui.goto("views/listings.py")
    for l in favorites:
        ui.render(ui.listing_card(l))
        bc1, bc2 = st.columns([1.4, 1])
        with bc1:
            if st.button(f"👁 {t('l.details')}", key=f"favd_{l['id']}", use_container_width=True):
                st.session_state["open_listing"] = l["id"]
                ui.goto("views/listings.py")
        with bc2:
            if st.button(f"💔 {t('p.delete')}", key=f"unfav_{l['id']}", use_container_width=True):
                L.toggle_favorite(user["id"], l["id"])
                st.rerun()
        st.write("")

with tab3:
    if not my_reports:
        st.info(t("pr.none"))
    for r in my_reports:
        status = t("pr.report_done") if r["status"] != "ouvert" else t("pr.report_open")
        pill = '<span class="k-pill ok">' if r["status"] != "ouvert" else '<span class="k-pill warn">'
        ui.render(
            f"""
            <div class="k-card" style="box-shadow:none;padding:.8rem 1rem">
                <div class="k-top">
                    <div><b>🏠 {html.escape(r['listing_title'])}</b>
                         <span class="k-mini"> — {html.escape(r['listing_city'])}</span><br>
                         <span class="k-mini">🚩 {html.escape(r['reason'])}</span></div>
                    <div>{pill}{status}</span></div>
                </div>
                {('<div class="k-mini" style="margin-top:.35rem">' + html.escape(r['details']) + '</div>') if r.get('details') else ''}
            </div>
            """
        )
        st.write("")

st.write("")
ui.section(t("pr.danger"))
ui.alert(t("pr.delete_warn"))
if st.button(t("pr.delete_account")):
    auth.delete_account(user["id"])
    ui.flash("👋")
    ui.goto("views/home.py")
