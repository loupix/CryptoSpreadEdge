#!/bin/bash

# Script de déploiement Docker Swarm pour CryptoSpreadEdge

set -e

echo "🚀 Déploiement de CryptoSpreadEdge sur Docker Swarm..."

# Vérifier si Docker Swarm est initialisé
if ! docker info | grep -q "Swarm: active"; then
    echo "🔧 Initialisation de Docker Swarm..."
    docker swarm init
fi

# Construire l'image
echo "🐳 Construction de l'image Docker..."
docker build -f infrastructure/docker/services/cryptospreadedge/Dockerfile -t cryptospreadedge:latest .

# Créer les répertoires sur les nœuds
echo "📁 Création des répertoires sur les nœuds..."
docker service create --name setup-dirs --mode global --mount type=bind,source=/var/lib/cryptospreadedge,target=/var/lib/cryptospreadedge alpine sh -c "mkdir -p /var/lib/cryptospreadedge/data /var/lib/cryptospreadedge/logs && chmod 777 /var/lib/cryptospreadedge/data /var/lib/cryptospreadedge/logs"

# Attendre que les répertoires soient créés
sleep 10

# Supprimer le service temporaire
docker service rm setup-dirs

# Déployer la stack
echo "🚀 Déploiement de la stack..."
docker stack deploy -c infrastructure/docker/swarm/docker-stack.yml cryptospreadedge

# Attendre que les services soient déployés
echo "⏳ Attente du déploiement..."
sleep 60

# Vérifier le statut des services
echo "🔍 Statut des services:"
docker service ls

echo "📊 Statut de la stack:"
docker stack services cryptospreadedge

echo "✅ Déploiement terminé!"
echo ""
echo "🌐 Services disponibles:"
echo "- Application: http://localhost:8000"
echo "- Prometheus: http://localhost:9090"
echo "- Grafana: http://localhost:3000"
echo "- Kibana: http://localhost:5601"
echo ""
echo "📋 Commandes utiles:"
echo "- Voir les logs: docker service logs -f cryptospreadedge_cryptospreadedge"
echo "- Mettre à jour: docker service update cryptospreadedge_cryptospreadedge"
echo "- Arrêter: docker stack rm cryptospreadedge"