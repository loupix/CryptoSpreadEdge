"""
Configuration des plateformes pour CryptoSpreadEdge
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class PlatformType(Enum):
    """Types de plateformes"""
    EXCHANGE = "exchange"
    DEX = "dex"
    DATA_SOURCE = "data_source"
    AGGREGATOR = "aggregator"


class PlatformTier(Enum):
    """Niveaux de plateformes"""
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"
    EMERGING = "emerging"


@dataclass
class PlatformConfig:
    """Configuration d'une plateforme"""
    name: str
    platform_type: PlatformType
    tier: PlatformTier
    enabled: bool
    priority: int  # 1-10, plus élevé = plus prioritaire
    api_required: bool
    rate_limit: int  # requêtes par minute
    timeout: int  # timeout en secondes
    retry_attempts: int
    features: List[str]
    supported_symbols: List[str]
    supported_timeframes: List[str]
    min_trade_amount: float
    max_trade_amount: float
    fees: Dict[str, float]
    regions: List[str]
    languages: List[str]
    api_docs: str
    status_page: str
    support_contact: str


# Configuration des exchanges
EXCHANGE_CONFIGS = {
    "binance": PlatformConfig(
        name="Binance",
        platform_type=PlatformType.EXCHANGE,
        tier=PlatformTier.TIER_1,
        enabled=True,
        priority=10,
        api_required=True,
        rate_limit=1200,
        timeout=30,
        retry_attempts=3,
        features=["spot", "futures", "margin", "options", "staking", "lending"],
        supported_symbols=["BTC", "ETH", "BNB", "ADA", "DOT", "LINK", "LTC", "BCH", "XRP", "EOS"],
        supported_timeframes=["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"],
        min_trade_amount=0.00001,
        max_trade_amount=1000000,
        fees={"maker": 0.001, "taker": 0.001},
        regions=["global"],
        languages=["en", "zh", "ko", "ja", "ru", "tr", "es", "fr", "de", "it"],
        api_docs="https://binance-docs.github.io/apidocs/",
        status_page="https://www.binance.com/en/status",
        support_contact="https://www.binance.com/en/support"
    ),
    
    "coinbase": PlatformConfig(
        name="Coinbase Pro",
        platform_type=PlatformType.EXCHANGE,
        tier=PlatformTier.TIER_1,
        enabled=True,
        priority=9,
        api_required=True,
        rate_limit=10,
        timeout=30,
        retry_attempts=3,
        features=["spot", "margin", "staking", "fiat_onramp"],
        supported_symbols=["BTC", "ETH", "LTC", "BCH", "ETC", "ZRX", "BAT", "REP", "ZEC", "XRP"],
        supported_timeframes=["1m", "5m", "15m", "1h", "6h", "1d"],
        min_trade_amount=0.01,
        max_trade_amount=100000,
        fees={"maker": 0.005, "taker": 0.005},
        regions=["us", "eu", "uk"],
        languages=["en"],
        api_docs="https://docs.pro.coinbase.com/",
        status_page="https://status.coinbase.com/",
        support_contact="https://help.coinbase.com/"
    ),
    
    "kraken": PlatformConfig(
        name="Kraken",
        platform_type=PlatformType.EXCHANGE,
        tier=PlatformTier.TIER_1,
        enabled=True,
        priority=8,
        api_required=True,
        rate_limit=1,
        timeout=30,
        retry_attempts=3,
        features=["spot", "futures", "margin", "staking", "fiat_onramp"],
        supported_symbols=["BTC", "ETH", "LTC", "BCH", "ETC", "XRP", "ADA", "DOT", "LINK", "UNI"],
        supported_timeframes=["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"],
        min_trade_amount=0.0001,
        max_trade_amount=500000,
        fees={"maker": 0.0016, "taker": 0.0026},
        regions=["us", "eu", "ca", "jp"],
        languages=["en", "de", "fr", "es", "it", "pt", "ru", "ja", "ko", "zh"],
        api_docs="https://www.kraken.com/features/api",
        status_page="https://status.kraken.com/",
        support_contact="https://support.kraken.com/"
    ),
    
    "okx": PlatformConfig(
        name="OKX",
        platform_type=PlatformType.EXCHANGE,
        tier=PlatformTier.TIER_1,
        enabled=True,
        priority=9,
        api_required=True,
        rate_limit=20,
        timeout=30,
        retry_attempts=3,
        features=["spot", "futures", "options", "margin", "staking", "defi"],
        supported_symbols=["BTC", "ETH", "OKB", "ADA", "DOT", "LINK", "LTC", "BCH", "XRP", "EOS"],
        supported_timeframes=["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"],
        min_trade_amount=0.00001,
        max_trade_amount=1000000,
        fees={"maker": 0.0008, "taker": 0.001},
        regions=["global"],
        languages=["en", "zh", "ko", "ja", "ru", "tr", "es", "fr", "de", "it"],
        api_docs="https://www.okx.com/docs-v5/en/",
        status_page="https://status.okx.com/",
        support_contact="https://support.okx.com/"
    ),
    
    "bybit": PlatformConfig(
        name="Bybit",
        platform_type=PlatformType.EXCHANGE,
        tier=PlatformTier.TIER_2,
        enabled=True,
        priority=7,
        api_required=True,
        rate_limit=120,
        timeout=30,
        retry_attempts=3,
        features=["spot", "futures", "options", "copy_trading"],
        supported_symbols=["BTC", "ETH", "ADA", "DOT", "LINK", "LTC", "BCH", "XRP", "EOS", "TRX"],
        supported_timeframes=["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"],
        min_trade_amount=0.00001,
        max_trade_amount=1000000,
        fees={"maker": 0.001, "taker": 0.001},
        regions=["global"],
        languages=["en", "zh", "ko", "ja", "ru", "tr", "es", "fr", "de", "it"],
        api_docs="https://bybit-exchange.github.io/docs/",
        status_page="https://status.bybit.com/",
        support_contact="https://www.bybit.com/support"
    ),
    
    "bitget": PlatformConfig(
        name="Bitget",
        platform_type=PlatformType.EXCHANGE,
        tier=PlatformTier.TIER_2,
        enabled=True,
        priority=6,
        api_required=True,
        rate_limit=20,
        timeout=30,
        retry_attempts=3,
        features=["spot", "futures", "margin", "copy_trading"],
        supported_symbols=["BTC", "ETH", "ADA", "DOT", "LINK", "LTC", "BCH", "XRP", "EOS", "TRX"],
        supported_timeframes=["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"],
        min_trade_amount=0.00001,
        max_trade_amount=100000,
        fees={"maker": 0.001, "taker": 0.001},
        regions=["global"],
        languages=["en", "zh", "ko", "ja", "ru", "tr", "es", "fr", "de", "it"],
        api_docs="https://bitgetlimited.github.io/apidoc/en/spot/",
        status_page="https://status.bitget.com/",
        support_contact="https://www.bitget.com/support"
    ),
    
    "gateio": PlatformConfig(
        name="Gate.io",
        platform_type=PlatformType.EXCHANGE,
        tier=PlatformTier.TIER_2,
        enabled=True,
        priority=6,
        api_required=True,
        rate_limit=900,
        timeout=30,
        retry_attempts=3,
        features=["spot", "futures", "margin", "staking", "lending"],
        supported_symbols=["BTC", "ETH", "GT", "ADA", "DOT", "LINK", "LTC", "BCH", "XRP", "EOS"],
        supported_timeframes=["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"],
        min_trade_amount=0.00001,
        max_trade_amount=100000,
        fees={"maker": 0.002, "taker": 0.002},
        regions=["global"],
        languages=["en", "zh", "ko", "ja", "ru", "tr", "es", "fr", "de", "it"],
        api_docs="https://www.gate.io/docs/developers/apiv4/",
        status_page="https://status.gate.io/",
        support_contact="https://www.gate.io/support"
    ),
    
    "huobi": PlatformConfig(
        name="Huobi Global",
        platform_type=PlatformType.EXCHANGE,
        tier=PlatformTier.TIER_2,
        enabled=True,
        priority=6,
        api_required=True,
        rate_limit=100,
        timeout=30,
        retry_attempts=3,
        features=["spot", "futures", "margin", "staking", "mining"],
        supported_symbols=["BTC", "ETH", "HT", "ADA", "DOT", "LINK", "LTC", "BCH", "XRP", "EOS"],
        supported_timeframes=["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"],
        min_trade_amount=0.00001,
        max_trade_amount=100000,
        fees={"maker": 0.002, "taker": 0.002},
        regions=["global"],
        languages=["en", "zh", "ko", "ja", "ru", "tr", "es", "fr", "de", "it"],
        api_docs="https://huobiapi.github.io/docs/spot/v1/en/",
        status_page="https://status.huobi.com/",
        support_contact="https://www.huobi.com/support"
    ),
    
    "kucoin": PlatformConfig(
        name="KuCoin",
        platform_type=PlatformType.EXCHANGE,
        tier=PlatformTier.TIER_2,
        enabled=True,
        priority=7,
        api_required=True,
        rate_limit=1800,
        timeout=30,
        retry_attempts=3,
        features=["spot", "futures", "margin", "staking", "lending", "trading_bot"],
        supported_symbols=["BTC", "ETH", "KCS", "ADA", "DOT", "LINK", "LTC", "BCH", "XRP", "EOS"],
        supported_timeframes=["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"],
        min_trade_amount=0.00001,
        max_trade_amount=100000,
        fees={"maker": 0.001, "taker": 0.001},
        regions=["global"],
        languages=["en", "zh", "ko", "ja", "ru", "tr", "es", "fr", "de", "it"],
        api_docs="https://docs.kucoin.com/",
        status_page="https://status.kucoin.com/",
        support_contact="https://www.kucoin.com/support"
    ),
    
    "bitfinex": PlatformConfig(
        name="Bitfinex",
        platform_type=PlatformType.EXCHANGE,
        tier=PlatformTier.TIER_3,
        enabled=True,
        priority=5,
        api_required=True,
        rate_limit=30,
        timeout=30,
        retry_attempts=3,
        features=["spot", "margin", "lending"],
        supported_symbols=["BTC", "ETH", "LTC", "BCH", "ETC", "XRP", "ADA", "DOT", "LINK", "UNI"],
        supported_timeframes=["1m", "5m", "15m", "30m", "1h", "3h", "6h", "12h", "1d", "1w"],
        min_trade_amount=0.00001,
        max_trade_amount=100000,
        fees={"maker": 0.001, "taker": 0.002},
        regions=["global"],
        languages=["en"],
        api_docs="https://docs.bitfinex.com/",
        status_page="https://status.bitfinex.com/",
        support_contact="https://support.bitfinex.com/"
    ),
    
    "bitstamp": PlatformConfig(
        name="Bitstamp",
        platform_type=PlatformType.EXCHANGE,
        tier=PlatformTier.TIER_3,
        enabled=True,
        priority=4,
        api_required=True,
        rate_limit=600,
        timeout=30,
        retry_attempts=3,
        features=["spot", "fiat_onramp"],
        supported_symbols=["BTC", "ETH", "LTC", "BCH", "XRP", "ADA", "DOT", "LINK", "UNI", "AAVE"],
        supported_timeframes=["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d"],
        min_trade_amount=0.0001,
        max_trade_amount=10000,
        fees={"maker": 0.0025, "taker": 0.0025},
        regions=["eu", "us"],
        languages=["en"],
        api_docs="https://www.bitstamp.net/api/",
        status_page="https://status.bitstamp.net/",
        support_contact="https://www.bitstamp.net/support"
    ),
    
    "gemini": PlatformConfig(
        name="Gemini",
        platform_type=PlatformType.EXCHANGE,
        tier=PlatformTier.TIER_3,
        enabled=True,
        priority=4,
        api_required=True,
        rate_limit=600,
        timeout=30,
        retry_attempts=3,
        features=["spot", "staking", "fiat_onramp", "custody"],
        supported_symbols=["BTC", "ETH", "LTC", "BCH", "ETC", "ZRX", "BAT", "REP", "ZEC", "XRP"],
        supported_timeframes=["1m", "5m", "15m", "1h", "6h", "1d"],
        min_trade_amount=0.00001,
        max_trade_amount=50000,
        fees={"maker": 0.0025, "taker": 0.0025},
        regions=["us", "eu", "uk", "ca"],
        languages=["en"],
        api_docs="https://docs.gemini.com/rest-api/",
        status_page="https://status.gemini.com/",
        support_contact="https://support.gemini.com/"
    ),
    
    "bittrex": PlatformConfig(
        name="Bittrex",
        platform_type=PlatformType.EXCHANGE,
        tier=PlatformTier.TIER_3,
        enabled=True,
        priority=3,
        api_required=True,
        rate_limit=60,
        timeout=30,
        retry_attempts=3,
        features=["spot", "staking"],
        supported_symbols=["BTC", "ETH", "LTC", "BCH", "ETC", "XRP", "ADA", "DOT", "LINK", "UNI"],
        supported_timeframes=["1m", "5m", "15m", "30m", "1h", "6h", "1d"],
        min_trade_amount=0.00001,
        max_trade_amount=10000,
        fees={"maker": 0.0025, "taker": 0.0025},
        regions=["us"],
        languages=["en"],
        api_docs="https://bittrex.github.io/api/v3",
        status_page="https://status.bittrex.com/",
        support_contact="https://support.bittrex.com/"
    ),
    
    "mexc": PlatformConfig(
        name="MEXC Global",
        platform_type=PlatformType.EXCHANGE,
        tier=PlatformTier.EMERGING,
        enabled=True,
        priority=5,
        api_required=True,
        rate_limit=1200,
        timeout=30,
        retry_attempts=3,
        features=["spot", "futures", "staking", "new_listings"],
        supported_symbols=["BTC", "ETH", "MX", "ADA", "DOT", "LINK", "LTC", "BCH", "XRP", "EOS"],
        supported_timeframes=["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"],
        min_trade_amount=0.00001,
        max_trade_amount=100000,
        fees={"maker": 0.002, "taker": 0.002},
        regions=["global"],
        languages=["en", "zh", "ko", "ja", "ru", "tr", "es", "fr", "de", "it"],
        api_docs="https://mexcdevelop.github.io/apidocs/spot_v3_en/",
        status_page="https://status.mexc.com/",
        support_contact="https://www.mexc.com/support"
    ),
    
    "whitebit": PlatformConfig(
        name="WhiteBIT",
        platform_type=PlatformType.EXCHANGE,
        tier=PlatformTier.EMERGING,
        enabled=True,
        priority=4,
        api_required=True,
        rate_limit=600,
        timeout=30,
        retry_attempts=3,
        features=["spot", "futures", "staking", "fiat_onramp"],
        supported_symbols=["BTC", "ETH", "WBT", "ADA", "DOT", "LINK", "LTC", "BCH", "XRP", "EOS"],
        supported_timeframes=["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"],
        min_trade_amount=0.00001,
        max_trade_amount=50000,
        fees={"maker": 0.001, "taker": 0.001},
        regions=["global"],
        languages=["en", "ru", "uk", "tr", "es", "fr", "de", "it"],
        api_docs="https://whitebit-exchange.github.io/api-docs/",
        status_page="https://status.whitebit.com/",
        support_contact="https://whitebit.com/support"
    ),
    
    "phemex": PlatformConfig(
        name="Phemex",
        platform_type=PlatformType.EXCHANGE,
        tier=PlatformTier.EMERGING,
        enabled=True,
        priority=4,
        api_required=True,
        rate_limit=120,
        timeout=30,
        retry_attempts=3,
        features=["spot", "futures", "copy_trading"],
        supported_symbols=["BTC", "ETH", "ADA", "DOT", "LINK", "LTC", "BCH", "XRP", "EOS", "TRX"],
        supported_timeframes=["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"],
        min_trade_amount=0.00001,
        max_trade_amount=100000,
        fees={"maker": 0.0001, "taker": 0.0006},
        regions=["global"],
        languages=["en", "zh", "ko", "ja", "ru", "tr", "es", "fr", "de", "it"],
        api_docs="https://phemex.com/api-docs",
        status_page="https://status.phemex.com/",
        support_contact="https://phemex.com/support"
    )
}

