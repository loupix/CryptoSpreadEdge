"""
Liste complète des exchanges et plateformes supportées par CryptoSpreadEdge
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional


class ExchangeType(Enum):
    """Types d'exchanges"""
    SPOT = "spot"
    FUTURES = "futures"
    OPTIONS = "options"
    MARGIN = "margin"
    DERIVATIVES = "derivatives"
    DEX = "dex"  # Decentralized Exchange


class ExchangeTier(Enum):
    """Niveaux d'exchanges par volume et fiabilité"""
    TIER_1 = "tier_1"  # Top exchanges (Binance, Coinbase, etc.)
    TIER_2 = "tier_2"  # Exchanges majeurs
    TIER_3 = "tier_3"  # Exchanges régionaux/spécialisés
    EMERGING = "emerging"  # Nouveaux exchanges


@dataclass
class ExchangeInfo:
    """Informations sur un exchange"""
    name: str
    id: str
    country: str
    tier: ExchangeTier
    types: List[ExchangeType]
    api_docs: str
    rate_limit: int  # requests per minute
    has_websocket: bool
    has_rest_api: bool
    has_futures: bool
    has_margin: bool
    has_staking: bool
    supported_currencies: int
    trading_pairs: int
    volume_24h_usd: float
    trust_score: int  # 1-10
    fees: Dict[str, float]  # maker/taker fees
    min_trade: float
    max_trade: float
    kyc_required: bool
    fiat_support: List[str]
    features: List[str]


# Exchanges Tier 1 (Top exchanges)
EXCHANGES_TIER_1 = {
    "binance": ExchangeInfo(
        name="Binance",
        id="binance",
        country="Global",
        tier=ExchangeTier.TIER_1,
        types=[ExchangeType.SPOT, ExchangeType.FUTURES, ExchangeType.MARGIN, ExchangeType.OPTIONS],
        api_docs="https://binance-docs.github.io/apidocs/",
        rate_limit=1200,
        has_websocket=True,
        has_rest_api=True,
        has_futures=True,
        has_margin=True,
        has_staking=True,
        supported_currencies=350,
        trading_pairs=1200,
        volume_24h_usd=15000000000,
        trust_score=10,
        fees={"maker": 0.001, "taker": 0.001},
        min_trade=0.00001,
        max_trade=1000000,
        kyc_required=False,
        fiat_support=["USD", "EUR", "GBP", "JPY"],
        features=["spot", "futures", "margin", "options", "staking", "lending"]
    ),
    
    "coinbase": ExchangeInfo(
        name="Coinbase Pro",
        id="coinbasepro",
        country="USA",
        tier=ExchangeTier.TIER_1,
        types=[ExchangeType.SPOT, ExchangeType.MARGIN],
        api_docs="https://docs.pro.coinbase.com/",
        rate_limit=10,
        has_websocket=True,
        has_rest_api=True,
        has_futures=False,
        has_margin=True,
        has_staking=True,
        supported_currencies=100,
        trading_pairs=200,
        volume_24h_usd=2000000000,
        trust_score=10,
        fees={"maker": 0.005, "taker": 0.005},
        min_trade=0.01,
        max_trade=100000,
        kyc_required=True,
        fiat_support=["USD", "EUR", "GBP"],
        features=["spot", "margin", "staking", "fiat_onramp"]
    ),
    
    "kraken": ExchangeInfo(
        name="Kraken",
        id="kraken",
        country="USA",
        tier=ExchangeTier.TIER_1,
        types=[ExchangeType.SPOT, ExchangeType.FUTURES, ExchangeType.MARGIN],
        api_docs="https://www.kraken.com/features/api",
        rate_limit=1,
        has_websocket=True,
        has_rest_api=True,
        has_futures=True,
        has_margin=True,
        has_staking=True,
        supported_currencies=200,
        trading_pairs=400,
        volume_24h_usd=1500000000,
        trust_score=9,
        fees={"maker": 0.0016, "taker": 0.0026},
        min_trade=0.0001,
        max_trade=500000,
        kyc_required=True,
        fiat_support=["USD", "EUR", "GBP", "CAD", "JPY"],
        features=["spot", "futures", "margin", "staking", "fiat_onramp"]
    ),
    
    "okx": ExchangeInfo(
        name="OKX",
        id="okx",
        country="Global",
        tier=ExchangeTier.TIER_1,
        types=[ExchangeType.SPOT, ExchangeType.FUTURES, ExchangeType.OPTIONS, ExchangeType.MARGIN],
        api_docs="https://www.okx.com/docs-v5/en/",
        rate_limit=20,
        has_websocket=True,
        has_rest_api=True,
        has_futures=True,
        has_margin=True,
        has_staking=True,
        supported_currencies=300,
        trading_pairs=800,
        volume_24h_usd=8000000000,
        trust_score=9,
        fees={"maker": 0.0008, "taker": 0.001},
        min_trade=0.00001,
        max_trade=1000000,
        kyc_required=False,
        fiat_support=["USD", "EUR", "GBP"],
        features=["spot", "futures", "options", "margin", "staking", "defi"]
    )
}

