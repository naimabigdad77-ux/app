# 🏠 Edu-Dar — إيدو-دار

Prototype d'application de logement étudiant au Maroc : les étudiants trouvent un logement
ou une colocation **directement entre eux**, sans agence et sans frais abusifs.

Interface bilingue **Français / الدارجة**, construite avec **Streamlit** et stockée dans un
fichier **SQLite** local (`data/edudar.db`).

---

## 🚀 Démarrage

```bash
pip install -r requirements.txt
streamlit run app.py
```

L'application s'ouvre sur `http://localhost:8501`. La base de données et les données de
démonstration sont créées automatiquement au premier lancement.

## 👤 Comptes de démonstration

| E-mail | Mot de passe | Rôle |
|---|---|---|
| `salma.benali@um5.ac.ma` | `etudiant2026` | étudiante vérifiée, 1 annonce |
| `youssef.amrani@ufc.ac.ma` | `etudiant2026` | propriétaire vérifié, annonces |
| `khadija.mernissi@gmail.com` | `etudiant2026` | compte **non vérifié** (exemple) |

Pour repartir de zéro : supprimez `data/edudar.db` puis relancez l'application.

---

## ✨ Fonctionnalités

### 1. Annonces de logement et de colocation
- Deux types d'offres : **je propose** un logement / **je cherche** un colocataire
- Filtres : ville, type (studio, chambre, appartement, colocation…), budget max,
  préférence filles/garçons, meublé, charges comprises, mots-clés
- Tri par date, prix ou popularité
- Score de **fiabilité** (0-100) calculé pour chaque annonce

### 2. Vérification du statut étudiant
- L'inscription exige une adresse universitaire marocaine (`@ac.ma`, `@ensias.ac.ma`…)
- Un **code à 6 chiffres** est généré et validé (mode démonstration : le code s'affiche
  dans l'app, faute de serveur de messagerie connecté)
- Les comptes vérifiants obtiennent un badge qui augmente leur score de fiabilité

### 3. Messagerie étudiant ↔ étudiant
- Conversation créée automatiquement autour d'une annonce
- Compteur de messages non lus dans la barre latérale
- Aucun intermédiaire, aucune commission

### 4. Calculateur de budget
- Revenus (bourse CNE/CNO, aide familiale, emploi) et dépenses (transport, nourriture…)
- Calcule le **loyer maximum conseillé** (33 % des revenus nets), le reste à vivre et un verdict
  coloré avec conseils spécifiques au contexte marocain

### 5. Signalement d'arnaques
- Signalement depuis chaque annonce (motif + détails)
- Le score de fiabilité chute automatiquement
- **Modération automatique** : une annonce avec 3 signalements ouverts est retirée

---

## 🗂 Structure du projet

```
app/
├── app.py                 # Point d'entrée : thème, langue, navigation
├── requirements.txt
├── assets/style.css       # Habillage (couleurs, cartes, hero)
├── core/
│   ├── db.py              # Schéma SQLite + données de démonstration
│   ├── i18n.py            # Traductions FR / الدارجة
│   ├── auth.py            # Inscription, connexion, vérification @ac.ma
│   ├── listings.py        # Recherche, publication, favoris, score de fiabilité
│   ├── messaging.py       # Conversations et messages
│   ├── reports.py         # Signalements et modération automatique
│   ├── budget.py          # Logique du calculateur de budget
│   └── ui.py              # Composants visuels partagés
└── views/
    ├── home.py            # Accueil
    ├── listings.py        # Recherche + fiche annonce (dialogue)
    ├── publish.py         # Publication
    ├── inbox.py           # Messagerie
    ├── budget.py          # Calculateur
    ├── profile.py         # Profil + vérification + annonces
    └── account.py         # Connexion / inscription
```

## 🔐 Sécurité (état du prototype)

- Mots de passe hachés avec **PBKDF2-HMAC-SHA256** (120 000 itérations + sel aléatoire)
- La vérification par e-mail est **simulée** : aucun e-mail n'est réellement envoyé
- Les données vivent dans un fichier local, non chiffré — à remplacer par une vraie base
  (Supabase, PostgreSQL…) avant toute mise en production

## 🧭 Pistes pour la suite

- Envoi réel des codes de vérification (SMTP / Resend)
- Photos uploadées (Stockage S3 / Supabase Storage)
- Carte des logements (folium / pydeck) et calcul de distance fac ↔ logement
- Avis et notation entre étudiants
- Contrat de colocation générable en PDF
- Déploiement sur Streamlit Community Cloud
