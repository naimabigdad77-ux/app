# 🏠 Edu-Dar — إيدو-دار

Prototype d'application de logement étudiant au Maroc : les étudiants trouvent un logement
ou une colocation **directement auprès des propriétaires et des agents**, sans intermédiaire
ni frais abusifs.

Deux types de comptes cohabitent :

- **Étudiant(e)** — inscription avec un e-mail universitaire (`@ac.ma`) ouvrant droit au badge
  « étudiant vérifié » après validation d'un code à 6 chiffres ;
- **Propriétaire ou agent immobilier** — inscription libre avec n'importe quel e-mail valide
  (ils ne sont **pas** forcément des étudiants), identifiés par un badge dédié et par leur
  téléphone / documents.

Interface bilingue **Français / الدارجة**, construite avec **Streamlit** et stockée dans un
fichier **SQLite** local (`data/edudar.db`).

---

## 🚀 Démarrage

```bash
pip install -r requirements.txt
streamlit run app.py
```

L'application s'ouvre sur `http://localhost:8501`. La base de données est créée
automatiquement au premier lancement : **l'application démarre vide**, sans aucune donnée
de test.

## 👤 Comptes de démonstration

Aucune donnée fictive n'est créée par défaut. Pour obtenir un jeu complet de démo
(annonces, conversations, signalements) :

```bash
EDUDAR_DEMO=1 streamlit run app.py      # Windows : $env:EDUDAR_DEMO="1"
```

| E-mail | Mot de passe | Rôle |
|---|---|---|
| `salma.benali@um5.ac.ma` | `etudiant2026` | étudiante vérifiée, 1 annonce |
| `youssef.amrani@ufc.ac.ma` | `etudiant2026` | propriétaire vérifié, annonces |
| `khadija.mernissi@gmail.com` | `etudiant2026` | étudiante **non vérifiée** (exemple) |
| `fatimazahra.elidrissi@gmail.com` | `etudiant2026` | **propriétaire** (pas étudiante) |
| `contact@nour-immobilier.ma` | `etudiant2026` | **agent immobilier** (pas étudiant) |

Pour repartir de zéro : supprimez le dossier `data/` puis relancez l'application.

---

## ✨ Fonctionnalités

### 1. Annonces de logement et de colocation
- Deux types d'offres : **je propose** un logement / **je cherche** un colocataire
- Filtres : ville, type (studio, chambre, appartement, colocation…), budget max,
  préférence filles/garçons, meublé, charges comprises, mots-clés
- Tri par date, prix ou popularité
- **Photos** : jusqu'à 4 photos par annonce (JPG, PNG, WebP), miniature automatique,
  galerie dans la fiche détail
- Score de **fiabilité** (0-100) calculé pour chaque annonce
- **15 villes** et **50 universités / écoles** marocaines dans les menus : universités
  publiques (UM5, UFC, UCA, UIZ Agadir, UM6P…) et grandes écoles (ENCG Agadir, ENCG
  Casablanca, ENSIAS, EMI, ENSA, EST, FST, INPT, INSEA…)

### 2. Deux types de comptes : étudiants, propriétaires et agents
- **Étudiant(e)** : l'inscription exige une adresse universitaire marocaine (`@ac.ma`,
  `@ensias.ac.ma`…), puis un **code à 6 chiffres** est validé (mode démonstration : le code
  s'affiche dans l'app, faute de serveur de messagerie connecté) → badge « étudiant vérifié ».
- **Propriétaire ou agent** : inscription avec n'importe quel e-mail valide — ils ne sont pas
  forcément des étudiants. Badge « Propriétaire / Agent » et score de fiabilité distinct.
- Les deux peuvent publier, contacter et signaler.

### 3. Messagerie directe, sans intermédiaire
- Conversation créée automatiquement autour d'une annonce
- Compteur de messages non lus dans la barre latérale
- Aucune commission, aucun intermédiaire

### 4. Calculateur de budget
- Revenus (bourse CNE/CNO, aide familiale, emploi) et dépenses (transport, nourriture…)
- Calcule le **loyer maximum conseillé** (33 % des revenus nets), le reste à vivre et un verdict
  coloré avec conseils spécifiques au contexte marocain

### 5. Signalement d'arnaques
- Signalement depuis chaque annonce (motif + détails)
- Le score de fiabilité chute automatiquement
- **Modération automatique** : une annonce avec 3 signalements ouverts est retirée

### 6. Interface bilingue et thème sombre
- Interface en **français** et en **دارجة** (arabe), commutable à tout moment
- Bouton **🌙 Mode sombre** dans la barre latérale ; au premier chargement, le thème suit
  la préférence système du navigateur (`st.context.theme`)
- Le thème sombre est un simple fichier (`assets/dark.css`) ajouté au CSS de base, sans
  changer le thème natif de Streamlit

### 7. Photos des annonces
- Jusqu'à **4 photos** par annonce (JPG, PNG, WebP, 5 Mo max chacune)
- Type et taille vérifiés à l'envoi, miniature générée côté serveur (Pillow)
- Affichées en vignette sur les cartes et en galerie dans la fiche détail
- Stockées dans `data/images/` (hors version controlée) et supprimées avec l'annonce

---

## 🗂 Structure du projet

```
app/
├── app.py                 # Point d'entrée : thème, langue, navigation
├── requirements.txt
├── assets/style.css       # Habillage (couleurs, cartes, hero)
├── assets/dark.css        # Surcharge du thème sombre
├── core/
│   ├── db.py              # Schéma SQLite + seed démo (EDUDAR_DEMO=1)
│   ├── i18n.py            # Traductions FR / الدارجة
│   ├── auth.py            # Inscription, connexion, vérification @ac.ma
│   ├── listings.py        # Recherche, publication, favoris, score de fiabilité
│   ├── images.py          # Téléversement, miniatures et suppression des photos
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
- Stockage des photos sur un cloud (S3 / Supabase Storage)
- Carte des logements (folium / pydeck) et calcul de distance fac ↔ logement
- Avis et notation entre étudiants
- Contrat de colocation générable en PDF
- Déploiement sur Streamlit Community Cloud
