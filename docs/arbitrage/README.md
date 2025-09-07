# Système d'Arbitrage CryptoSpreadEdge

## Vue d'ensemble

Le système d'arbitrage de CryptoSpreadEdge est conçu pour détecter et exécuter automatiquement des opportunités d'arbitrage entre différentes plateformes de trading de cryptomonnaies. Il surveille les prix en temps réel, calcule les profits potentiels et exécute les trades de manière optimale.

## Fonctionnalités

- **Surveillance des prix en temps réel** sur 25+ plateformes
- **Détection automatique** des opportunités d'arbitrage
- **Calcul de profit** avec prise en compte des frais
- **Gestion des risques** avancée
- **Exécution optimisée** des ordres
- **Monitoring complet** des performances

## Architecture

### Composants principaux

1. **ArbitrageEngine** - Cœur du système
2. **PriceMonitor** - Surveillance des prix
3. **ExecutionEngine** - Exécution des ordres
4. **RiskManager** - Gestion des risques
5. **ProfitCalculator** - Calcul des profits

### Flux de données

```
Prix des exchanges → PriceMonitor → ArbitrageEngine → RiskManager
                                                      ↓
ProfitCalculator ← ExecutionEngine ← Opportunités validées
```

## Installation et Configuration

### Prérequis

- Python 3.11+
- Clés API des exchanges (optionnel pour les tests)
- Redis (pour le cache)
- InfluxDB (pour les métriques)

### Configuration

1. **Copier la configuration d'exemple** :
```bash
cp config/arbitrage_config.py.example config/arbitrage_config.py
```

2. **Configurer les exchanges** :
```python
# Dans config/arbitrage_config.py
EXCHANGE_CONFIGS = {
    "binance": ExchangeConfig(
        enabled=True,
        sandbox=True,  # Utiliser le sandbox pour les tests
        api_key="votre_cle_api",
        secret_key="votre_secret"
    )
}
```

3. **Ajuster les paramètres** :
```python
DEFAULT_ARBITRAGE_CONFIG = ArbitrageConfig(
    min_spread_percentage=0.001,  # 0.1% minimum
    max_spread_percentage=0.05,   # 5% maximum
    min_volume=0.01,              # Volume minimum
    max_order_size=1000.0         # Taille max des ordres
)
```

## Utilisation

### Démarrage rapide

```bash
# Démarrer le système d'arbitrage
python scripts/arbitrage/start_arbitrage.py

# Tester le système
python scripts/arbitrage/test_arbitrage_system.py

# Démarrer l'application complète
python start.py run dev
```

### Scripts disponibles

- `start_arbitrage.py` - Démarre uniquement le système d'arbitrage
- `test_arbitrage_system.py` - Lance les tests du système
- `start.py` - Démarre l'application complète avec arbitrage

## Configuration avancée

### Paramètres de détection

```python
# Seuils de détection
min_spread_percentage = 0.001    # Spread minimum (0.1%)
max_spread_percentage = 0.05     # Spread maximum (5%)
min_volume = 0.01                # Volume minimum
min_confidence = 0.8             # Confiance minimum (80%)
max_risk_score = 0.7             # Score de risque maximum (70%)
```

### Gestion des risques

```python
# Limites de risque
max_position_size = 10000.0      # Position max (USD)
max_daily_loss = 1000.0          # Perte quotidienne max (USD)
max_daily_trades = 100           # Nombre max de trades/jour
```

### Exchanges supportés

- **Tier 1** : Binance, OKX, Coinbase, Kraken
- **Tier 2** : Bybit, Bitget, Gate.io, Huobi, KuCoin
- **Tier 3** : Bitfinex, Bitstamp, Gemini, Bittrex

## Monitoring et Alertes

### Métriques surveillées

- Nombre d'opportunités détectées
- Taux d'exécution
- Profit net
- Temps d'exécution moyen
- Alertes de risque

### Logs

Les logs sont stockés dans `logs/arbitrage.log` avec rotation automatique.

### Alertes

- Changements de prix significatifs (>5%)
- Pics de volume (>2x la moyenne)
- Dépassement des limites de risque
- Erreurs d'exécution

## API et Intégration

### Statut du système

```python
from src.arbitrage.arbitrage_engine import arbitrage_engine

# Obtenir les statistiques
stats = arbitrage_engine.get_statistics()
print(f"Opportunités trouvées: {stats['opportunities_found']}")
print(f"Profit net: {stats['net_profit']:.2f} USD")
```

### Configuration dynamique

```python
# Modifier les paramètres en cours d'exécution
arbitrage_engine.min_spread_percentage = 0.002  # 0.2%
arbitrage_engine.max_risk_score = 0.5           # 50%
```

## Sécurité

### Bonnes pratiques

1. **Utiliser le sandbox** pour les tests
2. **Limiter les montants** en mode production
3. **Surveiller les logs** régulièrement
4. **Configurer les alertes** de risque
5. **Sauvegarder les configurations**

### Gestion des clés API

- Stocker les clés dans des variables d'environnement
- Utiliser des clés avec permissions limitées
- Activer l'authentification 2FA sur les exchanges
- Surveiller l'utilisation des clés

## Dépannage

### Problèmes courants

1. **Aucune opportunité détectée**
   - Vérifier la connectivité aux exchanges
   - Ajuster les seuils de détection
   - Vérifier les symboles surveillés

2. **Erreurs d'exécution**
   - Vérifier les clés API
   - Contrôler les limites de trading
   - Vérifier la liquidité

3. **Performance dégradée**
   - Réduire la fréquence de scan
   - Optimiser les connexions
   - Surveiller l'utilisation mémoire

### Logs utiles

```bash
# Surveiller les logs en temps réel
tail -f logs/arbitrage.log

# Filtrer les erreurs
grep "ERROR" logs/arbitrage.log

# Voir les opportunités détectées
grep "opportunity" logs/arbitrage.log
```

## Performance

### Optimisations

- **Cache des prix** pour réduire les requêtes
- **Connexions WebSocket** pour les données temps réel
- **Exécution parallèle** des ordres
- **Filtrage intelligent** des opportunités

### Métriques de performance

- Latence de détection : <2 secondes
- Temps d'exécution : <30 secondes
- Taux de succès : >95%
- Uptime : >99%

## Évolutions futures

- **Arbitrage cross-chain** (blockchain)
- **Machine Learning** pour la prédiction
- **Interface web** pour le monitoring
- **API REST** pour l'intégration
- **Support des DEX** (Uniswap, etc.)

## Support

Pour toute question ou problème :

1. Consulter la documentation
2. Vérifier les logs
3. Tester avec le sandbox
4. Ouvrir une issue sur GitHub

## Avertissement

Le trading de cryptomonnaies comporte des risques élevés. Ce système est fourni à des fins éducatives et de recherche. Utilisez-le à vos propres risques et avec des montants que vous pouvez vous permettre de perdre.