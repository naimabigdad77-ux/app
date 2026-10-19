"""Edu-Dar — logement étudiant au Maroc, sans agence.

Point d'entrée Streamlit : lance `streamlit run app.py`.
"""

import streamlit as st

from core import auth
from core import db
from core import messaging as M
from core import ui
from core.i18n import LANGS, t

st.set_page_config(
    page_title="Edu-Dar — Logement étudiant au Maroc",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Thème : première visite → on suit la préférence système du navigateur/OS.
if "theme_dark" not in st.session_state:
    try:
        st.session_state["theme_dark"] = st.context.theme == "dark"
    except Exception:          # contexte indisponible (tests, bare mode)
        st.session_state["theme_dark"] = False

ui.load_css()
db.init_db()

st.session_state.setdefault("lang", "fr")
st.session_state.setdefault("user_id", None)

# --------------------------------------------------------------------------- #
# Barre latérale : marque, langue, compte
# --------------------------------------------------------------------------- #
with st.sidebar:
    ui.brand_block()
    st.write("")

    st.radio(
        t("lang.label"),
        options=list(LANGS),
        format_func=lambda k: LANGS[k],
        key="lang",
        horizontal=True,
        label_visibility="collapsed",
    )

    ui.toggle_dark()

    st.write("")
    st.markdown('<div class="k-sep"></div>', unsafe_allow_html=True)

    user = auth.current_user()
    if user:
        badge = ui.owner_badge(user["is_verified"], user.get("account_type"))
        ui.render(
            f"""
            <div class="k-card" style="box-shadow:none;padding:.85rem">
                <b>{user['full_name']}</b><br>
                <span class="k-mini">✉️ {user['email']}</span><br>
                <div style="margin-top:.4rem">{badge}</div>
            </div>
            """
        )
        unread = M.unread_total(user["id"])
        if unread:
            st.caption(f"✉️ {t('m.unread', n=unread)}")
        if st.button(f"🚪 {t('a.logout')}", use_container_width=True):
            auth.logout()
            st.rerun()
    else:
        st.info(t("a.demo_hint"))

    st.write("")
    flash = st.session_state.pop("flash", None)
    if flash:
        st.success(flash)

    st.markdown(f'<div class="k-foot-note">{t("footer.note")}</div>', unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# Navigation
# --------------------------------------------------------------------------- #
pages = [
    st.Page("views/home.py", title=t("nav.home"), icon="🏠", default=True),
    st.Page("views/listings.py", title=t("nav.listings"), icon="🔍"),
    st.Page("views/budget.py", title=t("nav.budget"), icon="💶"),
]

if user:
    pages += [
        st.Page("views/publish.py", title=t("nav.publish"), icon="➕"),
        st.Page("views/inbox.py", title=t("nav.inbox"),
                icon="✉️" if M.unread_total(user["id"]) == 0 else "📨"),
        st.Page("views/profile.py", title=t("nav.profile"), icon="👤"),
    ]
else:
    pages.append(st.Page("views/account.py", title=t("nav.account"), icon="🔑"))

st.navigation(pages).run()
