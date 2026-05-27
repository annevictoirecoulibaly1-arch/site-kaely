# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    postgresql-client-common \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Security: Create non-root user immediately to prevent root execution
RUN groupadd -r django && useradd -r -g django django

WORKDIR /app

# Installer les runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client-common \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copier les dépendances Python du builder
COPY --from=builder /root/.local /home/django/.local

# Copier l'application
COPY . .

# Créer des répertoires nécessaires et donner les permissions
RUN mkdir -p /app/staticfiles /app/media \
    && chown -R django:django /app \
    && chown -R django:django /home/django

# Ajouter /home/django/.local/bin au PATH
ENV PATH=/home/django/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Security: Force non-root execution and prevent privilege escalation
USER django

# Security: Health check to ensure container is running as non-root
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD id -u && id -u | grep -q '^django$' || exit 1

# Exposer le port
EXPOSE 8000

# Commande de démarrage
CMD sh -c "python manage.py migrate && gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 120 Safeplace.wsgi:application"
