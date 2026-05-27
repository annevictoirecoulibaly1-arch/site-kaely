.PHONY: help build up down logs migrate shell createsuperuser clean test

help:
	@echo "[SAFE] SafePlace - Commandes disponibles"
	@echo ""
	@echo "make build          - Construire les images Docker"
	@echo "make up             - Démarrer les services"
	@echo "make down           - Arrêter les services"
	@echo "make logs           - Afficher les logs en temps réel"
	@echo "make migrate        - Exécuter les migrations DB"
	@echo "make shell          - Accéder au shell Django"
	@echo "make createsuperuser- Créer un superutilisateur"
	@echo "make collectstatic  - Collecter les fichiers statiques"
	@echo "make clean          - Supprimer les volumes et images"
	@echo "make test           - Exécuter les tests"
	@echo "make backup         - Sauvegarder la base de données"
	@echo "make restore        - Restaurer la base de données"
	@echo ""

build:
	@echo "[TOOLS] Construction des images Docker..."
	docker-compose build

up:
	@echo "[ROCKET] Démarrage des services..."
	docker-compose up -d
	@echo "[CHECK] Services démarrés!"
	@echo "  - Site: http://localhost"
	@echo "  - Admin: http://localhost/admin"

down:
	@echo "[STOP] Arrêt des services..."
	docker-compose down
	@echo "[CHECK] Services arrêtés!"

logs:
	@echo "[LIST] Affichage des logs..."
	docker-compose logs -f

logs-web:
	docker-compose logs -f web

logs-db:
	docker-compose logs -f db

logs-celery:
	docker-compose logs -f celery

migrate:
	@echo "[PACKAGE] Exécution des migrations..."
	docker-compose exec web python manage.py migrate
	@echo "[CHECK] Migrations exécutées!"

shell:
	@echo "[SNAKE] Accès au shell Django..."
	docker-compose exec web python manage.py shell

createsuperuser:
	@echo "[USER] Création du superutilisateur..."
	docker-compose exec web python manage.py createsuperuser

collectstatic:
	@echo "[PACKAGE] Collecte des fichiers statiques..."
	docker-compose exec web python manage.py collectstatic --noinput
	@echo "[CHECK] Fichiers statiques collectés!"

loaddata:
	@echo "[CHART] Chargement des données initiales..."
	docker-compose exec web python manage.py loaddata initial_data 2>/dev/null || echo "[WARNING] Aucune donnée initiale trouvée"

dumpdata:
	@echo "[SAVE] Export des données..."
	docker-compose exec web python manage.py dumpdata --indent 2 > data/dump.json
	@echo "[CHECK] Données exportées dans data/dump.json"

clean:
	@echo "[CLEAN] Nettoyage complet..."
	docker-compose down -v
	docker system prune -f
	@echo "[CHECK] Nettoyage terminé!"

test:
	@echo "[TEST] Exécution des tests..."
	docker-compose exec web python manage.py test
	@echo "[CHECK] Tests terminés!"

test-coverage:
	@echo "[CHART] Tests avec couverture..."
	docker-compose exec web coverage run --source='.' manage.py test
	docker-compose exec web coverage report
	docker-compose exec web coverage html
	@echo "[CHECK] Rapport HTML généré dans htmlcov/index.html"

backup:
	@echo "[SAVE] Sauvegarde de la base de données..."
	@mkdir -p backups
	docker-compose exec -T db pg_dump -U safeplace_user safeplace_db > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "[CHECK] Sauvegarde effectuée!"

restore:
	@echo "[DOWNLOAD] Restauration de la base de données..."
	@if [ -z "$(BACKUP)" ]; then \
		echo "[CROSS] Veuillez spécifier le fichier de sauvegarde: make restore BACKUP=backups/backup_file.sql"; \
	else \
		docker-compose exec -T db psql -U safeplace_user safeplace_db < $(BACKUP); \
		echo "[CHECK] Restauration effectuée!"; \
	fi

ps:
	@echo "[SEARCH] État des services..."
	docker-compose ps

redis-cli:
	@echo "[RED] Accès à Redis..."
	docker-compose exec redis redis-cli

psql:
	@echo "[DB] Accès à PostgreSQL..."
	docker-compose exec db psql -U safeplace_user -d safeplace_db

celery-inspect:
	@echo "[SEARCH] Inspection des tâches Celery..."
	docker-compose exec celery celery -A Safeplace inspect active

celery-purge:
	@echo "[CLEAN] Purge des tâches Celery..."
	docker-compose exec celery celery -A Safeplace purge -f

restart:
	@echo "[RELOAD] Redémarrage des services..."
	docker-compose restart
	@echo "[CHECK] Services redémarrés!"

restart-web:
	docker-compose restart web

restart-db:
	docker-compose restart db

restart-redis:
	docker-compose restart redis

restart-celery:
	docker-compose restart celery celery_beat

requirements:
	@echo "[PAGE] Mise à jour des dépendances..."
	pip list --outdated
	docker-compose exec -T web pip list --outdated

init: build up migrate createsuperuser collectstatic
	@echo "[CHECK] Initialisation complète!"

dev:
	@echo "[GEAR] Démarrage en mode développement..."
	DEBUG=True docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

prod:
	@echo "[ROCKET] Démarrage en mode production..."
	DEBUG=False docker-compose up -d
	make migrate
	make collectstatic

.SILENT:
