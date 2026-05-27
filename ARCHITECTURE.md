# Architecture — The SafePlace by K

Document de référence technique pour l'architecture de la plateforme.

## 1. Vue d'ensemble

**The SafePlace by K** est une plateforme de podcast et de médias chrétienne construite sur Django 4.2. L'application a été refactorisée vers une **architecture découplée** : le backend gère la logique métier et expose une API REST, tandis que le tableau de bord d'administration est un microservice indépendant hébergé séparément.

## 2. Architecture découplée

### A. Backend (`podcastSafe`)

- **Rôle** : Logique métier, persistance des données, site public.
- **Technologie** : Django 4.2, Django REST Framework 3.14.
- **Responsabilités** :
  - Gestion des Episodes (podcasts et vidéos), Live Streams, Catégories.
  - Abonnements aux notifications et formulaire de contact.
  - Exposition des API REST pour le Dashboard.
  - Tâches asynchrones via Celery (mise à jour des lives, notifications email).
- **Hébergement** : Conteneurisé via Docker (Railway, Fly.io, VPS).

### B. Dashboard (`dashboard-service`)

- **Rôle** : Interface d'administration pour la gestion du contenu.
- **Technologie** : Django indépendant, déployable sur Netlify.
- **Responsabilités** :
  - Publication d'épisodes et vidéos.
  - Gestion des live streams.
  - Consultation des messages de contact.
  - Visualisation des analytics.
- **Hébergement** : Netlify, avec proxy Nginx local en développement (port 8001).

## 3. Communication inter-services

| Mécanisme | Détail |
|-----------|--------|
| Protocole | HTTP REST (JSON) |
| Authentification | En-tête `X-API-KEY` (valeur de `DASHBOARD_API_KEY`) |
| CORS | Le backend autorise explicitement l'origine Netlify du dashboard |
| Redirection utilisateur | `GET /dashboard/` → `302` vers `DASHBOARD_NETLIFY_URL` |

## 4. Modèles de données

### Episode

| Champ | Type | Description |
|-------|------|-------------|
| `title` | CharField(200) | Titre de l'épisode |
| `description` | TextField | Description |
| `episode_type` | CharField | `podcast` ou `video` |
| `category` | FK → Category | Catégorie (nullable) |
| `audio_url` | URLField | URL MP3 (podcasts) |
| `video_url` | URLField | URL YouTube / vidéo (vidéos) |
| `video_file` | FileField | Fichier vidéo local (optionnel) |
| `duration` | CharField(10) | Durée (ex: `42:30`) |
| `cover_color` | CharField(7) | Couleur de couverture hex |
| `views_count` | IntegerField | Nombre de vues |
| `is_published` | BooleanField | Publié ou brouillon |
| `created_at` | DateTimeField | Date de création (auto) |

### LiveStream

| Champ | Type | Description |
|-------|------|-------------|
| `title` | CharField | Titre du live |
| `description` | TextField | Description |
| `platform` | CharField | `youtube`, `facebook`, `tiktok`, `instagram`, `spotify` |
| `stream_url` | URLField | URL du stream |
| `embed_url` | URLField | URL d'intégration iframe |
| `status` | CharField | `scheduled`, `live`, `ended` |
| `scheduled_at` | DateTimeField | Date planifiée (nullable) |
| `viewers_count` | IntegerField | Nombre de spectateurs |

### Subscription

| Champ | Type | Description |
|-------|------|-------------|
| `first_name` | CharField(100) | Prénom |
| `last_name` | CharField(100) | Nom |
| `email` | EmailField (unique) | Adresse email |
| `notify_podcasts` | BooleanField | Notifier pour les podcasts |
| `notify_live` | BooleanField | Notifier pour les lives |
| `notify_videos` | BooleanField | Notifier pour les vidéos |
| `is_active` | BooleanField | Abonnement actif |

### ContactMessage

| Champ | Type | Description |
|-------|------|-------------|
| `name` | CharField | Nom complet |
| `email` | EmailField | Email de l'expéditeur |
| `subject` | CharField | Sujet |
| `message` | TextField | Corps du message |
| `priority` | CharField | `normal`, `high` |
| `is_read` | BooleanField | Lu ou non |

## 5. API REST — Endpoints

Tous les endpoints sont sous `/api/v1/` et requièrent `X-API-KEY`.