# Exchanges Tier 2 (Exchanges majeurs)
EXCHANGES_TIER_2 = {
    "bybit": ExchangeInfo(
        name="Bybit",
        id="bybit",
        country="Global",
        tier=ExchangeTier.TIER_2,
        types=[ExchangeType.SPOT, ExchangeType.FUTURES, ExchangeType.OPTIONS],
        api_docs="https://bybit-exchange.github.io/docs/",
        rate_limit=120,
        has_websocket=True,
        has_rest_api=True,
        has_futures=True,
        has_margin=False,
        has_staking=False,
        supported_currencies=200,
        trading_pairs=500,
        volume_24h_usd=3000000000,
        trust_score=8,
        fees={"maker": 0.001, "taker": 0.001},
        min_trade=0.00001,
        max_trade=1000000,
        kyc_required=False,
        fiat_support=["USD"],
        features=["spot", "futures", "options", "copy_trading"]
    ),
    
    "bitget": ExchangeInfo(
        name="Bitget",
        id="bitget",
        country="Global",
        tier=ExchangeTier.TIER_2,
        types=[ExchangeType.SPOT, ExchangeType.FUTURES, ExchangeType.MARGIN],
        api_docs="https://bitgetlimited.github.io/apidoc/en/spot/",
        rate_limit=20,
        has_websocket=True,
        has_rest_api=True,
        has_futures=True,
        has_margin=True,
        has_staking=False,
        supported_currencies=150,
        trading_pairs=300,
        volume_24h_usd=1000000000,
        trust_score=7,
        fees={"maker": 0.001, "taker": 0.001},
        min_trade=0.00001,
        max_trade=100000,
        kyc_required=False,
        fiat_support=["USD"],
        features=["spot", "futures", "margin", "copy_trading"]
    ),
    
    "gateio": ExchangeInfo(
        name="Gate.io",
        id="gateio",
        country="Global",
        tier=ExchangeTier.TIER_2,
        types=[ExchangeType.SPOT, ExchangeType.FUTURES, ExchangeType.MARGIN],
        api_docs="https://www.gate.io/docs/developers/apiv4/",
        rate_limit=900,
        has_websocket=True,
        has_rest_api=True,
        has_futures=True,
        has_margin=True,
        has_staking=True,
        supported_currencies=400,
        trading_pairs=1000,
        volume_24h_usd=2000000000,
        trust_score=7,
        fees={"maker": 0.002, "taker": 0.002},
        min_trade=0.00001,
        max_trade=100000,
        kyc_required=False,
        fiat_support=["USD", "EUR"],
        features=["spot", "futures", "margin", "staking", "lending"]
    ),
    
    "huobi": ExchangeInfo(
        name="Huobi Global",
        id="huobi",
        country="Global",
        tier=ExchangeTier.TIER_2,
        types=[ExchangeType.SPOT, ExchangeType.FUTURES, ExchangeType.MARGIN],
        api_docs="https://huobiapi.github.io/docs/spot/v1/en/",
        rate_limit=100,
        has_websocket=True,
        has_rest_api=True,
        has_futures=True,
        has_margin=True,
        has_staking=True,
        supported_currencies=300,
        trading_pairs=600,
        volume_24h_usd=1500000000,
        trust_score=7,
        fees={"maker": 0.002, "taker": 0.002},
        min_trade=0.00001,
        max_trade=100000,
        kyc_required=False,
        fiat_support=["USD", "EUR"],
        features=["spot", "futures", "margin", "staking", "mining"]
    ),
    
    "kucoin": ExchangeInfo(
        name="KuCoin",
        id="kucoin",
        country="Global",
        tier=ExchangeTier.TIER_2,
        types=[ExchangeType.SPOT, ExchangeType.FUTURES, ExchangeType.MARGIN],
        api_docs="https://docs.kucoin.com/",
        rate_limit=1800,
        has_websocket=True,
        has_rest_api=True,
        has_futures=True,
        has_margin=True,
        has_staking=True,
        supported_currencies=500,
        trading_pairs=800,
        volume_24h_usd=1000000000,
        trust_score=8,
        fees={"maker": 0.001, "taker": 0.001},
        min_trade=0.00001,
        max_trade=100000,
        kyc_required=False,
        fiat_support=["USD", "EUR"],
        features=["spot", "futures", "margin", "staking", "lending", "trading_bot"]
    )
}

