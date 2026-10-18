"""Calculateur de budget logement étudiant (montants en dirhams)."""

from __future__ import annotations

RENT_RATIO_SAFE = 0.33   # seuil sain
RENT_RATIO_MAX = 0.40    # au-delà : situation tendue


def compute(
    bourse: float,
    famille: float,
    travail: float,
    autres_rev: float,
    transport: float,
    nourriture: float,
    tel: float,
    loisirs: float,
    scolarite: float,
    autres_dep: float,
    loyer: float,
    charges: float,
) -> dict:
    revenus = bourse + famille + travail + autres_rev
    depenses = transport + nourriture + tel + loisirs + scolarite + autres_dep
    disponible = revenus - depenses
    cout_logement = loyer + charges

    loyer_max = max(0.0, disponible * RENT_RATIO_SAFE)
    reste = disponible - cout_logement
    ratio = (cout_logement / revenus) if revenus > 0 else 0.0

    if revenus <= 0:
        verdict = "invalid"
    elif cout_logement == 0:
        verdict = "none"
    elif ratio <= RENT_RATIO_SAFE and reste >= 0:
        verdict = "good"
    elif ratio <= RENT_RATIO_MAX and reste >= 0:
        verdict = "ok"
    else:
        verdict = "bad"

    return {
        "revenus": revenus,
        "depenses": depenses,
        "disponible": disponible,
        "cout_logement": cout_logement,
        "loyer_max": loyer_max,
        "reste": reste,
        "ratio": ratio,
        "verdict": verdict,
        # combien de mois de loyer le reste couvrirait (épargne de sécurité)
        "mois_couverts": (reste / cout_logement) if cout_logement > 0 and reste > 0 else 0.0,
    }


# Revenus étudiants plausibles au Maroc (points de départ modifiables)
SAMPLE_REVENUS = {
    "bourse": 1400.0,   # bourse CNE/CNO selon établissement
    "famille": 1500.0,
    "travail": 800.0,
    "autres_rev": 0.0,
}

SAMPLE_DEPENSES = {
    "transport": 300.0,
    "nourriture": 1200.0,
    "tel": 150.0,
    "loisirs": 400.0,
    "scolarite": 500.0,
    "autres_dep": 150.0,
}
