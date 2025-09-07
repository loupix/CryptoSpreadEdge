# Dockerfile optimisé pour le service de prédiction ML
FROM nvidia/cuda:11.8-devel-ubuntu20.04

# Métadonnées
LABEL maintainer="CryptoSpreadEdge Team"
LABEL service="prediction"
LABEL version="1.0.0"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app
ENV WORKERS=1
ENV TIMEOUT=30
ENV CUDA_VISIBLE_DEVICES=0

# Installer Python et les dépendances système
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libopenblas-dev \
    liblapack-dev \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

# Créer des liens symboliques
RUN ln -s /usr/bin/python3.11 /usr/bin/python && \
    ln -s /usr/bin/pip3 /usr/bin/pip

# Créer un utilisateur non-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Créer le répertoire de travail
WORKDIR /app

# Copier les requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Installer PyTorch avec support CUDA
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Copier le code source
COPY src/ ./src/
COPY config/ ./config/

# Créer les répertoires nécessaires
RUN mkdir -p /app/logs /app/cache /app/models /app/data

# Changer les permissions
RUN chown -R appuser:appuser /app

# Passer à l'utilisateur non-root
USER appuser

# Exposer le port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=120s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Commande de démarrage
CMD ["python", "-m", "uvicorn", "src.microservices.prediction_service:app", \
     "--host", "0.0.0.0", "--port", "8000", "--workers", "1", \
     "--log-level", "info", "--access-log"]