# Configuration des DEX
DEX_CONFIGS = {
    "uniswap": PlatformConfig(
        name="Uniswap",
        platform_type=PlatformType.DEX,
        tier=PlatformTier.TIER_2,
        enabled=True,
        priority=8,
        api_required=False,
        rate_limit=0,  # Pas de limite
        timeout=30,
        retry_attempts=3,
        features=["dex", "liquidity_pools", "farming", "governance"],
        supported_symbols=["ETH", "USDC", "USDT", "WBTC", "DAI", "UNI", "LINK", "AAVE", "COMP", "MKR"],
        supported_timeframes=["1m", "5m", "15m", "1h", "4h", "1d"],
        min_trade_amount=0.00001,
        max_trade_amount=1000000,
        fees={"maker": 0.003, "taker": 0.003},
        regions=["global"],
        languages=["en"],
        api_docs="https://docs.uniswap.org/",
        status_page="https://status.uniswap.org/",
        support_contact="https://help.uniswap.org/"
    ),
    
    "pancakeswap": PlatformConfig(
        name="PancakeSwap",
        platform_type=PlatformType.DEX,
        tier=PlatformTier.TIER_2,
        enabled=True,
        priority=7,
        api_required=False,
        rate_limit=0,
        timeout=30,
        retry_attempts=3,
        features=["dex", "liquidity_pools", "farming", "lottery", "nft"],
        supported_symbols=["BNB", "BUSD", "USDT", "USDC", "CAKE", "ETH", "BTCB", "ADA", "DOT", "LINK"],
        supported_timeframes=["1m", "5m", "15m", "1h", "4h", "1d"],
        min_trade_amount=0.00001,
        max_trade_amount=1000000,
        fees={"maker": 0.0025, "taker": 0.0025},
        regions=["global"],
        languages=["en", "zh", "ko", "ja", "ru", "tr", "es", "fr", "de", "it"],
        api_docs="https://docs.pancakeswap.finance/",
        status_page="https://status.pancakeswap.finance/",
        support_contact="https://docs.pancakeswap.finance/help"
    ),
    
    "sushiswap": PlatformConfig(
        name="SushiSwap",
        platform_type=PlatformType.DEX,
        tier=PlatformTier.TIER_3,
        enabled=True,
        priority=6,
        api_required=False,
        rate_limit=0,
        timeout=30,
        retry_attempts=3,
        features=["dex", "liquidity_pools", "farming", "lending"],
        supported_symbols=["ETH", "USDC", "USDT", "WBTC", "DAI", "SUSHI", "LINK", "AAVE", "COMP", "MKR"],
        supported_timeframes=["1m", "5m", "15m", "1h", "4h", "1d"],
        min_trade_amount=0.00001,
        max_trade_amount=1000000,
        fees={"maker": 0.0025, "taker": 0.0025},
        regions=["global"],
        languages=["en"],
        api_docs="https://docs.sushi.com/",
        status_page="https://status.sushi.com/",
        support_contact="https://help.sushi.com/"
    )
}

