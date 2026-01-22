"""
Market Data Router - Real-time cryptocurrency prices
Provides endpoints to fetch current market prices from CoinGecko API
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from services.market_data_service import market_data_service

router = APIRouter()

@router.get("/prices")
async def get_all_prices() -> Dict[str, Any]:
    """
    Get all current cryptocurrency prices
    
    Returns:
        Dictionary containing prices for BTC, ETH, and USDT with metadata
    """
    try:
        prices_data = market_data_service.get_all_prices()
        return prices_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch prices: {str(e)}")

@router.get("/prices/{symbol}")
async def get_price(symbol: str) -> Dict[str, Any]:
    """
    Get current price for a specific cryptocurrency
    
    Args:
        symbol: Cryptocurrency symbol (e.g., "BTC-USD", "ETH-USD")
        
    Returns:
        Price data for the requested symbol
    """
    try:
        all_prices = market_data_service.get_all_prices()
        
        if symbol not in all_prices["prices"]:
            raise HTTPException(
                status_code=404, 
                detail=f"Symbol {symbol} not found. Available: {list(all_prices['prices'].keys())}"
            )
        
        return all_prices["prices"][symbol]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch price: {str(e)}")

@router.get("/convert")
async def convert_currency(
    from_currency: str,
    to_currency: str = "USD",
    amount: float = 1.0
) -> Dict[str, Any]:
    """
    Convert between cryptocurrencies and fiat
    
    Args:
        from_currency: Source currency (e.g., "BTC", "ETH")
        to_currency: Target currency (default: "USD")
        amount: Amount to convert (default: 1.0)
        
    Returns:
        Conversion result with rate and converted amount
    """
    try:
        rate = market_data_service.get_conversion_rate(from_currency, to_currency)
        
        if rate == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Conversion rate not available for {from_currency} to {to_currency}"
            )
        
        converted_amount = amount * rate
        
        return {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "amount": amount,
            "rate": rate,
            "converted_amount": converted_amount,
            "timestamp": market_data_service.last_update.isoformat() if market_data_service.last_update else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")
