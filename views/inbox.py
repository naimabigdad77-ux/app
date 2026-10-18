"""Messagerie — contact direct entre étudiants."""

import html

import streamlit as st

from core import auth
from core import listings as L
from core import messaging as M
from core import ui
from core.i18n import t

st.title(f"✉️ {t('m.title')}")
st.caption(t("m.sub"))

user = auth.current_user()
if user is None:
    st.warning(t("m.need_login"))
    if st.button(t("a.login_t"), type="primary"):
        ui.goto("views/account.py")
    st.stop()

convs = M.list_conversations(user["id"])
left, right = st.columns([1.05, 2], gap="large")

# --------------------------------------------------------------------------- #
# Liste des conversations
# --------------------------------------------------------------------------- #
with left:
    ui.section(t("m.conversations"), hint=t("m.unread", n=M.unread_total(user["id"])))
    if not convs:
        st.info(t("m.empty"))
        st.caption(t("m.empty_hint"))
        if st.button(f"🔍 {t('home.cta')}", use_container_width=True):
            ui.goto("views/listings.py")
    for c in convs:
        active = st.session_state.get("active_conv") == c["id"]
        dot = "🟢" if c["unread"] else "⚪"
        badge = f" • {t('m.unread', n=c['unread'])}" if c["unread"] else ""
        label = f"{dot} {c['other_name']}{badge}"
        if st.button(label, key=f"conv_{c['id']}", use_container_width=True,
                     type="primary" if active else "secondary"):
            st.session_state["active_conv"] = c["id"]
            st.rerun()
        st.caption(f"🏠 {c['listing_title']} — {c['listing_city']}")
        if c.get("last_body"):
            st.caption(f"💬 {c['last_body'][:70]}")
        st.write("")

# --------------------------------------------------------------------------- #
# Fil de discussion
# --------------------------------------------------------------------------- #
with right:
    conv_id = st.session_state.get("active_conv")
    conv = next((c for c in convs if c["id"] == conv_id), None)

    if conv is None:
        st.info(t("m.pick"))
    else:
        st.markdown(
            f"""
            <div class="k-card" style="box-shadow:none;background:#fdfaf4;padding:.8rem 1rem">
                <div style="display:flex;justify-content:space-between;gap:.6rem;flex-wrap:wrap">
                    <div><b>👤 {html.escape(conv['other_name'])}</b>
                        {'<span class="k-pill ok">✅ ' + t('l.verified_badge') + '</span>' if conv['other_verified'] else '<span class="k-pill warn">⚠️ ' + t('l.unverified_badge') + '</span>'}
                    </div>
                    <div class="k-mini">🏠 {html.escape(conv['listing_title'])}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if conv["listing_status"] != "active":
            st.warning(t("m.listing_gone"))
        st.write("")

        M.mark_read(conv_id, user["id"])
        for m in M.messages_of(conv_id):
            mine = m["sender_id"] == user["id"]
            who = "Moi" if mine else conv["other_name"]
            body = html.escape(m["body"]).replace("\n", "<br>")
            cls = "me" if mine else "them"
            st.markdown(
                f'<div class="k-msg {cls}"><div class="who">{html.escape(who)}</div>{body}</div>',
                unsafe_allow_html=True,
            )

        st.write("")
        with st.form("msg_form", clear_on_submit=True):
            body = st.text_area(t("m.input"), key="msg_body", height=90)
            send = st.form_submit_button(f"➤ {t('m.send')}", type="primary",
                                         use_container_width=True)
        if send and (body or "").strip():
            M.send_message(conv_id, user["id"], body)
            st.rerun()

        st.write("")
        ui.alert(t("m.warning"))