# Configuration des sources de données alternatives
DATA_SOURCE_CONFIGS = {
    "coinmarketcap": PlatformConfig(
        name="CoinMarketCap",
        platform_type=PlatformType.DATA_SOURCE,
        tier=PlatformTier.TIER_1,
        enabled=True,
        priority=9,
        api_required=True,
        rate_limit=10000,
        timeout=30,
        retry_attempts=3,
        features=["market_data", "historical_data", "news", "social_sentiment"],
        supported_symbols=["BTC", "ETH", "BNB", "ADA", "DOT", "LINK", "LTC", "BCH", "XRP", "EOS"],
        supported_timeframes=["1h", "4h", "1d", "1w", "1M"],
        min_trade_amount=0,
        max_trade_amount=0,
        fees={"maker": 0, "taker": 0},
        regions=["global"],
        languages=["en", "zh", "ko", "ja", "ru", "tr", "es", "fr", "de", "it"],
        api_docs="https://coinmarketcap.com/api/documentation/v1/",
        status_page="https://status.coinmarketcap.com/",
        support_contact="https://coinmarketcap.com/contact"
    ),
    
    "coingecko": PlatformConfig(
        name="CoinGecko",
        platform_type=PlatformType.DATA_SOURCE,
        tier=PlatformTier.TIER_1,
        enabled=True,
        priority=8,
        api_required=False,
        rate_limit=50,
        timeout=30,
        retry_attempts=3,
        features=["market_data", "historical_data", "defi_data", "nft_data"],
        supported_symbols=["BTC", "ETH", "BNB", "ADA", "DOT", "LINK", "LTC", "BCH", "XRP", "EOS"],
        supported_timeframes=["1h", "4h", "1d", "1w", "1M"],
        min_trade_amount=0,
        max_trade_amount=0,
        fees={"maker": 0, "taker": 0},
        regions=["global"],
        languages=["en", "zh", "ko", "ja", "ru", "tr", "es", "fr", "de", "it"],
        api_docs="https://www.coingecko.com/en/api/documentation",
        status_page="https://status.coingecko.com/",
        support_contact="https://www.coingecko.com/contact"
    ),
    
    "cryptocompare": PlatformConfig(
        name="CryptoCompare",
        platform_type=PlatformType.DATA_SOURCE,
        tier=PlatformTier.TIER_2,
        enabled=True,
        priority=7,
        api_required=True,
        rate_limit=100000,
        timeout=30,
        retry_attempts=3,
        features=["market_data", "historical_data", "news", "social_sentiment"],
        supported_symbols=["BTC", "ETH", "BNB", "ADA", "DOT", "LINK", "LTC", "BCH", "XRP", "EOS"],
        supported_timeframes=["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"],
        min_trade_amount=0,
        max_trade_amount=0,
        fees={"maker": 0, "taker": 0},
        regions=["global"],
        languages=["en"],
        api_docs="https://min-api.cryptocompare.com/documentation",
        status_page="https://status.cryptocompare.com/",
        support_contact="https://www.cryptocompare.com/contact"
    ),
    
    "messari": PlatformConfig(
        name="Messari",
        platform_type=PlatformType.DATA_SOURCE,
        tier=PlatformTier.TIER_2,
        enabled=True,
        priority=6,
        api_required=True,
        rate_limit=1000,
        timeout=30,
        retry_attempts=3,
        features=["market_data", "on_chain_data", "fundamental_data", "research"],
        supported_symbols=["BTC", "ETH", "BNB", "ADA", "DOT", "LINK", "LTC", "BCH", "XRP", "EOS"],
        supported_timeframes=["1h", "4h", "1d", "1w", "1M"],
        min_trade_amount=0,
        max_trade_amount=0,
        fees={"maker": 0, "taker": 0},
        regions=["global"],
        languages=["en"],
        api_docs="https://messari.io/api/docs",
        status_page="https://status.messari.io/",
        support_contact="https://messari.io/contact"
    ),
    
    "glassnode": PlatformConfig(
        name="Glassnode",
        platform_type=PlatformType.DATA_SOURCE,
        tier=PlatformTier.TIER_2,
        enabled=True,
        priority=6,
        api_required=True,
        rate_limit=1000,
        timeout=30,
        retry_attempts=3,
        features=["on_chain_data", "network_metrics", "market_indicators"],
        supported_symbols=["BTC", "ETH"],
        supported_timeframes=["1h", "4h", "1d", "1w", "1M"],
        min_trade_amount=0,
        max_trade_amount=0,
        fees={"maker": 0, "taker": 0},
        regions=["global"],
        languages=["en"],
        api_docs="https://docs.glassnode.com/",
        status_page="https://status.glassnode.com/",
        support_contact="https://glassnode.com/contact"
    ),
    
    "defillama": PlatformConfig(
        name="DeFiLlama",
        platform_type=PlatformType.DATA_SOURCE,
        tier=PlatformTier.TIER_2,
        enabled=True,
        priority=5,
        api_required=False,
        rate_limit=1000,
        timeout=30,
        retry_attempts=3,
        features=["defi_data", "tvl_data", "protocol_metrics"],
        supported_symbols=["ETH", "USDC", "USDT", "WBTC", "DAI", "UNI", "LINK", "AAVE", "COMP", "MKR"],
        supported_timeframes=["1h", "4h", "1d", "1w"],
        min_trade_amount=0,
        max_trade_amount=0,
        fees={"maker": 0, "taker": 0},
        regions=["global"],
        languages=["en"],
        api_docs="https://defillama.com/docs/api",
        status_page="https://status.defillama.com/",
        support_contact="https://defillama.com/contact"
    )
}

