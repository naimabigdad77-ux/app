"""Calculateur de budget logement étudiant."""

import streamlit as st

from core import budget as B
from core import ui
from core.i18n import t
from core.listings import fmt_mad

st.title(f"💶 {t('b.title')}")
st.caption(t("b.sub"))
st.write("")

left, right = st.columns([1.25, 1], gap="large")

with left:
    ui.section(t("b.rev"))
    c = st.columns(2)
    with c[0]:
        bourse = st.number_input(t("b.bourse"), min_value=0, step=50,
                                 value=int(B.SAMPLE_REVENUS["bourse"]), key="bd_bourse")
        famille = st.number_input(t("b.family"), min_value=0, step=50,
                                  value=int(B.SAMPLE_REVENUS["famille"]), key="bd_fam")
    with c[1]:
        travail = st.number_input(t("b.job"), min_value=0, step=50,
                                  value=int(B.SAMPLE_REVENUS["travail"]), key="bd_trav")
        autres_rev = st.number_input(t("b.other"), min_value=0, step=50,
                                     value=0, key="bd_arev")

    ui.section(t("b.exp"))
    c = st.columns(2)
    with c[0]:
        transport = st.number_input(t("b.transport"), min_value=0, step=50,
                                    value=int(B.SAMPLE_DEPENSES["transport"]), key="bd_trans")
        nourriture = st.number_input(t("b.food"), min_value=0, step=50,
                                     value=int(B.SAMPLE_DEPENSES["nourriture"]), key="bd_food")
        tel = st.number_input(t("b.tel"), min_value=0, step=25,
                              value=int(B.SAMPLE_DEPENSES["tel"]), key="bd_tel")
    with c[1]:
        loisirs = st.number_input(t("b.fun"), min_value=0, step=50,
                                  value=int(B.SAMPLE_DEPENSES["loisirs"]), key="bd_fun")
        scolarite = st.number_input(t("b.school"), min_value=0, step=50,
                                    value=int(B.SAMPLE_DEPENSES["scolarite"]), key="bd_sch")
        autres_dep = st.number_input(t("b.other_exp"), min_value=0, step=50,
                                     value=int(B.SAMPLE_DEPENSES["autres_dep"]), key="bd_aexp")

    ui.section(t("b.current"))
    c = st.columns(2)
    with c[0]:
        loyer = st.number_input(t("b.rent"), min_value=0, step=100, value=2000, key="bd_rent")
    with c[1]:
        charges = st.number_input(t("b.charges"), min_value=0, step=50, value=200, key="bd_chg")

res = B.compute(bourse, famille, travail, autres_rev,
                transport, nourriture, tel, loisirs, scolarite, autres_dep,
                loyer, charges)

with right:
    ui.section(t("b.result"))
    if res["verdict"] == "invalid":
        st.warning(t("b.verdict_bad"))
    else:
        if res["verdict"] == "good":
            st.success(t("b.verdict_good"))
        elif res["verdict"] == "ok":
            st.warning(t("b.verdict_ok"))
        elif res["verdict"] == "bad":
            st.error(t("b.verdict_bad"))

        st.metric(t("b.total_rev"), fmt_mad(res["revenus"]))
        st.metric(t("b.total_exp"), fmt_mad(res["depenses"]))
        st.metric(t("b.available"), fmt_mad(res["disponible"]))
        st.metric(t("b.rent_max"), fmt_mad(res["loyer_max"]))
        st.metric(t("b.affordable"), fmt_mad(res["cout_logement"]))
        st.metric(t("b.left"), fmt_mad(res["reste"]))

        st.write("")
        pct = res["ratio"] * 100
        st.progress(min(1.0, res["ratio"] / 0.5))
        st.caption(f"{t('b.ratio')} : **{pct:.0f} %** (seuil conseillé : 33 %)")

st.write("")
ui.section(t("b.tip"))
t1, t2, t3 = st.columns(3)
with t1:
    ui.alert(t("b.tip1"))
with t2:
    ui.alert(t("b.tip2"))
with t3:
    ui.alert(t("b.tip3"))

st.write("")
if st.button(f"🔍 {t('home.cta')}"):
    ui.goto("views/listings.py")