# Exchanges Tier 3 (Exchanges régionaux/spécialisés)
EXCHANGES_TIER_3 = {
    "bitfinex": ExchangeInfo(
        name="Bitfinex",
        id="bitfinex",
        country="Global",
        tier=ExchangeTier.TIER_3,
        types=[ExchangeType.SPOT, ExchangeType.MARGIN],
        api_docs="https://docs.bitfinex.com/",
        rate_limit=30,
        has_websocket=True,
        has_rest_api=True,
        has_futures=False,
        has_margin=True,
        has_staking=False,
        supported_currencies=100,
        trading_pairs=200,
        volume_24h_usd=500000000,
        trust_score=6,
        fees={"maker": 0.001, "taker": 0.002},
        min_trade=0.00001,
        max_trade=100000,
        kyc_required=True,
        fiat_support=["USD", "EUR"],
        features=["spot", "margin", "lending"]
    ),
    
    "bitstamp": ExchangeInfo(
        name="Bitstamp",
        id="bitstamp",
        country="Luxembourg",
        tier=ExchangeTier.TIER_3,
        types=[ExchangeType.SPOT],
        api_docs="https://www.bitstamp.net/api/",
        rate_limit=600,
        has_websocket=True,
        has_rest_api=True,
        has_futures=False,
        has_margin=False,
        has_staking=False,
        supported_currencies=50,
        trading_pairs=100,
        volume_24h_usd=200000000,
        trust_score=8,
        fees={"maker": 0.0025, "taker": 0.0025},
        min_trade=0.0001,
        max_trade=10000,
        kyc_required=True,
        fiat_support=["USD", "EUR", "GBP"],
        features=["spot", "fiat_onramp"]
    ),
    
    "gemini": ExchangeInfo(
        name="Gemini",
        id="gemini",
        country="USA",
        tier=ExchangeTier.TIER_3,
        types=[ExchangeType.SPOT],
        api_docs="https://docs.gemini.com/rest-api/",
        rate_limit=600,
        has_websocket=True,
        has_rest_api=True,
        has_futures=False,
        has_margin=False,
        has_staking=True,
        supported_currencies=50,
        trading_pairs=100,
        volume_24h_usd=300000000,
        trust_score=8,
        fees={"maker": 0.0025, "taker": 0.0025},
        min_trade=0.00001,
        max_trade=50000,
        kyc_required=True,
        fiat_support=["USD", "EUR", "GBP", "CAD"],
        features=["spot", "staking", "fiat_onramp", "custody"]
    ),
    
    "bittrex": ExchangeInfo(
        name="Bittrex",
        id="bittrex",
        country="USA",
        tier=ExchangeTier.TIER_3,
        types=[ExchangeType.SPOT],
        api_docs="https://bittrex.github.io/api/v3",
        rate_limit=60,
        has_websocket=False,
        has_rest_api=True,
        has_futures=False,
        has_margin=False,
        has_staking=True,
        supported_currencies=200,
        trading_pairs=300,
        volume_24h_usd=100000000,
        trust_score=6,
        fees={"maker": 0.0025, "taker": 0.0025},
        min_trade=0.00001,
        max_trade=10000,
        kyc_required=True,
        fiat_support=["USD"],
        features=["spot", "staking"]
    )
}

# Exchanges émergents
EXCHANGES_EMERGING = {
    "mexc": ExchangeInfo(
        name="MEXC Global",
        id="mexc",
        country="Global",
        tier=ExchangeTier.EMERGING,
        types=[ExchangeType.SPOT, ExchangeType.FUTURES],
        api_docs="https://mexcdevelop.github.io/apidocs/spot_v3_en/",
        rate_limit=1200,
        has_websocket=True,
        has_rest_api=True,
        has_futures=True,
        has_margin=False,
        has_staking=True,
        supported_currencies=300,
        trading_pairs=600,
        volume_24h_usd=800000000,
        trust_score=6,
        fees={"maker": 0.002, "taker": 0.002},
        min_trade=0.00001,
        max_trade=100000,
        kyc_required=False,
        fiat_support=["USD"],
        features=["spot", "futures", "staking", "new_listings"]
    ),
    
    "whitebit": ExchangeInfo(
        name="WhiteBIT",
        id="whitebit",
        country="Global",
        tier=ExchangeTier.EMERGING,
        types=[ExchangeType.SPOT, ExchangeType.FUTURES],
        api_docs="https://whitebit-exchange.github.io/api-docs/",
        rate_limit=600,
        has_websocket=True,
        has_rest_api=True,
        has_futures=True,
        has_margin=False,
        has_staking=True,
        supported_currencies=200,
        trading_pairs=400,
        volume_24h_usd=300000000,
        trust_score=5,
        fees={"maker": 0.001, "taker": 0.001},
        min_trade=0.00001,
        max_trade=50000,
        kyc_required=False,
        fiat_support=["USD", "EUR"],
        features=["spot", "futures", "staking", "fiat_onramp"]
    ),
    
    "phemex": ExchangeInfo(
        name="Phemex",
        id="phemex",
        country="Global",
        tier=ExchangeTier.EMERGING,
        types=[ExchangeType.SPOT, ExchangeType.FUTURES],
        api_docs="https://phemex.com/api-docs",
        rate_limit=120,
        has_websocket=True,
        has_rest_api=True,
        has_futures=True,
        has_margin=False,
        has_staking=False,
        supported_currencies=100,
        trading_pairs=200,
        volume_24h_usd=200000000,
        trust_score=5,
        fees={"maker": 0.0001, "taker": 0.0006},
        min_trade=0.00001,
        max_trade=100000,
        kyc_required=False,
        fiat_support=["USD"],
        features=["spot", "futures", "copy_trading"]
    )
}

# DEX (Decentralized Exchanges)
DEX_EXCHANGES = {
    "uniswap": ExchangeInfo(
        name="Uniswap",
        id="uniswap",
        country="Global",
        tier=ExchangeTier.TIER_2,
        types=[ExchangeType.DEX],
        api_docs="https://docs.uniswap.org/",
        rate_limit=0,  # No rate limit
        has_websocket=False,
        has_rest_api=False,
        has_futures=False,
        has_margin=False,
        has_staking=True,
        supported_currencies=1000,
        trading_pairs=5000,
        volume_24h_usd=2000000000,
        trust_score=8,
        fees={"maker": 0.003, "taker": 0.003},
        min_trade=0.00001,
        max_trade=1000000,
        kyc_required=False,
        fiat_support=[],
        features=["dex", "liquidity_pools", "farming", "governance"]
    ),
    
    "pancakeswap": ExchangeInfo(
        name="PancakeSwap",
        id="pancakeswap",
        country="Global",
        tier=ExchangeTier.TIER_2,
        types=[ExchangeType.DEX],
        api_docs="https://docs.pancakeswap.finance/",
        rate_limit=0,
        has_websocket=False,
        has_rest_api=False,
        has_futures=False,
        has_margin=False,
        has_staking=True,
        supported_currencies=500,
        trading_pairs=2000,
        volume_24h_usd=1000000000,
        trust_score=7,
        fees={"maker": 0.0025, "taker": 0.0025},
        min_trade=0.00001,
        max_trade=1000000,
        kyc_required=False,
        fiat_support=[],
        features=["dex", "liquidity_pools", "farming", "lottery", "nft"]
    ),
    
    "sushiswap": ExchangeInfo(
        name="SushiSwap",
        id="sushiswap",
        country="Global",
        tier=ExchangeTier.TIER_3,
        types=[ExchangeType.DEX],
        api_docs="https://docs.sushi.com/",
        rate_limit=0,
        has_websocket=False,
        has_rest_api=False,
        has_futures=False,
        has_margin=False,
        has_staking=True,
        supported_currencies=200,
        trading_pairs=1000,
        volume_24h_usd=300000000,
        trust_score=6,
        fees={"maker": 0.0025, "taker": 0.0025},
        min_trade=0.00001,
        max_trade=1000000,
        kyc_required=False,
        fiat_support=[],
        features=["dex", "liquidity_pools", "farming", "lending"]
    )
}

# Agrégation de tous les exchanges
ALL_EXCHANGES = {
    **EXCHANGES_TIER_1,
    **EXCHANGES_TIER_2,
    **EXCHANGES_TIER_3,
    **EXCHANGES_EMERGING,
    **DEX_EXCHANGES
}

# Exchanges par priorité (pour l'arbitrage)
PRIORITY_EXCHANGES = [
    "binance", "coinbase", "kraken", "okx",  # Tier 1
    "bybit", "bitget", "gateio", "huobi", "kucoin",  # Tier 2
    "bitfinex", "bitstamp", "gemini",  # Tier 3
    "mexc", "whitebit", "phemex"  # Emerging
]

# Exchanges par type
SPOT_EXCHANGES = [k for k, v in ALL_EXCHANGES.items() if ExchangeType.SPOT in v.types]
FUTURES_EXCHANGES = [k for k, v in ALL_EXCHANGES.items() if ExchangeType.FUTURES in v.types]
MARGIN_EXCHANGES = [k for k, v in ALL_EXCHANGES.items() if ExchangeType.MARGIN in v.types]
DEX_EXCHANGES_LIST = [k for k, v in ALL_EXCHANGES.items() if ExchangeType.DEX in v.types]

# Exchanges par région
US_EXCHANGES = ["coinbase", "kraken", "bitstamp", "gemini", "bittrex"]
EU_EXCHANGES = ["bitstamp", "kraken"]
ASIA_EXCHANGES = ["binance", "okx", "huobi", "kucoin", "mexc", "whitebit"]
GLOBAL_EXCHANGES = ["binance", "okx", "bybit", "bitget", "gateio", "phemex"]


def get_exchange_info(exchange_id: str) -> Optional[ExchangeInfo]:
    """Récupère les informations d'un exchange"""
    return ALL_EXCHANGES.get(exchange_id)


def get_exchanges_by_tier(tier: ExchangeTier) -> List[str]:
    """Récupère les exchanges par tier"""
    return [k for k, v in ALL_EXCHANGES.items() if v.tier == tier]


def get_exchanges_by_type(exchange_type: ExchangeType) -> List[str]:
    """Récupère les exchanges par type"""
    return [k for k, v in ALL_EXCHANGES.items() if exchange_type in v.types]


def get_top_volume_exchanges(limit: int = 10) -> List[str]:
    """Récupère les exchanges avec le plus gros volume"""
    sorted_exchanges = sorted(
        ALL_EXCHANGES.items(),
        key=lambda x: x[1].volume_24h_usd,
        reverse=True
    )
    return [k for k, v in sorted_exchanges[:limit]]


def get_lowest_fee_exchanges(limit: int = 10) -> List[str]:
    """Récupère les exchanges avec les plus bas frais"""
    sorted_exchanges = sorted(
        ALL_EXCHANGES.items(),
        key=lambda x: x[1].fees["taker"],
        reverse=False
    )
    return [k for k, v in sorted_exchanges[:limit]]


