"""
Service for fetching live trading data for the chart.

Originally this used Finnhub, but your Finnhub key is returning 403 (forbidden),
so we now use Binance's free public /klines endpoint instead. The rest of the
app (router, frontend) continues to work the same way.
"""
import requests
from sqlalchemy.orm import Session
from schemas import OHLCVData

BINANCE_API_URL = "https://api.binance.com/api/v3/klines"


def _map_symbol_to_binance(symbol: str) -> str:
    """Maps 'BTC-USD' → 'BTCUSDT', 'ETH-USD' → 'ETHUSDT', etc."""
    parts = symbol.upper().split("-")
    if len(parts) != 2:
        return f"{parts[0]}USDT"
    
    base, quote = parts
    if quote == "USD":
        quote = "USDT"
    return f"{base}{quote}"
    

def _map_timeframe_to_binance(timeframe: str) -> str:
    """Maps app timeframes to Binance intervals."""
    timeframe_map = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "6h": "6h",
        "12h": "12h",
        "1d": "1d",
    }
    return timeframe_map.get(timeframe, "1h")


def get_ohlcv_data(db: Session, symbol: str, timeframe: str) -> list[OHLCVData]:
    """
    Fetch OHLCV data from Binance public API.

    Note: The 'db' session parameter is kept for signature consistency
    with the router, but is not used.
    """
    binance_symbol = _map_symbol_to_binance(symbol)
    interval = _map_timeframe_to_binance(timeframe)
    
    params = {
        "symbol": binance_symbol,
        "interval": interval,
        "limit": 500,  # last 500 candles
    }
    
    try:
        res = requests.get(BINANCE_API_URL, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        
        if not isinstance(data, list) or not data:
            print(
                f"Binance returned no data for symbol={binance_symbol}, "
                f"interval={interval}, raw={data}"
            )
            return []
            
        ohlcv_data: list[OHLCVData] = []
        for kline in data:
            # Binance kline format:
            # [0] open time (ms), [1] open, [2] high, [3] low, [4] close,
            # [5] volume, [6] close time, ...
            ohlcv_data.append(
                OHLCVData(
                    time=int(kline[0] // 1000),  # seconds since epoch
                    open=float(kline[1]),
                    high=float(kline[2]),
                    low=float(kline[3]),
                    close=float(kline[4]),
                    volume=float(kline[5]),
                )
            )

        return ohlcv_data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Binance: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred in get_ohlcv_data: {e}")
        return []
