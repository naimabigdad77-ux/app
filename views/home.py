"""Page d'accueil — présentation du service et dernières annonces."""

import streamlit as st

from core import listings as L
from core import reports as R
from core import ui
from core.i18n import t

ui.hero()

b1, b2, b3 = st.columns([1.15, 1.15, 1.3])
with b1:
    if st.button(f"🔍 {t('home.cta')}", type="primary", use_container_width=True):
        ui.goto("views/listings.py")
with b2:
    if st.button(f"➕ {t('home.cta2')}", use_container_width=True):
        ui.goto("views/publish.py" if st.session_state.get("user_id") else "views/account.py")
with b3:
    if st.button(f"💶 {t('home.cta3')}", use_container_width=True):
        ui.goto("views/budget.py")

st.write("")

stats = L.count_stats()
ui.stat_tiles({
    str(stats["listings"]): t("home.stat.listings"),
    str(stats["cities"]): t("home.stat.cities"),
    str(stats["verified"]): t("home.stat.verified"),
    str(stats["reports"]): t("home.stat.reports"),
})

# --------------------------------------------------------------------------- #
ui.section(t("home.how"), hint=t("home.how.hint"))
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(
        f'<div class="k-step"><div class="n">1</div><h4>{t("home.step1.t")}</h4>'
        f'<p>{t("home.step1.d")}</p></div>', unsafe_allow_html=True)
with c2:
    st.markdown(
        f'<div class="k-step"><div class="n">2</div><h4>{t("home.step2.t")}</h4>'
        f'<p>{t("home.step2.d")}</p></div>', unsafe_allow_html=True)
with c3:
    st.markdown(
        f'<div class="k-step"><div class="n">3</div><h4>{t("home.step3.t")}</h4>'
        f'<p>{t("home.step3.d")}</p></div>', unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
latest = L.list_listings(sort="new")[:3]
ui.section(t("home.latest"), hint=t("home.latest.hint"))

if not latest:
    st.info(t("home.empty"))
else:
    cols = st.columns(len(latest))
    for col, l in zip(cols, latest):
        with col:
            st.markdown(ui.listing_card(l), unsafe_allow_html=True)
            if st.button(f"👉 {t('l.details')}", key=f"home_d{l['id']}", use_container_width=True):
                st.session_state["open_listing"] = l["id"]
                ui.goto("views/listings.py")
    st.write("")
    if st.button(f"{t('home.see_all')} →"):
        ui.goto("views/listings.py")

# --------------------------------------------------------------------------- #
open_reports = R.global_open_reports()
ui.section("🛡️ " + ("Protection contre les arnaques" if st.session_state.get("lang") != "ary"
                     else "الحماية من النصابة"))
ui.alert(t("home.safety"))

if open_reports:
    ui.info_line(
        ("{n} annonce(s) actuellement en cours de modération suite à des signalements."
         .format(n=open_reports)) if st.session_state.get("lang") != "ary"
        else "{n} إعلان كينين دابا قيد المراجعة من بعد بلاغات.".format(n=open_reports),
        icon="⚖️",
    )

st.markdown(
    f'<div class="k-foot-note">{t("footer.note")}</div>',
    unsafe_allow_html=True,
)
