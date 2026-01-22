"""
Binance API Service
Fetches market data from Binance public API (no authentication required)
"""
import requests
import logging
import time
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class BinanceService:
    """Service for fetching crypto market data from Binance API"""
    
    BASE_URL = "https://api.binance.com/api/v3"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'P2P-Trading-Simulator/1.0',
            'Accept': 'application/json'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests (Binance is fast)
    
    def get_symbol_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current price for a trading symbol
        Uses public endpoint: /api/v3/ticker/price
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT", "ETHUSDT")
            
        Returns:
            Dictionary with price data or None if error
        """
        try:
            # Normalize symbol - Binance uses uppercase symbols like BTCUSDT
            symbol = symbol.upper().strip()
            
            # Rate limiting
            time_since_last = time.time() - self.last_request_time
            if time_since_last < self.min_request_interval:
                time.sleep(self.min_request_interval - time_since_last)
            
            url = f"{self.BASE_URL}/ticker/price"
            params = {'symbol': symbol}
            
            response = self.session.get(url, params=params, timeout=10)
            self.last_request_time = time.time()
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"✅ Fetched price for {symbol}: ${data.get('price', 0)}")
            return {
                "symbol": data.get("symbol", symbol),
                "price": float(data.get("price", 0))
            }
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                error_data = e.response.json()
                error_msg = error_data.get("msg", "Invalid symbol")
                logger.warning(f"Invalid symbol {symbol}: {error_msg}")
            elif e.response.status_code == 429:
                logger.warning(f"⚠️ Rate limit hit for {symbol}")
            else:
                logger.error(f"HTTP error {e.response.status_code} fetching price for {symbol}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching price for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_symbol_price for {symbol}: {type(e).__name__}: {e}")
            return None
    
    def get_24hr_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get 24hr ticker statistics for a symbol
        Uses public endpoint: /api/v3/ticker/24hr
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT", "ETHUSDT")
            
        Returns:
            Dictionary with 24hr statistics or None if error
        """
        try:
            # Normalize symbol
            symbol = symbol.upper().strip()
            
            # Rate limiting
            time_since_last = time.time() - self.last_request_time
            if time_since_last < self.min_request_interval:
                time.sleep(self.min_request_interval - time_since_last)
            
            url = f"{self.BASE_URL}/ticker/24hr"
            params = {'symbol': symbol}
            
            response = self.session.get(url, params=params, timeout=10)
            self.last_request_time = time.time()
            
            response.raise_for_status()
            data = response.json()
            
            # Format the response
            formatted_data = {
                "symbol": data.get("symbol", symbol),
                "price": float(data.get("lastPrice", 0)),
                "price_change": float(data.get("priceChange", 0)),
                "price_change_percent": float(data.get("priceChangePercent", 0)),
                "high_price": float(data.get("highPrice", 0)),
                "low_price": float(data.get("lowPrice", 0)),
                "volume": float(data.get("volume", 0)),
                "quote_volume": float(data.get("quoteVolume", 0)),  # Volume in USDT
                "open_price": float(data.get("openPrice", 0)),
                "prev_close_price": float(data.get("prevClosePrice", 0)),
                "bid_price": float(data.get("bidPrice", 0)),
                "ask_price": float(data.get("askPrice", 0)),
                "count": int(data.get("count", 0))  # Number of trades
            }
            
            logger.info(f"✅ Fetched 24hr ticker for {symbol}: ${formatted_data['price']} ({formatted_data['price_change_percent']:+.2f}%)")
            return formatted_data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                error_data = e.response.json()
                error_msg = error_data.get("msg", "Invalid symbol")
                logger.warning(f"Invalid symbol {symbol}: {error_msg}")
            elif e.response.status_code == 429:
                logger.warning(f"⚠️ Rate limit hit for {symbol}")
            else:
                logger.error(f"HTTP error {e.response.status_code} fetching 24hr ticker for {symbol}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching 24hr ticker for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_24hr_ticker for {symbol}: {type(e).__name__}: {e}")
            return None
    
    def get_all_prices(self) -> Optional[Dict[str, float]]:
        """
        Get all symbol prices
        Uses public endpoint: /api/v3/ticker/price
        
        Returns:
            Dictionary mapping symbols to prices
        """
        try:
            # Rate limiting
            time_since_last = time.time() - self.last_request_time
            if time_since_last < self.min_request_interval:
                time.sleep(self.min_request_interval - time_since_last)
            
            url = f"{self.BASE_URL}/ticker/price"
            
            response = self.session.get(url, timeout=10)
            self.last_request_time = time.time()
            
            response.raise_for_status()
            data = response.json()
            
            prices = {item["symbol"]: float(item["price"]) for item in data}
            logger.info(f"✅ Fetched prices for {len(prices)} symbols")
            return prices
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching all prices: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_all_prices: {type(e).__name__}: {e}")
            return None
    
    def search_symbols(self, query: str, limit: int = 20) -> List[Dict[str, str]]:
        """
        Search for trading symbols (Binance doesn't have a search endpoint,
        so we get all prices and filter)
        
        Args:
            query: Search query (coin symbol like BTC, ETH)
            limit: Maximum number of results
            
        Returns:
            List of matching symbols
        """
        try:
            all_prices = self.get_all_prices()
            if not all_prices:
                return []
            
            query_upper = query.upper().strip()
            matches = []
            
            # Common USDT pairs
            common_quote = "USDT"
            
            for symbol in all_prices.keys():
                # Check if symbol starts with query and ends with common quote currencies
                if symbol.startswith(query_upper) and (
                    symbol.endswith(common_quote) or 
                    symbol.endswith("BUSD") or
                    symbol.endswith("BTC")
                ):
                    # Extract base symbol (remove quote currency)
                    base = symbol.replace(common_quote, "").replace("BUSD", "").replace("BTC", "")
                    matches.append({
                        "symbol": symbol,
                        "base": base,
                        "quote": symbol.replace(base, ""),
                        "price": all_prices[symbol]
                    })
                    if len(matches) >= limit:
                        break
            
            logger.info(f"Found {len(matches)} symbols matching '{query}'")
            return matches
            
        except Exception as e:
            logger.error(f"Error searching symbols: {type(e).__name__}: {e}")
            return []
    
    def normalize_symbol(self, input_symbol: str) -> str:
        """
        Normalize user input to Binance symbol format
        Converts BTC -> BTCUSDT, ETH -> ETHUSDT, etc.
        
        Args:
            input_symbol: User input (BTC, ETH, bitcoin, etc.)
            
        Returns:
            Binance symbol format (BTCUSDT, ETHUSDT, etc.)
        """
        # Remove spaces and convert to uppercase
        symbol = input_symbol.upper().strip()
        
        # If it already ends with USDT, BUSD, BTC, etc., return as-is
        if any(symbol.endswith(q) for q in ["USDT", "BUSD", "BTC", "ETH", "BNB", "EUR", "GBP"]):
            return symbol
        
        # Common mappings (symbol -> Binance trading pair)
        symbol_map = {
            "BTC": "BTCUSDT",
            "BITCOIN": "BTCUSDT",
            "ETH": "ETHUSDT",
            "ETHEREUM": "ETHUSDT",
            "BNB": "BNBUSDT",
            "BINANCE": "BNBUSDT",
            "SOL": "SOLUSDT",
            "SOLANA": "SOLUSDT",
            "XRP": "XRPUSDT",
            "RIPPLE": "XRPUSDT",
            "ADA": "ADAUSDT",
            "CARDANO": "ADAUSDT",
            "DOGE": "DOGEUSDT",
            "DOGECOIN": "DOGEUSDT",
            "DOT": "DOTUSDT",
            "POLKADOT": "DOTUSDT",
            "MATIC": "MATICUSDT",
            "POLYGON": "MATICUSDT",
            "AVAX": "AVAXUSDT",
            "AVALANCHE": "AVAXUSDT",
            "LINK": "LINKUSDT",
            "CHAINLINK": "LINKUSDT",
            "UNI": "UNIUSDT",
            "UNISWAP": "UNIUSDT",
            "LTC": "LTCUSDT",
            "LITECOIN": "LTCUSDT",
            "TRX": "TRXUSDT",
            "TRON": "TRXUSDT",
            "ATOM": "ATOMUSDT",
            "COSMOS": "ATOMUSDT",
        }
        
        # Try direct mapping first
        if symbol in symbol_map:
            return symbol_map[symbol]
        
        # If not found, try to append USDT (most common pair on Binance)
        return f"{symbol}USDT"
    
    def get_coin_name(self, symbol: str) -> str:
        """
        Get friendly name for a cryptocurrency symbol
        
        Args:
            symbol: Cryptocurrency symbol (BTC, ETH, etc.)
            
        Returns:
            Friendly name (Bitcoin, Ethereum, etc.)
        """
        name_map = {
            "BTC": "Bitcoin",
            "ETH": "Ethereum",
            "BNB": "Binance Coin",
            "SOL": "Solana",
            "XRP": "Ripple",
            "ADA": "Cardano",
            "DOGE": "Dogecoin",
            "DOT": "Polkadot",
            "MATIC": "Polygon",
            "AVAX": "Avalanche",
            "LINK": "Chainlink",
            "UNI": "Uniswap",
            "LTC": "Litecoin",
            "TRX": "Tron",
            "ATOM": "Cosmos",
        }
        return name_map.get(symbol.upper(), symbol.upper())


# Global instance
binance_service = BinanceService()

