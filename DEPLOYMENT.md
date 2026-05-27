# Guide de déploiement — The SafePlace by K

## Checklist pré-déploiement

### Sécurité
- [ ] Générer une nouvelle `SECRET_KEY`
- [ ] Passer `DEBUG=False`
- [ ] Configurer `ALLOWED_HOSTS` avec votre domaine
- [ ] Certificats SSL/TLS (HTTPS)
- [ ] Mots de passe forts pour DB et Redis
- [ ] Changer `DASHBOARD_API_KEY` par une valeur aléatoire forte

### Application
- [ ] Tester tous les endpoints API
- [ ] Vérifier l'envoi des emails (contact, notifications)
- [ ] Sauvegarder la base de données avant toute migration
- [ ] Vérifier les logs après le démarrage

### Infrastructure
- [ ] CPU/RAM suffisant (minimum 1 vCPU / 512 Mo RAM)
- [ ] Espace disque pour les uploads médias
- [ ] Backups automatiques activés

---

## Architecture de déploiement

Le projet utilise une architecture découplée :

- **Backend Django** (port 8000) — Application principale + API REST
- **Dashboard** (port 8001 en local, Netlify en production) — Interface d'administration
- **Nginx** — Reverse proxy exposant les ports 80 et 443

### Communication inter-services

Le Dashboard consomme les API du Backend via `MAIN_API_URL`. L'authentification se fait par l'en-tête `X-API-KEY` avec la valeur de `DASHBOARD_API_KEY` (identique sur les deux services).

### Variables côté Backend

```env
DASHBOARD_URL=https://votre-dashboard.netlify.app
DASHBOARD_API_KEY=<clé forte aléatoire>
```

### Variables côté Dashboard

```env
MAIN_API_URL=https://votre-api.com/api/v1/
MAIN_SITE_URL=https://votre-site.com
DASHBOARD_API_KEY=<même clé que le backend>
```

### Endpoints API disponibles pour le Dashboard

```
GET    /api/v1/dashboard-data/              Statistiques globales
GET    /api/v1/analytics/                   Analytics détaillées
GET    /api/v1/episodes/                    Liste des épisodes
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

Tous les endpoints requièrent :
```
X-API-KEY: <valeur de DASHBOARD_API_KEY>
```

---

## Options de déploiement du Backend

### 1. AWS EC2

```bash
# Créer une instance EC2 Ubuntu 22.04

# Installer Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Cloner le projet
git clone <repo>
cd the-SafePlaceBy-K

# Configurer
cp .env.example .env
# Éditer .env avec les vraies valeurs

# Déployer
docker-compose up -d

# Initialiser la DB
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### 2. Heroku

```bash
# Installer Heroku CLI
npm i -g heroku
heroku login

# Créer l'app
heroku create votre-app-name

# Configurer les variables
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=<clé générée>
heroku config:set ALLOWED_HOSTS=votre-app.herokuapp.com
heroku config:set DASHBOARD_API_KEY=<clé forte>

# Déployer
git push heroku main

# Voir les logs
heroku logs --tail
```

### 3. Digital Ocean (Droplet)

```bash
# Créer un Droplet Ubuntu 22.04, SSH dedans

# Installer Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Installer Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Pointer votre DNS vers l'IP du Droplet, puis suivre les étapes AWS ci-dessus
```

### 4. Render (recommandé pour la simplicité)

1. Connecter votre dépôt GitHub à Render.
2. Créer un **Web Service** avec le `Dockerfile` à la racine.
3. Ajouter les variables d'environnement dans le dashboard Render.
4. Render redéploie automatiquement à chaque push sur `main`.

### 5. Railway

Railway détecte automatiquement le `Dockerfile`. Ajoutez les variables d'environnement et provisionnez PostgreSQL et Redis depuis le marketplace Railway.

---

## SSL / HTTPS

### Let's Encrypt (gratuit)

