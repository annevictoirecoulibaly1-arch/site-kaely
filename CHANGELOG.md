# Changelog

Toutes les modifications notables de ce projet sont documentées ici.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/)
et ce projet respecte le [Versionnage Sémantique](https://semver.org/lang/fr/).

---

## [1.1.0] - 2026-05-26

### Corrigé
- `requirements.txt` : suppression des 8 dépendances en double ; ajout de `django-celery-beat==2.6.0` (requis par le scheduler Celery Beat dans `docker-compose.yml`)
- `settings.py` : la variable d'environnement lue était `DJANGO_SECRET_KEY` alors que `docker-compose.yml` injecte `SECRET_KEY` — corrigé pour correspondre
- `settings.py` : idem pour `DJANGO_DEBUG` → `DEBUG`
- `settings.py` : `CELERY_BROKER_URL` et `CELERY_RESULT_BACKEND` avaient le mot de passe Redis codé en dur (`redis_password_123`) ; l'URL est maintenant construite dynamiquement depuis `REDIS_HOST`, `REDIS_PORT` et `REDIS_PASSWORD`
- `settings.py` : ajout de la section Email complète (`EMAIL_*`, `DEFAULT_FROM_EMAIL`, `ADMINS`) — ces variables étaient utilisées dans `views.py` et `tasks.py` mais jamais définies
- `settings.py` : correction du commentaire indiquant "Django 6.0.5" (version inexistante) en "Django 4.2"
- `api_urls.py` : `subscriptions_api` était définie dans `api_views.py` mais absente des URL patterns — route `GET /api/v1/subscriptions/` ajoutée

### Mis à jour
- `README.md` : refonte complète — suppression des références Stripe, correction des endpoints API, suppression des placeholders `[TAG]`, table des variables d'environnement à jour
- `ARCHITECTURE.md` : correction de la version Django (4.2), correction de `DJANGO_SECRET_KEY` → `SECRET_KEY` dans la table des variables, mise à jour des endpoints, date de génération
- `DEPLOYMENT.md` : suppression de toutes les références Stripe, ajout de Railway comme option de déploiement, correction des endpoints API, clarification de la checklist
- `CHANGELOG.md` : correction de la v1.0.0 (retrait des mentions Stripe/PayPal intégrés)

---

## [1.0.0] - 2026-05-13

### Ajouté
- Version initiale de The SafePlace by K
- Application Django principale avec gestion des podcasts, vidéos et lives
- API REST via Django REST Framework pour l'intégration du dashboard
- Microservice Dashboard indépendant
- Authentification par clé API entre les services (`X-API-KEY`)
- Système d'abonnement aux notifications (email)
- Formulaire de contact avec envoi d'email

### Modifié
- Refonte de l'interface en design immersif pour la page d'accueil et les lives
- Remplacement de l'authentification basique par une authentification par clé API pour le dashboard

### Corrigé
- Routes API pour la publication d'épisodes depuis le dashboard
- Communication inter-services via les URLs API correctes