def get_high_trust_exchanges(min_score: int = 8) -> List[str]:
    """Récupère les exchanges avec un score de confiance élevé"""
    return [k for k, v in ALL_EXCHANGES.items() if v.trust_score >= min_score]


def get_exchanges_with_websocket() -> List[str]:
    """Récupère les exchanges avec support WebSocket"""
    return [k for k, v in ALL_EXCHANGES.items() if v.has_websocket]


def get_exchanges_with_futures() -> List[str]:
    """Récupère les exchanges avec support futures"""
    return [k for k, v in ALL_EXCHANGES.items() if v.has_futures]


def get_exchanges_with_margin() -> List[str]:
    """Récupère les exchanges avec support margin"""
    return [k for k, v in ALL_EXCHANGES.items() if v.has_margin]


def get_exchanges_with_staking() -> List[str]:
    """Récupère les exchanges avec support staking"""
    return [k for k, v in ALL_EXCHANGES.items() if v.has_staking]


def get_exchanges_by_region(region: str) -> List[str]:
    """Récupère les exchanges par région"""
    region_map = {
        "us": US_EXCHANGES,
        "eu": EU_EXCHANGES,
        "asia": ASIA_EXCHANGES,
        "global": GLOBAL_EXCHANGES
    }
    return region_map.get(region.lower(), [])


def get_arbitrage_candidates() -> List[str]:
    """Récupère les exchanges recommandés pour l'arbitrage"""
    # Combinaison de volume élevé, frais bas, et fiabilité
    candidates = []
    
    # Tier 1 avec frais bas
    for exchange in ["binance", "okx"]:
        if exchange in ALL_EXCHANGES:
            candidates.append(exchange)
    
    # Tier 2 avec bon volume
    for exchange in ["bybit", "bitget", "gateio", "kucoin"]:
        if exchange in ALL_EXCHANGES:
            candidates.append(exchange)
    
    # Tier 3 fiables
    for exchange in ["bitfinex", "bitstamp", "gemini"]:
        if exchange in ALL_EXCHANGES:
            candidates.append(exchange)
    
    return candidates


def get_market_data_sources() -> List[str]:
    """Récupère les sources de données de marché recommandées"""
    # Exchanges avec de bonnes APIs de données
    return [
        "binance", "coinbase", "kraken", "okx", "bybit",
        "bitget", "gateio", "huobi", "kucoin", "bitfinex"
    ]


def get_trading_exchanges() -> List[str]:
    """Récupère les exchanges recommandés pour le trading"""
    # Exchanges avec de bonnes APIs de trading
    return [
        "binance", "coinbase", "kraken", "okx", "bybit",
        "bitget", "gateio", "huobi", "kucoin"
    ]


def get_futures_trading_exchanges() -> List[str]:
    """Récupère les exchanges recommandés pour le trading futures"""
    return [
        "binance", "okx", "bybit", "bitget", "gateio",
        "huobi", "kucoin", "mexc", "whitebit", "phemex"
    ]


def get_dex_exchanges() -> List[str]:
    """Récupère les DEX disponibles"""
    return list(DEX_EXCHANGES.keys())


def get_total_exchanges_count() -> int:
    """Retourne le nombre total d'exchanges supportés"""
    return len(ALL_EXCHANGES)


def get_exchanges_summary() -> Dict[str, int]:
    """Retourne un résumé des exchanges par catégorie"""
    return {
        "total": len(ALL_EXCHANGES),
        "tier_1": len(EXCHANGES_TIER_1),
        "tier_2": len(EXCHANGES_TIER_2),
        "tier_3": len(EXCHANGES_TIER_3),
        "emerging": len(EXCHANGES_EMERGING),
        "dex": len(DEX_EXCHANGES),
        "spot": len(SPOT_EXCHANGES),
        "futures": len(FUTURES_EXCHANGES),
        "margin": len(MARGIN_EXCHANGES),
        "websocket": len(get_exchanges_with_websocket()),
        "staking": len(get_exchanges_with_staking())
    }