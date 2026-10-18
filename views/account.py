"""Connexion / inscription (avec vérification de l'e-mail universitaire)."""

import streamlit as st

from core import auth
from core import ui
from core.db import CITIES, UNIVERSITIES
from core.i18n import t

st.title(f"🔑 {t('nav.account')}")
st.caption(t("a.demo_hint"))

login_tab, reg_tab = st.tabs([f"👤 {t('a.tabs_login')}", f"📝 {t('a.tabs_reg')}"])

with login_tab:
    with st.form("login_form"):
        email = st.text_input(t("a.email"), key="lg_email",
                              placeholder="salma.benali@um5.ac.ma")
        password = st.text_input(t("a.password"), type="password", key="lg_pass")
        ok = st.form_submit_button(t("a.do_login"), type="primary", use_container_width=True)
    if ok:
        success, msg = auth.login(email, password)
        if success:
            ui.flash(msg)
            ui.goto("views/home.py")
        else:
            st.error(msg)

with reg_tab:
    with st.form("register_form"):
        st.info(t("a.email_help"))
        account_type = st.radio(
            t("a.account_type"), ["etudiant", "proprietaire"], key="rg_type", horizontal=True,
            format_func=lambda v: t("a.type_etudiant") if v == "etudiant"
            else t("a.type_proprietaire"),
        )
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input(t("a.name"), key="rg_name")
            email = st.text_input(t("a.email"), key="rg_email", placeholder=t("a.email_ph"))
            phone = st.text_input(t("a.phone"), key="rg_phone", placeholder="06 XX XX XX XX")
        with c2:
            university = st.selectbox(t("a.university"), UNIVERSITIES, key="rg_uni")
            city = st.selectbox(t("a.city"), CITIES, key="rg_city")
            pwd = st.text_input(t("a.password"), type="password", key="rg_pwd")
            pwd2 = st.text_input(t("a.password2"), type="password", key="rg_pwd2")
        ok = st.form_submit_button(t("a.do_reg"), type="primary", use_container_width=True)
    if ok:
        success, msg = auth.register(name, email, pwd, pwd2, phone, university, city,
                                     account_type)
        if success:
            ui.flash(msg)
            ui.goto("views/profile.py")
        else:
            st.error(msg)

st.write("")
ui.alert(t("home.safety"))
