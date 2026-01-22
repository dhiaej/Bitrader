"""
CoinGecko Service with Technical Indicators
Fetches historical price data and calculates technical indicators for AI predictions
"""
import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import time
import json
from pathlib import Path
from ta.trend import MACD, EMAIndicator, SMAIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator, VolumeWeightedAveragePrice

logger = logging.getLogger(__name__)


class CoinGeckoService:
    """Service for fetching crypto data from CoinGecko API with technical analysis"""
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    CACHE_DIR = Path("cache/coingecko")
    CACHE_DURATION = 21600  # 6 hours cache (increased to avoid rate limits)
    
    # Map our symbols to CoinGecko IDs
    SYMBOL_MAP = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "LTC": "litecoin",
        "SOL": "solana",
        "DOGE": "dogecoin",
        "USDT": "tether"
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'P2P-Trading-Simulator/1.0',
            'Accept': 'application/json'
        })
        
        # Create cache directory
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 2.0  # Minimum 2 seconds between requests
        
        # Fallback data - used when API is unavailable
        self._generate_demo_data_if_needed()
    
    def get_coin_id(self, symbol: str) -> str:
        """Convert symbol to CoinGecko coin ID"""
        return self.SYMBOL_MAP.get(symbol.upper(), symbol.lower())
    
    def _generate_demo_data_if_needed(self):
        """Generate demo data for all symbols if cache is empty"""
        for symbol in ["BTC", "ETH", "LTC", "SOL", "DOGE"]:
            cache_file = self.CACHE_DIR / f"{self.get_coin_id(symbol)}_30d.json"
            if not cache_file.exists():
                logger.info(f"Generating demo data for {symbol}")
                demo_data = self._generate_demo_data(symbol)
                with open(cache_file, 'w') as f:
                    json.dump(demo_data, f)
    
    def _generate_demo_data(self, symbol: str) -> Dict:
        """Generate realistic demo data for a cryptocurrency with unique patterns"""
        import random
        from datetime import datetime, timedelta
        
        # Base prices and volatility for different cryptos
        crypto_params = {
            "BTC": {"base": 95000.0, "volatility": 1.5, "trend": 0.02},   # Lower volatility, slight uptrend
            "ETH": {"base": 3500.0, "volatility": 2.5, "trend": -0.01},   # Higher volatility, slight downtrend
            "LTC": {"base": 100.0, "volatility": 3.0, "trend": 0.01},     # Medium volatility
            "SOL": {"base": 200.0, "volatility": 3.5, "trend": 0.03},     # High volatility, uptrend
            "DOGE": {"base": 0.35, "volatility": 4.0, "trend": -0.02}     # Very high volatility, downtrend
        }
        
        params = crypto_params.get(symbol, {"base": 1000.0, "volatility": 2.0, "trend": 0.0})
        base_price = params["base"]
        volatility = params["volatility"]
        trend = params["trend"]
        
        # Generate 30 days of hourly data (720 data points)
        prices = []
        volumes = []
        market_caps = []
        
        current_time = datetime.now()
        current_price = float(base_price)
        
        # Add unique seed for each crypto
        random.seed(hash(symbol) % 1000000)
        
        for i in range(720):  # 30 days * 24 hours
            timestamp = int((current_time - timedelta(hours=720-i)).timestamp() * 1000)
            
            # Random walk with trend and unique volatility per crypto
            change_percent = random.gauss(trend, volatility)
            current_price = float(current_price * (1 + change_percent / 100))
            
            # Ensure price stays somewhat realistic
            current_price = max(current_price, base_price * 0.5)  # Don't drop below 50% of base
            current_price = min(current_price, base_price * 1.5)  # Don't go above 150% of base
            
            # Add some volume and market cap with variation
            volume_multiplier = random.uniform(5000000, 30000000) * (1 + abs(change_percent) / 10)
            market_cap_multiplier = random.uniform(800000000, 3000000000)
            
            volume = float(current_price * volume_multiplier)
            market_cap = float(current_price * market_cap_multiplier)
            
            prices.append([timestamp, round(current_price, 2)])
            volumes.append([timestamp, round(volume, 2)])
            market_caps.append([timestamp, round(market_cap, 2)])
        
        # Reset random seed
        random.seed()
        
        return {
            "prices": prices,
            "total_volumes": volumes,
            "market_caps": market_caps
        }
    
    def fetch_historical_data(
        self, 
        symbol: str, 
        days: int = 30,
        vs_currency: str = "usd"
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical price data from CoinGecko with caching and rate limiting
        
        Args:
            symbol: Cryptocurrency symbol (BTC, ETH, etc.)
            days: Number of days of historical data (1-365)
            vs_currency: Fiat currency to compare against (default: usd)
            
        Returns:
            DataFrame with columns: timestamp, price, volume, market_cap
        """
        try:
            coin_id = self.get_coin_id(symbol)
            
            # Check cache first
            cache_file = self.CACHE_DIR / f"{coin_id}_{days}d.json"
            if cache_file.exists():
                cache_age = time.time() - cache_file.stat().st_mtime
                if cache_age < self.CACHE_DURATION:
                    logger.info(f"✅ Using cached data for {symbol} (age: {cache_age/3600:.1f}h)")
                    with open(cache_file, 'r') as f:
                        cached_data = json.load(f)
                        return self._parse_data_to_dataframe(cached_data)
            
            # Rate limiting
            time_since_last = time.time() - self.last_request_time
            if time_since_last < self.min_request_interval:
                sleep_time = self.min_request_interval - time_since_last
                logger.info(f"Rate limiting: sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
            
            # CoinGecko market_chart endpoint - free and unlimited!
            url = f"{self.BASE_URL}/coins/{coin_id}/market_chart"
            params = {
                'vs_currency': vs_currency,
                'days': days,
                'interval': 'hourly' if days <= 90 else 'daily'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            self.last_request_time = time.time()
            
            response.raise_for_status()
            
            data = response.json()
            
            # Cache the response
            with open(cache_file, 'w') as f:
                json.dump(data, f)
            
            return self._parse_data_to_dataframe(data)
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning(f"⚠️ Rate limit hit for {symbol}. Using cached data...")
                # Try to use old cache even if expired
                if cache_file.exists():
                    logger.info(f"✅ Using stale cache for {symbol} (better than nothing)")
                    with open(cache_file, 'r') as f:
                        cached_data = json.load(f)
                        return self._parse_data_to_dataframe(cached_data)
                else:
                    # Generate demo data as last resort
                    logger.info(f"⚠️ No cache available, using demo data for {symbol}")
                    demo_data = self._generate_demo_data(symbol)
                    with open(cache_file, 'w') as f:
                        json.dump(demo_data, f)
                    return self._parse_data_to_dataframe(demo_data)
            logger.error(f"HTTP error fetching data from CoinGecko for {symbol}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from CoinGecko for {symbol}: {e}")
            # Try cache as fallback
            if cache_file.exists():
                logger.info(f"Using cached data due to request error")
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    return self._parse_data_to_dataframe(cached_data)
            return None
        except Exception as e:
            logger.error(f"Unexpected error in fetch_historical_data for {symbol}: {e}")
            return None
    
    def _parse_data_to_dataframe(self, data: Dict) -> Optional[pd.DataFrame]:
        """Parse CoinGecko API response to DataFrame"""
        try:
            # Extract price, volume, and market cap data
            prices = data.get('prices', [])
            volumes = data.get('total_volumes', [])
            market_caps = data.get('market_caps', [])
            
            if not prices:
                logger.warning("No price data in response")
                return None
            
            # Create DataFrame
            df = pd.DataFrame({
                'timestamp': [pd.Timestamp(p[0], unit='ms') for p in prices],
                'price': [p[1] for p in prices],
                'volume': [v[1] if v else 0 for v in volumes],
                'market_cap': [m[1] if m else 0 for m in market_caps]
            })
            
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            logger.info(f"Parsed {len(df)} data points")
            return df
        except Exception as e:
            logger.error(f"Error parsing data to DataFrame: {e}")
            return None
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators on price data
        
        Args:
            df: DataFrame with 'price', 'volume' columns
            
        Returns:
            DataFrame with added technical indicator columns
        """
        try:
            if df is None or df.empty or len(df) < 20:
                logger.warning("Insufficient data for technical indicators")
                return df
            
            # Make a copy to avoid modifying original
            df = df.copy()
            
            close = df['price']
            volume = df['volume']
            
            # === TREND INDICATORS ===
            
            # Simple Moving Averages
            df['sma_7'] = SMAIndicator(close=close, window=7).sma_indicator()
            df['sma_14'] = SMAIndicator(close=close, window=14).sma_indicator()
            df['sma_30'] = SMAIndicator(close=close, window=30).sma_indicator()
            
            # Exponential Moving Averages
            df['ema_12'] = EMAIndicator(close=close, window=12).ema_indicator()
            df['ema_26'] = EMAIndicator(close=close, window=26).ema_indicator()
            
            # MACD (Moving Average Convergence Divergence)
            macd = MACD(close=close)
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_diff'] = macd.macd_diff()
            
            # === MOMENTUM INDICATORS ===
            
            # RSI (Relative Strength Index)
            df['rsi'] = RSIIndicator(close=close, window=14).rsi()
            
            # Stochastic Oscillator
            if len(df) >= 14:
                stoch = StochasticOscillator(
                    high=close,  # Using close as proxy for high
                    low=close,   # Using close as proxy for low
                    close=close,
                    window=14,
                    smooth_window=3
                )
                df['stoch_k'] = stoch.stoch()
                df['stoch_d'] = stoch.stoch_signal()
            
            # === VOLATILITY INDICATORS ===
            
            # Bollinger Bands
            bollinger = BollingerBands(close=close, window=20, window_dev=2)
            df['bb_high'] = bollinger.bollinger_hband()
            df['bb_mid'] = bollinger.bollinger_mavg()
            df['bb_low'] = bollinger.bollinger_lband()
            df['bb_width'] = bollinger.bollinger_wband()
            
            # === VOLUME INDICATORS ===
            
            if volume.sum() > 0:  # Only if we have volume data
                df['obv'] = OnBalanceVolumeIndicator(close=close, volume=volume).on_balance_volume()
            
            # === CUSTOM INDICATORS ===
            
            # Price change percentage
            df['price_change_pct'] = close.pct_change() * 100
            
            # Volatility (standard deviation of returns)
            df['volatility'] = df['price_change_pct'].rolling(window=14).std()
            
            # Trend strength (difference between price and SMA30)
            df['trend_strength'] = ((close - df['sma_30']) / df['sma_30']) * 100
            
            logger.info(f"Calculated technical indicators successfully")
            return df
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return df
    
    def analyze_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze technical indicators and generate trading signals
        
        Args:
            df: DataFrame with technical indicators
            
        Returns:
            Dictionary with analysis results and signals
        """
        try:
            if df is None or df.empty:
                return {"error": "No data available"}
            
            # Get latest values (most recent row)
            latest = df.iloc[-1]
            previous = df.iloc[-2] if len(df) > 1 else latest
            
            analysis = {
                "current_price": float(latest['price']),
                "price_change_24h": float(latest['price_change_pct']) if 'price_change_pct' in latest else 0,
                
                # Trend Analysis
                "trend": {
                    "sma_7": float(latest['sma_7']) if not pd.isna(latest.get('sma_7')) else 0,
                    "sma_14": float(latest['sma_14']) if not pd.isna(latest.get('sma_14')) else 0,
                    "sma_30": float(latest['sma_30']) if not pd.isna(latest.get('sma_30')) else 0,
                    "ema_12": float(latest['ema_12']) if not pd.isna(latest.get('ema_12')) else 0,
                    "ema_26": float(latest['ema_26']) if not pd.isna(latest.get('ema_26')) else 0,
                    "trend_strength": float(latest['trend_strength']) if not pd.isna(latest.get('trend_strength')) else 0,
                    "direction": "bullish" if latest['price'] > latest.get('sma_30', latest['price']) else "bearish"
                },
                
                # Momentum Analysis
                "momentum": {
                    "rsi": float(latest['rsi']) if not pd.isna(latest.get('rsi')) else 50,
                    "rsi_signal": self._get_rsi_signal(latest.get('rsi', 50)),
                    "macd": float(latest['macd']) if not pd.isna(latest.get('macd')) else 0,
                    "macd_signal": float(latest['macd_signal']) if not pd.isna(latest.get('macd_signal')) else 0,
                    "macd_histogram": float(latest['macd_diff']) if not pd.isna(latest.get('macd_diff')) else 0,
                    "macd_crossover": self._check_macd_crossover(latest, previous)
                },
                
                # Volatility Analysis
                "volatility": {
                    "current": float(latest['volatility']) if not pd.isna(latest.get('volatility')) else 0,
                    "bb_upper": float(latest['bb_high']) if not pd.isna(latest.get('bb_high')) else 0,
                    "bb_middle": float(latest['bb_mid']) if not pd.isna(latest.get('bb_mid')) else 0,
                    "bb_lower": float(latest['bb_low']) if not pd.isna(latest.get('bb_low')) else 0,
                    "bb_position": self._get_bb_position(latest),
                    "risk_level": self._get_risk_level(latest.get('volatility', 0))
                },
                
                # Volume Analysis
                "volume": {
                    "current": float(latest['volume']),
                    "trend": "increasing" if latest['volume'] > df['volume'].tail(10).mean() else "decreasing"
                },
                
                # Overall Signal
                "signals": self._generate_signals(latest, previous, df)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing indicators: {e}")
            return {"error": str(e)}
    
    def _get_rsi_signal(self, rsi: float) -> str:
        """Interpret RSI value"""
        if pd.isna(rsi):
            return "neutral"
        if rsi >= 70:
            return "overbought"
        elif rsi <= 30:
            return "oversold"
        elif rsi >= 60:
            return "bullish"
        elif rsi <= 40:
            return "bearish"
        return "neutral"
    
    def _check_macd_crossover(self, latest: pd.Series, previous: pd.Series) -> str:
        """Check for MACD signal line crossover"""
        try:
            macd_curr = latest.get('macd', 0)
            signal_curr = latest.get('macd_signal', 0)
            macd_prev = previous.get('macd', 0)
            signal_prev = previous.get('macd_signal', 0)
            
            if pd.isna(macd_curr) or pd.isna(signal_curr):
                return "none"
            
            # Bullish crossover: MACD crosses above signal
            if macd_prev < signal_prev and macd_curr > signal_curr:
                return "bullish"
            # Bearish crossover: MACD crosses below signal
            elif macd_prev > signal_prev and macd_curr < signal_curr:
                return "bearish"
            return "none"
        except:
            return "none"
    
    def _get_bb_position(self, latest: pd.Series) -> str:
        """Determine price position relative to Bollinger Bands"""
        try:
            price = latest['price']
            bb_high = latest.get('bb_high', 0)
            bb_low = latest.get('bb_low', 0)
            bb_mid = latest.get('bb_mid', 0)
            
            if pd.isna(bb_high) or pd.isna(bb_low):
                return "unknown"
            
            if price >= bb_high:
                return "above_upper_band"
            elif price <= bb_low:
                return "below_lower_band"
            elif price > bb_mid:
                return "upper_half"
            else:
                return "lower_half"
        except:
            return "unknown"
    
    def _get_risk_level(self, volatility: float) -> str:
        """Determine risk level based on volatility"""
        if pd.isna(volatility):
            return "unknown"
        if volatility > 5:
            return "very_high"
        elif volatility > 3:
            return "high"
        elif volatility > 2:
            return "moderate"
        elif volatility > 1:
            return "low"
        return "very_low"
    
    def _generate_signals(self, latest: pd.Series, previous: pd.Series, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate trading signals based on multiple indicators"""
        signals = {
            "buy_signals": [],
            "sell_signals": [],
            "overall_score": 0  # Range: -100 (strong sell) to +100 (strong buy)
        }
        
        score = 0
        
        # RSI Signals
        rsi = latest.get('rsi', 50)
        if not pd.isna(rsi):
            if rsi <= 30:
                signals["buy_signals"].append("RSI oversold (<30)")
                score += 15
            elif rsi >= 70:
                signals["sell_signals"].append("RSI overbought (>70)")
                score -= 15
            elif rsi < 40:
                score += 5
            elif rsi > 60:
                score -= 5
        
        # MACD Signals
        macd_crossover = self._check_macd_crossover(latest, previous)
        if macd_crossover == "bullish":
            signals["buy_signals"].append("MACD bullish crossover")
            score += 20
        elif macd_crossover == "bearish":
            signals["sell_signals"].append("MACD bearish crossover")
            score -= 20
        
        # Trend Signals (Moving Averages)
        price = latest['price']
        sma_30 = latest.get('sma_30', price)
        if not pd.isna(sma_30):
            if price > sma_30:
                signals["buy_signals"].append("Price above SMA30")
                score += 10
            else:
                signals["sell_signals"].append("Price below SMA30")
                score -= 10
        
        # Bollinger Bands Signals
        bb_position = self._get_bb_position(latest)
        if bb_position == "below_lower_band":
            signals["buy_signals"].append("Price below lower Bollinger Band")
            score += 15
        elif bb_position == "above_upper_band":
            signals["sell_signals"].append("Price above upper Bollinger Band")
            score -= 15
        
        # Volume Confirmation
        if latest['volume'] > df['volume'].tail(20).mean() * 1.5:
            signals["buy_signals"].append("High volume confirming move")
            score += 5
        
        # Golden Cross / Death Cross (EMA 12 vs EMA 26)
        ema_12 = latest.get('ema_12', 0)
        ema_26 = latest.get('ema_26', 0)
        ema_12_prev = previous.get('ema_12', 0)
        ema_26_prev = previous.get('ema_26', 0)
        
        if not pd.isna(ema_12) and not pd.isna(ema_26):
            if ema_12_prev < ema_26_prev and ema_12 > ema_26:
                signals["buy_signals"].append("Golden Cross (EMA12 > EMA26)")
                score += 25
            elif ema_12_prev > ema_26_prev and ema_12 < ema_26:
                signals["sell_signals"].append("Death Cross (EMA12 < EMA26)")
                score -= 25
        
        signals["overall_score"] = max(-100, min(100, score))
        
        return signals
    
    def get_simple_price(self, coin_id: str, vs_currencies: str = "usd") -> Optional[Dict[str, Any]]:
        """
        Fetch simple price data from CoinGecko API
        Uses the simple/price endpoint: https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd
        
        Args:
            coin_id: CoinGecko coin ID (e.g., "bitcoin", "ethereum")
            vs_currencies: Comma-separated list of vs currencies (default: "usd")
            
        Returns:
            Dictionary with price data or None if error
        """
        try:
            # Rate limiting
            time_since_last = time.time() - self.last_request_time
            if time_since_last < self.min_request_interval:
                sleep_time = self.min_request_interval - time_since_last
                time.sleep(sleep_time)
            
            url = f"{self.BASE_URL}/simple/price"
            params = {
                'ids': coin_id.lower(),
                'vs_currencies': vs_currencies,
                'include_market_cap': 'true',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true',
                'include_last_updated_at': 'true'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            self.last_request_time = time.time()
            
            response.raise_for_status()
            data = response.json()
            
            logger.debug(f"CoinGecko API response for {coin_id}: {data}")
            
            # Check if coin exists in response
            coin_id_lower = coin_id.lower()
            if not data or coin_id_lower not in data:
                logger.warning(f"Coin {coin_id_lower} not found in CoinGecko response. Available coins: {list(data.keys()) if data else 'No data'}")
                return None
            
            coin_data = data[coin_id_lower]
            
            # Format the response
            formatted_data = {
                "coin_id": coin_id_lower,
                "symbol": coin_id.upper(),  # Will be updated if we get more info
                "price_usd": coin_data.get(vs_currencies, 0),
                "market_cap_usd": coin_data.get(f"{vs_currencies}_market_cap", 0),
                "volume_24h_usd": coin_data.get(f"{vs_currencies}_24h_vol", 0),
                "change_24h_percent": coin_data.get(f"{vs_currencies}_24h_change", 0),
                "last_updated": coin_data.get("last_updated_at", int(time.time()))
            }
            
            # Validate that we got at least a price (0 could be valid for some coins, but very unlikely)
            if formatted_data["price_usd"] == 0:
                logger.warning(f"No price data (price=0) returned for {coin_id_lower}, but continuing anyway")
                # Don't return None, as 0 might be a valid price for some edge cases
            
            logger.info(f"✅ Fetched simple price data for {coin_id}: ${formatted_data['price_usd']}")
            return formatted_data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning(f"⚠️ Rate limit hit for {coin_id}")
            elif e.response.status_code == 404:
                logger.warning(f"Coin {coin_id} not found (404) on CoinGecko")
            else:
                logger.error(f"HTTP error {e.response.status_code} fetching simple price from CoinGecko for {coin_id}: {e}")
                try:
                    error_body = e.response.text[:200]
                    logger.error(f"Error response body: {error_body}")
                except:
                    pass
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching simple price from CoinGecko for {coin_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_simple_price for {coin_id}: {type(e).__name__}: {e}", exc_info=True)
            return None
    
    def search_coins(self, query: str, limit: int = 20) -> List[Dict[str, str]]:
        """
        Search for coins by name or symbol
        Uses the search endpoint to find matching coins
        
        Args:
            query: Search query (coin name or symbol)
            limit: Maximum number of results
            
        Returns:
            List of dictionaries with coin info {id, name, symbol}
        """
        try:
            # Rate limiting
            time_since_last = time.time() - self.last_request_time
            if time_since_last < self.min_request_interval:
                sleep_time = self.min_request_interval - time_since_last
                time.sleep(sleep_time)
            
            url = f"{self.BASE_URL}/search"
            params = {'query': query}
            
            response = self.session.get(url, params=params, timeout=15)
            self.last_request_time = time.time()
            
            response.raise_for_status()
            data = response.json()
            
            coins = []
            for coin in data.get("coins", [])[:limit]:
                coins.append({
                    "id": coin.get("id", ""),
                    "name": coin.get("name", ""),
                    "symbol": coin.get("symbol", "").upper()
                })
            
            logger.info(f"Found {len(coins)} coins matching '{query}'")
            return coins
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning(f"⚠️ Rate limit hit for search")
            logger.error(f"HTTP error searching coins on CoinGecko: {e}")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching coins on CoinGecko: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in search_coins: {e}")
            return []


# Global instance
coingecko_service = CoinGeckoService()
