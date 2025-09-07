"""
Configuration du système d'arbitrage CryptoSpreadEdge
"""

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class ArbitrageConfig:
    """Configuration principale de l'arbitrage"""
    
    # Symboles à surveiller
    symbols: List[str] = None
    
    # Exchanges à utiliser
    exchanges: List[str] = None
    
    # Paramètres de détection
    min_spread_percentage: float = 0.001  # 0.1% minimum
    max_spread_percentage: float = 0.05   # 5% maximum
    min_volume: float = 0.01              # Volume minimum
    min_confidence: float = 0.8           # Confiance minimum
    max_risk_score: float = 0.7           # Score de risque maximum
    
    # Paramètres d'exécution
    max_execution_time: float = 30.0      # secondes
    retry_attempts: int = 3
    retry_delay: float = 1.0              # secondes
    max_order_size: float = 10000.0       # USD
    
    # Paramètres de monitoring
    price_update_interval: float = 1.0    # secondes
    opportunity_scan_interval: float = 2.0  # secondes
    performance_report_interval: float = 30.0  # secondes
    
    # Limites de risque
    max_position_size: float = 10000.0    # USD
    max_daily_loss: float = 1000.0        # USD
    max_daily_trades: int = 100
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = [
                "BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", 
                "DOT/USDT", "LINK/USDT", "LTC/USDT", "BCH/USDT", 
                "XRP/USDT", "EOS/USDT"
            ]
        
        if self.exchanges is None:
            self.exchanges = [
                "binance", "okx", "bybit", "bitget", "gateio", 
                "huobi", "kucoin", "coinbase", "kraken"
            ]


@dataclass
class ExchangeConfig:
    """Configuration d'un exchange"""
    name: str
    enabled: bool = True
    sandbox: bool = True
    api_key: str = ""
    secret_key: str = ""
    passphrase: str = ""  # Pour OKX
    rate_limit: int = 1200
    priority: int = 1  # 1 = haute priorité, 3 = basse priorité


# Configuration par défaut
DEFAULT_ARBITRAGE_CONFIG = ArbitrageConfig()

# Configuration des exchanges
EXCHANGE_CONFIGS = {
    "binance": ExchangeConfig(
        name="Binance",
        enabled=True,
        sandbox=True,
        rate_limit=1200,
        priority=1
    ),
    "okx": ExchangeConfig(
        name="OKX",
        enabled=True,
        sandbox=True,
        rate_limit=600,
        priority=1
    ),
    "bybit": ExchangeConfig(
        name="Bybit",
        enabled=True,
        sandbox=True,
        rate_limit=600,
        priority=2
    ),
    "bitget": ExchangeConfig(
        name="Bitget",
        enabled=True,
        sandbox=True,
        rate_limit=600,
        priority=2
    ),
    "gateio": ExchangeConfig(
        name="Gate.io",
        enabled=True,
        sandbox=True,
        rate_limit=600,
        priority=2
    ),
    "huobi": ExchangeConfig(
        name="Huobi",
        enabled=True,
        sandbox=True,
        rate_limit=600,
        priority=2
    ),
    "kucoin": ExchangeConfig(
        name="KuCoin",
        enabled=True,
        sandbox=True,
        rate_limit=600,
        priority=2
    ),
    "coinbase": ExchangeConfig(
        name="Coinbase Pro",
        enabled=True,
        sandbox=True,
        rate_limit=10,
        priority=3
    ),
    "kraken": ExchangeConfig(
        name="Kraken",
        enabled=True,
        sandbox=True,
        rate_limit=15,
        priority=3
    )
}

# Configuration des frais par exchange
EXCHANGE_FEES = {
    "binance": {"maker": 0.001, "taker": 0.001},
    "okx": {"maker": 0.0008, "taker": 0.001},
    "bybit": {"maker": 0.001, "taker": 0.001},
    "bitget": {"maker": 0.001, "taker": 0.001},
    "gateio": {"maker": 0.002, "taker": 0.002},
    "huobi": {"maker": 0.002, "taker": 0.002},
    "kucoin": {"maker": 0.001, "taker": 0.001},
    "coinbase": {"maker": 0.005, "taker": 0.005},
    "kraken": {"maker": 0.0016, "taker": 0.0026}
}

# Configuration des alertes
ALERT_CONFIG = {
    "price_change_threshold": 0.05,  # 5%
    "volume_spike_threshold": 2.0,   # 2x le volume moyen
    "max_alerts_per_minute": 10,
    "alert_retention_hours": 24
}

# Configuration des logs
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "logs/arbitrage.log",
    "max_size_mb": 100,
    "backup_count": 5
}


def get_arbitrage_config() -> ArbitrageConfig:
    """Retourne la configuration d'arbitrage"""
    return DEFAULT_ARBITRAGE_CONFIG


def get_exchange_config(exchange_id: str) -> ExchangeConfig:
    """Retourne la configuration d'un exchange"""
    return EXCHANGE_CONFIGS.get(exchange_id, ExchangeConfig(name=exchange_id))


def get_enabled_exchanges() -> List[str]:
    """Retourne la liste des exchanges activés"""
    return [
        exchange_id for exchange_id, config in EXCHANGE_CONFIGS.items()
        if config.enabled
    ]


def get_exchange_fees(exchange_id: str) -> Dict[str, float]:
    """Retourne les frais d'un exchange"""
    return EXCHANGE_FEES.get(exchange_id, {"maker": 0.001, "taker": 0.001})


def validate_config() -> bool:
    """Valide la configuration"""
    try:
        config = get_arbitrage_config()
        
        # Vérifier les paramètres de base
        if config.min_spread_percentage <= 0:
            return False
        if config.max_spread_percentage <= config.min_spread_percentage:
            return False
        if config.min_volume <= 0:
            return False
        if config.min_confidence <= 0 or config.min_confidence > 1:
            return False
        if config.max_risk_score <= 0 or config.max_risk_score > 1:
            return False
        
        # Vérifier qu'il y a au moins un exchange activé
        enabled_exchanges = get_enabled_exchanges()
        if not enabled_exchanges:
            return False
        
        # Vérifier qu'il y a au moins un symbole
        if not config.symbols:
            return False
        
        return True
    
    except Exception:
        return False


if __name__ == "__main__":
    # Test de la configuration
    print("Configuration d'arbitrage:")
    config = get_arbitrage_config()
    print(f"Symboles: {config.symbols}")
    print(f"Exchanges: {config.exchanges}")
    print(f"Spread min: {config.min_spread_percentage:.3%}")
    print(f"Spread max: {config.max_spread_percentage:.3%}")
    
    print("\nExchanges activés:")
    for exchange_id in get_enabled_exchanges():
        exchange_config = get_exchange_config(exchange_id)
        fees = get_exchange_fees(exchange_id)
        print(f"  {exchange_id}: {exchange_config.name} (frais: {fees['maker']:.3%}/{fees['taker']:.3%})")
    
    print(f"\nConfiguration valide: {validate_config()}")