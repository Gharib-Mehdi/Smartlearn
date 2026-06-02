# 🎓 SmartLearn

> Application web intelligente de détection du style d'apprentissage VAK avec recommandations personnalisées par IA.

SmartLearn est un projet de fin d'année (PFA) développé avec Django. Il permet à un étudiant de passer un quiz psychopédagogique basé sur le modèle **VAK** (Visuel, Auditif, Kinesthésique), d'obtenir ses scores détaillés, et de recevoir des recommandations d'apprentissage personnalisées générées par un modèle de langage (LLM) via l'API **Groq**.

---

## ✨ Fonctionnalités

- **Authentification complète** — inscription, connexion, déconnexion
- **Quiz VAK interactif** — 12 questions avec choix multiples catégorisés par style
- **Calcul automatique des scores** — pourcentages Visuel / Auditif / Kinesthésique et détermination du style dominant
- **Recommandations IA personnalisées** — générées par `llama-3.3-70b-versatile` via l'API Groq, adaptées au profil de chaque utilisateur
- **Système de fallback** — recommandations statiques de qualité si l'API est indisponible
- **Historique des sessions** — consultation des quiz précédents depuis le tableau de bord
- **Interface responsive** — support du mode clair/sombre

---

## 🛠️ Stack technique

| Couche | Technologie |
|---|---|
| Backend | Django 6.x (Python 3.13) |
| Base de données | SQLite3 |
| Frontend | HTML / CSS / JavaScript vanilla |
| Fichiers statiques | WhiteNoise |
| LLM API | Groq (`llama-3.3-70b-versatile`) |
| Variables d'environnement | python-decouple |
| Déploiement | Railway |

---

## 📁 Structure du projet

```
SMARTLEARN/
├── smartlearn/          # Configuration Django (settings, urls, wsgi)
├── quiz/                # Application principale
│   ├── models.py        # Modèles : Quiz, Question, Choix, Reponse, Resultat, Recommandation
│   ├── views.py         # Vues : authentification, quiz, résultats, dashboard
│   ├── urls.py
│   ├── forms.py
│   ├── admin.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── llm_service.py   # Intégration API Groq + fallback
│   ├── fixtures/        # Données initiales (questions du quiz)
│   ├── management/      # Commandes Django custom
│   ├── migrations/
│   └── templatetags/
├── accounts/            # Gestion des comptes utilisateurs
├── templates/           # Templates HTML
├── static/              # CSS, JS, images
├── staticfiles/         # Fichiers statiques collectés (production)
├── db.sqlite3
├── manage.py
├── .env.example
└── requirements.txt
```

---

## 🚀 Installation locale

### Prérequis

- Python 3.10+
- pip
- Une clé API Groq gratuite → [console.groq.com](https://console.groq.com)

### Étapes

**1. Cloner le dépôt**

```bash
git clone https://github.com/ton-username/smartlearn.git
cd smartlearn
```

**2. Créer un environnement virtuel**

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
```

**3. Installer les dépendances**

```bash
pip install -r requirements.txt
```

**4. Configurer les variables d'environnement**

Copie `.env.example` en `.env` et remplis les valeurs :

```bash
cp .env.example .env
```

Contenu du `.env` :

```env
SECRET_KEY=une-clé-secrète-django
DEBUG=True
GROQ_API_KEY=gsk_ta_clé_groq_ici
```

**5. Appliquer les migrations**

```bash
python manage.py migrate
```

**6. Charger les données initiales (questions du quiz)**

```bash
python manage.py loaddata quiz/fixtures/*.json
```

**7. Lancer le serveur**

```bash
python manage.py runserver
```

L'application est accessible sur [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🔑 Variables d'environnement

| Variable | Description | Obligatoire |
|---|---|---|
| `SECRET_KEY` | Clé secrète Django | ✅ |
| `DEBUG` | Mode debug (`True` / `False`) | ✅ |
| `GROQ_API_KEY` | Clé API Groq pour le LLM | ✅ (fallback si absente) |

---

## 🧠 Fonctionnement de l'IA

Après soumission du quiz, le backend :

1. Calcule les scores VAK et détermine le style dominant
2. Construit un prompt personnalisé avec le profil de l'utilisateur
3. Envoie le prompt à l'API Groq (`llama-3.3-70b-versatile`)
4. Sauvegarde la recommandation générée en base de données
5. Affiche le résultat structuré en 4 parties : profil, points forts, stratégies, outils

En cas d'indisponibilité de l'API, un système de **fallback** affiche automatiquement des recommandations prédéfinies de qualité selon le style dominant détecté.

---

## 📊 Modèle VAK

Le modèle **VAK** (Visuel, Auditif, Kinesthésique) est un modèle psychopédagogique qui catégorise les préférences sensorielles dans l'apprentissage :

- **Visuel** — apprend mieux par les images, schémas, vidéos
- **Auditif** — apprend mieux par l'écoute, les discussions, les enregistrements
- **Kinesthésique** — apprend mieux par la pratique, l'expérimentation, le mouvement

---

## 🗂️ Diagrammes UML

Le projet est documenté par 4 diagrammes UML :

- **Cas d'utilisation** — interactions entre l'étudiant et le système LLM
- **Classes** — structure statique des entités Django (Utilisateur, Quiz, Question, Choix, Reponse, Resultat, Recommandation, ServiceLLM)
- **Séquence** — déroulement chronologique d'une session complète (authentification → quiz → calcul → recommandation IA)
- **Activité** — flux dynamique avec swimlanes (Utilisateur / Système / API LLM)

---

## 📦 Déploiement (Railway)

Le projet est configuré pour un déploiement sur [Railway](https://railway.app) :

- `whitenoise` pour les fichiers statiques
- `CSRF_TRUSTED_ORIGINS` configuré pour `*.railway.app`
- Variables d'environnement à définir dans le dashboard Railway

---

## 👥 Auteurs

Projet réalisé dans le cadre d'un **Projet de Fin d'Année (PFA)**.

---

## 📄 Licence

Ce projet est développé à des fins académiques.
