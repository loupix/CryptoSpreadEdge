# Dockerfile pour CryptoSpreadEdge
FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Créer l'utilisateur non-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Créer le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/

# Créer les répertoires nécessaires
RUN mkdir -p /app/data /app/logs /app/models

# Changer les permissions
RUN chown -R appuser:appuser /app

# Passer à l'utilisateur non-root
USER appuser

# Exposer le port
EXPOSE 8000

# Point d'entrée
CMD ["python", "-m", "src.main"]