# Configuration des agrégateurs
AGGREGATOR_CONFIGS = {
    "thegraph": PlatformConfig(
        name="The Graph",
        platform_type=PlatformType.AGGREGATOR,
        tier=PlatformTier.TIER_2,
        enabled=True,
        priority=7,
        api_required=True,
        rate_limit=1000,
        timeout=30,
        retry_attempts=3,
        features=["blockchain_data", "defi_data", "nft_data"],
        supported_symbols=["ETH", "USDC", "USDT", "WBTC", "DAI", "UNI", "LINK", "AAVE", "COMP", "MKR"],
        supported_timeframes=["1h", "4h", "1d", "1w"],
        min_trade_amount=0,
        max_trade_amount=0,
        fees={"maker": 0, "taker": 0},
        regions=["global"],
        languages=["en"],
        api_docs="https://thegraph.com/docs/",
        status_page="https://status.thegraph.com/",
        support_contact="https://thegraph.com/contact"
    ),
    
    "moralis": PlatformConfig(
        name="Moralis",
        platform_type=PlatformType.AGGREGATOR,
        tier=PlatformTier.TIER_2,
        enabled=True,
        priority=6,
        api_required=True,
        rate_limit=1000,
        timeout=30,
        retry_attempts=3,
        features=["web3_data", "nft_data", "defi_data"],
        supported_symbols=["ETH", "USDC", "USDT", "WBTC", "DAI", "UNI", "LINK", "AAVE", "COMP", "MKR"],
        supported_timeframes=["1h", "4h", "1d", "1w"],
        min_trade_amount=0,
        max_trade_amount=0,
        fees={"maker": 0, "taker": 0},
        regions=["global"],
        languages=["en"],
        api_docs="https://docs.moralis.io/",
        status_page="https://status.moralis.io/",
        support_contact="https://moralis.io/contact"
    ),
    
    "alchemy": PlatformConfig(
        name="Alchemy",
        platform_type=PlatformType.AGGREGATOR,
        tier=PlatformTier.TIER_2,
        enabled=True,
        priority=6,
        api_required=True,
        rate_limit=1000,
        timeout=30,
        retry_attempts=3,
        features=["blockchain_data", "web3_data", "nft_data"],
        supported_symbols=["ETH", "USDC", "USDT", "WBTC", "DAI", "UNI", "LINK", "AAVE", "COMP", "MKR"],
        supported_timeframes=["1h", "4h", "1d", "1w"],
        min_trade_amount=0,
        max_trade_amount=0,
        fees={"maker": 0, "taker": 0},
        regions=["global"],
        languages=["en"],
        api_docs="https://docs.alchemy.com/",
        status_page="https://status.alchemy.com/",
        support_contact="https://alchemy.com/contact"
    )
}

