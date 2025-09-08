"""
Configuration avancée des plateformes d'échange
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime


class PlatformType(Enum):
    """Types de plateformes"""
    CENTRALIZED = "centralized"
    DECENTRALIZED = "decentralized"
    HYBRID = "hybrid"


class TradingType(Enum):
    """Types de trading supportés"""
    SPOT = "spot"
    FUTURES = "futures"
    MARGIN = "margin"
    OPTIONS = "options"
    PERPETUAL = "perpetual"


class OrderType(Enum):
    """Types d'ordres supportés"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    OCO = "oco"  # One-Cancels-Other
    ICEBERG = "iceberg"
    TWAP = "twap"  # Time-Weighted Average Price


@dataclass
class TradingFees:
    """Structure des frais de trading"""
    maker: float
    taker: float
    withdrawal: Dict[str, float]  # Par devise
    deposit: Dict[str, float]  # Par devise
    minimum_fee: float = 0.0
    fee_tier: str = "default"


@dataclass
class TradingLimits:
    """Structure des limites de trading"""
    min_order_size: float
    max_order_size: float
    min_price: float
    max_price: float
    min_quantity: float
    max_quantity: float
    price_precision: int
    quantity_precision: int
    daily_trading_limit: Optional[float] = None
    monthly_trading_limit: Optional[float] = None


@dataclass
class WithdrawalLimits:
    """Structure des limites de retrait"""
    min_amount: float
    max_amount: float
    daily_limit: float
    monthly_limit: float
    kyc_required: bool = True
    verification_level: str = "basic"


@dataclass
class APIEndpoints:
    """Structure des endpoints API"""
    base_url: str
    sandbox_url: str
    websocket_url: str
    rest_endpoints: Dict[str, str]
    websocket_endpoints: Dict[str, str]


@dataclass
class SecurityFeatures:
    """Structure des fonctionnalités de sécurité"""
    ip_whitelist: bool
    api_key_permissions: bool
    two_factor_auth: bool
    withdrawal_whitelist: bool
    trading_password: bool
    rate_limiting: bool
    request_signing: bool


@dataclass
class PlatformConfig:
    """Configuration complète d'une plateforme"""
    name: str
    display_name: str
    platform_type: PlatformType
    trading_types: List[TradingType]
    supported_order_types: List[OrderType]
    supported_pairs: List[str]
    trading_fees: TradingFees
    trading_limits: TradingLimits
    withdrawal_limits: WithdrawalLimits
    api_endpoints: APIEndpoints
    security_features: SecurityFeatures
    countries: List[str]
    is_regulated: bool
    regulation_authorities: List[str]
    kyc_required: bool
    features: List[str]
    metadata: Dict[str, Any]


class PlatformConfigManager:
    """Gestionnaire des configurations de plateformes"""
    
    def __init__(self):
        self.configs: Dict[str, PlatformConfig] = {}
        self._load_default_configs()
    
    def _load_default_configs(self):
        """Charge les configurations par défaut des plateformes"""
        
        # Binance
        binance_config = PlatformConfig(
            name="binance",
            display_name="Binance",
            platform_type=PlatformType.CENTRALIZED,
            trading_types=[TradingType.SPOT, TradingType.FUTURES, TradingType.MARGIN, TradingType.OPTIONS],
            supported_order_types=[OrderType.MARKET, OrderType.LIMIT, OrderType.STOP, OrderType.STOP_LIMIT, OrderType.OCO],
            supported_pairs=["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "DOTUSDT"],
            trading_fees=TradingFees(
                maker=0.001,
                taker=0.001,
                withdrawal={"BTC": 0.0005, "ETH": 0.01, "USDT": 1.0},
                deposit={"BTC": 0.0, "ETH": 0.0, "USDT": 0.0},
                minimum_fee=0.0,
                fee_tier="VIP0"
            ),
            trading_limits=TradingLimits(
                min_order_size=10.0,
                max_order_size=1000000.0,
                min_price=0.00000001,
                max_price=1000000.0,
                min_quantity=0.00001,
                max_quantity=1000000.0,
                price_precision=8,
                quantity_precision=8,
                daily_trading_limit=1000000.0,
                monthly_trading_limit=10000000.0
            ),
            withdrawal_limits=WithdrawalLimits(
                min_amount=0.001,
                max_amount=100000.0,
                daily_limit=100000.0,
                monthly_limit=1000000.0,
                kyc_required=True,
                verification_level="basic"
            ),
            api_endpoints=APIEndpoints(
                base_url="https://api.binance.com",
                sandbox_url="https://testnet.binance.vision",
                websocket_url="wss://stream.binance.com:9443",
                rest_endpoints={
                    "ticker": "/api/v3/ticker/24hr",
                    "orderbook": "/api/v3/depth",
                    "trades": "/api/v3/trades",
                    "klines": "/api/v3/klines",
                    "account": "/api/v3/account",
                    "order": "/api/v3/order",
                    "open_orders": "/api/v3/openOrders"
                },
                websocket_endpoints={
                    "ticker": "!ticker@arr",
                    "orderbook": "{symbol}@depth",
                    "trades": "{symbol}@trade",
                    "klines": "{symbol}@kline_{interval}"
                }
            ),
            security_features=SecurityFeatures(
                ip_whitelist=True,
                api_key_permissions=True,
                two_factor_auth=True,
                withdrawal_whitelist=True,
                trading_password=False,
                rate_limiting=True,
                request_signing=True
            ),
            countries=["US", "EU", "ASIA"],
            is_regulated=True,
            regulation_authorities=["FCA", "MAS"],
            kyc_required=True,
            features=["spot", "futures", "margin", "options", "staking", "lending"],
            metadata={
                "founding_year": 2017,
                "headquarters": "Malta",
                "ceo": "Changpeng Zhao",
                "website": "https://binance.com"
            }
        )
        
        # Coinbase Pro
        coinbase_config = PlatformConfig(
            name="coinbase",
            display_name="Coinbase Pro",
            platform_type=PlatformType.CENTRALIZED,
            trading_types=[TradingType.SPOT, TradingType.MARGIN],
            supported_order_types=[OrderType.MARKET, OrderType.LIMIT, OrderType.STOP, OrderType.STOP_LIMIT],
            supported_pairs=["BTC-USD", "ETH-USD", "LTC-USD", "BCH-USD", "ETC-USD"],
            trading_fees=TradingFees(
                maker=0.005,
                taker=0.005,
                withdrawal={"BTC": 0.0005, "ETH": 0.01, "USD": 0.0},
                deposit={"BTC": 0.0, "ETH": 0.0, "USD": 0.0},
                minimum_fee=0.0,
                fee_tier="default"
            ),
            trading_limits=TradingLimits(
                min_order_size=1.0,
                max_order_size=1000000.0,
                min_price=0.01,
                max_price=1000000.0,
                min_quantity=0.00001,
                max_quantity=1000000.0,
                price_precision=2,
                quantity_precision=8,
                daily_trading_limit=50000.0,
                monthly_trading_limit=500000.0
            ),
            withdrawal_limits=WithdrawalLimits(
                min_amount=0.001,
                max_amount=100000.0,
                daily_limit=10000.0,
                monthly_limit=100000.0,
                kyc_required=True,
                verification_level="intermediate"
            ),
            api_endpoints=APIEndpoints(
                base_url="https://api.pro.coinbase.com",
                sandbox_url="https://api-public.sandbox.pro.coinbase.com",
                websocket_url="wss://ws-feed.pro.coinbase.com",
                rest_endpoints={
                    "ticker": "/products/{product_id}/ticker",
                    "orderbook": "/products/{product_id}/book",
                    "trades": "/products/{product_id}/trades",
                    "klines": "/products/{product_id}/candles",
                    "account": "/accounts",
                    "order": "/orders",
                    "open_orders": "/orders"
                },
                websocket_endpoints={
                    "ticker": "ticker",
                    "orderbook": "level2",
                    "trades": "matches",
                    "klines": "candles"
                }
            ),
            security_features=SecurityFeatures(
                ip_whitelist=True,
                api_key_permissions=True,
                two_factor_auth=True,
                withdrawal_whitelist=True,
                trading_password=True,
                rate_limiting=True,
                request_signing=True
            ),
            countries=["US", "EU", "UK"],
            is_regulated=True,
            regulation_authorities=["SEC", "FCA", "BaFin"],
            kyc_required=True,
            features=["spot", "margin", "staking", "institutional"],
            metadata={
                "founding_year": 2012,
                "headquarters": "San Francisco",
                "ceo": "Brian Armstrong",
                "website": "https://pro.coinbase.com"
            }
        )
        
        # Kraken
        kraken_config = PlatformConfig(
            name="kraken",
            display_name="Kraken",
            platform_type=PlatformType.CENTRALIZED,
            trading_types=[TradingType.SPOT, TradingType.FUTURES, TradingType.MARGIN],
            supported_order_types=[OrderType.MARKET, OrderType.LIMIT, OrderType.STOP, OrderType.STOP_LIMIT],
            supported_pairs=["XBTUSD", "ETHUSD", "LTCUSD", "BCHUSD", "ADAUSD"],
            trading_fees=TradingFees(
                maker=0.0016,
                taker=0.0026,
                withdrawal={"BTC": 0.0005, "ETH": 0.005, "USD": 5.0},
                deposit={"BTC": 0.0, "ETH": 0.0, "USD": 0.0},
                minimum_fee=0.0,
                fee_tier="default"
            ),
            trading_limits=TradingLimits(
                min_order_size=1.0,
                max_order_size=1000000.0,
                min_price=0.0001,
                max_price=1000000.0,
                min_quantity=0.00001,
                max_quantity=1000000.0,
                price_precision=4,
                quantity_precision=8,
                daily_trading_limit=100000.0,
                monthly_trading_limit=1000000.0
            ),
            withdrawal_limits=WithdrawalLimits(
                min_amount=0.001,
                max_amount=100000.0,
                daily_limit=10000.0,
                monthly_limit=100000.0,
                kyc_required=True,
                verification_level="intermediate"
            ),
            api_endpoints=APIEndpoints(
                base_url="https://api.kraken.com",
                sandbox_url="https://api-sandbox.kraken.com",
                websocket_url="wss://ws.kraken.com",
                rest_endpoints={
                    "ticker": "/0/public/Ticker",
                    "orderbook": "/0/public/Depth",
                    "trades": "/0/public/Trades",
                    "klines": "/0/public/OHLC",
                    "account": "/0/private/Balance",
                    "order": "/0/private/AddOrder",
                    "open_orders": "/0/private/OpenOrders"
                },
                websocket_endpoints={
                    "ticker": "ticker",
                    "orderbook": "book",
                    "trades": "trade",
                    "klines": "ohlc"
                }
            ),
            security_features=SecurityFeatures(
                ip_whitelist=True,
                api_key_permissions=True,
                two_factor_auth=True,
                withdrawal_whitelist=True,
                trading_password=False,
                rate_limiting=True,
                request_signing=True
            ),
            countries=["US", "EU", "UK", "CA"],
            is_regulated=True,
            regulation_authorities=["FCA", "FinCEN"],
            kyc_required=True,
            features=["spot", "futures", "margin", "staking", "institutional"],
            metadata={
                "founding_year": 2011,
                "headquarters": "San Francisco",
                "ceo": "Jesse Powell",
                "website": "https://kraken.com"
            }
        )
        
        # Bybit
        bybit_config = PlatformConfig(
            name="bybit",
            display_name="Bybit",
            platform_type=PlatformType.CENTRALIZED,
            trading_types=[TradingType.SPOT, TradingType.FUTURES, TradingType.PERPETUAL],
            supported_order_types=[OrderType.MARKET, OrderType.LIMIT, OrderType.STOP, OrderType.STOP_LIMIT],
            supported_pairs=["BTCUSDT", "ETHUSDT", "XRPUSDT", "ADAUSDT", "DOTUSDT"],
            trading_fees=TradingFees(
                maker=0.0001,
                taker=0.0006,
                withdrawal={"BTC": 0.0005, "ETH": 0.01, "USDT": 1.0},
                deposit={"BTC": 0.0, "ETH": 0.0, "USDT": 0.0},
                minimum_fee=0.0,
                fee_tier="VIP0"
            ),
            trading_limits=TradingLimits(
                min_order_size=5.0,
                max_order_size=1000000.0,
                min_price=0.00001,
                max_price=1000000.0,
                min_quantity=0.001,
                max_quantity=1000000.0,
                price_precision=5,
                quantity_precision=6,
                daily_trading_limit=1000000.0,
                monthly_trading_limit=10000000.0
            ),
            withdrawal_limits=WithdrawalLimits(
                min_amount=0.001,
                max_amount=100000.0,
                daily_limit=100000.0,
                monthly_limit=1000000.0,
                kyc_required=False,
                verification_level="basic"
            ),
            api_endpoints=APIEndpoints(
                base_url="https://api.bybit.com",
                sandbox_url="https://api-testnet.bybit.com",
                websocket_url="wss://stream.bybit.com",
                rest_endpoints={
                    "ticker": "/v2/public/tickers",
                    "orderbook": "/v2/public/orderBook/L2",
                    "trades": "/v2/public/trading-records",
                    "klines": "/v2/public/kline/list",
                    "account": "/v2/private/account/balance",
                    "order": "/v2/private/order/create",
                    "open_orders": "/v2/private/order/list"
                },
                websocket_endpoints={
                    "ticker": "tickers",
                    "orderbook": "orderBookL2_25",
                    "trades": "trade",
                    "klines": "klineV2"
                }
            ),
            security_features=SecurityFeatures(
                ip_whitelist=True,
                api_key_permissions=True,
                two_factor_auth=True,
                withdrawal_whitelist=True,
                trading_password=False,
                rate_limiting=True,
                request_signing=True
            ),
            countries=["US", "EU", "ASIA"],
            is_regulated=False,
            regulation_authorities=[],
            kyc_required=False,
            features=["spot", "futures", "perpetual", "options"],
            metadata={
                "founding_year": 2018,
                "headquarters": "Singapore",
                "ceo": "Ben Zhou",
                "website": "https://bybit.com"
            }
        )
        
        # Gate.io
        gateio_config = PlatformConfig(
            name="gateio",
            display_name="Gate.io",
            platform_type=PlatformType.CENTRALIZED,
            trading_types=[TradingType.SPOT, TradingType.FUTURES, TradingType.MARGIN, TradingType.PERPETUAL],
            supported_order_types=[OrderType.MARKET, OrderType.LIMIT, OrderType.STOP, OrderType.STOP_LIMIT],
            supported_pairs=["BTC_USDT", "ETH_USDT", "GT_USDT", "DOGE_USDT", "SHIB_USDT"],
            trading_fees=TradingFees(
                maker=0.002,
                taker=0.002,
                withdrawal={"BTC": 0.0005, "ETH": 0.01, "USDT": 1.0},
                deposit={"BTC": 0.0, "ETH": 0.0, "USDT": 0.0},
                minimum_fee=0.0,
                fee_tier="default"
            ),
            trading_limits=TradingLimits(
                min_order_size=1.0,
                max_order_size=1000000.0,
                min_price=0.00000001,
                max_price=1000000.0,
                min_quantity=0.00001,
                max_quantity=1000000.0,
                price_precision=8,
                quantity_precision=8,
                daily_trading_limit=1000000.0,
                monthly_trading_limit=10000000.0
            ),
            withdrawal_limits=WithdrawalLimits(
                min_amount=0.001,
                max_amount=100000.0,
                daily_limit=100000.0,
                monthly_limit=1000000.0,
                kyc_required=False,
                verification_level="basic"
            ),
            api_endpoints=APIEndpoints(
                base_url="https://api.gateio.ws",
                sandbox_url="https://fx-api-testnet.gateio.ws",
                websocket_url="wss://api.gateio.ws/ws/v4/",
                rest_endpoints={
                    "ticker": "/api/v4/spot/tickers",
                    "orderbook": "/api/v4/spot/order_book",
                    "trades": "/api/v4/spot/trades",
                    "klines": "/api/v4/spot/candlesticks",
                    "account": "/api/v4/spot/accounts",
                    "order": "/api/v4/spot/orders",
                    "open_orders": "/api/v4/spot/open_orders"
                },
                websocket_endpoints={
                    "ticker": "spot.tickers",
                    "orderbook": "spot.order_book",
                    "trades": "spot.trades",
                    "klines": "spot.candlesticks"
                }
            ),
            security_features=SecurityFeatures(
                ip_whitelist=True,
                api_key_permissions=True,
                two_factor_auth=True,
                withdrawal_whitelist=True,
                trading_password=False,
                rate_limiting=True,
                request_signing=True
            ),
            countries=["US", "EU", "ASIA"],
            is_regulated=False,
            regulation_authorities=[],
            kyc_required=False,
            features=["spot", "futures", "margin", "perpetual", "options", "staking"],
            metadata={
                "founding_year": 2013,
                "headquarters": "Cayman Islands",
                "ceo": "Lin Han",
                "website": "https://gate.io"
            }
        )
        
        # OKX
        okx_config = PlatformConfig(
            name="okx",
            display_name="OKX",
            platform_type=PlatformType.CENTRALIZED,
            trading_types=[TradingType.SPOT, TradingType.FUTURES, TradingType.MARGIN, TradingType.PERPETUAL, TradingType.OPTIONS],
            supported_order_types=[OrderType.MARKET, OrderType.LIMIT, OrderType.STOP, OrderType.STOP_LIMIT, OrderType.OCO],
            supported_pairs=["BTC-USDT", "ETH-USDT", "OKB-USDT", "ADA-USDT", "DOT-USDT"],
            trading_fees=TradingFees(
                maker=0.0008,
                taker=0.001,
                withdrawal={"BTC": 0.0005, "ETH": 0.01, "USDT": 1.0},
                deposit={"BTC": 0.0, "ETH": 0.0, "USDT": 0.0},
                minimum_fee=0.0,
                fee_tier="VIP0"
            ),
            trading_limits=TradingLimits(
                min_order_size=5.0,
                max_order_size=1000000.0,
                min_price=0.00001,
                max_price=1000000.0,
                min_quantity=0.00001,
                max_quantity=1000000.0,
                price_precision=5,
                quantity_precision=8,
                daily_trading_limit=1000000.0,
                monthly_trading_limit=10000000.0
            ),
            withdrawal_limits=WithdrawalLimits(
                min_amount=0.001,
                max_amount=100000.0,
                daily_limit=100000.0,
                monthly_limit=1000000.0,
                kyc_required=True,
                verification_level="basic"
            ),
            api_endpoints=APIEndpoints(
                base_url="https://www.okx.com",
                sandbox_url="https://www.okx.com",
                websocket_url="wss://ws.okx.com:8443/ws/v5/public",
                rest_endpoints={
                    "ticker": "/api/v5/market/ticker",
                    "orderbook": "/api/v5/market/books",
                    "trades": "/api/v5/market/trades",
                    "klines": "/api/v5/market/candles",
                    "account": "/api/v5/account/balance",
                    "order": "/api/v5/trade/order",
                    "open_orders": "/api/v5/trade/orders-pending"
                },
                websocket_endpoints={
                    "ticker": "tickers",
                    "orderbook": "books",
                    "trades": "trades",
                    "klines": "candles"
                }
            ),
            security_features=SecurityFeatures(
                ip_whitelist=True,
                api_key_permissions=True,
                two_factor_auth=True,
                withdrawal_whitelist=True,
                trading_password=False,
                rate_limiting=True,
                request_signing=True
            ),
            countries=["US", "EU", "ASIA"],
            is_regulated=True,
            regulation_authorities=["FCA", "MAS"],
            kyc_required=True,
            features=["spot", "futures", "margin", "perpetual", "options", "staking", "defi"],
            metadata={
                "founding_year": 2017,
                "headquarters": "Malta",
                "ceo": "Jay Hao",
                "website": "https://okx.com"
            }
        )
        
        # Stockage des configurations
        self.configs = {
            "binance": binance_config,
            "coinbase": coinbase_config,
            "kraken": kraken_config,
            "bybit": bybit_config,
            "gateio": gateio_config,
            "okx": okx_config
        }
    
    def get_config(self, platform_name: str) -> Optional[PlatformConfig]:
        """Récupère la configuration d'une plateforme"""
        return self.configs.get(platform_name.lower())
    
    def get_all_configs(self) -> Dict[str, PlatformConfig]:
        """Récupère toutes les configurations"""
        return self.configs.copy()
    
    def get_platforms_by_type(self, platform_type: PlatformType) -> List[PlatformConfig]:
        """Récupère les plateformes par type"""
        return [config for config in self.configs.values() if config.platform_type == platform_type]
    
    def get_platforms_by_trading_type(self, trading_type: TradingType) -> List[PlatformConfig]:
        """Récupère les plateformes supportant un type de trading"""
        return [config for config in self.configs.values() if trading_type in config.trading_types]
    
    def get_platforms_by_country(self, country: str) -> List[PlatformConfig]:
        """Récupère les plateformes disponibles dans un pays"""
        return [config for config in self.configs.values() if country in config.countries]
    
    def get_platforms_by_feature(self, feature: str) -> List[PlatformConfig]:
        """Récupère les plateformes supportant une fonctionnalité"""
        return [config for config in self.configs.values() if feature in config.features]
    
    def add_custom_config(self, config: PlatformConfig):
        """Ajoute une configuration personnalisée"""
        self.configs[config.name.lower()] = config
    
    def update_config(self, platform_name: str, updates: Dict[str, Any]):
        """Met à jour une configuration existante"""
        if platform_name.lower() in self.configs:
            config = self.configs[platform_name.lower()]
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
    
    def export_config(self, platform_name: str) -> Dict[str, Any]:
        """Exporte une configuration en dictionnaire"""
        config = self.get_config(platform_name)
        if config:
            return asdict(config)
        return {}
    
    def import_config(self, platform_name: str, config_data: Dict[str, Any]):
        """Importe une configuration depuis un dictionnaire"""
        try:
            config = PlatformConfig(**config_data)
            self.configs[platform_name.lower()] = config
        except Exception as e:
            raise ValueError(f"Erreur import configuration {platform_name}: {e}")
    
    def validate_config(self, config: PlatformConfig) -> List[str]:
        """Valide une configuration et retourne les erreurs"""
        errors = []
        
        if not config.name:
            errors.append("Le nom de la plateforme est requis")
        
        if not config.api_endpoints.base_url:
            errors.append("L'URL de base de l'API est requise")
        
        if config.trading_fees.maker < 0 or config.trading_fees.taker < 0:
            errors.append("Les frais de trading doivent être positifs")
        
        if config.trading_limits.min_order_size <= 0:
            errors.append("La taille minimale d'ordre doit être positive")
        
        if config.trading_limits.max_order_size <= config.trading_limits.min_order_size:
            errors.append("La taille maximale d'ordre doit être supérieure à la minimale")
        
        return errors


# Instance globale
platform_config_manager = PlatformConfigManager()