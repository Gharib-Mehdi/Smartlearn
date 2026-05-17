# SmartLearn — Recapitulatif complet du projet (contexte pour rapport / LLM)

Ce document decrit l'application **SmartLearn** de maniere exhaustive : objectifs, architecture, fonctionnalites, evolution du developpement, problemes rencontres et solutions, configuration et pistes pour un rapport académique. Il peut etre fourni tel quel a un LLM (ex. ChatGPT) comme contexte pour rediger un rapport de projet.

---

## 1. Vision et objectifs du projet

**SmartLearn** est une application web **Django** qui permet de :

1. **Identifier le style d'apprentissage** d'un utilisateur selon le modele **VAK** (Visuel, Auditif, Kinesthesique).
2. **Passer un quiz** en ligne avec des questions a choix multiples.
3. **Calculer automatiquement** les scores et pourcentages par style, puis determiner un **style dominant** et un **type de profil** (dominant / mixte / equilibre).
4. **Generer des recommandations personnalisees** via une **API LLM** (OpenAI `gpt-4o-mini`), avec **fallback** si l'API echoue ou si la cle n'est pas configuree.
5. **Conserver l'historique** des sessions et afficher une **evolution** sur plusieurs tentatives.
6. Offrir une **interface admin personnalisee** (staff) pour statistiques globales et **gestion CRUD des questions** du quiz actif.
7. Proposer une page **Ressources** pedagogiques par style, et des fonctionnalites UX (theme clair/sombre, partage du profil, etc.).

Le design suit un **design system** decrit dans `smartlearn_design_system.json` (couleurs, composants, espacements) implemente dans `static/css/main.css`.

---

## 2. Stack technique

| Composant | Choix |
|-----------|--------|
| Framework backend | **Django** (version installee typiquement 4.2+ ou 6.x selon environnement) |
| Base de donnees | **SQLite** (`db.sqlite3`) |
| Authentification | **Django Auth** (`User` integre) |
| Frontend | **HTML**, **CSS** custom + **Bootstrap 5.3** (CDN) |
| JavaScript | **Vanilla** (`static/js/theme.js`, `static/js/quiz.js`, scripts inline dans templates) |
| Graphiques | **Chart.js 4.x** (CDN) |
| Typographie | **Inter** (Google Fonts) |
| IA | **OpenAI** (`openai` SDK, modele `gpt-4o-mini`) |
| Configuration | **python-decouple** + variables `.env` / `os.environ` |
| Fichiers statiques prod | **WhiteNoise** (`CompressedManifestStaticFilesStorage`) |

Fichier `requirements.txt` (indicatif) :

- `django>=4.2`
- `openai>=1.0.0`
- `python-decouple`
- `whitenoise`

Fichier `.env.example` : `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `OPENAI_API_KEY` (ou Anthropic en option commentee).

---

## 3. Structure du depot (organisation des fichiers)

```
SMARTLEARN/
├── manage.py
├── requirements.txt
├── .env.example
├── smartlearn_design_system.json    # Reference design (non servi par Django par defaut)
├── recap.md                          # Ce document
├── WORKLOG_REVIEW.md                 # Journal chronologique des prompts (si present)
├── db.sqlite3
├── smartlearn/                       # Projet Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── quiz/                             # Application metier
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── admin.py
│   ├── services/llm_service.py
│   ├── templatetags/quiz_extras.py
│   ├── fixtures/initial_data.json
│   ├── management/commands/add_neutre_choices.py
│   └── migrations/ (0001_initial, 0002_..., 0003_resultat_profil_type)
├── accounts/                         # Inscription / connexion / deconnexion
│   ├── views.py, urls.py, forms.py, models.py (vide / commentaire User)
├── templates/
│   ├── base.html
│   ├── accounts/login.html, register.html
│   └── quiz/ (landing, dashboard, quiz, results, admin_dashboard, admin_question_edit, ressources)
└── static/
    ├── css/main.css
    └── js/theme.js, quiz.js