# Configuration complète
ALL_PLATFORM_CONFIGS = {
    **EXCHANGE_CONFIGS,
    **DEX_CONFIGS,
    **DATA_SOURCE_CONFIGS,
    **AGGREGATOR_CONFIGS
}

# Fonctions utilitaires
def get_platform_config(platform_name: str) -> Optional[PlatformConfig]:
    """Récupère la configuration d'une plateforme"""
    return ALL_PLATFORM_CONFIGS.get(platform_name)

def get_platforms_by_type(platform_type: PlatformType) -> List[str]:
    """Récupère les plateformes par type"""
    return [
        name for name, config in ALL_PLATFORM_CONFIGS.items()
        if config.platform_type == platform_type
    ]

def get_platforms_by_tier(tier: PlatformTier) -> List[str]:
    """Récupère les plateformes par tier"""
    return [
        name for name, config in ALL_PLATFORM_CONFIGS.items()
        if config.tier == tier
    ]

def get_enabled_platforms() -> List[str]:
    """Récupère les plateformes activées"""
    return [
        name for name, config in ALL_PLATFORM_CONFIGS.items()
        if config.enabled
    ]

def get_platforms_by_priority(min_priority: int = 5) -> List[str]:
    """Récupère les plateformes par priorité"""
    return [
        name for name, config in ALL_PLATFORM_CONFIGS.items()
        if config.priority >= min_priority and config.enabled
    ]

def get_platforms_by_region(region: str) -> List[str]:
    """Récupère les plateformes par région"""
    return [
        name for name, config in ALL_PLATFORM_CONFIGS.items()
        if region in config.regions and config.enabled
    ]

def get_platforms_by_feature(feature: str) -> List[str]:
    """Récupère les plateformes par fonctionnalité"""
    return [
        name for name, config in ALL_PLATFORM_CONFIGS.items()
        if feature in config.features and config.enabled
    ]

def get_trading_platforms() -> List[str]:
    """Récupère les plateformes de trading"""
    return get_platforms_by_type(PlatformType.EXCHANGE) + get_platforms_by_type(PlatformType.DEX)

def get_data_platforms() -> List[str]:
    """Récupère les plateformes de données"""
    return get_platforms_by_type(PlatformType.DATA_SOURCE) + get_platforms_by_type(PlatformType.AGGREGATOR)

def get_platform_summary() -> Dict[str, int]:
    """Retourne un résumé des plateformes"""
    return {
        "total": len(ALL_PLATFORM_CONFIGS),
        "exchanges": len(EXCHANGE_CONFIGS),
        "dex": len(DEX_CONFIGS),
        "data_sources": len(DATA_SOURCE_CONFIGS),
        "aggregators": len(AGGREGATOR_CONFIGS),
        "enabled": len(get_enabled_platforms()),
        "tier_1": len(get_platforms_by_tier(PlatformTier.TIER_1)),
        "tier_2": len(get_platforms_by_tier(PlatformTier.TIER_2)),
        "tier_3": len(get_platforms_by_tier(PlatformTier.TIER_3)),
        "emerging": len(get_platforms_by_tier(PlatformTier.EMERGING))
    }