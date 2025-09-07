# Scripts d'Arbitrage CryptoSpreadEdge

## Vue d'ensemble

Ce document décrit les scripts disponibles pour le système d'arbitrage CryptoSpreadEdge. Ces scripts permettent de tester, démarrer et gérer le système d'arbitrage.

## Scripts disponibles

### 1. `start_arbitrage.py`

**Description** : Démarre le système d'arbitrage complet en mode autonome.

**Utilisation** :
```bash
python scripts/arbitrage/start_arbitrage.py
```

**Fonctionnalités** :
- Démarre tous les composants d'arbitrage
- Surveillance continue des prix
- Détection et exécution d'opportunités
- Monitoring des performances
- Arrêt propre avec Ctrl+C

**Configuration** :
- Utilise la configuration par défaut
- Peut être personnalisé via les variables d'environnement
- Logs dans `logs/arbitrage.log`

### 2. `test_arbitrage_system.py`

**Description** : Lance une suite de tests complète pour valider le système d'arbitrage.

**Utilisation** :
```bash
python scripts/arbitrage/test_arbitrage_system.py
```

**Tests inclus** :
- Test des connecteurs d'exchanges
- Test du PriceMonitor
- Test du ProfitCalculator
- Test du RiskManager
- Test de l'ExecutionEngine
- Test de l'ArbitrageEngine
- Test d'intégration complet

**Résultat** :
- Rapport détaillé des tests
- Statut de chaque composant
- Résumé global des performances

### 3. `demo_arbitrage.py`

**Description** : Démonstration interactive du système d'arbitrage.

**Utilisation** :
```bash
python scripts/arbitrage/demo_arbitrage.py
```

**Démonstrations** :
- Calcul de profit avec exemples
- Détection d'opportunités fictives
- Gestion des risques
- Monitoring des prix
- Statistiques du système

**Avantages** :
- Aucun trade réel effectué
- Exemples concrets
- Compréhension du fonctionnement

### 4. `quick_start.py`

**Description** : Démarrage rapide pour une démonstration de 2 minutes.

**Utilisation** :
```bash
python scripts/arbitrage/quick_start.py
```

**Fonctionnalités** :
- Démarrage rapide des composants
- Surveillance pendant 2 minutes
- Affichage des statistiques en temps réel
- Résumé des performances
- Arrêt automatique

**Idéal pour** :
- Tests rapides
- Démonstrations
- Validation du système

## Configuration des scripts

### Variables d'environnement

Les scripts utilisent les variables d'environnement suivantes :

```bash
# Configuration générale
ARBITRAGE_ENABLED=true
ARBITRAGE_MODE=sandbox
LOG_LEVEL=INFO

# Symboles à surveiller
ARBITRAGE_SYMBOLS=BTC/USDT,ETH/USDT,BNB/USDT

# Exchanges à utiliser
ARBITRAGE_EXCHANGES=binance,okx,bybit

# Paramètres de détection
MIN_SPREAD_PERCENTAGE=0.001
MAX_SPREAD_PERCENTAGE=0.05
MIN_VOLUME=0.01
```

### Fichier de configuration

Copiez le fichier d'exemple :
```bash
cp config/environments/arbitrage.env.example config/environments/arbitrage.env
```

Puis modifiez les valeurs selon vos besoins.

## Utilisation recommandée

### Pour les développeurs

1. **Tests unitaires** :
```bash
python scripts/arbitrage/test_arbitrage_system.py
```

2. **Démonstration** :
```bash
python scripts/arbitrage/demo_arbitrage.py
```

3. **Test rapide** :
```bash
python scripts/arbitrage/quick_start.py
```

### Pour la production

1. **Configuration** :
```bash
# Copier et configurer l'environnement
cp config/environments/arbitrage.env.example config/environments/arbitrage.env
# Éditer le fichier avec vos clés API
```

2. **Démarrage** :
```bash
python scripts/arbitrage/start_arbitrage.py
```

3. **Monitoring** :
```bash
# Surveiller les logs
tail -f logs/arbitrage.log

# Vérifier le statut
python start.py status
```

## Dépannage

### Problèmes courants

1. **Erreur d'import** :
```bash
# Vérifier que le répertoire src est dans le PATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

2. **Erreur de connexion** :
```bash
# Vérifier les clés API
# Utiliser le mode sandbox pour les tests
```

3. **Erreur de permissions** :
```bash
# Rendre les scripts exécutables
chmod +x scripts/arbitrage/*.py
```

### Logs utiles

```bash
# Logs d'arbitrage
tail -f logs/arbitrage.log

# Logs généraux
tail -f logs/cryptospreadedge.log

# Filtrer les erreurs
grep "ERROR" logs/arbitrage.log
```

## Intégration avec l'application principale

### Démarrage via start.py

```bash
# Démarrer l'application complète avec arbitrage
python start.py run dev

# Vérifier le statut
python start.py status
```

### Configuration dans main.py

L'arbitrage est automatiquement activé si `ARBITRAGE_ENABLED=true` dans l'environnement.

## Sécurité

### Bonnes pratiques

1. **Utiliser le sandbox** pour les tests
2. **Limiter les montants** en production
3. **Surveiller les logs** régulièrement
4. **Configurer les alertes** de risque
5. **Sauvegarder les configurations**

### Gestion des clés API

- Stocker dans des variables d'environnement
- Utiliser des clés avec permissions limitées
- Activer l'authentification 2FA
- Surveiller l'utilisation

## Performance

### Optimisations

- **Cache des prix** pour réduire les requêtes
- **Connexions WebSocket** pour les données temps réel
- **Exécution parallèle** des ordres
- **Filtrage intelligent** des opportunités

### Métriques

- Latence de détection : <2 secondes
- Temps d'exécution : <30 secondes
- Taux de succès : >95%
- Uptime : >99%

## Support

Pour toute question ou problème :

1. Consulter les logs
2. Vérifier la configuration
3. Tester avec le sandbox
4. Ouvrir une issue sur GitHub

## Exemples d'utilisation

### Test complet du système

```bash
# 1. Tester tous les composants
python scripts/arbitrage/test_arbitrage_system.py

# 2. Voir la démonstration
python scripts/arbitrage/demo_arbitrage.py

# 3. Test rapide
python scripts/arbitrage/quick_start.py

# 4. Démarrage complet
python scripts/arbitrage/start_arbitrage.py
```

### Configuration personnalisée

```bash
# Exporter les variables d'environnement
export ARBITRAGE_SYMBOLS="BTC/USDT,ETH/USDT"
export ARBITRAGE_EXCHANGES="binance,okx"
export MIN_SPREAD_PERCENTAGE=0.002

# Démarrer avec la configuration personnalisée
python scripts/arbitrage/start_arbitrage.py
```

### Monitoring en production

```bash
# Démarrer le système
python scripts/arbitrage/start_arbitrage.py &

# Surveiller les logs
tail -f logs/arbitrage.log

# Vérifier le statut
python start.py status
```