```

---

## 4. Modele de donnees (app `quiz`)

### Enumerations

- **`StyleEnum`** : `VISUEL`, `AUDITIF`, `KINESTHESIQUE`, **`NEUTRE`** (choix "Autre" sans impact sur les scores V/A/K).

### Entites principales

| Modele | Role |
|--------|------|
| **Quiz** | Un quiz (titre, description, actif, date creation). |
| **Question** | Texte de la question, ordre, rattachee a un `Quiz`. |
| **Choix** | Texte, `style` (VAK ou NEUTRE), `lettre` (A, B, C, D). |
| **Session** | Une tentative : utilisateur, quiz, dates debut/fin, `terminee`. |
| **Reponse** | Un choix par question par session ; contrainte `unique_together` (`session`, `question`). |
| **Resultat** | Scores bruts V/A/K, pourcentages, `style_dominant`, **`neutral_count`**, **`profil_type`**, dates. |
| **Recommandation** | Texte genere par l'API ou fallback, `api_provider`, liee 1-1 a la session. |

### Logique `Resultat.calculer()`

- Les **pourcentages** sont calcules sur la base des **scores bruts** (nombre de reponses V, A, K — les reponses **NEUTRE** ne comptent pas dans ces scores).
- **`style_dominant`** : style ayant le **plus haut pourcentage** parmi les trois.
- **`profil_type`** (seuils sur les **pourcentages**, pas sur les scores bruts) :
  - **`EQUILIBRE`** si ecart entre 1er et 2e style **<= 2** points de pourcentage (profil multimodal).
  - **`MIXTE`** si ecart **<= 15** points.
  - **`DOMINANT`** sinon.
- Proprietes : `style_secondaire`, `label_style`, `label_style_secondaire` pour l'affichage.

### Compteur neutre

- Lors de la finalisation de session, **`neutral_count`** compte le nombre de reponses dont le choix a `style == NEUTRE`.
- Sur la page resultats, si **`neutral_count >= 3`**, un message supplementaire type "profil mixte" peut s'afficher (choix "Autre" frequent).

---

## 5. Flux utilisateur et URLs

### Fichier racine `smartlearn/urls.py` (ordre important)

Les routes **`quiz`** et **`accounts`** sont declarees **avant** `path("admin/", admin.site.urls)` pour eviter que l'**admin Django** ne capture des URLs comme `/admin/question/.../delete/` (conflit historique corrige).

### Routes app `quiz` (`quiz/urls.py`)

| URL | Vue | Acces |
|-----|-----|--------|
| `/` | `landing_view` | Public ; redirige vers dashboard si connecte. |
| `/dashboard/` | `dashboard_view` | `@login_required` ; staff redirige vers admin-dashboard. |
| `/quiz/start/` | `quiz_start_view` | Connecte ; cree une `Session`, stocke `session_id` en session Django. |
| `/quiz/question/<numero>/` | `quiz_question_view` | GET/POST ; progression 1..N. |
| `/quiz/submit/` | `quiz_submit_view` | Finalisation alternative si utilisee. |
| `/results/<session_id>/` | `results_view` | Proprietaire de la session uniquement (403 sinon). |
| `/admin-dashboard/` | `admin_dashboard_view` | `@staff_member_required`. |
| `/admin/question/add/` | `admin_question_add` | POST staff. |
| `/admin/question/<id>/edit/` | `admin_question_edit` | GET/POST staff. |
| `/admin/question/<id>/delete/` | `admin_question_delete` | POST staff. |
| `/ressources/` | `ressources_view` | Public (filtre optionnel `?style=`). |

### Routes `accounts`

- `/accounts/register/`, `/accounts/login/`, `/accounts/logout/` (POST pour logout).

### Session quiz cote serveur

- Cle de session : **`session_id`** = ID de la `Session` en cours (non terminee).
- A la derniere question validee, la session est **finalisee** : calcul `Resultat`, `calculer()`, generation recommandation, `session_id` supprime de la session HTTP.

---

## 6. Service LLM (`quiz/services/llm_service.py`)

- **`build_prompt(resultat)`** : construit un prompt en francais avec pourcentages VAK et style dominant.
- **`generate_recommendations(session)`** :
  - Appelle **OpenAI** avec `OPENAI_API_KEY` depuis `os.environ`.
  - En cas d'exception : cree une `Recommandation` avec **`api_provider='fallback'`**.
  - Fallbacks detailles par style V/A/K (texte avec markdown `**...**`).
  - Cas particulier **`profil_type == 'EQUILIBRE'`** : texte dedie "profil multimodal".

Les recommandations sont **persistees** en base : pas de rappel API a chaque rechargement de la page resultats.

---

## 7. Fonctionnalites detaillees

### Authentification

- Inscription avec username, email, deux mots de passe ; connexion automatique apres succes.
- Affichage des **erreurs de validation** par champ sur `register.html` (ex. mot de passe trop court).
- Login avec redirection `next` ou dashboard.

### Quiz

- **12 questions** ciblees dans la fixture (apres evolution du projet ; nombre exact en base depend du chargement fixture et suppressions admin).
- **4 choix** par question : A Visuel, B Auditif, C Kinesthesique, **D Neutre** ("Aucune de ces reponses ne me correspond vraiment").
- Style visuel du choix D : classe **`choice-neutre`** (bordure en pointilles, opacite reduite).
- JS `quiz.js` : selection visuelle, activation du bouton Valider, navigation clavier.

### Resultats

- Carte principale selon **`profil_type`** (equilibre / mixte / dominant clair).
- Graphique radar Chart.js (scores VAK).
- Carte recommandation avec conversion **markdown leger** (`**gras**`, `*italique*`) + `linebreaksbr`.
- Bouton **copier le profil** (texte ASCII pour compatibilite Windows).
- Lien vers ressources filtrees par style.

### Dashboard utilisateur

- Bienvenue + CTA nouveau quiz.
- Dernier resultat resume.
- **Graphique d'evolution** (ligne) si au moins **2 sessions** terminees (jusqu'a 6 dernieres, ordre chronologique).
- Tableau historique avec badges adaptes au **`profil_type`**.

### Admin (staff / superuser)

- Redirection depuis `/dashboard/` vers **`/admin-dashboard/`**.
- Statistiques : utilisateurs non-staff, sessions terminees, distribution styles (graphique donut), sessions par semaine (barres), tableau des 10 dernieres sessions.
- Liste des questions avec apercu des choix ; **modal** d'ajout ; liens edition / suppression.

### Ressources

- Page `/ressources/` avec filtres par style (visuel, auditif, kinesthesique) et cartes de contenu pedagogique.

### Theme clair / sombre

- Attribut `data-theme` sur `<html>`, persistance **`localStorage`** (`sl-theme`), script `theme.js`.
- Bouton toggle dans la navbar : icones **soleil / lune** via **entites HTML numeriques** pour eviter les problemes d'encodage de fichiers sous Windows.

### Django Admin natif

- Toujours disponible sur `/admin/` pour les modeles `Quiz`, `Question`, `Choix`, etc.

---

## 8. Templates et filtres personnalises

- **`quiz/templatetags/quiz_extras.py`** : filtres du type `style_badge_class`, `style_label` pour homogeneiser badges et libelles.

---

## 9. Donnees initiales et commandes utiles

### Fixture

- **`quiz/fixtures/initial_data.json`** : quiz actif, questions ordonnees, choix (incluant D NEUTRE apres evolutions).

### Commande management

- **`python manage.py add_neutre_choices`** : pour les bases deja remplies **sans** choix D, ajoute le choix neutre a chaque question qui n'en a pas.

### Commandes classiques

```bash
py -3 -m pip install -r requirements.txt
py -3 manage.py makemigrations
py -3 manage.py migrate
py -3 manage.py createsuperuser
py -3 manage.py loaddata initial_data
py -3 manage.py add_neutre_choices   # si necessaire
py -3 manage.py runserver
```

---

## 10. Migrations Django (quiz)

Ordre logique observe dans le projet :

1. **`0001_initial`** : schema initial des modeles quiz.
2. **`0002_resultat_neutral_count_alter_choix_style_and_more`** : ajout `neutral_count`, prise en charge `NEUTRE` sur `Choix.style`, ajustements lies.
3. **`0003_resultat_profil_type`** : ajout du champ `profil_type` sur `Resultat`.

---

## 11. Problemes rencontres et solutions (retour d'experience)

### 11.1 Installation pip (Windows)

- **Symptome** : echec ou blocage (`WinError 32`, timeout) lors de `pip install`.
- **Piste** : relancer avec `--no-cache-dir`, fermer antivirus/verrouillage, ou utiliser un venv dedie.

### 11.2 Encodage des templates (UnicodeDecodeError)

- **Symptome** : erreur au rendu de `/admin-dashboard/` : fichier template lu en UTF-8 mais contenant des octets invalides (souvent emojis ou encodage Windows-1252).
- **Solution** : corriger le fichier en UTF-8 valide ; a terme remplacer les emojis par du **texte ASCII** dans les templates pour fiabilite sous Windows.

### 11.3 Conflit URL `/admin/question/...` vs Django Admin

- **Symptome** : POST vers suppression de question renvoyait une **404** depuis `django.contrib.admin` (catch-all).
- **Cause** : `path("admin/", admin.site.urls)` etait evalue **avant** les URLs du quiz ; tout chemin commencant par `admin/` etait absorbe.
- **Solution** : inverser l'ordre dans `smartlearn/urls.py` — inclure **`quiz.urls`** et **`accounts.urls`** **puis** `admin.site.urls`.

### 11.4 Affichage "??" a la place des emojis

- **Cause** : encodage / police / sauvegarde des fichiers.
- **Mesures** : remplacement systematique des emojis par des etiquettes ASCII (`[IA]`, `[Copier]`, `V`/`A`/`K`, etc.) et usage d'entites HTML pour soleil/lune uniquement sur le toggle theme si souhaite.

### 11.5 Dashboard "Bonjour user ??"

- **Cause** : restes de caracteres corrompus ou placeholders apres suppression d'emoji.
- **Solution** : titre reduit a `Bonjour {{ user.username }}` sans suffixe parasite.

### 11.6 Markdown brut dans les recommandations

- **Solution** : `linebreaksbr` + petit script JS remplacant `**...**` et `*...*` par `<strong>` / `<em>`.

---

## 12. Securite et bonnes pratiques (a mentionner dans un rapport)

- **Cle API** : jamais en dur dans le code ; lire depuis `.env` / environnement.
- **CSRF** : formulaires POST avec `{% csrf_token %}`.
- **Acces aux resultats** : verification que la `Session` appartient a `request.user`.
- **Staff** : vues admin protegees par `@staff_member_required`.
- **Mots de passe** : validateurs Django par defaut.

---

## 13. Limites connues et pistes d'amelioration

- Le rendu markdown cote client est **simpliste** (regex) : ne couvre pas tout Markdown ; risque mineur si le LLM injecte du HTML.
- Pas de tests automatises decrits ici (pytest / Django TestCase) : piste pour renforcer la qualite.
- **Loaddata** sur une base non vide peut provoquer des conflits de PK : strategie de reset ou fixtures idempotentes a documenter.
- Harmoniser strictement le **nombre de questions** (12) entre fixture, base reelle et consigne pedagogique apres suppressions manuelles.

---

## 14. Suggestions de structure pour un rapport académique

1. **Introduction** : contexte pedagogique VAK, problematique (personnalisation de l'apprentissage).
2. **Analyse des besoins** : utilisateurs finaux, admin, contraintes techniques.
3. **Conception** : diagramme conceptuel (User — Session — Reponses — Resultat — Recommandation), maquettes / design system.
4. **Realisation** : stack, modules Django, service LLM, difficultes (encodage, routage admin).
5. **Tests** : scenarios (tout A = 100% visuel ; 4A-4B-4C = equilibre ; API absente = fallback).
6. **Conclusion** : apports, limites, travaux futurs (internationalisation, mobile, API REST, etc.).

---

## 15. Fichiers complementaires dans le depot

- **`WORKLOG_REVIEW.md`** : journal des prompts et modifications (si maintenu a jour).
- **`smartlearn_design_system.json`** : reference couleurs, composants, pages attendues.

---

*Document genere pour servir de base factuelle au rapport SmartLearn. Adapter les dates et captures d'ecran selon votre version locale du projet.*
