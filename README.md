# The SafePlace by K

Plateforme de podcast chrétienne moderne. Le backend Django gère la logique métier et l'API REST ; le tableau de bord est un microservice indépendant hébergeable séparément (Netlify, Vercel…).

## Architecture système

```
      ┌──────────────────────────────────┐
      │      Dashboard (Microservice)    │
      │      Hébergé sur Netlify         │
      └──────────────┬───────────────────┘
                     │ Appels API REST (X-API-KEY)
                     ▼
      ┌──────────────────────────────────┐
      │      Backend Django 4.2          │
      │      Hébergé sur Cloud / VPS     │
      └──────────────┬───────────────────┘
                     │
    ┌────────────────┼────────────────┬──────────────┐
    │                │                │              │
┌───▼──────┐   ┌────▼────┐      ┌───▼──────┐  ┌───▼──────┐
│PostgreSQL│   │  Redis  │      │ Celery   │  │ Celery   │
│   DB     │   │  Cache  │      │ Worker   │  │  Beat    │
└──────────┘   └─────────┘      └──────────┘  └──────────┘
```

## Composants

| Composant | Rôle | Technologie |
|-----------|------|-------------|
| `podcastSafe` | Backend principal, API REST, site public | Django 4.2, DRF |
| `dashboard-service` | Interface d'administration | Django indépendant → Netlify |
| PostgreSQL | Base de données principale | PostgreSQL 16 |
| Redis | Cache et broker Celery | Redis 7 |
| Celery / Celery Beat | Tâches asynchrones et planifiées | Celery 5.3, django-celery-beat |
| Nginx | Reverse proxy, fichiers statiques | Nginx Alpine |

## Installation locale (Docker)

```bash
# 1. Cloner
git clone https://github.com/coulibalyisrael727-png/the-SafePlaceBy-K.git
cd the-SafePlaceBy-K

# 2. Configurer l'environnement
cp .env.example .env
# Éditer .env avec vos valeurs (DB, Redis, email…)

# 3. Lancer tous les services
docker-compose up -d

# 4. Initialiser la base de données
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

Le site est accessible sur `http://localhost` (via Nginx) ou `http://localhost:8000` (Django direct).  
Le dashboard est sur `http://localhost:8001` ou via la route `/dashboard/` qui redirige vers Netlify.

## API

**Base URL :** `http://localhost/api/v1/`

Tous les endpoints protégés nécessitent l'en-tête :
```
X-API-KEY: <valeur de DASHBOARD_API_KEY>
```

### Endpoints disponibles

```
GET    /api/v1/dashboard-data/              Statistiques globales
GET    /api/v1/analytics/                   Analytics détaillées
GET    /api/v1/episodes/                    Liste des épisodes (filtres: status, type, search, page)
POST   /api/v1/episodes/create/             Créer un épisode
DELETE /api/v1/episodes/<pk>/delete/        Supprimer un épisode
GET    /api/v1/categories/                  Liste des catégories
GET    /api/v1/livestreams/                 Liste des live streams
POST   /api/v1/livestreams/create/          Créer un live stream
PUT    /api/v1/livestreams/<pk>/update/     Mettre à jour un live stream
DELETE /api/v1/livestreams/<pk>/delete/     Supprimer un live stream
GET    /api/v1/messages/                    Messages de contact
POST   /api/v1/messages/<pk>/read/          Marquer un message comme lu
POST   /api/v1/messages/mark-all-read/      Marquer tous les messages comme lus
DELETE /api/v1/messages/<pk>/delete/        Supprimer un message
GET    /api/v1/subscriptions/               Liste des abonnements
```

### Exemples

```bash
# Lister les épisodes
curl http://localhost/api/v1/episodes/ \
  -H "X-API-KEY: safeplace_secret_dashboard_key_2026"

# Créer un épisode
curl -X POST http://localhost/api/v1/episodes/create/ \
  -H "X-API-KEY: safeplace_secret_dashboard_key_2026" \
  -H "Content-Type: application/json" \
  -d '{"title": "Épisode 1", "description": "...", "episode_type": "podcast", "audio_url": "https://..."}'

# Créer un abonnement (endpoint public via formulaire)
curl -X POST http://localhost/contact/ \
  -d 'first_name=Jean&email=jean@example.com&subject=Contact&message=Bonjour'
```