```bash
# Installer Certbot
sudo apt-get install certbot python3-certbot-nginx

# Générer les certificats
sudo certbot certonly --standalone -d votre-domaine.com

# Copier pour Nginx
sudo cp /etc/letsencrypt/live/votre-domaine.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/votre-domaine.com/privkey.pem ./ssl/key.pem

# Renouvellement automatique
sudo certbot renew --dry-run
```

### Configuration Nginx HTTPS

Décommenter dans `nginx.conf` :

```nginx
server {
    listen 443 ssl http2;
    server_name votre-domaine.com www.votre-domaine.com;

    ssl_certificate     /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # ... reste de la configuration
}

# Redirection HTTP → HTTPS
server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Mise à jour continue

```bash
# Récupérer les changements
git pull origin main

# Reconstruire les images
docker-compose build

# Appliquer les migrations
docker-compose exec web python manage.py migrate

# Redémarrer les services
docker-compose up -d

# Vérifier les logs
docker-compose logs -f
```

### Rollback

```bash
docker-compose down
# Éditer docker-compose.yml pour pointer vers l'image précédente
docker-compose up -d
docker-compose logs -f
```

---

## Performance et monitoring

### Optimisations Docker

```bash
# Nettoyer les images inutilisées
docker image prune -a

# Nettoyer les volumes inutilisés
docker volume prune

# Augmenter les workers Gunicorn si CPU le permet
# Dans docker-compose.yml : gunicorn --workers 8 (2 * nb_CPU + 1)
```

### Outils de monitoring recommandés

| Outil | Usage |
|-------|-------|
| Sentry | Suivi des erreurs applicatives |
| Uptime Robot | Monitoring de disponibilité |
| Datadog / New Relic | APM et métriques |
| CloudWatch (AWS) | Logs et alertes |
| Prometheus + Grafana | Stack open source |

---

## Sécurité production

```bash
# 1. Firewall : n'autoriser que 80 et 443
# 2. SSH : désactiver le login root, utiliser clés SSH uniquement
# 3. Fail2Ban
sudo apt-get install fail2ban
sudo systemctl start fail2ban

# 4. Mises à jour système
sudo apt-get update && sudo apt-get upgrade -y

# 5. Backups DB quotidiens
docker-compose exec db pg_dump -U safeplace_user safeplace_db > backup_$(date +%Y%m%d).sql
```

---

## Troubleshooting

### 502 Bad Gateway

```bash
docker-compose logs web       # Vérifier Gunicorn
docker-compose restart web    # Redémarrer
docker-compose logs db        # Vérifier la connexion DB
```

### CPU élevé

```bash
# Augmenter les workers Gunicorn dans docker-compose.yml
# gunicorn --workers 8 --bind 0.0.0.0:8000 Safeplace.wsgi:application
```

### Disque plein

```bash
docker system prune           # Nettoyer Docker
du -sh /app/media             # Vérifier les uploads
```

### Celery ne traite pas les tâches

```bash
docker-compose exec redis redis-cli ping           # Vérifier Redis
docker-compose logs celery                         # Logs Celery
docker-compose restart celery celery_beat          # Redémarrer
```

### Base de données inaccessible

```bash
docker-compose logs db
docker-compose restart db
docker-compose exec db psql -U safeplace_user -d safeplace_db
```

---

## Étapes finales de validation

```bash
# Tester les pages principales
curl -I https://votre-domaine.com
curl -I https://votre-domaine.com/admin

# Tester l'API
curl https://votre-domaine.com/api/v1/dashboard-data/ \
  -H "X-API-KEY: <votre-DASHBOARD_API_KEY>"

# Vérifier les emails
# Soumettre le formulaire de contact et vérifier la réception

# Vérifier les performances
# GTmetrix, Google PageSpeed Insights

# Confirmer les logs sans erreurs
docker-compose logs -f
```

---

Votre application est maintenant en production. Pour les mises à jour futures, suivez le processus de déploiement ci-dessus.
