"""
Market Data Service - Multi-Source Integration
Fetches real-time cryptocurrency prices from multiple sources:
- Yahoo Finance (primary)
- CoinGecko API (backup 1)
- Binance Public API (backup 2)

Automatic failover with 5-minute cooldown for rate-limited sources
"""
import yfinance as yf  # type: ignore
import requests
import logging
from typing import Dict, Optional, Any, Union
from datetime import datetime, timedelta, timezone
from threading import Thread
from enum import Enum
import time

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Available data sources for market prices"""
    YAHOO_FINANCE = "yahoo_finance"
    COINGECKO = "coingecko"
    BINANCE = "binance"


class MultiSourceMarketDataService:
    """Service to fetch and cache real-time market prices from multiple sources with automatic failover"""
    
    def __init__(self, refresh_interval: int = 30):
        """
        Initialize the multi-source market data service
        
        Args:
            refresh_interval: Seconds between price updates (default: 30)
        """
        self.refresh_interval = refresh_interval
        self.prices: Dict[str, Dict[str, Any]] = {}
        self.last_update: Optional[datetime] = None
        self.is_running = False
        self._thread: Optional[Thread] = None
        
        # Track source availability and cooldowns
        self.source_cooldowns: Dict[DataSource, datetime] = {}
        self.active_source: Optional[DataSource] = None
        
        # Define cryptocurrencies to track (Top cryptos from Binance)
        self.crypto_symbols = {
            "BTC": {
                "name": "Bitcoin",
                "yahoo_symbol": "BTC-USD",
                "coingecko_id": "bitcoin",
                "binance_symbol": "BTCUSDT",
                "approx_market_cap": 1800000000000  # ~$1.8T
            },
            "ETH": {
                "name": "Ethereum",
                "yahoo_symbol": "ETH-USD",
                "coingecko_id": "ethereum",
                "binance_symbol": "ETHUSDT",
                "approx_market_cap": 400000000000  # ~$400B
            },
            "BNB": {
                "name": "BNB",
                "yahoo_symbol": "BNB-USD",
                "coingecko_id": "binancecoin",
                "binance_symbol": "BNBUSDT",
                "approx_market_cap": 85000000000  # ~$85B
            },
            "XRP": {
                "name": "XRP",
                "yahoo_symbol": "XRP-USD",
                "coingecko_id": "ripple",
                "binance_symbol": "XRPUSDT",
                "approx_market_cap": 140000000000  # ~$140B
            },
            "ADA": {
                "name": "Cardano",
                "yahoo_symbol": "ADA-USD",
                "coingecko_id": "cardano",
                "binance_symbol": "ADAUSDT",
                "approx_market_cap": 35000000000  # ~$35B
            },
            "SOL": {
                "name": "Solana",
                "yahoo_symbol": "SOL-USD",
                "coingecko_id": "solana",
                "binance_symbol": "SOLUSDT",
                "approx_market_cap": 65000000000  # ~$65B
            },
            "DOGE": {
                "name": "Dogecoin",
                "yahoo_symbol": "DOGE-USD",
                "coingecko_id": "dogecoin",
                "binance_symbol": "DOGEUSDT",
                "approx_market_cap": 28000000000  # ~$28B
            },
            "DOT": {
                "name": "Polkadot",
                "yahoo_symbol": "DOT-USD",
                "coingecko_id": "polkadot",
                "binance_symbol": "DOTUSDT",
                "approx_market_cap": 9000000000  # ~$9B
            },
            "MATIC": {
                "name": "Polygon",
                "yahoo_symbol": "MATIC-USD",
                "coingecko_id": "matic-network",
                "binance_symbol": "MATICUSDT",
                "approx_market_cap": 7000000000  # ~$7B
            },
            "AVAX": {
                "name": "Avalanche",
                "yahoo_symbol": "AVAX-USD",
                "coingecko_id": "avalanche-2",
                "binance_symbol": "AVAXUSDT",
                "approx_market_cap": 14000000000  # ~$14B
            },
            "LINK": {
                "name": "Chainlink",
                "yahoo_symbol": "LINK-USD",
                "coingecko_id": "chainlink",
                "binance_symbol": "LINKUSDT",
                "approx_market_cap": 11000000000  # ~$11B
            },
            "UNI": {
                "name": "Uniswap",
                "yahoo_symbol": "UNI-USD",
                "coingecko_id": "uniswap",
                "binance_symbol": "UNIUSDT",
                "approx_market_cap": 6000000000  # ~$6B
            },
            "ATOM": {
                "name": "Cosmos",
                "yahoo_symbol": "ATOM-USD",
                "coingecko_id": "cosmos",
                "binance_symbol": "ATOMUSDT",
                "approx_market_cap": 4000000000  # ~$4B
            },
            "LTC": {
                "name": "Litecoin",
                "yahoo_symbol": "LTC-USD",
                "coingecko_id": "litecoin",
                "binance_symbol": "LTCUSDT",
                "approx_market_cap": 6000000000  # ~$6B
            },
            "SHIB": {
                "name": "Shiba Inu",
                "yahoo_symbol": "SHIB-USD",
                "coingecko_id": "shiba-inu",
                "binance_symbol": "SHIBUSDT",
                "approx_market_cap": 9000000000  # ~$9B
            },
            "TRX": {
                "name": "TRON",
                "yahoo_symbol": "TRX-USD",
                "coingecko_id": "tron",
                "binance_symbol": "TRXUSDT",
                "approx_market_cap": 21000000000  # ~$21B
            },
            "ARB": {
                "name": "Arbitrum",
                "yahoo_symbol": "ARB-USD",
                "coingecko_id": "arbitrum",
                "binance_symbol": "ARBUSDT",
                "approx_market_cap": 3000000000  # ~$3B
            },
            "OP": {
                "name": "Optimism",
                "yahoo_symbol": "OP-USD",
                "coingecko_id": "optimism",
                "binance_symbol": "OPUSDT",
                "approx_market_cap": 2000000000  # ~$2B
            }
        }
        
    def start(self):
        """Start the background price update loop"""
        if self.is_running:
            logger.warning("Market data service is already running")
            return
            
        logger.info(f"Starting multi-source market data service (refresh interval: {self.refresh_interval}s)")
        logger.info("Data sources: CoinGecko → Binance → Yahoo Finance")
        
        # Fetch prices immediately on startup
        try:
            self._fetch_prices()
        except Exception as e:
            logger.error(f"Error on initial price fetch: {e}")
        
        self.is_running = True
        self._thread = Thread(target=self._run_update_loop, daemon=True)
        self._thread.start()
        
    def stop(self):
        """Stop the background price update loop"""
        logger.info("Stopping market data service")
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=5)
            
    def _run_update_loop(self):
        """Background loop to fetch prices periodically"""
        while self.is_running:
            try:
                self._fetch_prices()
            except Exception as e:
                logger.error(f"Error fetching market prices: {e}")
            
            time.sleep(self.refresh_interval)
    
    def _is_source_available(self, source: DataSource) -> bool:
        """Check if a data source is available (not in cooldown)"""
        if source not in self.source_cooldowns:
            return True
        
        cooldown_until = self.source_cooldowns[source]
        if datetime.now(timezone.utc) >= cooldown_until:
            # Cooldown expired, remove it
            del self.source_cooldowns[source]
            return True
            
        return False
    
    def _set_source_cooldown(self, source: DataSource, minutes: int = 5):
        """Set a cooldown period for a rate-limited source"""
        cooldown_until = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        self.source_cooldowns[source] = cooldown_until
        logger.warning(f"{source.value} is rate-limited. Cooldown until {cooldown_until.strftime('%H:%M:%S')}")
            
    def _fetch_prices(self):
        """Fetch latest prices from available sources with automatic failover"""
        
        # Try each source in order: CoinGecko → Binance → Yahoo Finance
        sources_to_try = [
            DataSource.COINGECKO,
            DataSource.BINANCE,
            DataSource.YAHOO_FINANCE
        ]
        
        for source in sources_to_try:
            if not self._is_source_available(source):
                continue
                
            logger.debug(f"Attempting to fetch prices from {source.value}...")
            
            success_count = 0
            total_symbols = len(self.crypto_symbols)
            
            for symbol, details in self.crypto_symbols.items():
                try:
                    price_data = None
                    
                    if source == DataSource.YAHOO_FINANCE:
                        price_data = self._fetch_from_yahoo(symbol, details)
                    elif source == DataSource.COINGECKO:
                        price_data = self._fetch_from_coingecko(symbol, details)
                    elif source == DataSource.BINANCE:
                        price_data = self._fetch_from_binance(symbol, details)
                    
                    if price_data:
                        price_data["source"] = source.value
                        self.prices[f"{symbol}-USD"] = price_data
                        success_count += 1
                        logger.debug(f"{symbol}: ${price_data['price']:.2f} from {source.value}")
                        
                except Exception as e:
                    logger.error(f"Error fetching {symbol} from {source.value}: {e}")
            
            # If we successfully fetched at least some prices, consider it a success
            if success_count > 0:
                self.active_source = source
                self.last_update = datetime.now(timezone.utc)
                logger.info(f"Market prices updated from {source.value} ({success_count}/{total_symbols} successful)")
                return
            else:
                # All symbols failed from this source - likely rate limited
                logger.warning(f"All symbols failed from {source.value}, setting cooldown")
                self._set_source_cooldown(source)
        
        # If we get here, all sources failed
        logger.error("All data sources failed or are in cooldown. Using cached prices.")
    
    def _fetch_from_yahoo(self, symbol: str, details: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fetch price from Yahoo Finance"""
        try:
            yahoo_symbol = details["yahoo_symbol"]
            ticker = yf.Ticker(yahoo_symbol)
            fast_info = ticker.fast_info
            
            # Cast fast_info to Dict for type safety
            info_dict = dict(fast_info) if fast_info else {}
            
            # Safely extract and convert numeric values with type validation
            def safe_float(value: Any, default: float = 0.0) -> float:
                """Safely convert value to float with fallback"""
                if value is None:
                    return default
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return default
            
            last_price = safe_float(info_dict.get('lastPrice')) or safe_float(info_dict.get('regularMarketPrice'))
            prev_close = safe_float(info_dict.get('previousClose'))
            
            # Calculate change with proper type safety
            change = 0.0
            change_percent = 0.0
            if prev_close > 0 and last_price > 0:
                change = last_price - prev_close
                change_percent = (change / prev_close) * 100
            
            return {
                "symbol": f"{symbol}-USD",
                "name": details["name"],
                "price": last_price,
                "change": change,
                "change_percent": change_percent,
                "volume": safe_float(info_dict.get("regularVolume")),
                "market_cap": safe_float(info_dict.get("marketCap")),
                "high_24h": safe_float(info_dict.get("dayHigh")),
                "low_24h": safe_float(info_dict.get("dayLow")),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            if "Too Many Requests" in str(e) or "Rate limit" in str(e):
                raise Exception(f"Yahoo Finance rate limit: {e}")
            logger.error(f"Yahoo Finance error for {symbol}: {e}")
            return None
    
    def _fetch_from_coingecko(self, symbol: str, details: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fetch price from CoinGecko API (free, no API key required)"""
        try:
            coingecko_id = details["coingecko_id"]
            
            # CoinGecko free API endpoint
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params: Dict[str, Union[str, bool]] = {
                "ids": coingecko_id,
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_24hr_vol": "true",
                "include_market_cap": "true"
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 429:
                logger.warning(f"CoinGecko rate limit reached for {symbol}")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            if coingecko_id not in data:
                return None
            
            coin_data = data[coingecko_id]
            price = coin_data.get("usd", 0)
            change_percent = coin_data.get("usd_24h_change", 0)
            change = (price * change_percent / 100) if price > 0 else 0
            
            return {
                "symbol": f"{symbol}-USD",
                "name": details["name"],
                "price": float(price),
                "change": float(change),
                "change_percent": float(change_percent),
                "volume": coin_data.get("usd_24h_vol", 0),
                "market_cap": coin_data.get("usd_market_cap", 0),
                "high_24h": 0,  # CoinGecko simple API doesn't provide this
                "low_24h": 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"CoinGecko error for {symbol}: {e}")
            return None
    
    def _fetch_from_binance(self, symbol: str, details: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fetch price from Binance Public API (free, no API key required)"""
        try:
            binance_symbol = details["binance_symbol"]
            
            # Binance public API endpoint
            url = "https://api.binance.com/api/v3/ticker/24hr"
            params: Dict[str, str] = {"symbol": binance_symbol}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 429:
                logger.warning(f"Binance rate limit reached for {symbol}")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            price = float(data.get("lastPrice", 0))
            change = float(data.get("priceChange", 0))
            change_percent = float(data.get("priceChangePercent", 0))
            
            return {
                "symbol": f"{symbol}-USD",
                "name": details["name"],
                "price": price,
                "change": change,
                "change_percent": change_percent,
                "volume": float(data.get("volume", 0)),
                "market_cap": details.get("approx_market_cap", 0),  # Use approximate market cap
                "high_24h": float(data.get("highPrice", 0)),
                "low_24h": float(data.get("lowPrice", 0)),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Binance error for {symbol}: {e}")
            return None
            
    def get_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for a specific symbol
        
        Args:
            symbol: Ticker symbol (e.g., "BTC-USD")
            
        Returns:
            Current price or None if not available
        """
        price_data = self.prices.get(symbol)
        return price_data.get("price") if price_data else None
        
    def get_all_prices(self) -> Dict[str, Any]:
        """Get all current market prices with source information
        
        Returns:
            Dictionary of all tracked prices with metadata and source status
        """
        # Get source status
        source_status = {}
        for source in DataSource:
            if source in self.source_cooldowns:
                cooldown_until = self.source_cooldowns[source]
                remaining = (cooldown_until - datetime.now(timezone.utc)).total_seconds()
                source_status[source.value] = {
                    "available": False,
                    "cooldown_remaining_seconds": max(0, int(remaining))
                }
            else:
                source_status[source.value] = {"available": True}
        
        return {
            "prices": self.prices,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "refresh_interval": self.refresh_interval,
            "active_source": self.active_source.value if self.active_source else None,
            "source_status": source_status
        }
        
    def get_conversion_rate(self, from_currency: str, to_currency: str = "USD") -> float:
        """
        Get conversion rate between currencies
        
        Args:
            from_currency: Source currency (e.g., "BTC", "ETH")
            to_currency: Target currency (default: "USD")
            
        Returns:
            Conversion rate or 1.0 if same currency or not found
        """
        if from_currency == to_currency:
            return 1.0
            
        if to_currency == "USD":
            symbol = f"{from_currency}-USD"
            price = self.get_price(symbol)
            return price if price else 0.0
            
        # For other conversions, use USD as intermediary
        from_price = self.get_price(f"{from_currency}-USD")
        to_price = self.get_price(f"{to_currency}-USD")
        
        if from_price and to_price and to_price != 0:
            return from_price / to_price
            
        return 0.0


# Global instance with 30-second refresh interval (from .env configuration)
market_data_service = MultiSourceMarketDataService(refresh_interval=30)