```
GET    /api/v1/dashboard-data/              Statistiques globales
GET    /api/v1/analytics/                   Analytics détaillées (param: days)
GET    /api/v1/episodes/                    Liste paginée des épisodes
POST   /api/v1/episodes/create/             Créer un épisode
DELETE /api/v1/episodes/<pk>/delete/        Supprimer un épisode
GET    /api/v1/categories/                  Liste des catégories
GET    /api/v1/livestreams/                 Liste des live streams
POST   /api/v1/livestreams/create/          Créer un live stream
PUT    /api/v1/livestreams/<pk>/update/     Mettre à jour un live stream
DELETE /api/v1/livestreams/<pk>/delete/     Supprimer un live stream
GET    /api/v1/messages/                    Messages de contact
POST   /api/v1/messages/<pk>/read/          Marquer comme lu
POST   /api/v1/messages/mark-all-read/      Tout marquer comme lu
DELETE /api/v1/messages/<pk>/delete/        Supprimer un message
GET    /api/v1/subscriptions/               Liste des abonnements
```

## 6. Variables d'environnement

### Backend

| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| `SECRET_KEY` | Clé secrète Django | (insecure dev key) |
| `DEBUG` | Mode debug | `True` |
| `ALLOWED_HOSTS` | Hôtes autorisés | `localhost,127.0.0.1` |
| `DATABASE_URL` | URL PostgreSQL complète (Supabase…) | — |
| `DB_NAME` | Nom de la base | `safeplace_db` |
| `DB_USER` | Utilisateur PostgreSQL | `safeplace_user` |
| `DB_PASSWORD` | Mot de passe PostgreSQL | — |
| `DB_HOST` | Hôte PostgreSQL | `db` |
| `REDIS_HOST` | Hôte Redis | `redis` |
| `REDIS_PORT` | Port Redis | `6379` |
| `REDIS_PASSWORD` | Mot de passe Redis | — |
| `DASHBOARD_API_KEY` | Clé partagée backend ↔ dashboard | `safeplace_secret_dashboard_key_2026` |
| `DASHBOARD_NETLIFY_URL` | URL production du dashboard | `https://dashboard-safeplace.netlify.app` |
| `EMAIL_HOST_USER` | Adresse email SMTP | — |
| `EMAIL_HOST_PASSWORD` | Mot de passe SMTP | — |
| `DEFAULT_FROM_EMAIL` | Expéditeur des emails | valeur de `EMAIL_HOST_USER` |
| `ADMIN_EMAIL` | Destinataire des alertes | — |

### Dashboard

| Variable | Description |
|----------|-------------|
| `MAIN_API_URL` | URL de l'API backend (`http://web:8000/api/v1/`) |
| `DASHBOARD_API_KEY` | Clé partagée (identique au backend) |

## 7. Structure des répertoires

```
.
├── Safeplace/                  # Configuration globale Django
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   ├── wsgi.py
│   └── asgi.py
├── podcastSafe/                # Application principale
│   ├── models/                 # Episode, LiveStream, Category, Subscription, ContactMessage
│   ├── views.py                # Vues publiques
│   ├── api_views.py            # Endpoints DRF
│   ├── api_urls.py             # Routes API
│   ├── urls.py                 # Routes publiques
│   ├── auth.py                 # Décorateurs @owner_required, @subscriber_required
│   ├── tasks.py                # Tâches Celery
│   ├── context_processors.py
│   ├── template/               # Templates HTML
│   ├── migrations/
│   └── tests/
├── dashboard-service/          # Microservice dashboard
├── static/                     # Fichiers statiques
├── ssl/                        # Certificats SSL
├── docker-compose.yml
├── Dockerfile
├── nginx.conf
└── requirements.txt
```

## 8. Tâches Celery planifiées

| Tâche | Déclencheur | Action |
|-------|-------------|--------|
| `update_live_stream_status` | Toutes les 5 min | Passe les streams planifiés dont `scheduled_at <= now` en `live` |
| `send_new_episode_notifications` | Quotidien | Prépare les notifications pour les nouveaux épisodes du jour |
| `send_daily_report` | Quotidien | Envoie un rapport journalier à `ADMIN_EMAIL` |

## 9. Stratégie de déploiement

### Backend (Docker)

1. Push sur `main` → détection du `Dockerfile` par l'hébergeur.
2. PostgreSQL et Redis provisionnés via `docker-compose` ou services managés.
3. `gunicorn` expose l'application sur le port 8000 derrière Nginx.

### Dashboard (Netlify)

1. Dépôt séparé ou sous-dossier `dashboard-service/`.
2. `netlify.toml` proxifie `/api/*` vers le backend pour éviter les problèmes CORS.
3. `DASHBOARD_API_KEY` partagée avec le backend via les variables d'environnement Netlify.

---

*Mis à jour le 2026-05-26*