## Pages disponibles

| URL | Description |
|-----|-------------|
| `/` | Accueil avec épisodes récents et lives |
| `/podcasts/` | Galerie de podcasts |
| `/podcasts/<pk>/` | Détail d'un épisode podcast |
| `/videos/` | Galerie de vidéos |
| `/videos/<pk>/` | Détail d'une vidéo |
| `/live/` | Lives en cours et planifiés |
| `/contact/` | Formulaire de contact |
| `/apropos/` | Page à propos |
| `/publish/` | Publier un épisode (propriétaire) |
| `/manage-live-streams/` | Gérer les lives (propriétaire) |
| `/dashboard/` | Redirection vers le dashboard Netlify |
| `/admin/` | Interface d'administration Django |

## Configuration

### Variables d'environnement essentielles

```env
# Sécurité
SECRET_KEY=<clé secrète Django>
DEBUG=False
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com

# Base de données
DB_NAME=safeplace_db
DB_USER=safeplace_user
DB_PASSWORD=<mot de passe sécurisé>
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<mot de passe Redis>

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe-app
DEFAULT_FROM_EMAIL=votre-email@gmail.com
ADMIN_EMAIL=admin@votre-domaine.com

# Dashboard
DASHBOARD_API_KEY=<clé secrète partagée>
DASHBOARD_NETLIFY_URL=https://dashboard-safeplace.netlify.app
```

### Donations

Le projet n'intègre pas de fournisseur de paiement natif. Pour accepter des dons, utilisez des liens externes (PayPal, Ko-fi, virement bancaire) configurables via votre template.

## Commandes utiles

```bash
# Logs
docker-compose logs -f
docker-compose logs -f web

# Shell Django
docker-compose exec web python manage.py shell

# Migrations
docker-compose exec web python manage.py migrate

# Superutilisateur
docker-compose exec web python manage.py createsuperuser

# Sauvegarde PostgreSQL
docker-compose exec db pg_dump -U safeplace_user safeplace_db > backup.sql

# Redis : vérifier la connexion
docker-compose exec redis redis-cli ping

# Celery : vérifier les tâches actives
docker-compose exec celery celery -A Safeplace inspect active

# Redémarrer tout
docker-compose restart

# Arrêter et supprimer les volumes
docker-compose down -v
```

## Sécurité — checklist production

```bash
# Générer une SECRET_KEY sécurisée
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Certificat SSL Let's Encrypt
sudo certbot certonly --standalone -d votre-domaine.com
sudo cp /etc/letsencrypt/live/votre-domaine.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/votre-domaine.com/privkey.pem ./ssl/key.pem
```

Variables `.env` minimales pour la production :
```env
DEBUG=False
SECRET_KEY=<clé générée>
ALLOWED_HOSTS=votre-domaine.com
REDIS_PASSWORD=<mot de passe fort>
DB_PASSWORD=<mot de passe fort>
DASHBOARD_API_KEY=<clé secrète forte>
```

## Dépannage

| Symptôme | Commande de diagnostic |
|----------|------------------------|
| 502 Bad Gateway | `docker-compose logs web` |
| Base de données injoignable | `docker-compose logs db` |
| Celery ne traite pas les tâches | `docker-compose exec redis redis-cli ping` |
| Port déjà utilisé | Modifier les ports dans `docker-compose.yml` |

## Ressources

- [Django 4.2](https://docs.djangoproject.com/en/4.2/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Celery](https://docs.celeryq.dev/)
- [Docker Compose](https://docs.docker.com/compose/)
- [PostgreSQL](https://www.postgresql.org/docs/)

## Licence

© 2024 The SafePlace by K. Tous droits réservés.
