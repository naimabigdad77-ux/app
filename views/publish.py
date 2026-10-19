"""Page de publication d'une annonce."""

import streamlit as st

from core import auth
from core import images as IMG
from core import listings as L
from core import ui
from core.db import CITIES, GENDER_PREFS, LISTING_TYPES, QUARTIERS, UNIVERSITIES
from core.i18n import t

st.title(f"➕ {t('p.title')}")
st.caption(t("p.sub"))

user = auth.current_user()
if user is None:
    st.warning(t("p.need_login"))
    if st.button(t("a.login_t"), type="primary"):
        ui.goto("views/account.py")
    st.stop()

st.write("")
st.markdown(f"**{t('p.b1')}**")
c1, c2 = st.columns([2.2, 1])
with c1:
    title = st.text_input(t("p.title_f"), key="pub_title", placeholder=t("p.title_ph"))
with c2:
    offer = st.selectbox(
        t("p.kind"), ["propose", "cherche"], key="pub_offer",
        format_func=lambda v: t("p.kind_propose") if v == "propose" else t("p.kind_cherche"),
    )
ltype = st.selectbox(t("l.type"), LISTING_TYPES, key="pub_type")

st.write("")
st.markdown(f"**{t('p.b2')}**")
r1 = st.columns([1, 1, 1.6])
with r1[0]:
    city = st.selectbox(t("l.city"), CITIES, key="pub_city")
with r1[1]:
    quartier = st.selectbox(t("p.quartier"), QUARTIERS[city], key="pub_quartier")
with r1[2]:
    university = st.selectbox(t("p.university"), UNIVERSITIES, key="pub_uni")

r2 = st.columns([1, 1, 1, 1])
with r2[0]:
    price = st.number_input(t("p.price"), min_value=0, max_value=30000, step=100,
                            value=2000, key="pub_price")
with r2[1]:
    charges_incl = st.checkbox(t("p.charges"), value=True, key="pub_charges")
with r2[2]:
    surface = st.number_input(t("p.surface"), min_value=0, max_value=500, step=1,
                              value=25, key="pub_surface")
with r2[3]:
    rooms = st.number_input(t("p.rooms"), min_value=0, max_value=20, step=1,
                            value=1, key="pub_rooms")

r3 = st.columns([1, 1, 1.3])
with r3[0]:
    furnished = st.checkbox(t("p.furnished"), value=True, key="pub_furn")
with r3[1]:
    gender = st.selectbox(t("p.gender"), GENDER_PREFS, key="pub_gender")
with r3[2]:
    dispo = st.date_input(t("p.dispo"), key="pub_dispo")

st.write("")
st.markdown(f"**{t('p.b3')}**")
description = st.text_area(t("p.desc"), key="pub_desc", height=130,
                           placeholder=t("p.desc_ph"))

r4 = st.columns([1, 1.4])
with r4[0]:
    phone = st.text_input(t("p.phone"), value=user.get("phone") or "", key="pub_phone")
with r4[1]:
    st.caption(t("p.image_help"))

uploads = st.file_uploader(
    f"📷 {t('p.photos')}",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True,
    key="pub_photos",
    help=t("p.image_help"),
)
if uploads:
    previews = [f for f in uploads if f.type in IMG.ALLOWED][:IMG.MAX_IMAGES]
    if previews:
        st.image(previews, width=150)
    if len(uploads) > IMG.MAX_IMAGES:
        st.warning(t("p.image_max", n=IMG.MAX_IMAGES))

st.write("")
if st.button(t("p.submit"), type="primary", use_container_width=True):
    errors = []
    if len(title.strip()) < 6:
        errors.append(t("p.err_title"))
    if not price or price <= 0:
        errors.append(t("p.err_price"))
    if len(description.strip()) < 30:
        errors.append(t("p.err_desc"))

    if errors:
        for e in errors:
            st.error(e)
    else:
        listing_id = L.add_listing(user["id"], {
            "title": title.strip(),
            "listing_type": ltype,
            "offer": offer,
            "city": city,
            "quartier": quartier,
            "university": university,
            "price_mad": int(price),
            "charges_incl": charges_incl,
            "surface": int(surface) or None,
            "rooms": int(rooms) or None,
            "furnished": furnished,
            "gender_pref": gender,
            "available_from": str(dispo),
            "description": description.strip(),
            "contact_phone": phone.strip() or None,
            "image_url": None,
        }, image_files=uploads)
        for k in list(st.session_state.keys()):
            if k.startswith("pub_"):
                del st.session_state[k]
        st.session_state["open_listing"] = listing_id
        ui.flash(t("p.done"))
        ui.goto("views/listings.py")

ui.alert(t("home.safety"), kind="info")
